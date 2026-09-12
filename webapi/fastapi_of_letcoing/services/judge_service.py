"""
判题服务模块

提供异步判题队列处理能力：
1. JudgeWorker 后台线程从 Redis 队列中拉取判题任务
2. 调用 GlotService 执行代码
3. 逐测试点对比输出，更新提交记录状态
4. 支持水平扩展（多个 Worker 实例同时消费）
"""

import asyncio
from contextlib import ExitStack
import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from core.di_container import get_container
from interfaces.service_interfaces import ICodeExecutionService, ILoggerService, IRedisService
from models.db_models import ContestSubmission, Submission, Testcase, Contest, get_database
from models.glot_models import CodeExecutionRequest
from controllers.contest_problem_controller import (
    _run_code,
    normalize_judge_output,
    _generate_testcases,
    _reference_looks_nondeterministic,
    _detect_language,
)
from services.judge_state import (
    ACCEPTED, CHECKING, CLAIMED, COMPILATION_ERROR, COMPILED, COMPILING,
    MEMORY_LIMIT_EXCEEDED, PARTIAL, QUEUED, RUNNING, SYSTEM_ERROR,
    OUTPUT_LIMIT_EXCEEDED, TIME_LIMIT_EXCEEDED, WRONG_ANSWER, TERMINAL_STATES, can_transition, is_terminal,
)
from services.contest_outbox import dispatch_pending_outbox
from services.compile_cache import prepare_cached as _prepare_program
from services.contest_operations import now as contest_now


