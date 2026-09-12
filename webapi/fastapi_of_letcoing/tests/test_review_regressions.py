import asyncio
import inspect
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from flask import g
from models import db_models as m
from services.config_service import ConfigService


def fixture_problem(public=True):
    user = m.User.create(username='owner')
    contest = m.Contest.create(title='ended', is_public=public, lifecycle_state='FINALIZED',
        end_time=datetime(2020, 1, 1))
    problem = m.ContestProblem.create(contest=contest, title='problem', problem_index='A', description='test', correct_answer='print(1)')
    return user, contest, problem


def test_library_results_require_auth(app):
    from controllers.problem_controller import LibraryProblemSubmissionResultController as C
    with app.test_request_context():
        assert C.get(None, 1)[1] == 401


def test_library_results_isolate_ownership_and_contest_type(app, db):
    from controllers.problem_controller import LibraryProblemSubmissionResultController as C
    user, contest, problem = fixture_problem()
    sub = m.ContestSubmission.create(user=user, contest=contest, contest_problem=problem,
        contest_eligible=False, status='WA', testcase_results=json.dumps([
            {'passed': False, 'actual': 'secret actual', 'expected': 'secret answer'}]))
    with app.test_request_context():
        g.current_user = user.to_dict()
        body, status = inspect.unwrap(C.get)(None, sub.id)
        assert status == 200 and 'secret' not in str(body)
        sub.contest_eligible = True
        sub.save()
        assert inspect.unwrap(C.get)(None, sub.id)[1] == 404
        sub.contest_eligible = False
        sub.save()
        g.current_user = {'id': user.id + 1, 'role': 'member'}
        assert inspect.unwrap(C.get)(None, sub.id)[1] == 404


def test_library_durable_idempotent_submission_with_redis_down(app, db):
    from controllers.problem_controller import LibraryProblemSubmitController as C
    user, contest, problem = fixture_problem()
    with app.test_request_context(method='POST', json={'contest_problem_id': problem.id,
            'code': 'print(1)', 'language': 'python'}, headers={'Idempotency-Key': 'retry'}):
        g.current_user = user.to_dict()
        with patch('controllers.problem_controller.inject', return_value=Mock(enqueue_with_state=Mock(return_value=False))):
            first, status = inspect.unwrap(C.post)(None)
            second, _ = inspect.unwrap(C.post)(None)
        assert status == 202 and first['submission_id'] == second['submission_id']
        sub = m.ContestSubmission.get_by_id(first['submission_id'])
        assert sub.job_id and not sub.contest_eligible and sub.code == 'print(1)'
        assert m.ContestJudgeOutbox.get().state == 'PENDING'


def test_private_ended_problem_hidden(app, db):
    from controllers.problem_controller import ProblemDetailController as C
    _, _, problem = fixture_problem(False)
    with app.test_request_context():
        assert C.get(None, 1000000 + problem.id)[1] == 404


def test_manager_announcement_hidden(app, db):
    from controllers.announcement_controller import AnnouncementDetailController as C
    ann = m.Announcement.create(title='private', content='secret', permission='manager')
    with app.test_request_context():
        assert C.get(None, ann.id)[1] == 404


def test_freeze_snapshot_roundtrip(db):
    from controllers.contest_rankings_controller import _load_public_snapshot
    _, contest, _ = fixture_problem()
    m.ContestScoreboardSnapshot.create(contest=contest, snapshot_kind='PUBLIC_FREEZE', payload='{"rankings": []}')
    assert _load_public_snapshot(contest) == {'rankings': []}


def test_provider_demotion_revokes_old_session(db):
    from services.user_service import UserService
    user = m.User.create(username='sso', provider='oidc', provider_id='1', role='manager')
    m.AuthSession.create(id='session', user=user, refresh_hash='old', expires_at=datetime.now()+timedelta(days=1))
    result = asyncio.run(UserService(ConfigService({})).find_or_create_user('oidc', '1', {'role': 'member'}))
    assert result['role'] == 'member' and m.AuthSession.get().revoked


