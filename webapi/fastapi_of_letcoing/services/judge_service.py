"""
判题服务模块

提供异步判题队列处理能力：
1. JudgeWorker 后台线程从 Redis 队列中拉取判题任务
2. 调用 GlotService 执行代码
3. 逐测试点对比输出，更新提交记录状态
4. 支持水平扩展（多个 Worker 实例同时消费）
"""

import asyncio
import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from core.di_container import get_container
from interfaces.service_interfaces import ICodeExecutionService, ILoggerService, IRedisService
from models.db_models import ContestSubmission, Submission, Testcase
from models.glot_models import CodeExecutionRequest
from controllers.contest_problem_controller import (
    _run_code,
    _prepare_program,
    normalize_judge_output,
    _generate_testcases,
    _reference_looks_nondeterministic,
    _detect_language,
)
from services.judge_state import (
    ACCEPTED, CHECKING, CLAIMED, COMPILATION_ERROR, COMPILED, COMPILING,
    MEMORY_LIMIT_EXCEEDED, PARTIAL, QUEUED, RUNNING, SYSTEM_ERROR,
    OUTPUT_LIMIT_EXCEEDED, TIME_LIMIT_EXCEEDED, WRONG_ANSWER, can_transition, is_terminal,
)


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
        self._last_recovery = 0.0

    def start(self):
        """启动后台判题线程"""
        if self._running:
            return
        self._running = True
        # 启动时仅回收租约已过期的任务，不搬走其他活跃 Worker 的任务。
        self._recover_expired_jobs()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.logger.info("JudgeWorker started")

    def stop(self):
        """停止后台判题线程"""
        self._running = False
        self.logger.info("JudgeWorker stopped")

    def _run_loop(self):
        """主循环：不断从 Redis 队列拉取判题任务"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            while self._running:
                try:
                    if time.monotonic() - self._last_recovery >= 10:
                        self._recover_expired_jobs()
                        self._last_recovery = time.monotonic()
                    # 轮转读取，避免普通题库提交持续涌入时比赛判题被永久饿死。
                    queues = [
                        ('judge_queue', self._process_task),
                        ('contest_judge_queue', self._process_contest_task),
                        ('testcase_gen_queue', self._process_gen_task),
                    ]
                    task_found = False
                    for offset in range(len(queues)):
                        index = (self._queue_cursor + offset) % len(queues)
                        queue_name, handler = queues[index]
                        claim = self.redis.list_claim(queue_name, f'{queue_name}:processing')
                        if claim:
                            self._queue_cursor = (index + 1) % len(queues)
                            task = claim['payload']
                            self.last_claim_at = datetime.now(timezone.utc)
                            self.active_job = task.get('job_id') or task.get('submission_id')
                            handled = handler(task)
                            self.last_completed_at = datetime.now(timezone.utc)
                            self.active_job = None
                            # 只有处理函数正常返回后才确认；抛异常时任务留在 processing，
                            # 下次 Worker 启动会自动恢复，形成 at-least-once 语义。
                            if handled is False:
                                self.logger.warning(
                                    f'Job from {queue_name} was not persisted; leaving it for retry'
                                )
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

    def _recover_expired_jobs(self):
        for queue_name in ('judge_queue', 'contest_judge_queue', 'testcase_gen_queue'):
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
            'alive': bool(self._running and self._thread and self._thread.is_alive()),
            'started_at': self.started_at.isoformat(),
            'last_claim_at': self.last_claim_at.isoformat() if self.last_claim_at else None,
            'last_completed_at': self.last_completed_at.isoformat() if self.last_completed_at else None,
            'active_job': self.active_job,
            'failure_count': self.failure_count,
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
        """处理单个判题任务"""
        submission_id = task.get("submission_id")
        problem_id = task.get("problem_id")
        code = task.get("code", "")
        language = task.get("language", "cpp")
        task_testcases = task.get("testcases", [])

        submission = None
        if submission_id:
            try:
                submission = Submission.get_by_id(submission_id)
            except Exception:
                pass

        from pages.problem_data import PROBLEMS
        pdata = PROBLEMS.get(problem_id)
        testcases = task_testcases or (pdata.get("testCases", []) if pdata else [])

        if not testcases:
            self.logger.warning(f"No testcases for problem {problem_id}, using empty")
            result_data = {
                'id': submission_id, 'status': 'AC', 'time_used': 0, 'memory_used': 0,
                'testcase_results': [], 'fail_testcase_index': None,
            }
            self._save_to_redis(submission_id, result_data)
            if submission:
                submission.status = Submission.AC
                submission.time_used = 0
                submission.memory_used = 0
                submission.testcase_results = json.dumps([])
                try:
                    submission.save()
                except Exception:
                    pass
            return

        if submission:
            submission.status = Submission.RUNNING
            try:
                submission.save()
            except Exception:
                pass

        results = []
        first_failed = None
        compile_error = None

        for idx, tc in enumerate(testcases):
            inp = tc.input_data if hasattr(tc, 'input_data') else tc['input']
            outp = tc.output_data if hasattr(tc, 'output_data') else tc['output']
            result = self._judge_single(code, language, inp, outp)
            result['testCaseIndex'] = idx
            if result["passed"]:
                # 通过的用例不回传输入/期望输出，避免测试数据泄露
                result['input'] = ''
                result['expected'] = ''
                results.append(result)
                continue
            result['input'] = inp
            results.append(result)
            if first_failed is None:
                first_failed = idx
            if result.get("stderr") and compile_error is None:
                compile_error = result["stderr"]
            # 性能优化：首个用例失败即停止后续执行（65 个用例无需全部跑完）
            break

        # 未执行的用例标记为失败，保持用例总数一致（整体结论已确定为 WA/CE）
        if first_failed is not None:
            for idx in range(len(results), len(testcases)):
                results.append({
                    "passed": False,
                    "stdout": "",
                    "stderr": "",
                    "input": "",
                    "expected": "",
                    "skipped": True,
                    "testCaseIndex": idx,
                })

        all_passed = first_failed is None

        final_status = 'AC' if all_passed else (
            'CE' if (first_failed is not None and results[first_failed].get("stderr")) else 'WA'
        )

        total_time = sum(r.get("time_used", 0) or 0 for r in results)

        result_data = {
            'id': submission_id,
            'status': final_status,
            'time_used': total_time,
            'memory_used': 0,
            'testcase_results': results,
            'fail_testcase_index': first_failed,
            'compile_error': (
                results[first_failed].get("stderr")
                if first_failed is not None and final_status == 'CE'
                else None
            ),
        }
        self._save_to_redis(submission_id, result_data)

        if submission:
            try:
                db_status = {
                    'AC': Submission.AC,
                    'WA': Submission.WA,
                    'CE': Submission.CE,
                }.get(final_status, Submission.WA)
                submission.status = db_status
                submission.time_used = total_time
                submission.memory_used = 0
                submission.testcase_results = json.dumps(results)
                submission.fail_testcase_index = first_failed
                submission.save()
            except Exception:
                pass

        self.logger.info(
            f"Submission {submission_id} done: {final_status} "
            f"(passed {sum(1 for r in results if r['passed'])}/{len(results)})"
        )

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
        try:
            fields.update(status=target, worker_id=self.worker_id)
            updated = ContestSubmission.update(**fields).where(
                (ContestSubmission.id == submission_id)
                & (ContestSubmission.attempt_id == attempt_id)
                & (ContestSubmission.status == expected)
            ).execute()
            return updated == 1
        except Exception as exc:
            self.logger.error(
                f'Contest submission state transition failed: {submission_id} '
                f'{expected}->{target}', exc
            )
            return False

    def _contest_submission(self, submission_id: int, job_id: str, attempt_id: int):
        try:
            submission = ContestSubmission.get_by_id(submission_id)
        except ContestSubmission.DoesNotExist:
            return None
        if submission.job_id != job_id or submission.attempt_id != attempt_id:
            return None
        return submission

    def _process_gen_task(self, task: dict):
        """后台生成比赛题目的测试用例（与判题解耦，避免阻塞建题请求）"""
        from models.db_models import ContestProblem, ContestTestcase

        problem_id = task.get("problem_id")
        correct_answer = task.get("correct_answer", "")
        count = int(task.get("count", 100) or 100)
        time_limit = int(task.get("time_limit", 1000) or 1000)
        memory_limit = int(task.get("memory_limit", 256) or 256)

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except Exception:
            return

        self._save_gen_status(problem_id, {
            "status": "generating", "generated": 0, "total": count,
        })
        try:
            # 静态拦截非确定性参考代码：一旦依赖时间/随机种子，建题时答案能过、
            # 正式比赛（不同时间/进程）提交却会出现“部分用例不通过”。直接拒绝生成，
            # 倒逼修正参考代码使其确定性，从源头消除该问题。
            lang = _detect_language(correct_answer)
            flagged, reason = _reference_looks_nondeterministic(correct_answer, lang)
            if flagged:
                ContestTestcase.delete().where(
                    ContestTestcase.contest_problem == problem
                ).execute()
                self._save_gen_status(problem_id, {
                    "status": "error",
                    "error": (
                        f"参考代码疑似非确定性（{reason}）。非确定性代码在正式比赛提交时"
                        "会出现“部分用例不通过”，因此无法生成可信测试用例。请移除对时间/随机"
                        "种子的依赖（如 srand(time(NULL))、chrono::now()、random_device、"
                        "Math.random()、random 未固定种子等），改为确定性实现后重新生成。"
                    ),
                    "generated": 0,
                    "total": count,
                })
                self.logger.warning(
                    f"Reference answer for problem {problem_id} is non-deterministic ({reason}); rejected."
                )
                return

            # 先清掉旧用例，保证重生成时数据一致
            ContestTestcase.delete().where(
                ContestTestcase.contest_problem == problem
            ).execute()

            testcases = _generate_testcases(
                correct_answer, count, time_limit, memory_limit
            )

            # 参考代码不可靠（非确定性或大量用例运行出错）时，拒绝生成：
            # 这类用例在正式比赛（另一时刻/进程）提交时会出现“部分不通过”，
            # 因此不保存任何用例，并给出明确错误，倒逼修正参考代码使其确定性。
            if len(testcases) < count:
                ContestTestcase.delete().where(
                    ContestTestcase.contest_problem == problem
                ).execute()
                self._save_gen_status(problem_id, {
                    "status": "error",
                    "error": (
                        "参考代码输出不稳定：在多次运行下结果不一致，或大量随机用例运行出错，"
                        "无法生成足够且可信的测试用例。请确认参考代码：①不依赖随机/时间种子"
                        "（如 srand(time(NULL))、chrono 取时间、random_device）；②无未初始化变量/"
                        "数组越界等未定义行为；③对随机输入都能正确运行。修正后重新生成。"
                    ),
                    "generated": 0,
                    "total": count,
                })
                self.logger.warning(
                    f"Reference answer for problem {problem_id} is non-deterministic/unstable; "
                    f"generated {len(testcases)}/{count}, rejected."
                )
                return

            for idx, tc in enumerate(testcases):
                ContestTestcase.create(
                    contest_problem=problem,
                    input_data=tc['input_data'],
                    expected_output=tc['expected_output'],
                    is_sample=tc['is_sample'],
                    sort_order=tc['sort_order'],
                )
            self._save_gen_status(problem_id, {
                "status": "done", "generated": len(testcases), "total": count,
            })
            self.logger.info(
                f"Testcases generated for problem {problem_id}: {len(testcases)}/{count}"
            )
        except Exception as exc:
            self.logger.error(f"Testcase generation failed for {problem_id}", exc)
            self._save_gen_status(problem_id, {
                "status": "error", "error": str(exc), "generated": 0, "total": count,
            })

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
            submitted_at = datetime.fromisoformat(str(submitted_at_raw)) if submitted_at_raw else datetime.now()
        except (TypeError, ValueError):
            submitted_at = datetime.now()

        if submission_id is None:
            return True

        submission = self._contest_submission(submission_id, job_id, attempt_id)
        if submission is None:
            # 旧 job 或已经被重试替换的 job，安全确认而不执行用户代码。
            return True
        if is_terminal(submission.status):
            return True
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
            judge_started_at=datetime.now(),
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
                finished_at=datetime.now(),
            )
            return True

        # 每个测试点独立执行，并严格使用题目设置的毫秒时限；编译耗时不计入
        # 运行时限（符合主流 OJ 规则），但会受到独立的编译超时保护。
        time_limit_sec = (problem.time_limit or 1000) / 1000.0
        memory_limit = problem.memory_limit or None

        testcases = list(
            ContestTestcase.select()
            .where(ContestTestcase.contest_problem == problem)
            .order_by(ContestTestcase.sort_order)
        )

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
                finished_at=datetime.now(),
            )
            return True

        # 一次提交只编译一次。此前每个测试点都会重新编译，100 组数据会把
        # C++/Java/Go 的排队时间放大两个数量级。
        if not self._transition_contest(
            submission_id, attempt_id, CLAIMED, COMPILING,
            compile_started_at=datetime.now(),
        ):
            return True
        program, compile_error, compile_stderr = _prepare_program(code, language)

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
                compile_finished_at=datetime.now(),
                finished_at=datetime.now(),
                error_message=compile_stderr or compile_error or '编译失败',
            )
            return True
        if not self._transition_contest(
            submission_id, attempt_id, COMPILING, COMPILED,
            compile_finished_at=datetime.now(),
        ):
            program.close()
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
            passed = normalize_judge_output(actual) == normalize_judge_output(expected)
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
            execution_started_at=datetime.now(),
        ):
            program.close()
            return True

        # 顺序判题：与生成测试用例时的运行环境一致（单进程、独占 CPU 时间片），
        # 避免多用例并行争抢 CPU 导致参考代码在正式比赛时限内被判 TLE。
        try:
            details = [_judge_one(tc) for tc in testcases]
        finally:
            if program is not None:
                program.close()

        execution_finished_at = datetime.now()
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
        elif passed > 0:
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
        runtime_status = next((direct_runtime_states[s] for s in status_set if s in direct_runtime_states), None)
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
                testcase_results=json.dumps(details, ensure_ascii=False),
                execution_finished_at=execution_finished_at,
            )
            persisted = claimed_for_check and self._transition_contest(
                submission_id, attempt_id, CHECKING,
                ACCEPTED if status == ACCEPTED else PARTIAL if status == PARTIAL else WRONG_ANSWER,
                verdict=status,
                finished_at=datetime.now(),
                checked_at=datetime.now(),
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
            return {
                "passed": False,
                "stdout": "",
                "stderr": str(e),
                "expected": expected,
                "time_used": 0,
            }

        stdout = (response.stdout or "").strip()
        stderr = (response.stderr or "").strip()
        expected_stripped = expected.strip()

        passed = bool(not stderr and stdout == expected_stripped)

        return {
            "passed": passed,
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
