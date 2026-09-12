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
    # 有版本欠账时报告已发布快照的年龄；静止且已追平的榜单不报警。
    oldest_projection = (m.Contest.select(fn.MIN(fn.COALESCE(snapshot.updated_at, m.Contest.created_at)))
        .join(snapshot, JOIN.LEFT_OUTER, on=((snapshot.contest == m.Contest.id) & (snapshot.snapshot_kind == 'LIVE')))
        .where(board_scope, ~m.Contest.lifecycle_state.in_(['FINALIZED', 'CANCELLED']),
            (snapshot.id.is_null()) | (m.Contest.scoreboard_requested_version > snapshot.scoreboard_version)).scalar())
    if isinstance(oldest_projection, str):
        from datetime import datetime
        oldest_projection = datetime.fromisoformat(oldest_projection)
    missing_freeze = (m.Contest.select(fn.MIN(m.Contest.freeze_time)).where(board_scope,
        ~m.Contest.lifecycle_state.in_(['FINALIZED', 'CANCELLED']), m.Contest.freeze_time <= current, m.Contest.thawed_at.is_null(),
        ~m.Contest.id.in_(snapshot.select(snapshot.contest).where(snapshot.snapshot_kind == 'PUBLIC_FREEZE'))).scalar())
    stale = max([0.] + [(current-value).total_seconds() for value in (oldest_projection, missing_freeze) if value])
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
        'projection_stale_seconds': stale, 'projection_version_lag': max(0, lag), 'unresolved_system_errors': errors, 'stages': latencies}


POOLS = ('all', 'contest', 'practice', 'rejudge', 'validation')
BUCKETS = (.01, .05, .1, .5, 1, 2, 5, 10, 30, 60, 300)
STAGES = {'queue': ('received_at', 'judge_started_at'),
          'compile': ('compile_started_at', 'compile_finished_at'),
          'execute': ('execution_started_at', 'execution_finished_at'),
          'total': ('received_at', 'finished_at')}


def observe_judgement(cache, row, pool, persistence_seconds):
    """终态成功提交后记录低基数累计直方图；Redis 丢失会重置指标，不影响判题。"""
    if pool not in POOLS:
        raise ValueError('unknown worker pool')
    values = {'persist': persistence_seconds}
    for stage, (start, end) in STAGES.items():
        first, last = getattr(row, start), getattr(row, end)
        if first and last:
            values[stage] = (last-first).total_seconds()
    pipe = cache._client.pipeline(transaction=True)
    import math
    for stage, value in values.items():
        if not math.isfinite(value) or value < 0:
            continue
        prefix = f'{pool}:{stage}:'
        pipe.hincrby('judge:stage:histogram', prefix+'count', 1)
        pipe.hincrbyfloat('judge:stage:histogram', prefix+'sum', value)
        for bound in BUCKETS:
            if value <= bound:
                pipe.hincrby('judge:stage:histogram', prefix+str(bound), 1)
    pipe.execute()


def judge_histogram_text(cache):
    values = cache._client.hgetall('judge:stage:histogram')
    name = 'letcoding_judge_stage_seconds'
    lines = [f'# HELP {name} Judge stage duration in seconds', f'# TYPE {name} histogram']
    for pool in POOLS:
        for stage in (*STAGES, 'persist'):
            prefix = f'{pool}:{stage}:'
            if prefix+'count' not in values:
                continue
            labels = f'pool="{pool}",stage="{stage}"'
            for bound in BUCKETS:
                lines.append(f'{name}_bucket{{{labels},le="{bound}"}} {int(values.get(prefix+str(bound), 0))}')
            count = int(values[prefix+'count'])
            lines.extend([f'{name}_bucket{{{labels},le="+Inf"}} {count}',
                f'{name}_count{{{labels}}} {count}',
                f'{name}_sum{{{labels}}} {float(values.get(prefix+"sum", 0))}'])
    return ('\n'.join(lines)+'\n').encode()
