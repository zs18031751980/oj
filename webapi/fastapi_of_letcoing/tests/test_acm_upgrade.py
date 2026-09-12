"""比赛公平性、保密性与可恢复性验收。"""
import inspect
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from flask import g
from models import db_models as m


def contest_fixture():
    user = m.User.create(username='competitor')
    now = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=8)
    contest = m.Contest.create(title='ACM', lifecycle_state='RUNNING',
        start_time=now-timedelta(hours=2), end_time=now+timedelta(hours=1),
        freeze_time=now-timedelta(minutes=30))
    problem = m.ContestProblem.create(contest=contest, title='A', problem_index='A',
        description='A', correct_answer='print(1)')
    m.ContestParticipant.create(contest=contest, user=user)
    return user, contest, problem


def test_freeze_persists_after_end(db):
    from controllers.contest_controller import _contest_is_frozen
    _, contest, _ = contest_fixture()
    contest.end_time = contest.freeze_time + timedelta(minutes=1)
    contest.save()
    assert _contest_is_frozen(contest)


def test_late_prefreeze_verdict_updates_public_without_postfreeze_leak(db):
    from controllers.contest_rankings_controller import refresh_live_projection, _load_public_snapshot
    user, contest, problem = contest_fixture()
    before = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', received_at=contest.freeze_time-timedelta(minutes=1), status='Running')
    refresh_live_projection(contest.id)
    before.status = 'AC'; before.verdict = 'AC'; before.save()
    m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', received_at=contest.freeze_time+timedelta(minutes=1), status='WA')
    m.Contest.update(scoreboard_requested_version=2).where(m.Contest.id == contest.id).execute()
    refresh_live_projection(contest.id)
    public = _load_public_snapshot(contest)
    assert public is not None
    assert public['rankings'][0]['solved_count'] == 1
    assert public['rankings'][0]['penalty'] == 89


def test_same_score_shares_rank():
    from services.contest_scoring import compute_acm_scoreboard
    rows = compute_acm_scoreboard(entries=[{'entry_id': 1}, {'entry_id': 2}],
        problem_indexes=['A'], submissions=[], start_at=datetime(2026, 1, 1))
    assert [row['rank'] for row in rows] == [1, 1]


def test_formal_idempotency_conflict_and_retry_after_end(app, db):
    from controllers.contest_controller import ContestProblemSubmitController as C
    user, contest, problem = contest_fixture()
    original = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        code='print(1)', language='python', idempotency_key='retry', job_id='job')
    def submit(code):
        with app.test_request_context(method='POST', json={'code': code, 'language': 'python'},
                headers={'Idempotency-Key': 'retry'}):
            g.current_user = user.to_dict()
            with patch('controllers.contest_controller._get_current_user', return_value=user):
                return inspect.unwrap(C.post)(None, contest.id, problem.id)
    assert submit('print(2)')[1] == 409
    contest.end_time = contest.freeze_time; contest.save()
    result, status = submit('print(1)')
    assert status == 202 and result['submission_id'] == original.id


def test_system_error_blocks_finalization(app, db):
    from controllers.contest_rankings_controller import ContestRankingsFinalizeController as C
    user, contest, problem = contest_fixture()
    user.role = 'manager'; user.save()
    contest.end_time = contest.freeze_time; contest.save()
    m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem, status='SystemError')
    with app.test_request_context(method='POST'):
        g.current_user = user.to_dict()
        with patch('controllers.contest_rankings_controller._get_current_user', return_value=user):
            assert C.post(None, contest.id)[1] == 409
    assert not m.ContestScoreboardSnapshot.select().where(m.ContestScoreboardSnapshot.snapshot_kind == 'FINAL').exists()