class JudgeWorker:
    """判题 Worker，后台线程从 Redis 队列拉取任务并判题"""

    def __init__(self, redis_service: IRedisService, code_service: ICodeExecutionService, logger: ILoggerService):
        self.redis = redis_service
        self.code_service = code_service
        self.logger = logger
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue_cursor = 0
        self.worker_id = f'worker-{os.getpid()}-{uuid4().hex[:12]}'
        self.started_at = datetime.now(timezone.utc)
        self.last_claim_at = None
        self.last_completed_at = None
        self.active_job = None
        self.failure_count = 0
        self.compile_cache_hits = 0
        self.audit_consecutive_failures = 0
        self.audit_last_success_unix = 0
        self.projection_consecutive_failures = 0
        self.projection_last_success_unix = 0
        self._last_recovery = 0.0
        self._stop_event = threading.Event()
        self._draining = threading.Event()
        self._claim_lock = threading.Lock()
        self._maintenance_thread = None
        self._projection_thread = None
        self._audit_thread = None
        self._heartbeat_thread = None
        self.pool = os.environ.get('JUDGE_WORKER_POOL', 'all')
        if self.pool not in {'all', 'contest', 'practice', 'rejudge', 'validation'}:
            raise ValueError('Invalid JUDGE_WORKER_POOL')
        self._reconcile_cursors = {}

    def queues(self):
        pools = {'contest': [('contest_judge_queue', self._process_contest_task)],
                 'practice': [('judge_queue', self._process_task), ('practice_judge_queue', self._process_contest_task)],
                 'rejudge': [('rejudge_queue', self._process_contest_task)],
                 'validation': [('testcase_gen_queue', self._process_gen_task)]}
        return [item for values in pools.values() for item in values] if self.pool == 'all' else pools[self.pool]

    def _background(self, operation, interval, uses_db=True):
        while not self._stop_event.is_set():
            try:
                if uses_db:
                    with get_database().connection_context():
                        operation()
                else:
                    operation()
            except Exception as exc:
                self.logger.error('Worker background task failed', exc)
            self._stop_event.wait(interval)

    def _refresh_projections(self):
        from controllers.contest_rankings_controller import refresh_dirty_projections
        from services.ranking_projection import refresh_rankings
        try:
            if self.pool in {'contest', 'all'}:
                refresh_dirty_projections()
            if self.pool in {'practice', 'all'}:
                refresh_rankings()
        except Exception:
            self.projection_consecutive_failures += 1
            raise
        else:
            self.projection_consecutive_failures = 0
            self.projection_last_success_unix = time.time()

    def _export_audit(self):
        from services.retention import export_audit
        directory = os.environ.get('AUDIT_EXPORT_DIR')
        if not directory:
            return
        try:
            result = export_audit(directory, getattr(self, '_audit_cursor', 0), 500)
        except Exception:
            self.audit_consecutive_failures = getattr(self, 'audit_consecutive_failures', 0)+1
            raise
        else:
            self.audit_consecutive_failures = 0
            self.audit_last_success_unix = time.time()
        # 全量循环校验副本，也覆盖序列号先分配、事务后提交造成的迟到记录。
        self._audit_cursor = result['next_cursor'] if result['exported'] == 500 else 0

    def start(self):
        """启动后台判题线程"""
        if self._running:
            return
        if any(thread and thread.is_alive() for thread in (self._thread, self._maintenance_thread,
                self._heartbeat_thread, self._projection_thread, self._audit_thread)):
            raise RuntimeError('previous Worker threads are still stopping')
        self._running = True
        self._stop_event.clear()
        self._draining.clear()
        # 启动时仅回收租约已过期的任务，不搬走其他活跃 Worker 的任务。
        self._maintenance_thread = threading.Thread(target=self._maintenance, daemon=True)
        self._maintenance_thread.start()
        self._heartbeat_thread = threading.Thread(target=self._background, args=(
            lambda: self.redis.set(f'judge:worker:{self.worker_id}', self.health(), 30), 5, False), daemon=True)
        self._heartbeat_thread.start()
        if os.environ.get('AUDIT_EXPORT_DIR'):
            self._audit_thread = threading.Thread(target=self._background, args=(self._export_audit, 10), daemon=True)
            self._audit_thread.start()
        if self.pool in {'contest', 'practice', 'all'}:
            self._projection_thread = threading.Thread(target=self._background, args=(self._refresh_projections, 2), daemon=True)
            self._projection_thread.start()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.logger.info("JudgeWorker started")

    def begin_drain(self) -> None:
        """停止新领取；已领取任务仍保留租约和心跳，直到结果持久化。"""
        with self._claim_lock:
            self._draining.set()

    def stop(self, timeout: float = 30) -> bool:
        """在一个总时间预算内排空；超时返回 False，调用方决定进程退出。"""
        deadline = time.monotonic() + max(0, timeout)
        self.begin_drain()
        if self._thread:
            self._thread.join(timeout=max(0, deadline-time.monotonic()))
            if self._thread.is_alive():
                self.logger.warning('Worker drain deadline exceeded; active job retains its lease')
                return False
        self._running = False
        self._stop_event.set()
        threads = (self._maintenance_thread, self._heartbeat_thread, self._projection_thread, self._audit_thread)
        for thread in threads:
            if thread:
                thread.join(timeout=max(0, deadline-time.monotonic()))
        stopped = all(not thread or not thread.is_alive() for thread in threads)
        if stopped:
            self.logger.info('JudgeWorker stopped')
        return stopped

    def _run_loop(self):
        """主循环：不断从 Redis 队列拉取判题任务"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            while self._running and not self._draining.is_set():
                try:
                    # 轮转读取，避免普通题库提交持续涌入时比赛判题被永久饿死。
                    queues = self.queues()
                    task_found = False
                    for offset in range(len(queues)):
                        index = (self._queue_cursor + offset) % len(queues)
                        queue_name, handler = queues[index]
                        with self._claim_lock:
                            if self._draining.is_set():
                                break
                            claim = self.redis.list_claim(queue_name, f'{queue_name}:processing')
                        if claim:
                            self._queue_cursor = (index + 1) % len(queues)
                            task = claim['payload']
                            self.last_claim_at = datetime.now(timezone.utc)
                            self.active_job = task.get('job_id') or task.get('submission_id')
                            self.logger.info(f'judge_claim queue={queue_name} job_id={task.get("job_id")} submission_id={task.get("submission_id")} attempt_id={task.get("attempt_id")}')
                            renew_stop = threading.Event()
                            def renew():
                                while not renew_stop.wait(20):
                                    try:
                                        if not self.redis.list_renew(f'{queue_name}:processing', claim['receipt']):
                                            return
                                    except Exception:
                                        self.logger.warning('Job lease renewal failed')
                            renew_thread = threading.Thread(target=renew, daemon=True)
                            renew_thread.start()
                            try:
                                with get_database().connection_context():
                                    handled = handler(task)
                            except Exception:
                                try:
                                    self.redis.list_nack(queue_name, f'{queue_name}:processing', claim['receipt'])
                                except Exception:
                                    pass
                                raise
                            finally:
                                renew_stop.set()
                                renew_thread.join(timeout=5)
                            self.last_completed_at = datetime.now(timezone.utc)
                            self.active_job = None
                            # 只有处理函数正常返回后才确认；抛异常时任务留在 processing，
                            # 下次 Worker 启动会自动恢复，形成 at-least-once 语义。
                            if handled is False:
                                self.logger.warning(
                                    f'Job from {queue_name} was not persisted; leaving it for retry'
                                )
                                self.redis.list_nack(queue_name, f'{queue_name}:processing', claim['receipt'])
                                continue
                            if not self.redis.list_ack(f'{queue_name}:processing', claim['receipt']):
                                self.logger.warning(f'Could not ack task from {queue_name}; it will be retried')
                            task_found = True
                            break
                    if not task_found:
                        time.sleep(0.5)
                except Exception as e:
                    self.failure_count += 1
                    self.active_job = None
                    self.logger.error("JudgeWorker loop error", e)
                    time.sleep(1)
        finally:
            self._loop.close()
            self._loop = None

    def _maintenance(self):
        from services.submission_outbox import dispatch_pending_regular
        from services.reference_validation import dispatch_pending_validations
        from controllers.contest_rankings_controller import refresh_dirty_projections
        from services.ranking_projection import refresh_rankings
        while not self._stop_event.is_set():
            try:
                with get_database().connection_context():
                    self._recover_expired_jobs()
                    self._persist_dead_jobs()
                    self._reconcile_dispatched_jobs()
                    dispatch_pending_outbox(self.redis)
                    dispatch_pending_regular(self.redis)
                    dispatch_pending_validations(self.redis)
                    from services.contest_packages import dispatch_package_validation
                    dispatch_package_validation(self.redis)
            except Exception as exc:
                self.logger.error('Judge maintenance failed', exc)
            if (os.environ.get('APP_ENV') == 'production'
                    and os.environ.get('JUDGE_BACKEND', 'docker') == 'docker'
                    and time.monotonic() >= getattr(self, '_next_reap', 0)):
                self._next_reap = time.monotonic() + 60
                try:
                    from services.sandbox_service import reap_expired_containers
                    reap_expired_containers()
                except Exception as exc:
                    self.logger.error('Sandbox reaper failed', exc)
            self._stop_event.wait(2)

    def _persist_dead_jobs(self):
        from models.db_models import ReferenceValidationJob, ContestProblem
        for queue, model in (('judge_queue', Submission), ('contest_judge_queue', ContestSubmission), ('practice_judge_queue', ContestSubmission), ('rejudge_queue', ContestSubmission), ('testcase_gen_queue', None)):
            for receipt in self.redis._client.lrange(queue + ':dead', 0, 99):
                try:
                    item = json.loads(receipt)
                    task = item.get('payload', item)
                    if not isinstance(task, dict):
                        raise ValueError('invalid task')
                except (ValueError, AttributeError):
                    self.redis.archive_dead(queue, receipt)
                    continue
                with get_database().atomic():
                    if model is not None:
                        row = model.get_or_none((model.id == task.get('submission_id')) & (model.job_id == task.get('job_id')))
                        if row and not is_terminal(row.status):
                            values = {'status': SYSTEM_ERROR}
                            if model == ContestSubmission:
                                values.update(verdict=SYSTEM_ERROR, finished_at=contest_now())
                            changed = model.update(**values).where((model.id == row.id) & (~model.status.in_(list(TERMINAL_STATES)))).execute()
                            if changed and model == ContestSubmission and row.contest_eligible:
                                Contest.update(scoreboard_requested_version=Contest.scoreboard_requested_version + 1).where(Contest.id == row.contest_id).execute()
                    else:
                        if task.get('package_digest'):
                            from models.db_models import ContestPackage
                            ContestPackage.update(validation_state='INVALID', validation_error='验证服务重试耗尽').where(
                                ContestPackage.digest == task['package_digest'], ContestPackage.validation_state.in_(['PENDING', 'RUNNING'])).execute()
                        job = ReferenceValidationJob.get_or_none(ReferenceValidationJob.id == task.get('job_id'))
                        if job and job.state != 'DONE':
                            ContestProblem.update(validation_status='INVALID', validation_error='执行服务多次失败，请重新保存题目以重试').where(
                                (ContestProblem.id == job.problem_id) & (ContestProblem.validation_version == job.version)).execute()
                            ReferenceValidationJob.update(state='DONE').where(ReferenceValidationJob.id == job.id).execute()
                # 先提交数据库，再移动死信；重放不会再次推进终态版本。
                self.redis.archive_dead(queue, receipt)

    def _reconcile_dispatched_jobs(self):
        """分页扫描未完成事实，Redis 全量丢失后也可补投；活跃任务由去重键保护。"""
        from models.db_models import SubmissionOutbox, ContestJudgeOutbox, ReferenceValidationJob
        from services.submission_outbox import dispatch_regular_entry
        from services.contest_outbox import dispatch_outbox_entry
        for queue, outbox, model, dispatch in (
            ('judge_queue', SubmissionOutbox, Submission, dispatch_regular_entry),
            ('contest_judge_queue', ContestJudgeOutbox, ContestSubmission, dispatch_outbox_entry),
        ):
            cursor = self._reconcile_cursors.get(queue, 0)
            rows = list(outbox.select(outbox, model).join(model).where(
                (outbox.id > cursor) & (outbox.state == 'DISPATCHED')
                & (~model.status.in_(list(TERMINAL_STATES)))).order_by(outbox.id).limit(100))
            for row in rows:
                from services.contest_outbox import queue_for
                actual_queue = queue_for(row.submission) if model == ContestSubmission else queue
                if not self.redis._client.exists(f'judge:enqueued:{actual_queue}:{row.submission.job_id}'):
                    row.state = 'PENDING'
                    dispatch(self.redis, row)
            self._reconcile_cursors[queue] = rows[-1].id if len(rows) == 100 else 0
        queue = 'testcase_gen_queue'
        cursor = self._reconcile_cursors.get(queue, '')
        rows = list(ReferenceValidationJob.select().where((ReferenceValidationJob.id > cursor)
            & (ReferenceValidationJob.state == 'DISPATCHED')).order_by(ReferenceValidationJob.id).limit(100))
        for row in rows:
            if not self.redis._client.exists(f'judge:enqueued:{queue}:{row.id}'):
                ReferenceValidationJob.update(state='PENDING').where(ReferenceValidationJob.id == row.id).execute()
        self._reconcile_cursors[queue] = rows[-1].id if len(rows) == 100 else ''

    def _recover_expired_jobs(self):
        for queue_name in ('judge_queue', 'contest_judge_queue', 'practice_judge_queue', 'rejudge_queue', 'testcase_gen_queue'):
            self.redis.list_retry_due(queue_name)
            recovered = self.redis.list_recover(
                f'{queue_name}:processing', queue_name,
            )
            if recovered:
                self.logger.warning(
                    f'Recovered {recovered} expired job(s) from {queue_name}'
                )

    def health(self) -> dict:
        return {
            'worker_id': self.worker_id,
            'heartbeat_unix': time.time(),
            'alive': bool(self._running and self._thread and self._thread.is_alive()),
            'draining': self._draining.is_set(),
            'accepting_jobs': bool(self._running and not self._draining.is_set()),
            'started_at': self.started_at.isoformat(),
            'last_claim_at': self.last_claim_at.isoformat() if self.last_claim_at else None,
            'last_completed_at': self.last_completed_at.isoformat() if self.last_completed_at else None,
            'active_job': self.active_job,
            'failure_count': self.failure_count,
            'compile_cache_hits': self.compile_cache_hits,
            'audit_enabled': bool(os.environ.get('AUDIT_EXPORT_DIR')),
            'audit_consecutive_failures': self.audit_consecutive_failures,
            'audit_last_success_unix': self.audit_last_success_unix,
            'projection_consecutive_failures': self.projection_consecutive_failures,
            'projection_last_success_unix': self.projection_last_success_unix,
            'pool': self.pool,
            'queue_length': self.redis.list_length('contest_judge_queue'),
            'processing_count': self.redis.list_length('contest_judge_queue:processing'),
        }

    def _save_to_redis(self, submission_id, data):
        """将提交结果写入 Redis 缓存"""
        try:
            key = f'submission:{submission_id}'
            self.redis.set(key, data, 3600)
        except Exception:
            pass

    def _process_task(self, task: dict):
        from pages.problem_data import PROBLEMS
        submission = Submission.get_by_id(task['submission_id'])
        if submission.job_id != task.get('job_id') or is_terminal(submission.status):
            return True
        old_attempt = submission.attempt_id
        changed = Submission.update(status=Submission.RUNNING, attempt_id=old_attempt + 1).where(
            (Submission.id == submission.id) & (Submission.attempt_id == old_attempt)
            & (Submission.status == submission.status)).execute()
        if changed != 1:
            return False
        testcases = PROBLEMS.get(submission.problem_id, {}).get('testCases', [])
        results = []
        final_status = ACCEPTED if testcases else SYSTEM_ERROR
        first_failed = None
        for index, tc in enumerate(testcases):
            result = self._judge_single(submission.code, submission.language, tc['input'], tc['output'])
            results.append({'passed': result['passed'], 'status': result.get('status', WRONG_ANSWER),
                            'testCaseIndex': index, 'time_used': result.get('time_used', 0)})
            if not result['passed']:
                final_status = result.get('status', WRONG_ANSWER)
                first_failed = index
                break
        persisted = Submission.update(status=final_status, testcase_results=json.dumps(results),
            time_used=sum(r['time_used'] for r in results), fail_testcase_index=first_failed).where(
            (Submission.id == submission.id) & (Submission.attempt_id == old_attempt + 1)
            & (Submission.status == Submission.RUNNING)).execute()
        return bool(persisted)

    def _save_contest_result(self, submission_id, data):
        """将比赛判题结果写入 Redis 缓存（与通用提交共用键前缀风格）"""
        try:
            self.redis.set(f"contest_submission:{submission_id}", data, 3600)
        except Exception:
            pass

    def _save_gen_status(self, problem_id, data):
        """将测试用例生成进度/结果写入 Redis，供前端轮询"""
        try:
            self.redis.set(f"testcase_gen:{problem_id}", data, 3600)
        except Exception:
            pass

    def _transition_contest(self, submission_id: int, attempt_id: int,
                            expected: str, target: str, **fields) -> bool:
        """以 submission + attempt + expected status 做栅栏更新。

        迟到的旧 Worker 即使拿到了相同 job，也无法覆盖新 attempt 或终态结果。
        """
        if not can_transition(expected, target):
            return False
        started = time.monotonic()
        try:
            archived_details = fields.pop('testcase_results', None) if is_terminal(target) else None
            fields.update(status=target, worker_id=self.worker_id)
            if is_terminal(target):
                fields['testcase_results'] = None
            with get_database().atomic():
                from services.contest_lifecycle import lock_contest
                current = ContestSubmission.get_by_id(submission_id)
                lock_contest(current.contest_id)
                updated = ContestSubmission.update(**fields).where(
                    (ContestSubmission.id == submission_id)
                    & (ContestSubmission.attempt_id == attempt_id)
                    & (ContestSubmission.status == expected)).execute()
                if updated == 1 and is_terminal(target):
                    from services.contest_operations import archive_judgement, emit
                    terminal = ContestSubmission.get_by_id(submission_id)
                    terminal.testcase_results = archived_details or current.testcase_results
                    archive_judgement(terminal, terminal.rejudge_batch_id)
                    emit(current.contest_id, 'judgement', {'submission_id': submission_id, 'status': target})
                if updated == 1 and is_terminal(target) and current.contest_eligible:
                    contest_id = ContestSubmission.get_by_id(submission_id).contest_id
                    Contest.update(scoreboard_requested_version=Contest.scoreboard_requested_version + 1).where(
                        Contest.id == contest_id).execute()
            if updated == 1 and is_terminal(target):
                try:
                    from services.contest_metrics import observe_judgement
                    observe_judgement(self.redis, terminal, getattr(self, 'pool', 'all'), time.monotonic()-started)
                except Exception:
                    self.logger.warning('Judge metric recording failed')
            return updated == 1
        except Exception:
            # 不把数据库失败伪装为状态冲突；外层保留 receipt 等待重试。
            raise

    def _contest_submission(self, submission_id: int, job_id: str, attempt_id: int):
        try:
            submission = ContestSubmission.get_by_id(submission_id)
        except ContestSubmission.DoesNotExist:
            return None
        if submission.job_id != job_id:
            return None
        return submission

    def _process_gen_task(self, task):
        if task.get('package_digest'):
            from services.contest_packages import validate_staged_package
            validate_staged_package(task['package_digest'])
            return True

        from services.reference_validation import process_validation
        if task.get('kind') != 'reference_validation':
            # 旧的通用随机生成任务不再执行：测试输入必须由出题人定义。
            return True
        return process_validation(task)

    def _process_contest_task(self, task: dict):
        """处理比赛题目判题任务（本地执行，对比题目存储的测试用例）"""
        from models.db_models import (
            Contest, ContestProblem, ContestTestcase, ContestSubmission, User,
        )

        submission_id = task.get("submission_id")
        job_id = task.get("job_id")
        attempt_id = int(task.get("attempt_id", 1) or 1)
        contest_id = task.get("contest_id")
        problem_id = task.get("problem_id")
        user_id = task.get("user_id")
        code = task.get("code", "")
        language = task.get("language", "cpp")
        submitted_at_raw = task.get("submitted_at")

        try:
            submitted_at = datetime.fromisoformat(str(submitted_at_raw)) if submitted_at_raw else contest_now()
        except (TypeError, ValueError):
            submitted_at = contest_now()

        if submission_id is None:
            return True

        submission = self._contest_submission(submission_id, job_id, attempt_id)
        if submission is None:
            # 旧 job 或已经被重试替换的 job，安全确认而不执行用户代码。
            return True
        if is_terminal(submission.status):
            return True
        if submission.rejudge_batch_id and submission.rejudge_batch.state != 'PENDING':
            return True
        attempt_id = submission.attempt_id
        if submission.status != QUEUED:
            # 同一 job 在租约过期后重新投递：提升 attempt 并把旧 Worker 隔离掉。
            # 旧 Worker 后续所有写入都带旧 attempt_id，因此不会覆盖本次重试。
            reclaimed = ContestSubmission.update(
                status=QUEUED,
                attempt_id=ContestSubmission.attempt_id + 1,
                worker_id=None,
            ).where(
                (ContestSubmission.id == submission_id)
                & (ContestSubmission.attempt_id == attempt_id)
                & (ContestSubmission.status == submission.status)
            ).execute()
            if reclaimed != 1:
                return True
            attempt_id += 1
        if not self._transition_contest(
            submission_id, attempt_id, QUEUED, CLAIMED,
            judge_started_at=contest_now(),
        ):
            # 可能是重复投递或另一个 Worker 已经认领；不能执行两次。
            return True
        code = submission.code
        contest_id = submission.contest_id
        problem_id = submission.contest_problem_id
        user_id = submission.user_id
        language = submission.language
        submitted_at = submission.submitted_at.isoformat() if submission.submitted_at else submitted_at_raw

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except Exception:
            self._save_contest_result(submission_id, {
                "status": "Error", "passed": 0, "total": 0, "details": [],
            })
            self._transition_contest(
                submission_id, attempt_id, CLAIMED, SYSTEM_ERROR,
                verdict=SYSTEM_ERROR,
                error_message='比赛题目不存在或读取失败',
                finished_at=contest_now(),
            )
            return True

        from services.contest_packages import publish_package, load_package, check_output
        from types import SimpleNamespace
        try:
            if not submission.package_digest:
                submission.package_digest = publish_package(problem).digest
                ContestSubmission.update(package_digest=submission.package_digest).where(
                    ContestSubmission.id == submission.id, ContestSubmission.attempt_id == attempt_id).execute()
            package = load_package(submission.package_digest)
            if os.environ.get('APP_ENV') == 'production' and package['runtime_image'] != os.environ.get('JUDGE_SANDBOX_IMAGE'):
                raise ValueError('Judge runtime differs from package')
        except ValueError:
            self._transition_contest(submission_id, attempt_id, CLAIMED, SYSTEM_ERROR,
                verdict=SYSTEM_ERROR, error_message='题包缺失、损坏或执行环境不匹配', finished_at=contest_now())
            return True
        from services.contest_packages import runtime_limits
        time_limit_sec, memory_limit = runtime_limits(package, language)
        testcases = [SimpleNamespace(**tc) for tc in package['cases']]
        is_acm = 'oi' not in (problem.contest.contest_type or '').lower()

        if not testcases:
            self._save_contest_result(submission_id, {
                "problem_id": problem_id,
                "contest_id": contest_id,
                "status": "NoTestcases",
                "passed": 0,
                "total": 0,
                "details": [],
            })
            self._transition_contest(
                submission_id, attempt_id, CLAIMED, SYSTEM_ERROR,
                verdict=SYSTEM_ERROR,
                error_message='题目没有可用测试用例',
                finished_at=contest_now(),
            )
            return True

        # 一次提交只编译一次。此前每个测试点都会重新编译，100 组数据会把
        # C++/Java/Go 的排队时间放大两个数量级。
        if not self._transition_contest(
            submission_id, attempt_id, CLAIMED, COMPILING,
            compile_started_at=contest_now(),
        ):
            return True
        program, compile_error, compile_stderr = _prepare_program(code, language)
        if getattr(program, 'cache_hit', False):
            self.compile_cache_hits += 1

        if program is None:
            self._save_contest_result(submission_id, {
                "problem_id": problem_id, "contest_id": contest_id, "user_id": user_id,
                "status": COMPILATION_ERROR, "passed": 0, "total": len(testcases),
                "score": 0, "details": [], "attempt_id": attempt_id, "job_id": job_id,
            })
            self._transition_contest(
                submission_id, attempt_id, COMPILING, COMPILATION_ERROR,
                verdict=COMPILATION_ERROR,
                total=len(testcases),
                compile_finished_at=contest_now(),
                finished_at=contest_now(),
                error_message=compile_stderr or compile_error or '编译失败',
            )
            return True
        with ExitStack() as resources:
            resources.callback(program.close)
            if not self._transition_contest(
                submission_id, attempt_id, COMPILING, COMPILED,
                compile_finished_at=contest_now(),
            ):
                return True

            def _judge_one(tc):
                expected = tc.expected_output or ""
                if program is None:
                    return {
                        "passed": False,
                        "status": compile_error or "CE",
                        "expected": expected,
                        "actual": None,
                        "time_used": 0,
                        "stderr": compile_stderr or "",
                    }
                output, err_type, time_used_ms, stderr = program.run(
                    tc.input_data, timeout=time_limit_sec, memory_limit=memory_limit,
                )
                metrics = dict(getattr(program, 'last_metrics', {}))
                if err_type is not None:
                    return {
                        "passed": False,
                        "status": err_type,
                        "expected": expected,
                        "actual": None,
                        "time_used": time_used_ms,
                        "stderr": stderr or "",
                        "cpu_time": metrics.get('cpu_time', time_used_ms),
                        "memory": metrics.get('memory', 0),
                        "output_size": metrics.get('output_size', 0),
                        "exit_code": metrics.get('exit_code'),
                        "signal": metrics.get('signal'),
                    }
                actual = output or ""
                passed = checker.check(actual, expected, tc.input_data)
                return {
                    "passed": passed,
                    "status": "AC" if passed else "WA",
                    "expected": expected,
                    "actual": actual,
                    "time_used": time_used_ms,
                    "stderr": "",
                    "cpu_time": metrics.get('cpu_time', time_used_ms),
                    "memory": metrics.get('memory', 0),
                    "output_size": metrics.get('output_size', 0),
                    "exit_code": metrics.get('exit_code'),
                    "signal": metrics.get('signal'),
                }

            if not self._transition_contest(
                submission_id, attempt_id, COMPILED, RUNNING,
                execution_started_at=contest_now(),
            ):
                return True

            # 顺序判题：与生成测试用例时的运行环境一致（单进程、独占 CPU 时间片），
            # 避免多用例并行争抢 CPU 导致参考代码在正式比赛时限内被判 TLE。
            from services.contest_packages import OutputChecker
            checker = OutputChecker(package['checker_config'])
            resources.callback(checker.close)
            details = []
            for tc in testcases:
                result = _judge_one(tc)
                details.append(result)
                if is_acm and not result['passed']:
                    break

        execution_finished_at = contest_now()
        total_cpu_time = sum(d.get('cpu_time', 0) or 0 for d in details)
        peak_memory = max((d.get('memory', 0) or 0 for d in details), default=0)
        output_size = sum(d.get('output_size', 0) or 0 for d in details)
        exit_codes = [d.get('exit_code') for d in details if d.get('exit_code') is not None]
        signals = [d.get('signal') for d in details if d.get('signal') is not None]

        passed = sum(1 for d in details if d["passed"])
        total = len(details)
        status_set = {d["status"] for d in details}

        # 综合判定（ACM 风格）：优先识别编译/运行/时限/内存错误
        if passed == total:
            status = "AC"
        elif "CE" in status_set:
            status = "CE"
        elif "TLE" in status_set:
            status = "TLE"
        elif "MLE" in status_set:
            status = "MLE"
        elif "OLE" in status_set:
            status = "OLE"
        elif "RE" in status_set:
            status = "RE"
        elif passed > 0 and not is_acm:
            status = "Partial"
        else:
            status = "WA"

        # 计算本题得分（OI 模式按通过用例比例计分，满分取题目配置的分值）
        problem_score = getattr(problem, "score", 100) or 100
        if total > 0:
            # 四舍五入取整，Partial 时按比例折算
            score = int(round(passed / total * problem_score))
        else:
            score = 0

        if is_acm:
            score = 0
        result_payload = {
            "problem_id": problem_id,
            "contest_id": contest_id,
            "user_id": user_id,
            "status": status,
            "passed": passed,
            "total": total,
            "score": score,
            "details": details,
            "cpu_time": total_cpu_time,
            "wall_time": sum(d.get('time_used', 0) or 0 for d in details),
            "memory": peak_memory,
            "output_size": output_size,
            "exit_code": exit_codes[-1] if exit_codes else None,
            "signal": signals[-1] if signals else None,
            "attempt_id": attempt_id,
            "job_id": job_id,
        }

        # 运行异常是 RUNNING 的直接终态；正常执行进入 CHECKING 后再落最终判定。
        direct_runtime_states = {
            "TLE": TIME_LIMIT_EXCEEDED,
            "MLE": MEMORY_LIMIT_EXCEEDED,
            "OLE": OUTPUT_LIMIT_EXCEEDED,
            "RE": "RE",
        }
        runtime_status = direct_runtime_states.get(status)
        if runtime_status:
            persisted = self._transition_contest(
                submission_id, attempt_id, RUNNING, runtime_status,
                verdict=runtime_status,
                passed=passed,
                total=total,
                score=score,
                cpu_time=total_cpu_time,
                wall_time=sum(d.get('time_used', 0) or 0 for d in details),
                memory=peak_memory,
                output_size=output_size,
                exit_code=exit_codes[-1] if exit_codes else None,
                signal=signals[-1] if signals else None,
                testcase_results=json.dumps(details, ensure_ascii=False),
                execution_finished_at=execution_finished_at,
                finished_at=execution_finished_at,
            )
        else:
            claimed_for_check = self._transition_contest(
                submission_id, attempt_id, RUNNING, CHECKING,
                passed=passed,
                total=total,
                score=score,
                cpu_time=total_cpu_time,
                wall_time=sum(d.get('time_used', 0) or 0 for d in details),
                memory=peak_memory,
                output_size=output_size,
                exit_code=exit_codes[-1] if exit_codes else None,
                signal=signals[-1] if signals else None,
                execution_finished_at=execution_finished_at,
            )
            persisted = claimed_for_check and self._transition_contest(
                submission_id, attempt_id, CHECKING,
                ACCEPTED if status == ACCEPTED else PARTIAL if status == PARTIAL else WRONG_ANSWER,
                verdict=status,
                testcase_results=json.dumps(details, ensure_ascii=False),
                finished_at=contest_now(),
                checked_at=contest_now(),
            )
        if not persisted:
            return False
        self._save_contest_result(submission_id, result_payload)
        self.logger.info(
            f"Contest submission {submission_id} done: {status} (passed {passed}/{total})"
        )

    def _judge_single(self, code: str, language: str, stdin: str, expected: str) -> dict:
        """执行单个测试点并对比输出"""
        request = CodeExecutionRequest(code=code, language=language, stdin=stdin)
        try:
            response = self._loop.run_until_complete(self.code_service.execute_code(request))
        except Exception as e:
            self.logger.error(f"Judge execution error", e)
            raise RuntimeError('执行服务暂时不可用，等待重试') from e

        if getattr(response, 'verdict', None) == SYSTEM_ERROR:
            raise RuntimeError('执行服务暂时不可用，等待重试')

        stdout = (response.stdout or "").strip()
        stderr = (response.stderr or "").strip()
        expected_stripped = expected.strip()

        status = getattr(response, 'verdict', None)
        passed = bool(response.success and stdout == expected_stripped)
        status = ACCEPTED if passed else (status if status and status != ACCEPTED else WRONG_ANSWER)

        return {
            "passed": passed,
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "expected": expected,
            "time_used": response.time_used if hasattr(response, "time_used") else 0,
        }


_worker_instance: Optional['JudgeWorker'] = None


def start_judge_worker():
    """启动全局判题 Worker（由 main.py 调用）"""
    global _worker_instance
    if _worker_instance is not None:
        return
    container = get_container()
    redis = container.resolve(IRedisService)
    code_service = container.resolve(ICodeExecutionService)
    logger = container.resolve(ILoggerService)
    _worker_instance = JudgeWorker(redis, code_service, logger)
    _worker_instance.start()


def get_judge_worker() -> Optional[JudgeWorker]:
    return _worker_instance
