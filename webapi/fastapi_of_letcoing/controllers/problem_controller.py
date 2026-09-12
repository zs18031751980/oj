"""Read-only problem catalog endpoints.

比赛结束后，比赛题目会动态并入题库（按比赛名称归类），并支持像普通题一样提交判题。
"""

import json
import hashlib
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from flask import g, request
from flask_restx import Namespace, Resource

from core.di_container import inject
from interfaces.service_interfaces import IRedisService
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware
from models.db_models import Contest, ContestProblem, ContestTestcase, ContestSubmission, ContestJudgeOutbox, User, get_database
from services.contest_lifecycle import lock_contest
from services.contest_outbox import dispatch_outbox_entry
from services.judge_state import TERMINAL_STATES, QUEUED
from utils.request_validation import execution_fields, json_object
from pages.problem_data import PROBLEMS


api = Namespace("problems", description="题库相关接口")

# 比赛题库题目在题库列表中的 id 偏移，避免与静态题号冲突（静态题号从 1001 起）。
LIBRARY_ID_BASE = 1_000_000

def _is_contest_ended(contest: Contest) -> bool:
    """比赛是否已结束（以结束时间或最终结算事实为准）

    数据库 end_time 按项目约定以 Asia/Shanghai（UTC+8）墙钟存储为 naive 值，
    故统一当作 UTC+8 解释后再与 UTC 当前时间比较，避免服务器本地时区
    （如 Zeabur 默认为 UTC）造成 8 小时偏差。
    """
    if not contest.is_public or contest.lifecycle_state in {"DRAFT", "READY", "CANCELLED"}:
        return False
    if contest.lifecycle_state == "FINALIZED":
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


def _ended_problem_query():
    current = datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)
    # 摘要查询不读取参考答案、描述或测试数据，过滤在数据库中完成。
    return (ContestProblem.select(
        ContestProblem.id, ContestProblem.contest, ContestProblem.title,
        ContestProblem.difficulty, ContestProblem.time_limit, ContestProblem.memory_limit,
        Contest.id, Contest.title, Contest.is_public, Contest.lifecycle_state, Contest.end_time)
        .join(Contest).where(Contest.is_public == True,
            ~Contest.lifecycle_state.in_(['DRAFT', 'READY', 'CANCELLED']),
            (Contest.lifecycle_state == 'FINALIZED') | (Contest.end_time <= current))
        .order_by(Contest.id, ContestProblem.sort_order, ContestProblem.id))