def test_projection_computes_outside_contest_lock_and_rejects_stale_version(db):
    from controllers import contest_rankings_controller as ranks
    _, contest, _ = contest_fixture()
    compute = ranks._compute_rankings
    def concurrent_change(*args, **kwargs):
        assert not db.in_transaction(), 'aggregation must not hold contest transaction'
        result = compute(*args, **kwargs)
        m.Contest.update(scoreboard_requested_version=m.Contest.scoreboard_requested_version+1).where(m.Contest.id == contest.id).execute()
        return result
    with patch.object(ranks, '_compute_rankings', side_effect=concurrent_change):
        ranks.refresh_live_projection(contest.id)
    assert not m.ContestScoreboardSnapshot.select().exists()


def test_cpu_budget_does_not_count_sleep_but_stops_busy_loop():
    import sys
    from services.execution_runtime import run_process
    result = run_process([sys.executable, '-c', 'import time; time.sleep(.25); print(42)'],
        '', 1, cpu_timeout=.15)
    assert not result['timed_out'] and result['stdout'].strip() == '42'
    result = run_process([sys.executable, '-c', 'while True: pass'], '', 2, cpu_timeout=.15)
    assert result['timed_out'] and result['wall_ms'] < 1500


def test_checker_modes_reject_nonfinite_and_accept_valid_tolerance():
    from services.contest_packages import check_output
    assert check_output('1  2\n', '1\n2', {'checker': 'tokens'})
    assert check_output('1.00000001', '1.0', {'checker': 'float', 'absolute_tolerance': 1e-6})
    assert not check_output('NaN', '1', {'checker': 'float'})
    assert not check_output('1 3', '1 2', {'checker': 'tokens'})


def test_package_is_immutable_and_detects_corruption(db):
    from services.contest_packages import publish_package, load_package
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='1', expected_output='2')
    package = publish_package(problem, actor_id=user.id)
    problem.time_limit = 9999; problem.save()
    assert load_package(package.digest)['time_limit'] == 1000
    package.payload = '{}'; package.save()
    import pytest
    with pytest.raises(ValueError, match='digest'):
        load_package(package.digest)


def test_thaw_requires_scoped_permission_and_is_audited(db):
    from services.contest_operations import thaw_contest
    user, contest, _ = contest_fixture()
    import pytest
    with pytest.raises(PermissionError):
        thaw_contest(contest.id, user, 'release scoreboard')
    m.ContestRole.create(contest=contest, user=user, role='director')
    thaw_contest(contest.id, user, 'release scoreboard')
    assert m.Contest.get_by_id(contest.id).thawed_at
    assert m.ContestAudit.get().action == 'thaw'


def test_rejudge_candidates_do_not_change_score_until_apply(db):
    from services.contest_operations import create_rejudge, apply_rejudge
    user, contest, problem = contest_fixture()
    user.role = 'manager'; user.save()
    original = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', code='print(1)', language='python', status='WA', verdict='WA')
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    batch = create_rejudge(contest.id, user, [original.id], 'test correction')
    candidate = m.ContestSubmission.get(m.ContestSubmission.rejudge_batch == batch.id)
    assert not candidate.contest_eligible and m.ContestSubmission.get_by_id(original.id).status == 'WA'
    candidate.status = 'AC'; candidate.verdict = 'AC'; candidate.save()
    apply_rejudge(batch.id, user, 'reviewed')
    assert m.ContestSubmission.get_by_id(original.id).status == 'AC'
    assert m.Judgement.select().where(m.Judgement.submission == original.id).count() == 2


def test_private_clarifications_and_event_feed_do_not_leak(db):
    from services.contest_operations import ask_clarification, answer_clarification, events_for
    user, contest, _ = contest_fixture()
    other = m.User.create(username='other')
    m.ContestParticipant.create(contest=contest, user=other)
    question = ask_clarification(contest.id, user, 'secret question')
    manager = m.User.create(username='director', role='manager')
    answer_clarification(question.id, manager, 'secret reply', broadcast=False)
    assert 'secret reply' in str(events_for(contest.id, user, 0))
    assert 'secret' not in str(events_for(contest.id, other, 0))


