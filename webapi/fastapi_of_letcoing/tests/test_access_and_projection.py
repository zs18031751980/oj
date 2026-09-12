import asyncio
import logging
from unittest.mock import patch

from flask import g, session
from playhouse.test_utils import count_queries

from models import db_models as m
from services.config_service import ConfigService
from services.jwt_service import JWTService


def test_submission_owner_boundary_hides_code_and_testcase_secrets(app, db):
    from controllers.submission_controller import SubmissionStatusController
    alice = m.User.create(username='alice')
    bob = m.User.create(username='bob')
    problem = m.Problem.create(id=123, title='test', description='test')
    submission = m.Submission.create(user=alice, problem=problem, code='private', language='python',
        testcase_results='[{"passed":false,"input":"secret input","expected_output":"secret answer"}]')
    with app.test_request_context():
        g.current_user = bob.to_dict()
        assert SubmissionStatusController.get.__wrapped__(None, submission.id)[1] == 404
        g.current_user = alice.to_dict()
        body, status = SubmissionStatusController.get.__wrapped__(None, submission.id)
        assert status == 200 and body['code'] == 'private'
        assert 'secret' not in str(body['testcase_results'])


def test_password_change_revokes_sessions_without_redis(db, cache):
    from services.database_service import DatabaseService
    config = ConfigService({'JWT_SECRET_KEY': 'a' * 48})
    user = m.User.create(username='alice')
    jwt = JWTService(config, logging.getLogger('test'), cache)
    tokens = jwt.generate_tokens(user.to_dict())
    with patch.object(cache, 'is_connected', return_value=False):
        assert jwt.verify_access_token(tokens.access_token)
        assert asyncio.run(DatabaseService(config).update(m.User, user.id, password_hash='new-hash'))
        assert jwt.verify_access_token(tokens.access_token) is None
        assert jwt.refresh_access_token(tokens.refresh_token) is None


def test_oauth_exchange_requires_binding_and_is_single_use(app, db, cache):
    from controllers.auth_controller import OAuthExchangeController
    from services.jwt_service import token_hash, utcnow
    from datetime import timedelta
    user = m.User.create(username='alice')
    m.OAuthGrant.create(id=token_hash('one-time-code'), user=user,
        binding_hash=token_hash('browser-cookie'), expires_at=utcnow() + timedelta(seconds=60))
    jwt = JWTService(ConfigService({'JWT_SECRET_KEY': 'a' * 48}), logging.getLogger('test'), cache)
    with app.test_request_context(method='POST', json={'code': 'one-time-code'}):
        session['oauth_exchange_binding'] = 'wrong-browser'
        assert OAuthExchangeController.post.__wrapped__(None)[1] == 400
        session['oauth_exchange_binding'] = 'browser-cookie'
        with patch('controllers.auth_controller.inject', return_value=jwt):
            body, status = OAuthExchangeController.post.__wrapped__(None)
            assert status == 200 and jwt.verify_access_token(body['access_token'])
            assert OAuthExchangeController.post.__wrapped__(None)[1] == 400


def test_rankings_query_count_does_not_grow_per_participant(db):
    from controllers.contest_rankings_controller import _compute_rankings
    contest = m.Contest.create(title='test')
    def add_participants(start, end):
        for index in range(start, end):
            user = m.User.create(username=f'user-{index}')
            m.ContestParticipant.create(contest=contest, user=user)
    add_participants(0, 1)
    with count_queries() as small:
        _compute_rankings(contest.id)
    add_participants(1, 40)
    with count_queries() as large:
        result = _compute_rankings(contest.id)
    assert len(result['rankings']) == 40
    assert large.count == small.count


def test_projection_rebuild_records_requested_version(db):
    from controllers.contest_rankings_controller import refresh_dirty_projections
    contest = m.Contest.create(title='test', scoreboard_requested_version=7)
    refresh_dirty_projections()
    snapshot = m.ContestScoreboardSnapshot.get(m.ContestScoreboardSnapshot.contest == contest.id)
    assert snapshot.scoreboard_version == 7
    with patch('controllers.contest_rankings_controller._compute_rankings', side_effect=AssertionError('unnecessary rebuild')):
        refresh_dirty_projections()


def test_provider_sync_cannot_reactivate_locally_disabled_account(db):
    from services.user_service import UserService
    user = m.User.create(username='alice', provider='test', provider_id='123', is_active=False)
    result = asyncio.run(UserService(ConfigService({})).find_or_create_user(
        'test', '123', {'username': 'alice', 'is_active': True}))
    assert result['is_active'] is False
    assert m.User.get_by_id(user.id).is_active is False
