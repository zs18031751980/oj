"""故障清理、排空和运维可用性回归。"""
import logging
import os
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from models import db_models as m
from test_acm_upgrade import contest_fixture
from test_job_reliability import worker, Executor
from services.judge_service import JudgeWorker


@pytest.mark.parametrize('target', ['Compiled', 'Running'])
def test_compiled_resources_closed_on_transition_error(db, worker, monkeypatch, target):
    from controllers.contest_problem_controller import _prepare_program
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    row = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        code='print(1)', language='python', job_id='cleanup', status='Pending')
    program, _, _ = _prepare_program('print(1)', 'python')
    transition = worker._transition_contest
    def fail(submission_id, attempt, expected, state, **fields):
        if state == target:
            raise RuntimeError('synthetic database outage')
        return transition(submission_id, attempt, expected, state, **fields)
    try:
        with patch('services.judge_service._prepare_program', return_value=(program, None, None)), \
             patch.object(worker, '_transition_contest', side_effect=fail):
            with pytest.raises(RuntimeError):
                worker._process_contest_task({'submission_id': row.id, 'job_id': row.job_id, 'attempt_id': row.attempt_id})
        assert not Path(program.workdir).exists()
    finally:
        program.close()


def test_drain_finishes_active_job_without_claiming_next(db, cache):
    instance = JudgeWorker(cache, Executor(), logging.getLogger('test'))
    entered, release = threading.Event(), threading.Event()
    handled = []
    def handler(task):
        handled.append(task['job_id'])
        entered.set()
        assert release.wait(5)
        return True
    for job in ['first', 'second']:
        cache.list_push('drain-test', {'job_id': job})
    # Only claim loop and heartbeat are needed; neither synthetic job uses a judge or database mutation.
    instance.queues = lambda: [('drain-test', handler)]
    try:
        instance._running = True
        instance._thread = threading.Thread(target=instance._run_loop, daemon=True)
        instance._thread.start()
        assert entered.wait(3)
        drain = getattr(instance, 'begin_drain', None)
        assert callable(drain), 'drain support missing'
        drain()
        assert instance.health()['draining'] and instance.health()['alive']
        assert instance.stop(timeout=.05) is False
        assert not instance._stop_event.is_set(), 'heartbeat must survive an unfinished drain'
        release.set()
        assert instance.stop(timeout=3) is True
        assert len(handled) == 1
        assert cache.list_length('drain-test') == 1
        assert cache.list_length('drain-test:processing') == 0
    finally:
        release.set()
        instance._running = False
        instance._stop_event.set()
        if instance._thread:
            instance._thread.join(timeout=5)


def test_fixed_arrival_load_does_not_wait_for_verdict():
    from deploy.contest_load import schedule_arrivals
    release = threading.Event()
    def slow(index, scheduled):
        release.wait(.3)
        return {'index': index, 'scheduled': scheduled}
    try:
        rows = schedule_arrivals(slow, count=8, rate=100, workers=2)
        assert len(rows) == 8
        assert sum(row.get('error') == 'generator_capacity' for row in rows) == 6
        assert max(row['schedule_lag_ms'] for row in rows) < 100
    finally:
        release.set()


def test_background_health_tracks_failure_and_recovery(db, worker, monkeypatch, tmp_path):
    monkeypatch.setenv('AUDIT_EXPORT_DIR', str(tmp_path))
    with patch('services.retention.export_audit', side_effect=OSError('disk unavailable')):
        with pytest.raises(OSError):
            worker._export_audit()
    assert worker.health()['audit_consecutive_failures'] == 1
    worker._export_audit()
    assert worker.health()['audit_consecutive_failures'] == 0
    assert worker.health()['audit_last_success_unix'] > 0


def test_projection_timestamp_advances_on_upsert(db):
    from datetime import timedelta
    from controllers.contest_rankings_controller import refresh_live_projection
    from services.contest_operations import now
    _, contest, _ = contest_fixture()
    refresh_live_projection(contest.id)
    old = now()-timedelta(hours=1)
    m.ContestScoreboardSnapshot.update(updated_at=old).execute()
    m.Contest.update(scoreboard_requested_version=1).execute()
    refresh_live_projection(contest.id)
    assert all(row.updated_at > old for row in m.ContestScoreboardSnapshot.select())


def test_backup_monitor_rejects_missing_and_future_manifest(tmp_path, monkeypatch):
    import json, time
    from services.observability import backup_metrics_text
    path = tmp_path/'manifest.json'
    monkeypatch.setenv('BACKUP_MANIFEST_FILE', str(path))
    assert b'letcoding_backup_status_up 0' in backup_metrics_text()
    path.write_text(json.dumps({'created_at_unix': time.time()+3600}))
    assert b'letcoding_backup_status_up 0' in backup_metrics_text()
    path.write_text(json.dumps({'created_at_unix': time.time()-120}))
    assert b'letcoding_backup_status_up 1' in backup_metrics_text()


