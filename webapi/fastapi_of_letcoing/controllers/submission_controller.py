"""
提交判题 API 控制器模块

提供题目提交、判题状态查询等接口。
判题流程：提交与 outbox 同事务落库，Redis 投递，Worker 持久化结果。
"""

import json
from datetime import datetime

from flask import g, request
from flask_restx import Namespace, Resource, fields

from core.di_container import inject
from interfaces.service_interfaces import IRedisService
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware
from models.db_models import Submission, SubmissionOutbox, User, get_database
from uuid import uuid4

api = Namespace('submissions', description='提交判题相关接口')

submission_model = api.model('SubmissionRequest', {
    'problem_id': fields.Integer(required=True, description='题目ID'),
    'code': fields.String(required=True, description='提交的源代码'),
    'language': fields.String(default='cpp', description='编程语言'),
})

submission_status_model = api.model('SubmissionStatus', {
    'id': fields.Integer(description='提交记录ID'),
    'status': fields.String(description='判题状态'),
    'time_used': fields.Integer(description='运行时间(ms)'),
    'memory_used': fields.Integer(description='内存消耗(KB)'),
    'testcase_results': fields.Raw(description='各测试点结果'),
    'fail_testcase_index': fields.Integer(description='首个失败测试点索引'),
    'created_at': fields.String(description='提交时间'),
})

error_model = api.model('ErrorResponse', {
    'error': fields.String(description='错误信息'),
})


def _get_problem_data(problem_id):
    """从内存数据获取题目信息"""
    from pages.problem_data import PROBLEMS
    return PROBLEMS.get(problem_id)


def _current_user_id():
    """从认证中间件获取当前登录用户 ID（未登录返回 None）"""
    current_user = getattr(g, 'current_user', None)
    if not current_user:
        return None
    try:
        return int(current_user.get('id'))
    except (TypeError, ValueError):
        return None


@api.route('')
class SubmissionListCreateController(Resource):
    @api.expect(submission_model)
    @api.doc('create_submission')
    @api.response(201, 'Created', submission_status_model)
    @api.response(400, 'Bad Request', error_model)
    @AuthMiddleware.require_auth
    @RateLimitMiddleware.rate_limit(max_requests=30, window_seconds=60)
    def post(self):
        """提交代码进行判题"""
        from utils.request_validation import json_object, execution_fields
        from services.glot_service import JUDGE0_LANGUAGES
        from services.submission_outbox import dispatch_regular_entry
        data = json_object()
        try:
            code, language, _ = execution_fields(data, 'cpp', JUDGE0_LANGUAGES)
            problem_id = data.get('problem_id')
            if type(problem_id) is not int or problem_id < 1:
                raise ValueError('题目ID必须为正整数')
        except ValueError as exc:
            return {'error': str(exc)}, 400
        if not _get_problem_data(problem_id):
            return {'error': '题目不存在'}, 404
        user_id = _current_user_id()
        key = request.headers.get('Idempotency-Key', '').strip() or None
        if key and len(key) > 128:
            return {'error': '幂等键过长'}, 400
        try:
            with get_database().atomic():
                # 同一用户的受理串行化，避免并发请求绕过待处理上限。
                if get_database().__class__.__name__ != 'SqliteDatabase':
                    User.select().where(User.id == user_id).for_update().get()
                existing = (Submission.select().where(
                    (Submission.user == user_id) & (Submission.idempotency_key == key)).first()) if key else None
                if existing:
                    return {'id': existing.id, 'status': existing.status, 'idempotent_replay': True}, 201
                pending = Submission.select().where(
                    (Submission.user == user_id) & (Submission.status.in_(['Pending', 'Running']))).count()
                if pending >= 3:
                    return {'error': '最多同时处理 3 个提交'}, 429, {'Retry-After': '5'}
                submission = Submission.create(user=user_id, problem=problem_id, code=code,
                    language=language, status=Submission.PENDING, job_id=uuid4().hex,
                    idempotency_key=key)
                outbox = SubmissionOutbox.create(submission=submission)
        except Exception:
            return {'error': '提交记录暂时无法保存，请稍后重试'}, 503
        dispatch_regular_entry(inject(IRedisService), outbox)
        return {'id': submission.id, 'status': submission.status, 'problem_id': problem_id,
                'created_at': submission.created_at.isoformat()}, 201

    @api.doc('list_submissions')
    @api.param('page', '页码（默认 1）')
    @api.param('per_page', '每页数量（默认 20，最大 50）')
    @AuthMiddleware.require_auth
    def get(self):
        """获取当前用户的提交历史（来自 PostgreSQL 持久化记录）"""
        user_id = _current_user_id()
        if not user_id:
            return {'error': '请先登录'}, 401

        try:
            page = max(int(request.args.get('page', 1)), 1)
            per_page = min(max(int(request.args.get('per_page', 20)), 1), 50)
        except (TypeError, ValueError):
            page, per_page = 1, 20

        query = Submission.select().where(Submission.user == user_id)
        total = query.count()
        rows = query.order_by(Submission.id.desc()).paginate(page, per_page)

        data = []
        for s in rows:
            pdata = _get_problem_data(s.problem_id)
            data.append({
                'id': s.id,
                'problem_id': s.problem_id,
                'problem_title': pdata.get('title') if pdata else f'题目 {s.problem_id}',
                'difficulty': pdata.get('difficulty') if pdata else None,
                'language': s.language,
                'status': s.status,
                'time_used': s.time_used,
                'created_at': s.created_at.isoformat() if s.created_at else None,
            })

        return {'total': total, 'page': page, 'per_page': per_page, 'data': data}, 200


@api.route('/<int:submission_id>')
@api.param('submission_id', '提交记录ID')
class SubmissionStatusController(Resource):
    @api.doc('get_submission_status')
    @api.response(200, 'Success', submission_status_model)
    @api.response(404, 'Not Found', error_model)
    @AuthMiddleware.require_auth
    def get(self, submission_id):
        """查询提交记录的状态和结果"""
        try:
            submission = Submission.get_by_id(submission_id)
        except Submission.DoesNotExist:
            return {'error': '提交记录不存在'}, 404
        user = g.current_user
        if str(submission.user_id) != str(user['id']) and user.get('role') != 'manager':
            return {'error': '提交记录不存在'}, 404
        raw = submission.to_dict()
        fields = ('id', 'status', 'time_used', 'memory_used', 'testcase_results',
                  'fail_testcase_index', 'created_at', 'code', 'language')
        data = {name: raw.get(name) for name in fields}
        data['problem_id'] = submission.problem_id
        if isinstance(data['testcase_results'], list):
            data['testcase_results'] = [
                {key: item[key] for key in ('passed', 'status', 'time_used', 'skipped', 'testCaseIndex') if key in item}
                for item in data['testcase_results']
            ]
        return data, 200
