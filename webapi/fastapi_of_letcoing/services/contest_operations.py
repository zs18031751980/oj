"""比赛控制、版本化复判、队伍和裁判答疑。所有写入保留审计或事件。"""
import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from models import db_models as m
from services.contest_lifecycle import lock_contest
from services.contest_packages import canonical, publish_package


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=8)


def allowed(contest_id, actor, capability):
    if not actor:
        return False
    if actor.role == 'manager':
        return True
    role = m.ContestRole.get_or_none(m.ContestRole.contest == contest_id, m.ContestRole.user == actor.id)
    grants = {'director': {'control', 'jury', 'rejudge', 'package'},
              'jury': {'jury', 'rejudge'}, 'setter': {'package'}, 'operator': {'health'}}
    return bool(role and capability in grants.get(role.role, set()))


def require(contest_id, actor, capability):
    if not allowed(contest_id, actor, capability):
        raise PermissionError('没有此比赛的操作权限')


def text_field(value, limit=4096):
    if not isinstance(value, str) or not value.strip() or len(value.encode()) > limit:
        raise ValueError('文本为空或超过长度限制')
    return value.strip()


def audit(contest_id, actor, action, reason, payload=None):
    return m.ContestAudit.create(contest=contest_id, actor=actor, action=action,
        reason=text_field(reason), payload=canonical(payload or {}))


def emit(contest_id, kind, payload, audience='jury', recipient_id=None):
    return m.ContestEvent.create(contest=contest_id, kind=kind, payload=canonical(payload),
        audience=audience, recipient_id=recipient_id)


def thaw_contest(contest_id, actor, reason):
    require(contest_id, actor, 'control')
    with m.get_database().atomic():
        contest = lock_contest(contest_id)
        if contest.lifecycle_state in {'DRAFT', 'READY', 'CANCELLED'}:
            raise ValueError('比赛当前状态不能解封')
        if not contest.thawed_at:
            contest.thawed_at = now()
            contest.save(only=[m.Contest.thawed_at])
            audit(contest_id, actor, 'thaw', reason)
            emit(contest_id, 'state', {'thawed': True}, 'public')
    return contest


def create_rejudge(contest_id, actor, submission_ids, reason):
    require(contest_id, actor, 'rejudge')
    if not isinstance(submission_ids, list) or not submission_ids or len(submission_ids) > 500:
        raise ValueError('复判每批需要 1 至 500 条提交')
    if any(type(value) is not int for value in submission_ids):
        raise ValueError('提交编号无效')
    reason = text_field(reason)
    with m.get_database().atomic():
        contest = lock_contest(contest_id)
        if contest.lifecycle_state in {'DRAFT', 'READY', 'CANCELLED'}:
            raise ValueError('当前比赛不可复判')
        if contest.lifecycle_state == 'FINALIZED':
            require(contest_id, actor, 'control')
        originals = list(m.ContestSubmission.select().where(m.ContestSubmission.contest == contest_id,
            m.ContestSubmission.id.in_(set(submission_ids)), m.ContestSubmission.contest_eligible == True))
        if len(originals) != len(set(submission_ids)):
            raise ValueError('提交不存在或不属于正式比赛')
        from services.judge_state import TERMINAL_STATES
        if any(s.status not in TERMINAL_STATES for s in originals):
            raise ValueError('仍在判题的提交不能复判')
        batch = m.RejudgeBatch.create(contest=contest, actor=actor, reason=reason)
        for original in originals:
            problem = original.contest_problem
            digest = problem.package_digest or original.package_digest
            if not digest:
                digest = publish_package(problem, actor.id).digest
            job = uuid4().hex
            candidate = m.ContestSubmission.create(contest=contest, user=original.user_id,
                team=original.team_id, contest_problem=problem, problem_index=original.problem_index,
                code=original.code, language=original.language, received_at=original.received_at,
                submitted_at=original.submitted_at, contest_eligible=False, status='Pending',
                job_id=job, judge_submission_id=job, queued_at=now(),
                package_digest=digest, rejudge_of=original.id, rejudge_batch=batch,
                rejudge_base_attempt=original.attempt_id)
            m.ContestJudgeOutbox.create(submission=candidate)
        audit(contest_id, actor, 'rejudge.create', reason, {'batch_id': batch.id, 'count': len(originals)})
        return batch


def archive_judgement(submission, batch_id=None):
    values = {key: getattr(submission, key) for key in (
        'status', 'verdict', 'passed', 'total', 'score', 'cpu_time', 'wall_time', 'memory',
        'output_size', 'exit_code', 'signal', 'testcase_results', 'error_message', 'worker_id')}
    return m.Judgement.create(submission=submission.rejudge_of or submission.id,
        attempt_id=submission.attempt_id, status=submission.status, payload=canonical(values),
        package_digest=submission.package_digest, batch_id=batch_id)


