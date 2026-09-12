"""生产保障回归：持续写入、批量上限、公平调度。"""
import json
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from models import db_models as m
from test_postgres import postgres
from test_acm_upgrade import contest_fixture


def test_postgres_projection_publishes_consistent_version_during_writes(postgres):
    m.run_schema_migrations()
    user, contest, problem = contest_fixture()
    submission = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        status='WA', problem_index='A', received_at=contest.start_time)
    from controllers import contest_rankings_controller as ranks
    compute = ranks._compute_rankings
    def concurrent_compute(*args, **kwargs):
        def write():
            with postgres.connection_context(), postgres.atomic():
                postgres.execute_sql("SET LOCAL lock_timeout='500ms'")
                m.ContestSubmission.update(status='AC').where(m.ContestSubmission.id == submission.id).execute()
                m.Contest.update(scoreboard_requested_version=m.Contest.scoreboard_requested_version+1).where(m.Contest.id == contest.id).execute()
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(write).result(timeout=3)
        return compute(*args, **kwargs)
    with patch.object(ranks, '_compute_rankings', side_effect=concurrent_compute):
        assert ranks.refresh_live_projection(contest.id)
    snapshot = m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.snapshot_kind == 'LIVE')
    assert snapshot.scoreboard_version == 0
    assert json.loads(snapshot.payload)['rankings'][0]['solved_count'] == 0
    assert ranks.refresh_live_projection(contest.id)
    snapshot = m.ContestScoreboardSnapshot.get_by_id(snapshot.id)
    assert json.loads(snapshot.payload)['rankings'][0]['solved_count'] == 1
    assert snapshot.scoreboard_version == m.Contest.get_by_id(contest.id).scoreboard_requested_version


def test_dirty_projection_rotates_past_continuously_dirty_contests(db):
    from controllers import contest_rankings_controller as ranks
    contests = [m.Contest.create(title=str(i), lifecycle_state='RUNNING') for i in range(25)]
    selected = []
    with patch.object(ranks, 'refresh_live_projection', side_effect=lambda cid: selected.append(cid)):
        for _ in range(3):
            ranks.refresh_dirty_projections()
    assert set(selected) == {c.id for c in contests}
    assert len(selected) <= 60


def test_event_backlog_falls_back_without_materializing_all_payloads(db):
    from controllers import contest_rankings_controller as ranks
    _, contest, _ = contest_fixture()
    ranks.refresh_live_projection(contest.id)
    m.ContestEvent.insert_many([dict(contest=contest.id, kind='submission', payload='{}') for _ in range(1200)]).execute()
    m.Contest.update(scoreboard_requested_version=1).where(m.Contest.id == contest.id).execute()
    read, queries = db.execute_sql, []
    def capture(sql, params=None, *args, **kwargs):
        if 'FROM "contestevent"' in sql and 'MAX(' not in sql:
            queries.append((sql, params))
        return read(sql, params, *args, **kwargs)
    with patch.object(db, 'execute_sql', side_effect=capture):
        assert ranks.refresh_live_projection(contest.id)
    assert queries and all('LIMIT' in sql for sql, _ in queries)
    assert m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.snapshot_kind == 'LIVE').event_cursor == 1200


def test_revoked_manager_object_cannot_keep_operating(db):
    from services import contest_operations as ops
    user, contest, _ = contest_fixture()
    user.role = 'manager'; user.save()
    m.User.update(role='member').where(m.User.id == user.id).execute()
    assert not ops.allowed(contest.id, user, 'control')


def test_sensitive_rejudge_requires_different_reviewer(db, monkeypatch):
    import pytest
    from services import contest_operations as ops
    user, contest, problem = contest_fixture()
    user.role = 'manager'; user.save()
    reviewer = m.User.create(username='reviewer', role='manager')
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    original = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem, status='WA')
    batch = ops.create_rejudge(contest.id, user, [original.id], 'review')
    m.ContestSubmission.update(status='AC', verdict='AC').where(m.ContestSubmission.rejudge_batch == batch).execute()
    monkeypatch.setenv('CONTEST_DUAL_REVIEW_MIN', '1')
    with pytest.raises(PermissionError):
        ops.apply_rejudge(batch.id, user, 'self approval')
    assert m.ContestSubmission.get_by_id(original.id).status == 'WA'
    assert ops.apply_rejudge(batch.id, reviewer, 'independent review').state == 'APPLIED'


