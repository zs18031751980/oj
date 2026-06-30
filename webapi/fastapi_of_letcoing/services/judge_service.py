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

from core.di_container import get_container
from interfaces.service_interfaces import ICodeExecutionService, ILoggerService, IRedisService
from models.db_models import Submission, Testcase
from models.glot_models import CodeExecutionRequest


class JudgeWorker:
    """判题 Worker，后台线程从 Redis 队列拉取任务并判题"""

    def __init__(self, redis_service: IRedisService, code_service: ICodeExecutionService, logger: ILoggerService):
        self.redis = redis_service
        self.code_service = code_service
        self.logger = logger
        self._running = False
        self._thread: threading.Thread | None = None

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
        while self._running:
            try:
                raw = self.redis.list_pop("judge_queue")
                if raw:
                    task = json.loads(raw) if isinstance(raw, str) else raw
                    self._process_task(task)
                else:
                    time.sleep(0.5)
            except Exception as e:
                self.logger.error("JudgeWorker loop error", e)
                time.sleep(1)

    def _process_task(self, task: dict):
        """处理单个判题任务"""
        submission_id = task.get("submission_id")
        problem_id = task.get("problem_id")
        code = task.get("code", "")
        language = task.get("language", "cpp")

        try:
            submission = Submission.get_by_id(submission_id)
        except Exception:
            self.logger.error(f"Submission {submission_id} not found")
            return

        testcases = list(Testcase.select().where(
            Testcase.problem == problem_id,
            Testcase.is_sample == False,
        ).order_by(Testcase.sort_order))

        if not testcases:
            self.logger.warning(f"No testcases for problem {problem_id}, using empty")
            submission.status = Submission.AC
            submission.time_used = 0
            submission.memory_used = 0
            submission.testcase_results = json.dumps([])
            submission.save()
            return

        submission.status = Submission.RUNNING
        submission.save()

        results = []
        first_failed = None

        for tc in testcases:
            result = self._judge_single(code, language, tc.input_data, tc.output_data)
            results.append(result)
            if not result["passed"] and first_failed is None:
                first_failed = tc.sort_order
                break

        all_passed = first_failed is None

        total_time = sum(r.get("time_used", 0) or 0 for r in results)

        submission.status = Submission.AC if all_passed else Submission.WA
        submission.time_used = total_time
        submission.memory_used = 0
        submission.testcase_results = json.dumps(results)
        submission.fail_testcase_index = first_failed
        submission.save()

        self.logger.info(
            f"Submission {submission_id} done: {submission.status} "
            f"(passed {sum(1 for r in results if r['passed'])}/{len(results)})"
        )

    def _judge_single(self, code: str, language: str, stdin: str, expected: str) -> dict:
        """执行单个测试点并对比输出"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            request = CodeExecutionRequest(code=code, language=language, stdin=stdin)
            response = loop.run_until_complete(self.code_service.execute_code(request))
            loop.close()
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


_worker_instance: JudgeWorker | None = None


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