def apply_rejudge(batch_id, actor, reason, cancel=False):
    batch = m.RejudgeBatch.get_by_id(batch_id)
    require(batch.contest_id, actor, 'rejudge')
    with m.get_database().atomic():
        contest = lock_contest(batch.contest_id)
        batch = m.RejudgeBatch.get_by_id(batch_id)
        if batch.state != 'PENDING':
            raise ValueError('复判批次已处理')
        if contest.lifecycle_state == 'CANCELLED' and not cancel:
            raise ValueError('已取消比赛不能应用复判')
        if contest.lifecycle_state == 'FINALIZED':
            require(contest.id, actor, 'control')
        candidates = list(m.ContestSubmission.select().where(m.ContestSubmission.rejudge_batch == batch))
        valid = {'AC', 'WA', 'CE', 'TLE', 'MLE', 'OLE', 'RE', 'SIGSEGV', 'SIGSYS', 'Partial'}
        if not cancel and any(c.status not in valid for c in candidates):
            raise ValueError('候选结果未完成或包含系统错误')
        if not cancel:
            for candidate in candidates:
                original = m.ContestSubmission.get_by_id(candidate.rejudge_of)
                if original.attempt_id != candidate.rejudge_base_attempt:
                    raise ValueError('原始判定已经变化，请重新创建复判批次')
                archive_judgement(original)
                fields = ('status', 'verdict', 'passed', 'total', 'score', 'cpu_time', 'wall_time',
                          'memory', 'output_size', 'exit_code', 'signal', 'testcase_results', 'error_message')
                for field in fields:
                    setattr(original, field, getattr(candidate, field))
                original.package_digest = candidate.package_digest
                original.attempt_id += 1
                original.save()
                archive_judgement(original, batch.id)
                emit(contest.id, 'judgement', {'submission_id': original.id, 'status': original.status})
            m.Contest.update(scoreboard_requested_version=m.Contest.scoreboard_requested_version+1).where(m.Contest.id == contest.id).execute()
        if cancel:
            m.ContestSubmission.update(status='Cancelled', verdict='Cancelled',
                attempt_id=m.ContestSubmission.attempt_id+1).where(m.ContestSubmission.rejudge_batch == batch).execute()
        batch.state = 'CANCELLED' if cancel else 'APPLIED'
        if not cancel and contest.lifecycle_state == 'FINALIZED':
            from controllers.contest_rankings_controller import _compute_rankings, _save_public_snapshot
            contest = m.Contest.get_by_id(contest.id)
            contest.final_revision += 1
            m.ContestScoreboardSnapshot.create(contest=contest, snapshot_kind=f'FINAL:{contest.final_revision}',
                payload=json.dumps(_compute_rankings(contest.id), ensure_ascii=False),
                scoreboard_version=contest.scoreboard_requested_version)
            if contest.freeze_time and not contest.thawed_at:
                _save_public_snapshot(contest, _compute_rankings(contest.id, cutoff_at=contest.freeze_time))
            contest.save(only=[m.Contest.final_revision])
        batch.reviewed_by = actor.id
        batch.save()
        audit(contest.id, actor, 'rejudge.'+batch.state.lower(), reason, {'batch_id': batch.id})
        return batch


def entry_user(contest_id, user_id):
    member = m.ContestTeamMember.get_or_none(m.ContestTeamMember.contest == contest_id,
        m.ContestTeamMember.user == user_id)
    return member.team.captain_id if member else user_id


def create_team(contest_id, actor, name, member_ids):
    require(contest_id, actor, 'control')
    if not isinstance(member_ids, list) or not 1 <= len(member_ids) <= 3 or len(set(member_ids)) != len(member_ids):
        raise ValueError('队伍需要 1 至 3 名不同成员')
    if any(type(value) is not int for value in member_ids):
        raise ValueError('成员编号无效')
    with m.get_database().atomic():
        contest = lock_contest(contest_id)
        if contest.start_time and now() >= contest.start_time:
            raise ValueError('开赛后不能变更队伍')
        if contest.lifecycle_state in {'CANCELLED', 'FINALIZED'}:
            raise ValueError('比赛不接受队伍变更')
        if m.User.select().where(m.User.id.in_(member_ids)).count() != len(member_ids):
            raise ValueError('成员不存在')
        team = m.ContestTeam.create(contest=contest, captain=member_ids[0], name=text_field(name, 120))
        for user_id in member_ids:
            m.ContestTeamMember.create(contest=contest, team=team, user=user_id)
            m.ContestParticipant.get_or_create(contest=contest, user=user_id)
        audit(contest_id, actor, 'team.create', '组建比赛队伍', {'team_id': team.id, 'member_ids': member_ids})
        m.Contest.update(scoreboard_requested_version=m.Contest.scoreboard_requested_version+1).where(m.Contest.id == contest_id).execute()
        return team