def _iter_ended_contest_problems():
    for cp in _ended_problem_query().iterator():
        yield cp.contest, cp


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
        from utils.pagination import pagination
        try:
            page = pagination(request.args)
        except ValueError as exc:
            return {'error': str(exc)}, 400
        text = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        difficulty = request.args.get('difficulty', '').strip()
        if max(map(len, (text, category, difficulty))) > 128:
            return {'error': '筛选条件过长'}, 400
        problems = [serialize_summary(PROBLEMS[key]) for key in sorted(PROBLEMS)]
        if text:
            problems = [p for p in problems if text.casefold() in
                (' '.join([str(p['id']), p['title'] or '', *(p['tags'] or [])])).casefold()]
        if category:
            problems = [p for p in problems if p['category'] == category]
        if difficulty:
            problems = [p for p in problems if p['difficulty'] == difficulty]
        query = _ended_problem_query()
        if text:
            query = query.where(ContestProblem.title.contains(text) |
                (ContestProblem.id + LIBRARY_ID_BASE).cast('text').contains(text))
        if category:
            if category.startswith('contest-') and category[8:].isdigit():
                query = query.where(Contest.id == int(category[8:]))
            else:
                query = query.where(Contest.id == -1)
        if difficulty:
            query = query.where(ContestProblem.difficulty == difficulty)
        static_count = len(problems)
        if page:
            offset, size = page
            total = static_count + query.count()
            problems = problems[offset:offset+size]
            remaining = size-len(problems)
            query = query.offset(max(0, offset-static_count)).limit(remaining)
        for cp in query.iterator():
            problems.append(serialize_summary(_library_summary(cp.contest, cp)))
        from utils.http_cache import conditional_json
        return conditional_json({'data': problems, 'total': total if page else len(problems)})


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
    @AuthMiddleware.require_auth
    @RateLimitMiddleware.rate_limit(max_requests=12, window_seconds=60)
    def post(self):
        user = g.current_user
        data = json_object()
        try:
            code, language, _ = execution_fields(data, 'cpp', {'cpp', 'python', 'java', 'go', 'javascript'})
            cp = ContestProblem.get_by_id(int(data.get('contest_problem_id')))
        except (ValueError, TypeError):
            return {'error': '题目、代码或语言参数无效'}, 400
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404
        raw_key = request.headers.get('Idempotency-Key', '').strip()
        if len(raw_key) > 128:
            return {'error': '幂等键过长'}, 400
        # 与正式比赛的客户端幂等键分域；数据库自增 ID 是唯一事实源。
        key = 'library:' + hashlib.sha256(raw_key.encode()).hexdigest() if raw_key else None
        with get_database().atomic():
            contest = lock_contest(cp.contest_id)
            if not _is_contest_ended(contest):
                return {'error': '题目不存在'}, 404
            query = User.select().where(User.id == user['id'])
            if get_database().__class__.__name__ != 'SqliteDatabase':
                query = query.for_update()
            query.get()
            if key:
                old = ContestSubmission.select().where(
                    (ContestSubmission.contest == contest) & (ContestSubmission.user == user['id'])
                    & (ContestSubmission.idempotency_key == key)).first()
                if old:
                    if old.code != code or old.language != language or old.contest_problem_id != cp.id:
                        return {'error': '幂等键已用于不同提交'}, 409
                    return {'submission_id': old.id, 'status': old.status, 'idempotent_replay': True}, 202
            active = ContestSubmission.select().where(ContestSubmission.user == user['id'],
                ContestSubmission.contest_eligible == False, ContestSubmission.rejudge_of.is_null(),
                ~ContestSubmission.status.in_(list(TERMINAL_STATES))).count()
            if active >= 3:
                return {'error': '最多同时处理 3 个比赛题目提交'}, 429
            now = datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)
            job_id = uuid4().hex
            sub = ContestSubmission.create(contest=contest, contest_problem=cp, user=user['id'],
                problem_index=cp.problem_index, code=code, language=language, status=QUEUED,
                job_id=job_id, judge_submission_id=job_id, contest_eligible=False,
                received_at=now, submitted_at=now, queued_at=now, idempotency_key=key)
            outbox = ContestJudgeOutbox.create(submission=sub)
        dispatched = dispatch_outbox_entry(inject(IRedisService), outbox)
        return {'submission_id': sub.id, 'status': sub.status, 'queue_pending_retry': not dispatched}, 202


@api.route("/library/submission/<int:submission_id>")
class LibraryProblemSubmissionResultController(Resource):
    @AuthMiddleware.require_auth
    def get(self, submission_id):
        sub = ContestSubmission.get_or_none(ContestSubmission.id == submission_id,
                                            ContestSubmission.contest_eligible == False, ContestSubmission.rejudge_of.is_null())
        user = g.current_user
        if sub is None or (sub.user_id != int(user['id']) and user.get('role') != 'manager'):
            return {'error': '提交记录不存在'}, 404
        try:
            from services.contest_operations import testcase_details
            details = testcase_details(sub)
        except (TypeError, ValueError):
            details = []
        # 隐藏用例的输入、期望输出与实际输出均不能回传，后者同样可以泄露输入。
        cases = [{'testCaseIndex': i, 'passed': bool(d.get('passed')),
                  'stdout': '', 'stderr': '', 'expected': '', 'input': ''}
                 for i, d in enumerate(details) if isinstance(d, dict)]
        return {'id': sub.id, 'status': sub.status, 'time_used': sub.cpu_time,
                'memory_used': sub.memory, 'testcase_results': cases,
                'fail_testcase_index': next((c['testCaseIndex'] for c in cases if not c['passed']), None),
                'compile_error': '编译失败，请检查代码' if sub.status == 'CE' else None}, 200
