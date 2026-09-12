"""审计副本与已完成 Outbox 归档；正式提交、判定、事件和最终榜不删除。"""
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from models import db_models as m


def _write_once(directory, name, data):
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError('archive directory must not be a symlink')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / name
    content = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str).encode()
    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.read_bytes() != content:
            raise ValueError('archive conflict: existing record differs')
        with target.open('rb') as stream:
            os.fsync(stream.fileno())
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return hashlib.sha256(content).hexdigest()
    temporary = directory / ('.pending-'+uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            os.chmod(temporary, 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if target.is_symlink() or target.read_bytes() != content:
                raise ValueError('archive conflict: concurrent record differs') from None
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(content).hexdigest()


def export_audit(directory, after=0, limit=500):
    if not 1 <= limit <= 1000 or after < 0:
        raise ValueError('invalid export range')
    rows = m.ContestAudit.select().where(m.ContestAudit.id > after).order_by(m.ContestAudit.id).limit(limit)
    count, cursor = 0, after
    for row in rows:
        _write_once(directory, f'audit-{row.id}.json', row.to_dict())
        count, cursor = count+1, row.id
    return {'exported': count, 'next_cursor': cursor}


def archive_outboxes(directory, before, limit=500, prune=False):
    from datetime import datetime, timedelta
    if not 1 <= limit <= 1000 or before > datetime.now()-timedelta(days=7):
        raise ValueError('archive requires at least seven days retention and a bounded batch')
    count, deleted = 0, 0
    for model, submission in ((m.ContestJudgeOutbox, m.ContestSubmission), (m.SubmissionOutbox, m.Submission)):
        if count >= limit:
            break
        query = (model.select(model).join(submission).where(model.state == 'DISPATCHED',
            model.dispatched_at < before, model.updated_at < before,
            submission.status.in_(['AC', 'WA', 'CE', 'TLE', 'MLE', 'OLE', 'RE', 'Partial', 'SIGSEGV', 'SIGSYS'])))
        if submission == m.ContestSubmission:
            # 候选及仍被待审核复判引用的原始提交都保留恢复记录。
            pending = m.ContestSubmission.alias()
            active = pending.select(pending.rejudge_of).join(m.RejudgeBatch,
                on=(pending.rejudge_batch == m.RejudgeBatch.id)).where(m.RejudgeBatch.state == 'PENDING',
                    pending.rejudge_of.is_null(False))
            query = query.where(submission.rejudge_batch.is_null(), ~submission.id.in_(active))
        ids = [r.id for r in query.order_by(model.id).limit(limit-count)]
        for row_id in ids:
            with m.get_database().atomic():
                row = model.get_by_id(row_id)
                if submission == m.ContestSubmission:
                    from services.contest_lifecycle import lock_contest
                    lock_contest(row.submission.contest_id)
                current = query.where(model.id == row_id)
                if m.get_database().__class__.__name__ != 'SqliteDatabase':
                    current = current.for_update()
                row = current.first()
                if row is None:
                    continue
                _write_once(directory, f'{model._meta.table_name}-{row.id}.json', row.to_dict())
                count += 1
                if prune:
                    deleted += model.delete().where(model.id == row.id).execute()
    return {'archived': count, 'pruned': deleted}
