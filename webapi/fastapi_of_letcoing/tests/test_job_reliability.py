import asyncio
import logging
from unittest.mock import patch
from uuid import uuid4

import pytest

from models import db_models as m
from models.glot_models import CodeExecutionResponse
from services.judge_service import JudgeWorker
from services.submission_outbox import dispatch_regular_entry


class Executor:
    async def execute_code(self, request):
        return CodeExecutionResponse('42\n', success=True, verdict='AC')


@pytest.fixture
def worker(cache):
    worker = JudgeWorker(cache, Executor(), logging.getLogger('test'))
    worker._loop = asyncio.new_event_loop()
    yield worker
    worker._loop.close()


def test_regular_outbox_duplicate_dispatch_produces_one_durable_result(db, cache, worker):
    from pages.problem_data import PROBLEMS
    user = m.User.create(username='alice')
    problem = m.Problem.create(id=991, title='42', description='output 42')
    submission = m.Submission.create(user=user, problem=problem, code='print(42)', language='python', job_id=uuid4().hex)
    outbox = m.SubmissionOutbox.create(submission=submission)
    assert dispatch_regular_entry(cache, outbox)
    assert dispatch_regular_entry(cache, outbox)
    assert cache.list_length('judge_queue') == 1
    claim = cache.list_claim('judge_queue', 'judge_queue:processing')
    with patch.dict(PROBLEMS, {991: {'testCases': [{'input': '', 'output': '42'}]}}):
        assert worker._process_task(claim['payload'])
    assert m.Submission.get_by_id(submission.id).status == 'AC'
    assert cache.list_ack('judge_queue:processing', claim['receipt'])
    cache._client.flushdb()
    assert m.Submission.get_by_id(submission.id).status == 'AC'


def test_missing_testcases_are_system_error_not_accepted(db, worker):
    user = m.User.create(username='alice')
    problem = m.Problem.create(id=9999, title='missing', description='missing')
    submission = m.Submission.create(user=user, problem=problem, code='print(42)', language='python', job_id=uuid4().hex)
    assert worker._process_task({'submission_id': submission.id, 'job_id': submission.job_id})
    assert m.Submission.get_by_id(submission.id).status == 'SystemError'


def test_repeated_worker_crash_recovers_latest_attempt(db, worker, monkeypatch):
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    user = m.User.create(username='alice')
    contest = m.Contest.create(title='test')
    problem = m.ContestProblem.create(contest=contest, problem_index='A', title='42',
        description='42', correct_answer='print(42)', language='python')
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='42')
    submission = m.ContestSubmission.create(contest=contest, contest_problem=problem, user=user,
        problem_index='A', code='print(42)', language='python', status='Running', attempt_id=2, job_id=uuid4().hex)
    worker._process_contest_task({'submission_id': submission.id, 'job_id': submission.job_id, 'attempt_id': 1})
    latest = m.ContestSubmission.get_by_id(submission.id)
    assert latest.status == 'AC'
    assert latest.attempt_id == 3
    assert not worker._transition_contest(submission.id, 2, 'Running', 'SystemError')
    assert m.Contest.get_by_id(contest.id).scoreboard_requested_version == 1


def test_lease_renewal_and_expiry_use_real_redis(cache):
    cache.list_push('q', {'id': 1})
    delivery = cache.list_claim('q', 'q:processing')
    lease_key = cache._lease_key('q:processing', delivery['receipt'])
    cache._client.expire(lease_key, 1)
    assert cache.list_renew('q:processing', delivery['receipt'])
    assert cache._client.ttl(lease_key) > 1
    assert cache.list_recover('q:processing', 'q') == 0


def test_execution_slots_are_released_and_independent_of_rate_budget(cache):
    first = cache.acquire_execution_slot('alice')
    second = cache.acquire_execution_slot('alice')
    assert first and second
    assert cache.acquire_execution_slot('alice') is None
    assert cache.acquire_execution_slot('bob')
    cache.release_execution_slot('alice', first)
    assert cache.acquire_execution_slot('alice')


def test_failed_delivery_retries_with_delay_then_enters_dead_letter_queue(cache):
    assert hasattr(cache, 'list_nack'), 'missing bounded retry path'
    cache.list_push('q', {'id': 1})
    for attempt in range(5):
        claim = cache.list_claim('q', 'q:processing')
        assert claim is not None
        assert cache.list_nack('q', 'q:processing', claim['receipt'])
        assert not cache.list_ack('q:processing', claim['receipt'])
        if attempt < 4:
            assert cache.list_length('q') == 0
            assert cache.list_retry_due('q') == 0
            receipt = cache._client.zrange('q:retry', 0, 0)[0]
            cache._client.zadd('q:retry', {receipt: 0})
            assert cache.list_retry_due('q') == 1
    assert cache.list_length('q:dead') == 1


def test_dispatched_outbox_is_recovered_after_redis_data_loss(db, cache, worker):
    user = m.User.create(username='alice')
    problem = m.Problem.create(id=999, title='test', description='test')
    submission = m.Submission.create(user=user, problem=problem, code='print(42)',
                                    language='python', job_id=uuid4().hex)
    outbox = m.SubmissionOutbox.create(submission=submission)
    assert dispatch_regular_entry(cache, outbox)
    cache._client.flushdb()
    worker._reconcile_dispatched_jobs()
    assert cache.list_length('judge_queue') == 1
    worker._reconcile_dispatched_jobs()
    assert cache.list_length('judge_queue') == 1


def test_dead_contest_job_updates_projection_and_is_archived(db, cache, worker):
    user = m.User.create(username='alice')
    contest = m.Contest.create(title='test')
    problem = m.ContestProblem.create(contest=contest, problem_index='A', title='A', description='test', correct_answer='print(1)')
    submission = m.ContestSubmission.create(user=user, contest=contest, contest_problem=problem,
        problem_index='A', code='print(1)', language='python', job_id=uuid4().hex)
    cache.list_push('contest_judge_queue:dead', {'payload': {'submission_id': submission.id, 'job_id': submission.job_id}})
    worker._persist_dead_jobs()
    latest = m.ContestSubmission.get_by_id(submission.id)
    assert latest.status == latest.verdict == 'SystemError'
    assert latest.finished_at is not None
    assert m.Contest.get_by_id(contest.id).scoreboard_requested_version == 1
    assert cache.list_length('contest_judge_queue:dead') == 0
    assert cache.list_length('contest_judge_queue:dead:archive') == 1


def test_transient_remote_executor_failure_keeps_submission_retryable(db, worker):
    from pages.problem_data import PROBLEMS
    user = m.User.create(username='alice')
    problem = m.Problem.create(id=998, title='test', description='test')
    submission = m.Submission.create(user=user, problem=problem, code='print(42)', language='python', job_id=uuid4().hex)
    async def unavailable(request):
        return CodeExecutionResponse('', 'unavailable', False, http_status=503, verdict='SystemError')
    with patch.dict(PROBLEMS, {998: {'testCases': [{'input': '', 'output': '42'}]}}), \
         patch.object(worker.code_service, 'execute_code', unavailable):
        with pytest.raises(RuntimeError):
            worker._process_task({'submission_id': submission.id, 'job_id': submission.job_id})
    assert m.Submission.get_by_id(submission.id).status == m.Submission.RUNNING