def participant(contest_id, actor):
    if not actor or not m.ContestParticipant.select().where(m.ContestParticipant.contest == contest_id,
            m.ContestParticipant.user == actor.id).exists():
        raise PermissionError('需要比赛参赛身份')


def ask_clarification(contest_id, actor, question):
    participant(contest_id, actor)
    with m.get_database().atomic():
        contest = lock_contest(contest_id)
        if contest.lifecycle_state in {'DRAFT', 'READY', 'CANCELLED', 'FINALIZED'}:
            raise ValueError('比赛暂不接受提问')
        return m.ContestClarification.create(contest=contest_id,
            author=entry_user(contest_id, actor.id), question=text_field(question))


def answer_clarification(question_id, actor, answer, broadcast=False):
    question = m.ContestClarification.get_by_id(question_id)
    require(question.contest_id, actor, 'jury')
    with m.get_database().atomic():
        lock_contest(question.contest_id)
        question = m.ContestClarification.get_by_id(question_id)
        if question.claimed_by and question.claimed_by != actor.id:
            raise ValueError('问题由另一裁判认领')
        question.answer = text_field(answer)
        question.broadcast = bool(broadcast)
        question.answered_by = actor.id
        question.save()
        emit(question.contest_id, 'clarification', {'id': question.id, 'question': question.question,
            'answer': question.answer}, 'public' if broadcast else 'entry', question.author_id)
        audit(question.contest_id, actor, 'clarification.answer', '裁判答疑', {'id': question.id, 'broadcast': broadcast})
        return question


def events_for(contest_id, actor, cursor, limit=100):
    contest = m.Contest.get_by_id(contest_id)
    jury = allowed(contest_id, actor, 'jury')
    if not jury and (not contest.is_public or contest.lifecycle_state in {'DRAFT', 'READY', 'CANCELLED'}):
        participant(contest_id, actor)
    rows = m.ContestEvent.select().where(m.ContestEvent.contest == contest_id, m.ContestEvent.id > max(0, int(cursor)))
    if not jury:
        visible = m.ContestEvent.audience == 'public'
        if actor:
            visible |= ((m.ContestEvent.audience == 'entry') & (m.ContestEvent.recipient_id == entry_user(contest_id, actor.id)))
        rows = rows.where(visible)
    return [{'id': e.id, 'type': e.kind, 'data': json.loads(e.payload)} for e in rows.order_by(m.ContestEvent.id).limit(min(max(1, limit), 200))]


def override_judgement(contest_id, submission_id, actor, verdict, reason, password):
    require(contest_id, actor, 'control')
    from werkzeug.security import check_password_hash
    if not isinstance(password, str) or not actor.password_hash or not check_password_hash(actor.password_hash, password):
        raise PermissionError('人工改判需要本地裁判账号重新认证')
    if verdict not in {'AC', 'WA', 'CE', 'TLE', 'MLE', 'OLE', 'RE'}:
        raise ValueError('无效的人工判定')
    with m.get_database().atomic():
        contest = lock_contest(contest_id)
        if contest.lifecycle_state in {'DRAFT', 'READY', 'CANCELLED', 'FINALIZED'}:
            raise ValueError('当前比赛状态禁止改判')
        submission = m.ContestSubmission.get(m.ContestSubmission.id == submission_id,
            m.ContestSubmission.contest == contest_id, m.ContestSubmission.contest_eligible == True)
        from services.judge_state import TERMINAL_STATES
        if submission.status not in TERMINAL_STATES:
            raise ValueError('处理中提交需要等待结束后改判')
        archive_judgement(submission)
        previous = submission.status
        submission.status = submission.verdict = verdict
        submission.score = (submission.contest_problem.score if verdict == 'AC' else 0) if 'oi' in (contest.contest_type or '').lower() else 0
        submission.passed = submission.total if verdict == 'AC' else 0
        submission.attempt_id += 1
        submission.error_message = None
        submission.testcase_results = None
        submission.save()
        archive_judgement(submission)
        audit(contest_id, actor, 'judgement.override', reason,
            {'submission_id': submission_id, 'before': previous, 'after': verdict})
        emit(contest_id, 'judgement', {'submission_id': submission_id, 'status': verdict})
        m.Contest.update(scoreboard_requested_version=m.Contest.scoreboard_requested_version+1).where(m.Contest.id == contest_id).execute()
        return submission


def testcase_details(submission):
    if submission.testcase_results:
        return json.loads(submission.testcase_results)
    record = m.Judgement.select(m.Judgement.payload).where(m.Judgement.submission == submission.id,
        m.Judgement.batch_id.is_null()).order_by(m.Judgement.id.desc()).first()
    if not record:
        return []
    return json.loads(json.loads(record.payload).get('testcase_results') or '[]')
