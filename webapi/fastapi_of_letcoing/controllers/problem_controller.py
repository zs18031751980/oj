"""Read-only problem catalog endpoints.

比赛结束后，比赛题目会动态并入题库（按比赛名称归类），并支持像普通题一样提交判题。
"""

import json
from datetime import datetime, timezone, timedelta
from flask import g, request
from flask_restx import Namespace, Resource

from core.di_container import inject
from interfaces.service_interfaces import IRedisService
from middleware.auth_middleware import AuthMiddleware
from models.db_models import Contest, ContestProblem, ContestTestcase
from pages.problem_data import PROBLEMS


api = Namespace("problems", description="题库相关接口")

# 比赛题库题目在题库列表中的 id 偏移，避免与静态题号冲突（静态题号从 1001 起）。
LIBRARY_ID_BASE = 1_000_000

def _is_contest_ended(contest: Contest) -> bool:
    """比赛是否已结束（已到结束时间或状态标记为 past）

    数据库 end_time 按项目约定以 Asia/Shanghai（UTC+8）墙钟存储为 naive 值，
    故统一当作 UTC+8 解释后再与 UTC 当前时间比较，避免服务器本地时区
    （如 Zeabur 默认为 UTC）造成 8 小时偏差。
    """
    if contest.status == "past":
        return True
    if contest.end_time is not None:
        end = contest.end_time
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone(timedelta(hours=8)))
        else:
            end = end.astimezone(timezone(timedelta(hours=8)))
        if end <= datetime.now(timezone.utc):
            return True
    return False


def _iter_ended_contest_problems():
    """遍历所有公开且已结束比赛的比赛题目，返回 (contest, contest_problem)"""
    contests = Contest.select().where(Contest.is_public == True)  # noqa: E712
    for contest in contests:
        if not _is_contest_ended(contest):
            continue
        for cp in ContestProblem.select().where(
            ContestProblem.contest == contest
        ).order_by(ContestProblem.sort_order):
            yield contest, cp


def _library_summary(contest: Contest, cp: ContestProblem) -> dict:
    """将比赛题目转换为题库列表摘要（带比赛名归类与 library id）"""
    return {
        "id": LIBRARY_ID_BASE + cp.id,
        "sourceNumber": cp.id,
        "category": f"contest-{contest.id}",
        "categoryLabel": contest.title,
        "title": cp.title,
        "difficulty": cp.difficulty,
        "tags": [],
        "interactive": False,
        "judgeable": True,
        "timeLimit": cp.time_limit,
        "memoryLimit": cp.memory_limit,
    }


def _library_detail(contest: Contest, cp: ContestProblem) -> dict:
    """将比赛题目转换为题库详情（不含测试用例与参考答案，避免泄露）"""
    try:
        samples = json.loads(cp.samples) if isinstance(cp.samples, str) else (cp.samples or [])
    except Exception:
        samples = []
    if not isinstance(samples, list):
        samples = []
    test_case_count = ContestTestcase.select().where(
        ContestTestcase.contest_problem == cp
    ).count()
    return {
        "id": LIBRARY_ID_BASE + cp.id,
        "sourceNumber": cp.id,
        "category": f"contest-{contest.id}",
        "categoryLabel": contest.title,
        "title": cp.title,
        "difficulty": cp.difficulty,
        "tags": [],
        "description": cp.description,
        "inputFormat": cp.input_desc,
        "outputFormat": cp.output_desc,
        "samples": samples,
        "testCaseCount": test_case_count,
        "interactive": False,
        "judgeable": True,
        "timeLimit": cp.time_limit,
        "memoryLimit": cp.memory_limit,
        "isLibrary": True,
        "contestProblemId": cp.id,
        "contestId": contest.id,
        "contestTitle": contest.title,
    }


def _decode_library_id(library_id: int):
    """若 id 属于比赛题库题目，返回 contest_problem_id，否则返回 None"""
    if library_id < LIBRARY_ID_BASE:
        return None
    return library_id - LIBRARY_ID_BASE


SUMMARY_FIELDS = (
    "id",
    "sourceNumber",
    "category",
    "categoryLabel",
    "title",
    "difficulty",
    "tags",
    "interactive",
    "judgeable",
    "timeLimit",
    "memoryLimit",
)


def serialize_summary(problem):
    summary = {key: problem.get(key) for key in SUMMARY_FIELDS}
    summary["category"] = summary["category"] or "general"
    summary["categoryLabel"] = summary["categoryLabel"] or "通用题库"
    summary["interactive"] = bool(summary["interactive"])
    summary["judgeable"] = summary["judgeable"] is not False
    return summary


