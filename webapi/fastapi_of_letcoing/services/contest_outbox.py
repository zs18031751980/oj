"""比赛判题任务的 Transactional Outbox。

提交事实和待投递记录在同一数据库事务落地；Redis 短暂故障时 Worker 会持续补投，
而不是把一份有效提交永久标为失败。
"""

from datetime import datetime, timezone

from models.db_models import ContestJudgeOutbox, ContestSubmission


def _task_for(submission: ContestSubmission) -> dict:
    return {
        'submission_id': submission.id,
        'job_id': submission.job_id,
        'attempt_id': submission.attempt_id,
        'contest_id': submission.contest_id,
        'problem_id': submission.contest_problem_id,
        'user_id': submission.user_id,
        'language': submission.language,
        'submitted_at': (submission.received_at or submission.submitted_at).isoformat(),
    }


def dispatch_outbox_entry(redis_service, outbox: ContestJudgeOutbox) -> bool:
    """尝试投递一条待发送记录；失败时保留 PENDING 供后续补偿。"""
    if outbox.state == 'DISPATCHED':
        return True
    submission = outbox.submission
    try:
        delivered = redis_service.enqueue_with_state(
            f'contest_submission:{submission.id}',
            {
                'problem_id': submission.contest_problem_id,
                'contest_id': submission.contest_id,
                'user_id': submission.user_id,
                'status': submission.status,
                'attempt_id': submission.attempt_id,
                'job_id': submission.job_id,
                'passed': 0,
                'total': 0,
                'details': [],
            },
            3600,
            'contest_judge_queue',
            _task_for(submission),
        )
    except Exception as exc:
        delivered = False
        outbox.last_error = str(exc)[:1000]
    outbox.dispatch_attempts += 1
    if delivered:
        outbox.state = 'DISPATCHED'
        outbox.dispatched_at = datetime.now(timezone.utc).replace(tzinfo=None)
        outbox.last_error = None
    else:
        outbox.state = 'PENDING'
        outbox.last_error = outbox.last_error or 'Redis 判题队列不可用'
    outbox.save()
    return bool(delivered)


def dispatch_pending_outbox(redis_service, limit: int = 50) -> int:
    """由任一 Worker 周期性补投；重复调用是安全的。"""
    pending = list(
        ContestJudgeOutbox.select()
        .where(ContestJudgeOutbox.state == 'PENDING')
        .order_by(ContestJudgeOutbox.created_at)
        .limit(limit)
    )
    return sum(1 for entry in pending if dispatch_outbox_entry(redis_service, entry))
