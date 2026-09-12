"""真实 HTTP 控制器 → DB/outbox → Redis → Worker → HTTP 结果的隔离回归。"""
import logging
from unittest.mock import patch

from flask_restx import Api
from werkzeug.security import generate_password_hash

from interfaces.service_interfaces import IJWTService, IUserService, IRedisService
from models import db_models as m
from services.config_service import ConfigService
from services.jwt_service import JWTService
from services.user_service import UserService
from test_job_reliability import worker
from test_review_regressions import fixture_problem


def test_login_library_judge_and_cache_loss_end_to_end(app, db, cache, worker, monkeypatch):
    from controllers.auth_controller import api as auth_api
    from controllers.problem_controller import api as problem_api
    from controllers.contest_rankings_controller import _compute_rankings
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    user, contest, problem = fixture_problem()
    user.password_hash = generate_password_hash('test-password'); user.save()
    m.ContestParticipant.create(contest=contest, user=user)
    m.ContestTestcase.create(contest_problem=problem, input_data='hidden input', expected_output='42')
    config = ConfigService({'JWT_SECRET_KEY': 'a' * 48})
    jwt = JWTService(config, logging.getLogger('test'), cache)
    services = {IJWTService: jwt, IUserService: UserService(config), IRedisService: cache}
    api = Api(app); api.add_namespace(auth_api, path='/auth'); api.add_namespace(problem_api, path='/problems')
    client = app.test_client()
    with patch('controllers.auth_controller.inject', side_effect=services.__getitem__), \
         patch('middleware.auth_middleware.inject', side_effect=services.__getitem__), \
         patch('controllers.problem_controller.inject', side_effect=services.__getitem__):
        login = client.post('/auth/login/password', json={'identifier': 'owner', 'password': 'test-password'})
        assert login.status_code == 200
        assert 'refresh_token' not in login.json['tokens']
        headers = {'Authorization': 'Bearer ' + login.json['tokens']['access_token'], 'Idempotency-Key': 'pipeline'}
        accepted = client.post('/problems/library/submit', headers=headers,
            json={'contest_problem_id': problem.id, 'code': 'print(42)', 'language': 'python'})
        assert accepted.status_code == 202
        claim = cache.list_claim('practice_judge_queue', 'practice_judge_queue:processing')
        assert worker._process_contest_task(claim['payload']) is not False
        cache.list_ack('practice_judge_queue:processing', claim['receipt'])
        cache._client.flushdb()
        path = f"/problems/library/submission/{accepted.json['submission_id']}"
        assert client.get(path).status_code == 401
        result = client.get(path, headers=headers)
        assert result.status_code == 200 and result.json['status'] == 'AC'
        assert 'hidden input' not in result.get_data(as_text=True)
        assert not result.json['testcase_results'][0]['expected']
        rankings = _compute_rankings(contest.id)
        assert len(rankings['rankings']) == 1
        assert rankings['rankings'][0]['solved_count'] == 0
        assert rankings['rankings'][0]['score'] == 0