def test_acm_worker_uses_pinned_package_and_does_not_report_partial(db, worker, monkeypatch):
    from services.contest_packages import publish_package
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='first', expected_output='42')
    second = m.ContestTestcase.create(contest_problem=problem, input_data='second', expected_output='43')
    package = publish_package(problem)
    second.expected_output = '42'; second.save()
    sub = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', code='print(42)', language='python', job_id='pinned', package_digest=package.digest)
    monkeypatch.setenv('APP_ENV', 'test'); monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    worker._process_contest_task({'submission_id': sub.id, 'job_id': sub.job_id})
    assert m.ContestSubmission.get_by_id(sub.id).status == 'WA'
    assert m.Judgement.select().where(m.Judgement.submission == sub.id).exists()


def test_queue_isolation_and_fairness(db, cache, monkeypatch):
    from services.contest_outbox import dispatch_outbox_entry
    from services.judge_service import JudgeWorker
    user, contest, problem = contest_fixture()
    practice = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        contest_eligible=False, job_id='practice')
    dispatch_outbox_entry(cache, m.ContestJudgeOutbox.create(submission=practice))
    assert cache.list_length('practice_judge_queue') == 1
    assert cache.list_length('contest_judge_queue') == 0
    for i, owner in enumerate([1, 1, 1, 2]):
        cache.list_push('contest_judge_queue', {'job_id': str(i), 'contest_id': 1, 'entry_id': owner})
    first = cache.list_claim('contest_judge_queue', 'contest_judge_queue:processing')
    second = cache.list_claim('contest_judge_queue', 'contest_judge_queue:processing')
    assert [first['payload']['entry_id'], second['payload']['entry_id']] == [1, 2]
    monkeypatch.setenv('JUDGE_WORKER_POOL', 'contest')
    instance = JudgeWorker(cache, Mock(), Mock())
    assert [key for key, _ in instance.queues()] == ['contest_judge_queue']


from test_job_reliability import worker


def test_team_scores_aggregate_and_members_cannot_change_after_start(db):
    from services.contest_operations import create_team
    from controllers.contest_rankings_controller import _compute_rankings
    user, contest, problem = contest_fixture()
    other = m.User.create(username='teammate')
    director = m.User.create(username='director', role='manager')
    start = contest.start_time
    contest.start_time = datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(hours=9); contest.save()
    team = create_team(contest.id, director, 'team', [user.id, other.id])
    contest.start_time = start; contest.save()
    m.ContestSubmission.create(contest=contest, user=other, team=team, contest_problem=problem,
        problem_index='A', status='AC', received_at=start+timedelta(minutes=10))
    board = _compute_rankings(contest.id)
    assert len(board['rankings']) == 1 and board['rankings'][0]['solved_count'] == 1
    import pytest
    with pytest.raises(ValueError, match='开赛'):
        create_team(contest.id, director, 'late', [director.id])


def test_operations_http_authorization_and_manual_override_requires_reauth(app, db, cache):
    from controllers.contest_operations_controller import api
    from flask_restx import Api
    from werkzeug.security import generate_password_hash
    user, contest, problem = contest_fixture()
    Api(app).add_namespace(api, path='/contests')
    client = app.test_client()
    with patch('controllers.contest_operations_controller._get_current_user', return_value=user), patch('middleware.auth_middleware.inject', return_value=cache):
        assert client.post(f'/{"contests"}/{contest.id}/thaw', json={'reason': 'release'}).status_code == 403
        user.role = 'manager'; user.password_hash = generate_password_hash('test-only-password'); user.save()
        sub = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem, status='WA')
        url = f'/contests/{contest.id}/submissions/{sub.id}/override'
        assert client.post(url, json={'verdict': 'AC', 'reason': 'verified'}).status_code == 403
        result = client.post(url, json={'verdict': 'AC', 'reason': 'verified', 'password': 'test-only-password'})
        assert result.status_code == 200
        assert m.ContestSubmission.get_by_id(sub.id).status == 'AC'
        assert m.ContestAudit.get(m.ContestAudit.action == 'judgement.override').actor_id == user.id