def test_oidc_defaults_to_validation_and_ignores_unverified_claims():
    from services.oidc_service import OIDCService
    import jwt
    service = OIDCService(ConfigService({}), Mock())
    assert not service._should_skip_id_token_validation('oidc')
    client = Mock()
    client.userinfo.return_value = {'sub': '1', 'preferred_username': 'alice', 'role': 'member'}
    token = {'id_token': jwt.encode({'sub': '1', 'role': 'manager'}, 'untrusted-key-' * 4)}
    assert service._get_user_info('oidc', client, token)['role'] == 'member'


def test_browser_refresh_retries_lost_response_but_rejects_different_replay(db):
    import logging
    from services.jwt_service import JWTService
    user = m.User.create(username='browser')
    service = JWTService(ConfigService({'JWT_SECRET_KEY': 's' * 48}), logging.getLogger('test'), Mock())
    old = service.generate_tokens(user.to_dict())
    first = service.refresh_browser_session(old.refresh_token, 'request-1')
    retry = service.refresh_browser_session(old.refresh_token, 'request-1')
    assert first.refresh_token == retry.refresh_token
    assert service.refresh_browser_session(first.refresh_token, 'request-1').refresh_token == first.refresh_token
    assert service.refresh_browser_session(old.refresh_token, 'request-2') is None
    assert service.verify_access_token(first.access_token) is None


def test_cookie_tokens_are_httponly_and_absent_from_json(app):
    from services.browser_session import browser_tokens
    @app.route('/login', methods=['POST'])
    def login():
        return browser_tokens({'access_token': 'access', 'refresh_token': 'secret'})
    response = app.test_client().post('/login', json={'remember': True})
    assert 'refresh_token' not in response.json
    assert 'HttpOnly' in response.headers['Set-Cookie']
    assert 'secret' not in response.get_data(as_text=True)


def test_discussion_page_is_bounded_with_constant_queries(app, db):
    from controllers.discussion_controller import DiscussionListController as C
    from playhouse.test_utils import count_queries
    user = m.User.create(username='author')
    for i in range(35):
        m.Discussion.create(author=user, title=str(i), content='private long body' * 1000)
    with app.test_request_context('/?limit=10&offset=0'):
        with patch('controllers.discussion_controller._get_current_user', return_value=user):
            with count_queries() as queries:
                rows, status = C.get(None)
    assert status == 200 and len(rows) == 10
    assert queries.count <= 3
    assert all(len(row.get('content', '')) <= 200 for row in rows)


def test_like_set_is_idempotent(app, db):
    from controllers.discussion_controller import DiscussionLikeController as C
    user = m.User.create(username='author')
    post = m.Discussion.create(author=user, title='post', content='body')
    with app.test_request_context(method='POST', json={'liked': True}):
        with patch('controllers.discussion_controller._get_current_user', return_value=user):
            assert C.post(None, post.id)[0]['liked']
            assert C.post(None, post.id)[0]['liked']
    assert m.Discussion.get_by_id(post.id).like_count == 1
    assert m.DiscussionLike.select().count() == 1


def test_finalization_ignores_practice_and_rolls_back_snapshot(app, db):
    from controllers.contest_rankings_controller import ContestRankingsFinalizeController as C
    import pytest
    user, contest, problem = fixture_problem()
    contest.lifecycle_state = 'RUNNING'; contest.save()
    user.role = 'manager'; user.save()
    m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        status='Pending', contest_eligible=False)
    with app.test_request_context(method='POST'):
        with patch('controllers.contest_rankings_controller._get_current_user', return_value=user):
            with patch.object(m.Contest, 'save', side_effect=RuntimeError('disk error')):
                with pytest.raises(RuntimeError):
                    C.post(None, contest.id)
    assert not m.ContestScoreboardSnapshot.select().where(m.ContestScoreboardSnapshot.snapshot_kind == 'FINAL').exists()
    assert m.Contest.get_by_id(contest.id).lifecycle_state == 'RUNNING'