def serialize_problem(problem):
    data = dict(problem)
    # 测试用例（含答案）不下发到前端，仅用于后端判题，防止答案泄露；
    # 前端只需要用例总数用于展示。
    test_cases = data.pop("testCases", None) or []
    data["testCaseCount"] = len(test_cases)
    data.setdefault("category", "general")
    data.setdefault("categoryLabel", "通用题库")
    data.setdefault("interactive", False)
    data.setdefault("judgeable", True)
    return data


@api.route("")
class ProblemListController(Resource):
    @api.doc("list_problems")
    def get(self):
        problems = [serialize_summary(PROBLEMS[problem_id]) for problem_id in sorted(PROBLEMS)]
        # 动态并入已结束比赛的比赛题目，按比赛名称归类
        for contest, cp in _iter_ended_contest_problems():
            problems.append(serialize_summary(_library_summary(contest, cp)))
        return {"data": problems, "total": len(problems)}, 200


@api.route("/<int:problem_id>")
class ProblemDetailController(Resource):
    @api.doc("get_problem")
    def get(self, problem_id):
        problem = PROBLEMS.get(problem_id)
        if problem is not None:
            return serialize_problem(problem), 200
        # 比赛题库题目（动态并入，id 带偏移）
        contest_problem_id = _decode_library_id(problem_id)
        if contest_problem_id is not None:
            try:
                cp = ContestProblem.get_by_id(contest_problem_id)
            except ContestProblem.DoesNotExist:
                return {"error": "题目不存在"}, 404
            contest = cp.contest
            if not _is_contest_ended(contest):
                return {"error": "题目不存在"}, 404
            return _library_detail(contest, cp), 200
        return {"error": "题目不存在"}, 404


@api.route("/library/submit")
class LibraryProblemSubmitController(Resource):
    @api.doc("submit_library_problem")
    @AuthMiddleware.require_auth
    def post(self):
        """提交已结束比赛的题目进行判题（复用比赛判题 Worker）"""
        user = getattr(g, "current_user", None)
        if not user:
            return {"error": "请先登录"}, 401

        data = request.get_json(silent=True) or {}
        contest_problem_id = data.get("contest_problem_id")
        code = str(data.get("code", ""))
        language = str(data.get("language", "cpp") or "cpp")
        if not contest_problem_id:
            return {"error": "缺少 contest_problem_id"}, 400
        if not code.strip():
            return {"error": "代码不能为空"}, 400

        try:
            cp = ContestProblem.get_by_id(int(contest_problem_id))
        except (ContestProblem.DoesNotExist, ValueError):
            return {"error": "题目不存在"}, 404

        contest = cp.contest
        if not _is_contest_ended(contest):
            return {"error": "比赛尚未结束，无法在题库中提交"}, 400

        redis_service = inject(IRedisService)
        submission_id = redis_service.increment("contest_submission:id_counter")
        if submission_id is None:
            import time as _time
            submission_id = int(_time.time() * 1000)

        redis_service.set(
            f"contest_submission:{submission_id}",
            {
                "problem_id": cp.id,
                "contest_id": contest.id,
                "user_id": user.get("id"),
                "status": "Pending",
                "passed": 0,
                "total": 0,
                "details": [],
            },
            3600,
        )
        redis_service.list_push(
            "contest_judge_queue",
            {
                "submission_id": submission_id,
                "contest_id": contest.id,
                "problem_id": cp.id,
                "user_id": user.get("id"),
                "code": code,
                "language": language,
                "library": True,
            },
        )
        return {"submission_id": submission_id, "status": "Pending"}, 202


@api.route("/library/submission/<int:submission_id>")
class LibraryProblemSubmissionResultController(Resource):
    @api.doc("get_library_submission_result")
    def get(self, submission_id):
        """轮询比赛题库题目的判题结果（归一化为通用提交结果结构）"""
        redis_service = inject(IRedisService)
        result = redis_service.get(f"contest_submission:{submission_id}")
        if not result:
            return {"error": "提交记录不存在或已过期"}, 404

        details = result.get("details") or []
        testcase_results = []
        first_failed = None
        compile_error = None
        for idx, d in enumerate(details):
            passed = bool(d.get("passed"))
            if not passed and first_failed is None:
                first_failed = idx
                if d.get("status") == "CE":
                    compile_error = d.get("actual") or "编译错误"
            testcase_results.append(
                {
                    "testCaseIndex": idx,
                    "passed": passed,
                    "stdout": d.get("actual") or "",
                    "stderr": "",
                    "expected": d.get("expected") or "",
                    "input": "",
                }
            )

        status = result.get("status", "WA")
        return {
            "id": submission_id,
            "status": status,
            "time_used": None,
            "memory_used": None,
            "testcase_results": testcase_results,
            "fail_testcase_index": first_failed,
            "compile_error": compile_error,
        }, 200