def test_overlapping_rejudge_cannot_overwrite_newer_approved_result(db):
    from services.contest_operations import create_rejudge, apply_rejudge
    user, contest, problem = contest_fixture()
    user.role = 'manager'; user.save()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    original = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem, status='WA')
    first = create_rejudge(contest.id, user, [original.id], 'first')
    second = create_rejudge(contest.id, user, [original.id], 'second')
    m.ContestSubmission.update(status='AC', verdict='AC').where(m.ContestSubmission.rejudge_of == original.id).execute()
    apply_rejudge(first.id, user, 'verified')
    import pytest
    with pytest.raises(ValueError, match='变化'):
        apply_rejudge(second.id, user, 'stale')


def test_projection_recomputes_only_changed_entry_and_matches_full_rebuild(db):
    from controllers import contest_rankings_controller as ranks
    from services.contest_operations import emit
    user, contest, problem = contest_fixture()
    other = m.User.create(username='unchanged')
    m.ContestParticipant.create(contest=contest, user=other)
    ranks.refresh_live_projection(contest.id)
    sub = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', received_at=contest.start_time+timedelta(minutes=10), status='AC')
    emit(contest.id, 'judgement', {'submission_id': sub.id, 'status': 'AC'})
    m.Contest.update(scoreboard_requested_version=1).where(m.Contest.id == contest.id).execute()
    original = ranks._compute_rankings
    selected = []
    def capture(*args, **kwargs):
        selected.append(kwargs.get('entry_ids'))
        return original(*args, **kwargs)
    with patch.object(ranks, '_compute_rankings', side_effect=capture):
        ranks.refresh_live_projection(contest.id)
    assert selected and all(value == {user.id} for value in selected)
    import json
    actual = json.loads(m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.snapshot_kind == 'LIVE').payload)
    assert actual == ranks._compute_rankings(contest.id)


def test_finalized_but_not_thawed_does_not_reveal_final_board(app, db):
    from controllers.contest_rankings_controller import ContestRankingsController as C
    user, contest, _ = contest_fixture()
    contest.lifecycle_state = 'FINALIZED'; contest.save()
    m.ContestScoreboardSnapshot.create(contest=contest, snapshot_kind='FINAL', payload='{"secret":"final"}')
    m.ContestScoreboardSnapshot.create(contest=contest, snapshot_kind='PUBLIC_FREEZE', payload='{"frozen":true}')
    with app.test_request_context():
        with patch('controllers.contest_rankings_controller._get_current_user', return_value=None):
            result = inspect.unwrap(C.get)(None, contest.id)
            assert 'secret' not in str(result) and result[0].get('frozen')


def test_registration_closes_at_start_and_end_is_exclusive(app, db):
    from controllers.contest_controller import ContestJoinController as C, _contest_time_error
    user, contest, _ = contest_fixture()
    late = m.User.create(username='late')
    with app.test_request_context(method='POST'):
        with patch('controllers.contest_controller._get_current_user', return_value=late):
            assert C.post(None, contest.id)[1] == 409
    assert _contest_time_error(contest, contest.end_time) == '比赛已结束'


def test_custom_checker_runs_in_sandbox_and_can_reject(db, monkeypatch):
    from services.contest_packages import check_output
    monkeypatch.setenv('APP_ENV', 'test'); monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    checker = {'checker': 'custom', 'language': 'python',
        'code': 'import json,sys; x=json.load(sys.stdin); sys.exit(0 if sorted(x["actual"].split()) == sorted(x["expected"].split()) else 1)'}
    assert check_output('2 1', '1 2', checker)
    assert not check_output('2 3', '1 2', checker)


