"""可复现的隔离容量样本；耗时仅记录，不作为跨机器的固定阈值。"""
import json
from datetime import timedelta
from pathlib import Path
from time import perf_counter

from flask_restx import Api
from test_postgres import postgres
from test_acm_upgrade import contest_fixture
from models import db_models as m


def test_projection_capacity_sample_and_conditional_reads(postgres, app):
    from controllers import contest_rankings_controller as ranks
    from services.contest_operations import emit
    m.run_schema_migrations()
    first, contest, problem = contest_fixture()
    users = [first]
    for index in range(1, 300):
        users.append(m.User.create(username=f'capacity-{index}'))
    m.ContestParticipant.insert_many([{'contest': contest.id, 'user': user.id} for user in users[1:]]).execute()
    for start in range(0, 300, 30):
        m.ContestSubmission.insert_many([{'contest': contest.id, 'contest_problem': problem.id,
            'user': user.id, 'problem_index': 'A', 'code': 'x'*4096, 'status': 'WA',
            'received_at': contest.start_time+timedelta(minutes=attempt+1)}
            for user in users[start:start+30] for attempt in range(10)]).execute()
    started = perf_counter()
    assert ranks.refresh_live_projection(contest.id)
    full_ms = (perf_counter()-started)*1000
    sub = m.ContestSubmission.create(contest=contest, contest_problem=problem, user=first,
        problem_index='A', status='AC', received_at=contest.start_time+timedelta(minutes=11))
    emit(contest.id, 'judgement', {'submission_id': sub.id, 'status': 'AC'})
    m.Contest.update(scoreboard_requested_version=1).where(m.Contest.id == contest.id).execute()
    started = perf_counter()
    assert ranks.refresh_live_projection(contest.id)
    incremental_ms = (perf_counter()-started)*1000
    snapshot = m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.snapshot_kind == 'LIVE')
    assert json.loads(snapshot.payload) == ranks._compute_rankings(contest.id)
    Api(app).add_namespace(ranks.api, path='/contests')
    client = app.test_client()
    url = f'/contests/{contest.id}/rankings'
    response = client.get(url)
    assert response.status_code == 200
    elapsed = []
    for _ in range(100):
        started = perf_counter()
        result = client.get(url, headers={'If-None-Match': response.headers['ETag']})
        elapsed.append((perf_counter()-started)*1000)
        assert result.status_code == 304 and not result.data
    Path('/tmp/oj-acm-capacity.json').write_text(json.dumps({
        'environment': 'isolated PostgreSQL / Flask test client; no network or Docker',
        'participants': 300, 'submissions': 3001, 'source_bytes_per_initial_submission': 4096,
        'full_live_and_frozen_ms': round(full_ms, 2), 'incremental_live_and_frozen_ms': round(incremental_ms, 2),
        'conditional_read_p95_ms': round(sorted(elapsed)[94], 2), 'conditional_reads': 100,
        'projection_matches_full_rebuild': True}, indent=2))