def test_regular_rankings_projection_keeps_correct_rank_when_paginated(db):
    from services.ranking_projection import refresh_rankings, ranking_page
    a = m.User.create(username='a'); b = m.User.create(username='b')
    easy = m.Problem.create(title='easy', description='', difficulty='简单')
    hard = m.Problem.create(title='hard', description='', difficulty='困难')
    m.Submission.create(user=a, problem=easy, code='x', language='python', status='AC')
    for _ in range(2):
        m.Submission.create(user=b, problem=hard, code='x', language='python', status='AC')
    refresh_rankings()
    assert ranking_page(1, 0)[0]['user_id'] == b.id
    assert ranking_page(1, 0)[0]['solved_count'] == 1
    assert ranking_page(1, 1)[0]['rank'] == 2


def test_production_rejects_insecure_public_endpoints():
    import pytest
    from core.runtime_config import validate_runtime_config
    with pytest.raises(ValueError, match='HTTPS'):
        validate_runtime_config({'APP_ENV': 'production', 'JWT_SECRET_KEY': 'a' * 48,
            'SECRET_KEY': 'b' * 48, 'FRONTEND_URL': 'http://site.test',
            'PUBLIC_BACKEND_URL': 'https://api.test', 'ALLOWED_ORIGINS': ['https://site.test']})


def test_browser_refresh_requires_csrf_and_sets_cookie_over_http(app, db, cache):
    import logging
    from flask_restx import Api
    from controllers.auth_controller import api as auth_api
    from services.browser_session import COOKIE_NAME
    from services.jwt_service import JWTService
    from middleware.request_middleware import register_request_hooks
    register_request_hooks(app)
    Api(app).add_namespace(auth_api, path='/auth')
    user = m.User.create(username='browser-http')
    service = JWTService(ConfigService({'JWT_SECRET_KEY': 's' * 48}), logging.getLogger('test'), cache)
    token = service.generate_tokens(user.to_dict())
    client = app.test_client(); client.set_cookie(COOKIE_NAME, token.refresh_token, path='/auth')
    with patch('controllers.auth_controller.inject', return_value=service), patch('middleware.auth_middleware.inject', return_value=cache):
        assert client.post('/auth/refresh', json={}).status_code == 403
        headers = {'X-CSRF-Protection': '1', 'Idempotency-Key': 'test-request'}
        assert client.post('/auth/refresh', json={}, headers={**headers, 'Origin': 'https://evil.test'}).status_code == 403
        response = client.post('/auth/refresh', json={}, headers=headers)
        assert response.status_code == 200
        assert 'refresh_token' not in response.json and 'HttpOnly' in response.headers['Set-Cookie']
        assert service.verify_access_token(response.json['access_token'])
        assert client.post('/auth/logout', json={}, headers=headers).status_code == 200
        assert service.verify_access_token(response.json['access_token']) is None


def test_provider_role_and_local_override_are_separate(db):
    from services.user_service import UserService
    user = m.User.create(username='override', provider='oidc', provider_id='2',
                         role='manager', local_role='manager', provider_role='staff')
    result = asyncio.run(UserService(ConfigService({})).find_or_create_user('oidc', '2', {'role': 'member'}))
    current = m.User.get_by_id(user.id)
    assert result['role'] == 'manager' and current.provider_role == 'member'


def test_library_does_not_trust_stale_past_flag(db):
    from controllers.problem_controller import _is_contest_ended
    contest = m.Contest.create(title='future', status='past', is_public=True,
        lifecycle_state='SCHEDULED', end_time=datetime.now()+timedelta(days=10))
    assert not _is_contest_ended(contest)


def test_rescan_is_not_anonymous(app):
    from controllers.learn_resources_controller import LearnRescan
    with app.test_request_context(method='POST'):
        assert LearnRescan.post(None)[1] == 401


def test_initial_live_snapshot_does_not_consume_future_event(db):
    from controllers.contest_rankings_controller import _save_live_projection
    contest = m.Contest.create(title='new', scoreboard_requested_version=0)
    _save_live_projection(contest, {'rankings': []})
    assert m.ContestScoreboardSnapshot.get().scoreboard_version == 0