def test_final_correction_preserves_original_snapshot(db):
    from services.contest_operations import create_rejudge, apply_rejudge
    from controllers.contest_rankings_controller import _save_final_snapshot, _compute_rankings
    user, contest, problem = contest_fixture()
    user.role = 'manager'; user.save()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    original = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', status='WA', received_at=contest.start_time+timedelta(minutes=1))
    before = _save_final_snapshot(contest, _compute_rankings(contest.id))
    contest.lifecycle_state = 'FINALIZED'; contest.save()
    batch = create_rejudge(contest.id, user, [original.id], 'final correction')
    m.ContestSubmission.update(status='AC', verdict='AC').where(m.ContestSubmission.rejudge_batch == batch).execute()
    apply_rejudge(batch.id, user, 'reviewed correction')
    import json
    assert json.loads(m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.snapshot_kind == 'FINAL').payload) == before
    assert m.Contest.get_by_id(contest.id).final_revision == 1
    corrected = m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.snapshot_kind == 'FINAL:1')
    assert json.loads(corrected.payload)['rankings'][0]['solved_count'] == 1


def test_public_problem_never_exposes_custom_checker(db):
    from controllers.contest_controller import _public_problem_data
    _, _, problem = contest_fixture()
    problem.checker_config = '{"checker":"custom","code":"secret checker"}'
    assert 'secret checker' not in str(_public_problem_data(problem))


def test_candidate_package_requires_worker_validation_before_activation(db, monkeypatch):
    from services.contest_packages import stage_package, validate_staged_package, activate_package
    user, contest, problem = contest_fixture()
    user.role = 'manager'; user.save()
    monkeypatch.setenv('APP_ENV', 'test'); monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    package = stage_package(problem.id, user, {'reference': 'print(42)', 'language': 'python',
        'cases': [{'input_data': '', 'expected_output': '42', 'is_sample': False}],
        'known_wrong': [{'code': 'print(1)', 'language': 'python'}]}, 'correct tests')
    import pytest
    with pytest.raises(ValueError, match='验证'):
        activate_package(package.digest, user, 'too early')
    validate_staged_package(package.digest)
    activate_package(package.digest, user, 'reviewed')
    assert m.ContestProblem.get_by_id(problem.id).package_digest == package.digest


def test_failed_input_validator_invalidates_package(db, monkeypatch):
    from services.contest_packages import stage_package, validate_staged_package
    user, _, problem = contest_fixture()
    user.role = 'manager'; user.save()
    monkeypatch.setenv('APP_ENV', 'test'); monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    package = stage_package(problem.id, user, {'reference': 'print(42)', 'language': 'python',
        'cases': [{'input_data': 'bad input', 'expected_output': '42', 'is_sample': False}],
        'validator': {'code': 'import sys; sys.exit(1)', 'language': 'python'}}, 'invalid test')
    validate_staged_package(package.digest)
    assert m.ContestPackage.get_by_id(package.digest).validation_state == 'INVALID'


def test_competition_health_reports_waiting_and_projection_lag(db):
    from services.contest_metrics import competition_health
    user, contest, problem = contest_fixture()
    m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        received_at=contest.start_time, queued_at=contest.start_time, status='Pending')
    m.Contest.update(scoreboard_requested_version=3).where(m.Contest.id == contest.id).execute()
    health = competition_health()
    assert health['waiting'] == 1 and health['oldest_wait_seconds'] > 7000
    assert health['projection_version_lag'] == 3


