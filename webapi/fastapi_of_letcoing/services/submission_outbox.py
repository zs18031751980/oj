"""普通提交与比赛相同：先落库，再可重试投递，Redis 只承担运输。"""
from datetime import datetime

from models.db_models import SubmissionOutbox


def dispatch_regular_entry(redis, outbox):
    if outbox.state == 'DISPATCHED':
        return True
    submission = outbox.submission
    try:
        sent = redis.enqueue_with_state(f'submission:{submission.id}',
            {'id': submission.id, 'user_id': submission.user_id, 'status': submission.status},
            3600, 'judge_queue', {'submission_id': submission.id, 'job_id': submission.job_id})
        if sent:
            SubmissionOutbox.update(state='DISPATCHED', dispatched_at=datetime.now(),
                dispatch_attempts=SubmissionOutbox.dispatch_attempts + 1, last_error=None).where(
                SubmissionOutbox.id == outbox.id).execute()
        return bool(sent)
    except Exception:
        # 即使 Redis 已接收而确认落库失败，job_id 去重仍保证再次投递安全。
        return False


def dispatch_pending_regular(redis, limit=50):
    rows = SubmissionOutbox.select().where(SubmissionOutbox.state == 'PENDING').order_by(
        SubmissionOutbox.created_at).limit(limit)
    return sum(bool(dispatch_regular_entry(redis, row)) for row in rows)
