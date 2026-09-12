import importlib.util
import io
import os
import sys
import time
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import pytest
from flask_restx import Api
from PIL import Image

from models import db_models as m


def test_oauth_callback_contains_only_bound_one_time_code(app, db):
    from controllers.auth_controller import _frontend_callback_url
    from models.auth_models import TokenResponse, UserInfo
    user = m.User.create(username='alice')
    with app.test_request_context():
        with patch('controllers.auth_controller._get_frontend_url', return_value='https://front.test'):
            url = _frontend_callback_url(TokenResponse('secret-access', 'secret-refresh', 900),
                                         UserInfo(str(user.id), 'alice', ''), '//evil.test')
        assert 'secret-access' not in url and 'secret-refresh' not in url
        assert parse_qs(urlparse(url).query)['next'] == ['/']
        assert 'code' in parse_qs(urlparse(url).query)


def test_regular_submission_returns_unavailable_when_db_save_fails(app, cache):
    from controllers.submission_controller import SubmissionListCreateController
    class FailedSubmission:
        PENDING = 'Pending'
        @staticmethod
        def create(**kwargs):
            raise RuntimeError('database down')
    with app.test_request_context(json={'problem_id': 1, 'code': 'print(1)'}):
        from flask import g
        g.current_user = {'id': 1}
        with patch('controllers.submission_controller.Submission', FailedSubmission), \
             patch('controllers.submission_controller.inject', return_value=cache), \
             patch('controllers.submission_controller._get_problem_data', return_value={'testCases': []}):
            response = SubmissionListCreateController.post.__wrapped__.__wrapped__(None)
            assert response[1] == 503
            assert cache.list_length('judge_queue') == 0


def test_avatar_rejects_spoofed_mime(app, db, tmp_path):
    from controllers.user_controller import UserAvatarController
    user = m.User.create(username='alice')
    with app.test_request_context(method='POST', data={'avatar': (io.BytesIO(b'<html>bad</html>'), 'evil.html', 'image/png')}):
        with patch('controllers.user_controller._get_current_user', return_value=user), \
             patch('controllers.user_controller._AVATAR_DIR', str(tmp_path)):
            assert UserAvatarController().post()[1] == 400


def test_application_factory_does_not_start_workers_or_run_migrations():
    assert importlib.util.find_spec('app_factory') is not None, 'missing side-effect-free app factory'
    from app_factory import create_app
    with patch('services.judge_service.start_judge_worker', side_effect=AssertionError('worker started')), \
         patch('models.db_models.run_schema_migrations', side_effect=AssertionError('migration ran')):
        app = create_app({'TESTING': True, 'JWT_SECRET_KEY': 'a' * 48, 'SECRET_KEY': 'b' * 48})
        assert app.test_client().get('/healthz').status_code == 200
        assert app.test_client().post('/code/run/public', json=[1]).status_code == 400


def test_production_rejects_missing_secrets():
    assert importlib.util.find_spec('core.runtime_config') is not None
    from core.runtime_config import validate_runtime_config
    with pytest.raises(ValueError):
        validate_runtime_config({'APP_ENV': 'production'})


def test_local_supervisor_deadline_covers_blocked_stdin(tmp_path):
    assert importlib.util.find_spec('services.execution_runtime') is not None
    from services.execution_runtime import run_process
    started = time.monotonic()
    result = run_process([sys.executable, '-c', 'import time; time.sleep(10)'],
                         'x' * 1000000, .15, cwd=str(tmp_path))
    assert result['timed_out']
    assert time.monotonic() - started < 2


def test_sandbox_refuses_implicit_local_execution(monkeypatch, tmp_path):
    assert importlib.util.find_spec('services.sandbox_service') is not None
    from services.sandbox_service import execute
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    with pytest.raises(RuntimeError):
        execute(['python3', '-c', 'print(1)'], '', 1, 256, str(tmp_path))


def test_problem_creation_never_executes_reference_code_in_api(app, db):
    from controllers.contest_problem_controller import ContestProblemListController
    user = m.User.create(username='manager', role='manager')
    contest = m.Contest.create(title='draft')
    data = {'problem_index': 'A', 'title': 'A', 'description': 'test',
            'correct_answer': 'print(1)', 'language': 'python',
            'testcases': [{'input': '', 'output': '1', 'is_sample': False}]}
    with app.test_request_context(f'/?contest_id={contest.id}', method='POST', json=data):
        with patch('controllers.contest_problem_controller._require_manager', return_value=(user, None)), \
             patch('controllers.contest_problem_controller._verify_reference_answer', side_effect=AssertionError('API executed code')):
            payload, status = ContestProblemListController().post()
            assert status == 201
            assert payload['testcase_generation'] == 'pending'


def test_transactional_error_response_rolls_back_partial_writes(db):
    from services.contest_lifecycle import transactional
    @transactional
    def operation():
        m.User.create(username='partial')
        return {'error': 'failed'}, 503
    assert operation()[1] == 503
    assert not m.User.select().where(m.User.username == 'partial').exists()


def test_log_formatter_is_structured_and_redacts_credentials():
    import json
    import logging
    from services import logger_service
    assert hasattr(logger_service, 'SafeJSONFormatter')
    record = logging.LogRecord('letcoding', logging.ERROR, __file__, 1,
        'failure Bearer synthetic-token password=synthetic-password https://host/callback?code=synthetic-code', (), None)
    rendered = logger_service.SafeJSONFormatter().format(record)
    assert json.loads(rendered)['level'] == 'ERROR'
    assert 'synthetic' not in rendered


def test_testcase_input_requires_text_and_byte_limit():
    from controllers.contest_problem_controller import _normalize_testcases
    for value in (None, {'nested': 1}, '汉' * 30000):
        with pytest.raises(ValueError):
            _normalize_testcases([{'input': value, 'output': ''}], [])