def test_formal_http_pipeline_keeps_own_verdict_visible_during_freeze(app, db, cache, worker, monkeypatch):
    from controllers.contest_controller import api as contests_api
    from controllers.contest_rankings_controller import api as rankings_api, refresh_live_projection
    from flask_restx import Api
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='secret input', expected_output='42')
    monkeypatch.setenv('APP_ENV', 'test'); monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    api = Api(app); api.add_namespace(contests_api, path='/contests'); api.add_namespace(rankings_api, path='/contests')
    from interfaces.service_interfaces import IJWTService
    jwt = Mock(); jwt.verify_access_token.return_value = user.to_dict()
    services = lambda kind: jwt if kind == IJWTService else cache
    client = app.test_client(); headers = {'Authorization': 'Bearer synthetic', 'Idempotency-Key': 'formal-http'}
    with patch('controllers.contest_controller.inject', side_effect=services), patch('middleware.auth_middleware.inject', side_effect=services):
        path = f'/contests/{contest.id}/problems/{problem.id}/submit'
        response = client.post(path, json={'code': 'print(42)', 'language': 'python'}, headers=headers)
        assert response.status_code == 202
        claim = cache.list_claim('contest_judge_queue', 'contest_judge_queue:processing')
        worker._process_contest_task(claim['payload'])
        cache.list_ack('contest_judge_queue:processing', claim['receipt'])
        refresh_live_projection(contest.id)
        result = client.get(f'/contests/{contest.id}/problems/{problem.id}/submission/{response.json["submission_id"]}', headers=headers)
        assert result.json['status'] == 'AC' and result.json['details'] == []
        assert result.json['passed'] == result.json['total'] == 0
        board = client.get(f'/contests/{contest.id}/rankings')
        assert board.json['rankings'][0]['solved_count'] == 0
        assert board.json['rankings'][0]['problems'][0]['status'] == 'Pending'
        conditional = client.get(f'/contests/{contest.id}/rankings', headers={'If-None-Match': board.headers['ETag']})
        assert conditional.status_code == 304


def test_scoring_normalizes_timezone_and_excludes_missing_timestamp():
    from services.contest_scoring import compute_acm_scoreboard
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = compute_acm_scoreboard(entries=[{'entry_id': 1}], problem_indexes=['A','B'], start_at=start,
        submissions=[{'id':1, 'entry_id':1, 'problem_index':'A', 'verdict':'AC',
            'received_at':'2026-01-01T09:00:00+08:00'},
            {'id':2, 'entry_id':1, 'problem_index':'B', 'verdict':'AC', 'received_at':None}])
    assert result[0]['penalty'] == 60 and result[0]['solved_count'] == 1


def test_team_idempotency_is_shared_by_team_members(app, db, cache):
    from controllers.contest_controller import ContestProblemSubmitController as C
    user, contest, problem = contest_fixture()
    other = m.User.create(username='teammate')
    m.ContestParticipant.create(contest=contest, user=other)
    team = m.ContestTeam.create(contest=contest, captain=user, name='team')
    for member in (user, other):
        m.ContestTeamMember.create(contest=contest, team=team, user=member)
    original = m.ContestSubmission.create(contest=contest, team=team, user=user, contest_problem=problem,
        code='print(1)', language='python', idempotency_key='shared', job_id='shared-job')
    with app.test_request_context(method='POST', json={'code':'print(1)','language':'python'}, headers={'Idempotency-Key':'shared'}):
        with patch('controllers.contest_controller._get_current_user', return_value=other), patch('controllers.contest_controller.inject', return_value=cache):
            result, status = inspect.unwrap(C.post)(None, contest.id, problem.id)
            assert status == 202 and result['submission_id'] == original.id


def test_unapproved_candidate_hidden_from_team_result_api(app, db):
    from controllers.contest_controller import ContestProblemSubmissionResultController as C
    user, contest, problem = contest_fixture()
    candidate = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        rejudge_of=999, contest_eligible=False, status='AC')
    with app.test_request_context():
        with patch('controllers.contest_controller._get_current_user', return_value=user):
            assert C.get(None, contest.id, problem.id, candidate.id)[1] == 404


def test_oi_scoreboard_excludes_rejudge_and_practice(db):
    from controllers.contest_rankings_controller import _compute_rankings
    user, contest, problem = contest_fixture()
    contest.contest_type = 'OI'; contest.save()
    m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', status='AC', score=100, contest_eligible=False)
    board = _compute_rankings(contest.id)
    assert all(row['score'] == 0 for row in board['rankings'])


