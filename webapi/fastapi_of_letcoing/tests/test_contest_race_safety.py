"""真实多连接验证重试和权限撤销的事务边界。"""
import inspect
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

import pytest
from flask import g
from models import db_models as m
from test_postgres import postgres
from test_acm_upgrade import contest_fixture


def concurrent_commit(database, operation):
    def execute():
        with database.connection_context(), database.atomic():
            operation()
    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(execute).result(timeout=5)


@pytest.mark.parametrize('conflict', [False, True])
def test_waiting_duplicate_precedes_quota(postgres, app, cache, conflict):
    from controllers import contest_controller as controller
    m.run_schema_migrations()
    user, contest, problem = contest_fixture()
    contest.active_submission_limit = 1; contest.save()
    lock = controller.lock_contest
    def another_request_finishes(contest_id):
        def accept():
            with postgres.atomic():
                lock(contest_id)
                row = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
                    idempotency_key='same-request', code='print(2)' if conflict else 'print(1)',
                    language='python', status='Pending', job_id='accepted-before-lock')
                m.ContestJudgeOutbox.create(submission=row)
        concurrent_commit(postgres, accept)
        return lock(contest_id)
    with app.test_request_context(method='POST', json={'code': 'print(1)', 'language': 'python'},
            headers={'Idempotency-Key': 'same-request'}):
        g.current_user = user.to_dict()
        with patch.object(controller, '_get_current_user', return_value=user), \
             patch.object(controller, 'inject', return_value=cache), \
             patch.object(controller, 'lock_contest', side_effect=another_request_finishes):
            result = inspect.unwrap(controller.ContestProblemSubmitController.post)(None, contest.id, problem.id)
    assert result[1] == (409 if conflict else 202)
    if not conflict:
        assert result[0]['job_id'] == 'accepted-before-lock' and result[0]['idempotent_replay']
    assert m.ContestSubmission.select().count() == 1
    assert m.ContestJudgeOutbox.select().count() == 1


@pytest.mark.parametrize('operation', ['rejudge', 'team', 'answer', 'stage', 'activate', 'rules', 'claim'])
def test_revocation_committed_before_lock_prevents_mutation(postgres, app, operation):
    from services import contest_operations as ops
    from services import contest_packages as packages
    from controllers import contest_operations_controller as controller
    m.run_schema_migrations()
    user, contest, problem = contest_fixture()
    user.role = 'manager'; user.save()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    row = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem, status='WA')
    question = m.ContestClarification.create(contest=contest, author=user, question='question')
    package = packages.publish_package(problem, user.id)
    if operation in {'team', 'rules'}:
        contest.lifecycle_state = 'DRAFT'
        contest.start_time = ops.now()+timedelta(hours=1)
        contest.save()
    lock = ops.lock_contest
    def revoke_then_lock(contest_id):
        concurrent_commit(postgres, lambda: m.User.update(role='member').where(m.User.id == user.id).execute())
        return lock(contest_id)
    actions = {
        'rejudge': lambda: ops.create_rejudge(contest.id, user, [row.id], 'reason'),
        'team': lambda: ops.create_team(contest.id, user, 'team', [user.id]),
        'answer': lambda: ops.answer_clarification(question.id, user, 'answer'),
        'stage': lambda: packages.stage_package(problem.id, user, {'cases': [{'input_data': '', 'expected_output': '2'}]}, 'reason'),
        'activate': lambda: packages.activate_package(package.digest, user, 'reason'),
        'rules': lambda: inspect.unwrap(controller.Rules.post)(None, contest.id),
        'claim': lambda: inspect.unwrap(controller.ClarificationAnswer.post)(None, contest.id, question.id),
    }
    payload = {'allowed_languages': ['python'], 'reason': 'reason'} if operation == 'rules' else {'action': 'claim'}
    with app.test_request_context(method='POST', json=payload):
        with patch.object(controller, '_get_current_user', return_value=user), \
             patch.object(ops, 'lock_contest', side_effect=revoke_then_lock):
            with pytest.raises(PermissionError):
                actions[operation]()
    assert m.User.get_by_id(user.id).role == 'member'
    assert m.ContestAudit.select().count() == 0
    assert m.RejudgeBatch.select().count() == 0
    assert m.ContestTeam.select().count() == 0
    assert m.ContestPackage.select().count() == 1
    assert m.ContestProblem.get_by_id(problem.id).package_digest is None
    assert m.ContestClarification.get_by_id(question.id).answer is None
    assert m.ContestClarification.get_by_id(question.id).claimed_by is None
    assert m.Contest.get_by_id(contest.id).allowed_languages == contest.allowed_languages


@pytest.mark.parametrize('revocation', ['account', 'participation'])
def test_submit_rechecks_identity_after_waiting(postgres, app, cache, revocation):
    from controllers import contest_controller as controller
    m.run_schema_migrations()
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='1')
    lock = controller.lock_contest
    def revoke_then_lock(contest_id):
        def revoke():
            if revocation == 'account':
                m.User.update(is_active=False).where(m.User.id == user.id).execute()
            else:
                m.ContestParticipant.delete().where(m.ContestParticipant.contest == contest,
                    m.ContestParticipant.user == user).execute()
        concurrent_commit(postgres, revoke)
        return lock(contest_id)
    with app.test_request_context(method='POST', json={'code': 'print(1)', 'language': 'python'}):
        g.current_user = user.to_dict()
        with patch.object(controller, '_get_current_user', return_value=user), \
             patch.object(controller, 'inject', return_value=cache), \
             patch.object(controller, 'lock_contest', side_effect=revoke_then_lock):
            result = inspect.unwrap(controller.ContestProblemSubmitController.post)(None, contest.id, problem.id)
    assert result[1] == 403
    assert not m.ContestSubmission.select().exists()
    assert not m.ContestJudgeOutbox.select().exists()
