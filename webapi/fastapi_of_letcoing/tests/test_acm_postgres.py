"""真实 PostgreSQL 多连接并发；不连接部署数据库。"""
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from test_postgres import postgres
from test_acm_upgrade import contest_fixture
from models import db_models as m


def test_projection_does_not_block_submission_writes(postgres):
    m.run_schema_migrations()
    _, contest, _ = contest_fixture()
    from controllers import contest_rankings_controller as ranks
    compute = ranks._compute_rankings
    def concurrent_compute(*args, **kwargs):
        def writer():
            with postgres.connection_context():
                postgres.execute_sql("SET lock_timeout = '500ms'")
                return m.Contest.update(scoreboard_requested_version=m.Contest.scoreboard_requested_version+1).where(m.Contest.id == contest.id).execute()
        with ThreadPoolExecutor(max_workers=1) as executor:
            assert executor.submit(writer).result(timeout=3) == 1
        return compute(*args, **kwargs)
    with patch.object(ranks, '_compute_rankings', side_effect=concurrent_compute):
        assert ranks.refresh_live_projection(contest.id) is True
    snapshot = m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.snapshot_kind == 'LIVE')
    assert snapshot.scoreboard_version == 0
    assert m.Contest.get_by_id(contest.id).scoreboard_requested_version > 0


def test_only_one_rejudge_batch_can_replace_same_original_revision(postgres):
    m.run_schema_migrations()
    from services.contest_operations import create_rejudge, apply_rejudge
    user, contest, problem = contest_fixture()
    user.role = 'manager'; user.save()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='42')
    original = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem, status='WA')
    batches = [create_rejudge(contest.id, user, [original.id], 'parallel') for _ in range(2)]
    m.ContestSubmission.update(status='AC', verdict='AC').where(m.ContestSubmission.rejudge_of == original.id).execute()
    def approve(batch_id):
        with postgres.connection_context():
            try:
                apply_rejudge(batch_id, user, 'review')
                return 'applied'
            except ValueError:
                return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(approve, [b.id for b in batches]))
    assert sorted(results) == ['applied', 'conflict']
    assert m.ContestSubmission.get_by_id(original.id).attempt_id == 2


def test_upgrade_keeps_released_final_visible_and_rebuilds_legacy_live(postgres):
    m.run_schema_migrations()
    _, contest, _ = contest_fixture()
    finalized = m.Contest.create(title='legacy-final', lifecycle_state='FINALIZED',
        freeze_time=contest.freeze_time, end_time=contest.freeze_time, finalized_at=contest.freeze_time)
    m.ContestScoreboardSnapshot.create(contest=finalized, snapshot_kind='FINAL', payload='{"rankings":[]}')
    m.ContestScoreboardSnapshot.create(contest=contest, snapshot_kind='LIVE', payload='{"rankings":[]}', scoreboard_version=0)
    postgres.execute_sql("DELETE FROM schema_migrations WHERE name='0020_acm_control'")
    postgres.execute_sql('ALTER TABLE contests DROP COLUMN thawed_at')
    postgres.execute_sql('ALTER TABLE contests DROP COLUMN final_revision')
    m.run_schema_migrations()
    assert m.Contest.get_by_id(finalized.id).thawed_at == finalized.finalized_at
    assert m.Contest.get_by_id(contest.id).scoreboard_requested_version > 0
    assert m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.contest == finalized.id).payload == '{"rankings":[]}'
