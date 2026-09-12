"""有界查询的比赛运行指标，不输出用户、源码或题目秘密。"""
from datetime import timedelta
from peewee import JOIN, fn

from models import db_models as m
from services.contest_operations import now


def competition_health(contest_id=None):
    scope = (m.ContestSubmission.contest == contest_id) if contest_id is not None else True
    board_scope = (m.Contest.id == contest_id) if contest_id is not None else True
    current = now()
    waiting, oldest = (m.ContestSubmission.select(fn.COUNT(m.ContestSubmission.id),
        fn.MIN(m.ContestSubmission.received_at)).where(m.ContestSubmission.contest_eligible == True, scope,
            m.ContestSubmission.status.in_(['Pending', 'Queued'])).tuples().get())
    snapshot = m.ContestScoreboardSnapshot
    lag = (m.Contest.select(fn.MAX(m.Contest.scoreboard_requested_version - fn.COALESCE(snapshot.scoreboard_version, 0)))
        .join(snapshot, JOIN.LEFT_OUTER, on=((snapshot.contest == m.Contest.id) & (snapshot.snapshot_kind == 'LIVE')))
        .where(board_scope, ~m.Contest.lifecycle_state.in_(['FINALIZED', 'CANCELLED'])).scalar() or 0)
    stages = {'queue': ('received_at', 'judge_started_at'), 'compile': ('compile_started_at', 'compile_finished_at'),
              'execute': ('execution_started_at', 'execution_finished_at'), 'total': ('received_at', 'finished_at')}
    columns = {field for pair in stages.values() for field in pair}
    rows = list(m.ContestSubmission.select(*(getattr(m.ContestSubmission, field) for field in columns)).where(
        m.ContestSubmission.contest_eligible == True, scope, m.ContestSubmission.finished_at >= current-timedelta(minutes=5))
        .order_by(m.ContestSubmission.finished_at.desc()).limit(1000))
    latencies = {}
    for stage, (start, finish) in stages.items():
        values = sorted(max(0., (getattr(row, finish)-getattr(row, start)).total_seconds()) for row in rows
            if getattr(row, finish) and getattr(row, start))
        latencies[stage] = {'samples': len(values), 'p95_seconds': values[min(len(values)-1, int(len(values)*.95))] if values else None}
    errors = m.ContestSubmission.select().where(m.ContestSubmission.contest_eligible == True, scope,
        m.ContestSubmission.status == 'SystemError').count()
    return {'waiting': waiting, 'oldest_wait_seconds': max(0., (current-oldest).total_seconds()) if oldest else 0.,
        'projection_version_lag': max(0, lag), 'unresolved_system_errors': errors, 'stages': latencies}