def test_restored_database_runs_application_pipeline(postgres, tmp_path):
    from deploy.recovery import create_backup, verify_backup
    m.run_schema_migrations()
    contest_fixture()
    directory = tmp_path/'backup'
    create_backup(postgres.connection(), directory, os.environ.get('PG_BINDIR', '/usr/lib/postgresql/17/bin'))
    report = verify_backup(postgres.connection(), directory, os.environ.get('PG_BINDIR', '/usr/lib/postgresql/17/bin'))
    assert report['application_check']['verdict'] == 'AC'
    assert report['application_check']['solved_count'] == 1
    assert report['schema_checked'] and report['sequences_checked'] > 0


from test_postgres import postgres


def test_cleanup_survives_checker_close_error(db, worker, monkeypatch):
    from controllers.contest_problem_controller import _prepare_program
    from services.contest_packages import OutputChecker
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    row = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        code='print(1)', language='python', job_id='checker-cleanup')
    program, _, _ = _prepare_program('print(1)', 'python')
    try:
        with patch('services.judge_service._prepare_program', return_value=(program, None, None)), \
                patch.object(OutputChecker, 'close', side_effect=OSError('cleanup failed')):
            with pytest.raises(OSError):
                worker._process_contest_task({'submission_id': row.id, 'job_id': row.job_id, 'attempt_id': row.attempt_id})
        assert not Path(program.workdir).exists()
    finally:
        program.close()


def test_projection_age_only_alerts_when_refresh_needed(db):
    from datetime import timedelta
    from services.contest_metrics import competition_health
    from services.contest_operations import now
    from controllers.contest_rankings_controller import refresh_live_projection
    _, contest, _ = contest_fixture()
    refresh_live_projection(contest.id)
    m.ContestScoreboardSnapshot.update(updated_at=now()-timedelta(hours=1)).execute()
    assert competition_health()['projection_stale_seconds'] == 0
    m.Contest.update(scoreboard_requested_version=1).execute()
    assert competition_health()['projection_stale_seconds'] >= 3599
    refresh_live_projection(contest.id)
    assert competition_health()['projection_stale_seconds'] == 0


def test_small_sample_p95_does_not_hide_slow_request():
    from deploy.contest_load import percentile
    assert percentile([10, 1000], .95) == 1000


@pytest.mark.parametrize('damage', ['index', 'sequence'])
def test_restore_rejects_broken_schema_or_sequence(postgres, tmp_path, monkeypatch, damage):
    from deploy import recovery
    import psycopg2
    m.run_schema_migrations()
    user, _, _ = contest_fixture()
    directory = tmp_path/'backup'
    recovery.create_backup(postgres.connection(), directory, os.environ.get('PG_BINDIR', '/usr/lib/postgresql/17/bin'))
    run = recovery._run
    def damage_restore(bindir, command, args, env):
        run(bindir, command, args, env)
        if command != 'pg_restore':
            return
        name = next(arg.split('=', 1)[1] for arg in args if arg.startswith('--dbname='))
        params = postgres.connection().get_dsn_parameters()
        params['dbname'] = name
        conn = psycopg2.connect(**params)
        try:
            with conn, conn.cursor() as cur:
                cur.execute('DROP INDEX idx_contest_waiting' if damage == 'index' else
                    "SELECT setval(pg_get_serial_sequence('users','id'),1,false)")
        finally:
            conn.close()
    monkeypatch.setattr(recovery, '_run', damage_restore)
    with pytest.raises(ValueError):
        recovery.verify_backup(postgres.connection(), directory, os.environ.get('PG_BINDIR', '/usr/lib/postgresql/17/bin'))
    assert m.User.get_by_id(user.id).username == 'competitor'
    assert postgres.execute_sql("SELECT count(*) FROM pg_database WHERE datname LIKE %s", ('oj_restore_%',)).fetchone()[0] == 0


def test_metrics_exclude_draining_capacity(app, db, cache):
    from services.observability import register_metrics
    register_metrics(app)
    app.config['METRICS_TOKEN'] = 'test-only'
    cache.set('judge:worker:draining', {'alive': True, 'pool': 'contest', 'draining': True,
        'heartbeat_unix': time.time(), 'accepting_jobs': False}, 30)
    with patch('core.di_container.inject', return_value=cache):
        response = app.test_client().get('/metrics', headers={'Authorization': 'Bearer test-only'})
    assert 'letcoding_worker_slots{pool="contest",state="alive"} 1' in response.text
    assert 'letcoding_worker_slots{pool="contest",state="accepting"} 0' in response.text
    assert 'letcoding_worker_slots{pool="contest",state="idle"} 0' in response.text
    assert 'letcoding_dependency_up{dependency="postgres"} 1' in response.text