def test_totp_is_single_use_and_bound_to_user(db, monkeypatch):
    import pytest
    from services import contest_operations as ops
    user, _, _ = contest_fixture()
    monkeypatch.setenv('JURY_TOTP_SECRETS', json.dumps({str(user.id): 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'}))
    verifier = getattr(ops, 'verify_jury_totp', None)
    assert callable(verifier), 'MFA verifier is missing'
    # RFC 6238 test vector at Unix 59s, truncated to six digits.
    verifier(user, '287082', timestamp=59)
    with pytest.raises(PermissionError):
        verifier(user, '287082', timestamp=59)
    with pytest.raises(PermissionError):
        verifier(user, '000000', timestamp=89)


def test_judge_histograms_aggregate_without_user_labels(db, cache):
    from services import contest_metrics as metrics
    from datetime import timedelta
    observer = getattr(metrics, 'observe_judgement', None)
    assert callable(observer), 'judge stage histograms missing'
    user, contest, problem = contest_fixture()
    row = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        received_at=contest.start_time, judge_started_at=contest.start_time+timedelta(seconds=2),
        finished_at=contest.start_time+timedelta(seconds=5))
    observer(cache, row, 'contest', .03)
    observer(cache, row, 'contest', .04)
    output = metrics.judge_histogram_text(cache).decode()
    assert 'letcoding_judge_stage_seconds_count{pool="contest",stage="queue"} 2' in output
    assert 'letcoding_judge_stage_seconds_sum{pool="contest",stage="queue"} 4.0' in output
    assert 'username=' not in output and 'user_id=' not in output


def test_retention_archives_only_old_terminal_dispatched_outboxes(db, tmp_path):
    from services import retention
    from datetime import datetime, timedelta
    user, contest, problem = contest_fixture()
    old = datetime.now()-timedelta(days=40)
    rows = [m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        status=status, finished_at=old) for status in ('AC', 'Pending', 'SystemError')]
    for row in rows:
        m.ContestJudgeOutbox.create(submission=row, state='DISPATCHED', dispatched_at=old)
    m.ContestJudgeOutbox.update(updated_at=old).execute()
    report = retention.archive_outboxes(tmp_path, before=datetime.now()-timedelta(days=30), limit=2)
    assert report['archived'] == 1
    assert m.ContestJudgeOutbox.select().count() == 3
    report = retention.archive_outboxes(tmp_path, before=datetime.now()-timedelta(days=30), limit=2, prune=True)
    assert report['pruned'] == 1
    assert m.ContestJudgeOutbox.select().count() == 2
    assert m.ContestSubmission.select().count() == 3


def test_audit_export_rejects_rewriting_existing_record(db, tmp_path):
    import pytest
    from services import retention
    user, contest, _ = contest_fixture()
    entry = m.ContestAudit.create(contest=contest, actor=user, action='thaw', reason='first')
    assert retention.export_audit(tmp_path)['exported'] == 1
    entry.reason = 'changed'; entry.save()
    with pytest.raises(ValueError, match='conflict'):
        retention.export_audit(tmp_path)


def test_submission_does_not_lock_global_user_row(postgres, app, cache):
    import inspect
    from flask import g
    from controllers.contest_controller import ContestProblemSubmitController as Controller
    m.run_schema_migrations()
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    def submit():
        with postgres.connection_context():
            postgres.execute_sql("SET lock_timeout='500ms'")
            with app.test_request_context(method='POST', json={'code': 'print(1)', 'language': 'python'}):
                g.current_user = user.to_dict()
                with patch('controllers.contest_controller._get_current_user', return_value=user), \
                     patch('controllers.contest_controller.inject', return_value=cache):
                    return inspect.unwrap(Controller.post)(None, contest.id, problem.id)[1]
    with postgres.atomic():
        postgres.execute_sql('SELECT id FROM users WHERE id=%s FOR NO KEY UPDATE', (user.id,))
        with ThreadPoolExecutor(max_workers=1) as executor:
            status = executor.submit(submit).result(timeout=5)
    assert status == 202


def test_backup_restores_and_detects_corruption(postgres, tmp_path):
    import os
    import pytest
    from deploy import recovery
    m.run_schema_migrations()
    _, contest, _ = contest_fixture()
    postgres.execute_sql('CREATE TABLE temporal_evidence (id int, value timestamptz)')
    postgres.execute_sql("INSERT INTO temporal_evidence VALUES (1, '2026-09-12 12:00:00+00')")
    postgres.execute_sql("SET TIME ZONE 'Pacific/Honolulu'")
    directory = tmp_path / 'backup'
    bindir = os.environ.get('PG_BINDIR', '/usr/lib/postgresql/17/bin')
    recovery.create_backup(postgres.connection(), directory, bindir)
    report = recovery.verify_backup(postgres.connection(), directory, bindir)
    assert report['passed'] and report['tables_checked'] >= 10
    assert m.Contest.get_by_id(contest.id).title == 'ACM'
    with (directory / 'database.dump').open('ab') as stream:
        stream.write(b'corruption')
    with pytest.raises(ValueError, match='checksum'):
        recovery.verify_backup(postgres.connection(), directory, bindir)


def test_node_calibration_rejects_fast_and_slow_node_mix():
    from deploy import calibrate_judge
    compare = getattr(calibrate_judge, 'compare_calibrations', None)
    assert callable(compare), 'cross-node calibration missing'
    reports = [{'image': 'sha256:'+'a'*64, 'cpu_ms': [100]*5},
               {'image': 'sha256:'+'a'*64, 'cpu_ms': [140]*5}]
    assert not compare(reports, max_ratio=1.1)['passed']
    reports[1]['cpu_ms'] = [105]*5
    assert compare(reports, max_ratio=1.1)['passed']
    reports[1]['image'] = 'sha256:'+'b'*64
    assert not compare(reports, max_ratio=1.1)['passed']


def test_wal_archive_is_durable_and_refuses_conflicting_overwrite(tmp_path):
    import pytest
    from deploy import archive_wal
    source = tmp_path / '000000010000000000000001'
    source.write_bytes(b'original WAL')
    archive_wal.archive(source, tmp_path/'archive')
    archive_wal.archive(source, tmp_path/'archive')
    source.write_bytes(b'different WAL')
    with pytest.raises(ValueError, match='conflict'):
        archive_wal.archive(source, tmp_path/'archive')
    assert (tmp_path/'archive'/source.name).read_bytes() == b'original WAL'


def test_lock_wait_is_exposed_as_histogram(app, db, cache):
    from services.observability import register_metrics
    from services.contest_lifecycle import lock_contest
    _, contest, _ = contest_fixture()
    app.config['METRICS_TOKEN'] = 'internal-test-token'
    register_metrics(app)
    @app.get('/lock-test')
    def lock_test():
        lock_contest(contest.id)
        return {'ok': True}
    client = app.test_client()
    assert client.get('/lock-test').status_code == 200
    with patch('core.di_container.inject', return_value=cache):
        response = client.get('/metrics', headers={'Authorization': 'Bearer internal-test-token'})
    assert response.status_code == 200
    assert 'letcoding_contest_lock_wait_seconds_count 1.0' in response.text


def test_release_rejects_mutable_image_tags(monkeypatch):
    import pytest
    from deploy import check_release
    monkeypatch.setenv('API_IMAGE', 'registry.example/api:latest')
    monkeypatch.setenv('JUDGE_SANDBOX_IMAGE', 'sha256:'+'a'*64)
    with pytest.raises(ValueError):
        check_release.validate_images('api')
    monkeypatch.setenv('API_IMAGE', 'registry.example/api@sha256:'+'b'*64)
    assert check_release.validate_images('api')


def test_disabled_judge_cannot_use_cached_actor(db):
    from services import contest_operations as ops
    user, contest, _ = contest_fixture()
    user.role = 'manager'; user.save()
    m.User.update(is_active=False).where(m.User.id == user.id).execute()
    assert not ops.allowed(contest.id, user, 'control')


def test_audit_background_rescans_for_late_commits(db, tmp_path, monkeypatch):
    import logging
    from services.judge_service import JudgeWorker
    user, contest, _ = contest_fixture()
    m.ContestAudit.create(id=2, contest=contest, actor=user, action='thaw', reason='later ID first')
    monkeypatch.setenv('AUDIT_EXPORT_DIR', str(tmp_path))
    worker = object.__new__(JudgeWorker)
    worker.logger = logging.getLogger('test')
    export = getattr(worker, '_export_audit', None)
    assert callable(export), 'asynchronous audit export missing'
    export()
    m.ContestAudit.create(id=1, contest=contest, actor=user, action='thaw', reason='earlier ID commits late')
    export(); export()
    assert (tmp_path/'audit-1.json').exists() and (tmp_path/'audit-2.json').exists()


def test_freeze_builds_public_snapshot_without_new_submissions(db):
    from datetime import timedelta
    from controllers import contest_rankings_controller as ranks
    from services.contest_operations import now
    _, contest, _ = contest_fixture()
    contest.freeze_time = now()+timedelta(minutes=5); contest.save()
    ranks.refresh_dirty_projections()
    assert not m.ContestScoreboardSnapshot.select().where(m.ContestScoreboardSnapshot.snapshot_kind == 'PUBLIC_FREEZE').exists()
    # Advance the deadline without any submission/version event.
    m.Contest.update(freeze_time=now()-timedelta(seconds=1)).where(m.Contest.id == contest.id).execute()
    ranks.refresh_dirty_projections()
    assert m.ContestScoreboardSnapshot.select().where(m.ContestScoreboardSnapshot.snapshot_kind == 'PUBLIC_FREEZE').exists()


def test_full_rebuild_reads_submissions_in_bounded_batches(db):
    from controllers import contest_rankings_controller as ranks
    user, contest, problem = contest_fixture()
    m.ContestSubmission.insert_many([dict(contest=contest.id, user=user.id, contest_problem=problem.id,
        problem_index='A', status='WA', received_at=contest.start_time) for _ in range(1200)]).execute()
    m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', status='AC', received_at=contest.start_time)
    queries, execute = [], db.execute_sql
    def capture(sql, params=None, *args, **kwargs):
        if 'FROM "contest_submissions"' in sql:
            queries.append(sql)
        return execute(sql, params, *args, **kwargs)
    with patch.object(db, 'execute_sql', side_effect=capture):
        data = ranks._compute_rankings(contest.id)
    assert data['rankings'][0]['solved_count'] == 1
    assert data['rankings'][0]['penalty'] == 24000
    assert len(queries) >= 3 and all('LIMIT' in sql for sql in queries)


def test_prune_stops_when_existing_archive_cannot_be_synced(db, tmp_path, monkeypatch):
    import os
    import pytest
    from datetime import datetime, timedelta
    from services import retention
    user, contest, problem = contest_fixture()
    row = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem, status='AC')
    old = datetime.now()-timedelta(days=40)
    record = m.ContestJudgeOutbox.create(submission=row, state='DISPATCHED', dispatched_at=old)
    m.ContestJudgeOutbox.update(updated_at=old).execute()
    before = datetime.now()-timedelta(days=30)
    retention.archive_outboxes(tmp_path, before)
    def disk_failure(_):
        raise OSError('archive disk unavailable')
    monkeypatch.setattr(os, 'fsync', disk_failure)
    with pytest.raises(OSError):
        retention.archive_outboxes(tmp_path, before, prune=True)
    assert m.ContestJudgeOutbox.get_by_id(record.id)
