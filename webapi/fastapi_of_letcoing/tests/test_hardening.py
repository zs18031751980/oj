"""回归目标：越权、故障时假成功、认证撤销失效、任务租约与输入边界。"""
import logging
from unittest.mock import patch

import pytest
from flask import g
from peewee import OperationalError

from core.db_robust import DatabaseUnavailableError, ensure_connected
from middleware.auth_middleware import RateLimitMiddleware
from models import db_models as m
from services.config_service import ConfigService
from services.jwt_service import JWTService


def test_anonymous_execution_is_rate_limited(app, cache):
    with patch('middleware.auth_middleware.inject', return_value=cache):
        @app.get('/expensive')
        @RateLimitMiddleware.rate_limit(2, 60)
        def expensive():
            return {'ok': True}
        client = app.test_client()
        assert client.get('/expensive').status_code == 200
        assert client.get('/expensive').status_code == 200
        assert client.get('/expensive').status_code == 429


def test_limits_do_not_share_route_budgets(app, cache):
    @app.before_request
    def identify():
        g.current_user = {'id': 1}
    with patch('middleware.auth_middleware.inject', return_value=cache):
        for path in ('/run', '/submit'):
            app.add_url_rule(path, path, RateLimitMiddleware.rate_limit(1, 60)(lambda: {'ok': True}))
        client = app.test_client()
        assert client.get('/run').status_code == 200
        assert client.get('/submit').status_code == 200


def test_db_context_does_not_attempt_to_reyield(db):
    with pytest.raises(DatabaseUnavailableError):
        with ensure_connected(db):
            raise OperationalError('simulated connection loss')


def test_submission_details_are_not_anonymous(app, db, cache):
    from flask_restx import Api
    from controllers.submission_controller import api
    Api(app).add_namespace(api, '/submissions')
    cache.set('submission:7', {'id': 7, 'code': 'private'}, 60)
    with patch('controllers.submission_controller.inject', return_value=cache):
        assert app.test_client().get('/submissions/7').status_code == 401


def test_disabled_user_and_logout_invalidate_both_tokens(db, cache):
    user = m.User.create(username='alice')
    service = JWTService(ConfigService({'JWT_SECRET_KEY': 'a' * 48}), logging.getLogger('test'), cache)
    tokens = service.generate_tokens(user.to_dict())
    assert service.verify_access_token(tokens.access_token)
    m.User.update(is_active=False).where(m.User.id == user.id).execute()
    assert service.verify_access_token(tokens.access_token) is None
    assert service.refresh_access_token(tokens.refresh_token) is None
    m.User.update(is_active=True).where(m.User.id == user.id).execute()
    tokens = service.generate_tokens(user.to_dict())
    assert service.revoke_token(tokens.access_token)
    assert service.refresh_access_token(tokens.refresh_token) is None


def test_refresh_is_one_time_and_replay_revokes_session(db, cache):
    user = m.User.create(username='alice')
    service = JWTService(ConfigService({'JWT_SECRET_KEY': 'a' * 48}), logging.getLogger('test'), cache)
    first = service.generate_tokens(user.to_dict())
    second = service.refresh_access_token(first.refresh_token)
    assert second is not None
    assert first.refresh_token != second.refresh_token
    assert service.refresh_access_token(first.refresh_token) is None
    assert service.verify_access_token(second.access_token) is None


def test_queue_duplicate_payloads_have_distinct_delivery_receipts(cache):
    cache.list_push('q', {'id': 1}, {'id': 1})
    first = cache.list_claim('q', 'q:processing')
    second = cache.list_claim('q', 'q:processing')
    assert first['receipt'] != second['receipt']
    assert cache.list_ack('q:processing', first['receipt'])
    assert cache.list_length('q:processing') == 1


def test_queue_expired_owner_cannot_ack_reclaimed_delivery(cache):
    cache.list_push('q', {'id': 1})
    first = cache.list_claim('q', 'q:processing')
    cache._client.delete(cache._lease_key('q:processing', first['receipt']))
    assert cache.list_recover('q:processing', 'q') == 1
    second = cache.list_claim('q', 'q:processing')
    assert not cache.list_ack('q:processing', first['receipt'])
    assert cache.list_ack('q:processing', second['receipt'])


def test_code_request_rejects_null_source(app):
    from controllers.code_controller import _parse_execution_request
    with app.test_request_context(json={'code': None}):
        value, error = _parse_execution_request()
        assert value is None
        assert error[1] == 400


def test_login_account_budget_spans_multiple_ips(app, cache):
    @app.post('/login')
    @RateLimitMiddleware.rate_limit(10, 60, account_max_requests=2)
    def login():
        return {'ok': True}
    with patch('middleware.auth_middleware.inject', return_value=cache):
        client = app.test_client()
        assert [client.post('/login', json={'identifier': 'alice'}, environ_base={'REMOTE_ADDR': f'192.0.2.{n}'}).status_code
                for n in range(1, 4)] == [200, 200, 429]


def test_invalid_database_url_does_not_fall_back_to_localhost():
    with pytest.raises(ValueError):
        ConfigService({'DATABASE_URL': 'postgresql://host:bad/database'}).get_database_config()