def test_heartbeat_does_not_depend_on_database():
    from services.judge_service import JudgeWorker
    worker = JudgeWorker(Mock(), Mock(), Mock())
    calls = []
    def beat():
        calls.append('alive')
        worker._stop_event.set()
    with patch('services.judge_service.get_database', side_effect=RuntimeError('DB unavailable')):
        worker._background(beat, 1, uses_db=False)
    assert calls == ['alive']


def test_terminal_testcase_details_live_in_judgement_archive(db, worker):
    user, contest, problem = contest_fixture()
    sub = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem, status='Checking')
    assert worker._transition_contest(sub.id, 1, 'Checking', 'AC', verdict='AC',
        testcase_results='[{"passed":true,"expected":"hidden"}]')
    assert m.ContestSubmission.get_by_id(sub.id).testcase_results is None
    assert 'hidden' in m.Judgement.get(m.Judgement.submission == sub.id).payload


def test_compilation_cache_verifies_artifacts_and_reuses_clean_copy(tmp_path, monkeypatch):
    from services.compile_cache import prepare_cached
    import json
    from pathlib import Path
    monkeypatch.setenv('APP_ENV', 'test'); monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1'); monkeypatch.setenv('JUDGE_COMPILE_CACHE', str(tmp_path / 'cache'))
    source = '#include <iostream>\nint main(){std::cout << 42;}'
    first, error, _ = prepare_cached(source, 'cpp')
    assert error is None and first.run('', 1, 128)[0].strip() == '42'
    first.close()
    second, error, _ = prepare_cached(source, 'cpp')
    assert second.cache_hit and second.run('', 1, 128)[0].strip() == '42'
    second.close()
    artifact = next((tmp_path / 'cache').glob('*/main'))
    artifact.write_bytes(b'corrupted')
    recovered, error, _ = prepare_cached(source, 'cpp')
    assert not recovered.cache_hit and recovered.run('', 1, 128)[0].strip() == '42'
    recovered.close()


def test_language_resource_profiles_are_explicit_and_bounded():
    from services.contest_packages import runtime_limits
    package = {'time_limit': 1000, 'memory_limit': 256,
        'language_limits': {'java': {'cpu_factor': 2, 'memory_extra_mb': 64}}}
    assert runtime_limits(package, 'java') == (2., 320)
    assert runtime_limits(package, 'cpp') == (1., 256)
    package['language_limits']['java']['cpu_factor'] = float('inf')
    import pytest
    with pytest.raises(ValueError):
        runtime_limits(package, 'java')


def test_worker_stage_timestamps_do_not_depend_on_host_timezone(db, worker, monkeypatch):
    import os
    import time
    from services.contest_operations import now
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='42')
    sub = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        received_at=now(), code='print(42)', language='python', job_id='utc-host')
    previous = os.environ.get('TZ')
    try:
        monkeypatch.setenv('TZ', 'UTC'); time.tzset()
        monkeypatch.setenv('APP_ENV', 'test'); monkeypatch.setenv('JUDGE_BACKEND', 'local')
        monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
        worker._process_contest_task({'submission_id': sub.id, 'job_id': sub.job_id})
        saved = m.ContestSubmission.get_by_id(sub.id)
        assert 0 <= (saved.finished_at-saved.received_at).total_seconds() < 10
    finally:
        if previous is None:
            os.environ.pop('TZ', None)
        else:
            os.environ['TZ'] = previous
        time.tzset()


def test_scoped_health_does_not_include_other_contests(db):
    from services.contest_metrics import competition_health
    user, contest, problem = contest_fixture()
    other = m.Contest.create(title='other', lifecycle_state='RUNNING', scoreboard_requested_version=99)
    other_problem = m.ContestProblem.create(contest=other, problem_index='A', title='other', description='', correct_answer='print(1)')
    m.ContestSubmission.create(contest=other, user=user, contest_problem=other_problem, status='Pending')
    health = competition_health(contest.id)
    assert health['waiting'] == 0 and health['projection_version_lag'] == 0
