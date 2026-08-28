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
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from core.di_container import get_container
from interfaces.service_interfaces import ICodeExecutionService, ILoggerService, IRedisService
from models.db_models import Submission, Testcase
from models.glot_models import CodeExecutionRequest
from controllers.contest_problem_controller import (
    _run_code,
    _generate_testcases,
    _reference_looks_nondeterministic,
    _detect_language,
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

    def start(self):
        """启动后台判题线程"""
        if self._running:
            return
        self._running = True
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
                    raw = self.redis.list_pop("judge_queue")
                    if raw:
                        task = json.loads(raw) if isinstance(raw, str) else raw
                        self._process_task(task)
                    else:
                        raw_contest = self.redis.list_pop("contest_judge_queue")
                        if raw_contest:
                            task = json.loads(raw_contest) if isinstance(raw_contest, str) else raw_contest
                            self._process_contest_task(task)
                        else:
                            raw_gen = self.redis.list_pop("testcase_gen_queue")
                            if raw_gen:
                                task = json.loads(raw_gen) if isinstance(raw_gen, str) else raw_gen
                                self._process_gen_task(task)
                            else:
                                time.sleep(0.5)
                except Exception as e:
                    self.logger.error("JudgeWorker loop error", e)
                    time.sleep(1)
        finally:
            self._loop.close()
            self._loop = None

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
        contest_id = task.get("contest_id")
        problem_id = task.get("problem_id")
        user_id = task.get("user_id")
        code = task.get("code", "")
        language = task.get("language", "cpp")

        if submission_id is None:
            return

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except Exception:
            self._save_contest_result(submission_id, {
                "status": "Error", "passed": 0, "total": 0, "details": [],
            })
            return

        # 按题目的运行时长与内存限制进行判题（time_limit 单位 ms → 秒）。
        # 不设 1s 下限，使“卡时间限制”的用例真正生效：生成时即按该时限校准
        # 用例规模，判题时也按该时限执行，二者一致。
        time_limit_sec = max((problem.time_limit or 1000) / 1000.0, 0.05)
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
            return

        def _judge_one(tc):
            expected = (tc.expected_output or "").strip()
            output, err_type, time_used_ms, stderr = _run_code(
                code, language, tc.input_data,
                timeout=time_limit_sec, memory_limit=memory_limit,
            )
            if err_type is not None:
                return {
                    "passed": False,
                    "status": err_type,
                    "expected": expected,
                    "actual": None,
                    "time_used": time_used_ms,
                    "stderr": stderr or "",
                }
            actual = (output or "").strip()
            passed = actual == expected
            # 答案数值正确但空白/换行不一致时归为 PE（格式错误），便于前端区分
            if not passed and actual.replace(" ", "").replace("\n", "") == expected.replace(" ", "").replace("\n", ""):
                return {
                    "passed": False,
                    "status": "PE",
                    "expected": expected,
                    "actual": actual,
                    "time_used": time_used_ms,
                    "stderr": "",
                }
            return {
                "passed": passed,
                "status": "AC" if passed else "WA",
                "expected": expected,
                "actual": actual,
                "time_used": time_used_ms,
                "stderr": "",
            }

        # 顺序判题：与生成测试用例时的运行环境一致（单进程、独占 CPU 时间片），
        # 避免多用例并行争抢 CPU 导致参考代码在正式比赛时限内被判 TLE。
        details = [_judge_one(tc) for tc in testcases]

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

        self._save_contest_result(submission_id, {
            "problem_id": problem_id,
            "contest_id": contest_id,
            "user_id": user_id,
            "status": status,
            "passed": passed,
            "total": total,
            "score": score,
            "details": details,
        })
        self.logger.info(
            f"Contest submission {submission_id} done: {status} (passed {passed}/{total})"
        )

        # 持久化提交记录，供实时排行榜聚合（失败不阻塞判题结果返回）
        # library 提交（比赛结束后在题库中做题）不计入比赛排行榜
        try:
            if (
                not task.get("library")
                and user_id is not None
                and contest_id is not None
            ):
                ContestSubmission.create(
                    contest_id=contest_id,
                    user_id=user_id,
                    contest_problem_id=problem_id,
                    problem_index=problem.problem_index or "",
                    status=status,
                    passed=passed,
                    total=total,
                    score=score,
                    language=language,
                    submitted_at=datetime.now(timezone.utc),
                )
        except Exception as exc:
            self.logger.error("保存比赛提交记录失败", exc)

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
