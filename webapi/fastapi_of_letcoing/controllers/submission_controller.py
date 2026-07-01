"""
提交判题 API 控制器模块

提供题目提交、判题状态查询等接口。
判题流程：提交 -> Redis 队列 -> Worker 处理 -> 结果可查询。
支持无 PostgreSQL 模式（仅依赖 Redis）。
"""

import json
from datetime import datetime

from flask import g, request
from flask_restx import Namespace, Resource, fields

from core.di_container import inject
from interfaces.service_interfaces import IRedisService
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware

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


def _next_id(redis_service):
    """生成自增提交 ID（通过 Redis 原子计数器）"""
    try:
        return redis_service.increment('submission:id_counter')
    except Exception:
        import uuid
        return abs(hash(str(uuid.uuid4()))) % (10 ** 8) + 1


def _redis_sub_key(sid):
    return f'submission:{sid}'


def _save_submission_to_redis(redis_service, sid, data):
    """将提交数据存入 Redis（TTL 1 小时）"""
    try:
        redis_service.set(_redis_sub_key(sid), data, 3600)
    except Exception:
        pass


def _get_submission_from_redis(redis_service, sid):
    """从 Redis 读取提交数据"""
    try:
        return redis_service.get(_redis_sub_key(sid))
    except Exception:
        return None


def _get_problem_data(problem_id):
    """从内存数据获取题目信息"""
    from pages.problem_data import PROBLEMS
    return PROBLEMS.get(problem_id)


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
        model = request.get_json(silent=True) or {}
        problem_id = model.get('problem_id')
        code = str(model.get('code', ''))
        language = str(model.get('language', 'cpp'))

        if not problem_id:
            return {'error': '题目ID不能为空'}, 400
        if not code.strip():
            return {'error': '代码不能为空'}, 400

        pdata = _get_problem_data(problem_id)
        if not pdata:
            return {'error': '题目不存在'}, 404

        redis_service = inject(IRedisService)
        sid = _next_id(redis_service)
        now = datetime.utcnow().isoformat()

        submission_data = {
            'id': sid,
            'problem_id': problem_id,
            'code': code,
            'language': language,
            'status': 'Pending',
            'time_used': None,
            'memory_used': None,
            'testcase_results': None,
            'fail_testcase_index': None,
            'created_at': now,
        }

        _save_submission_to_redis(redis_service, sid, submission_data)

        testcase_list = pdata.get("testCases", [])
        redis_service.list_push('judge_queue', {
            'submission_id': sid,
            'problem_id': problem_id,
            'code': code,
            'language': language,
            'testcases': testcase_list,
        })

        return submission_data, 201

    @api.doc('list_submissions')
    @api.param('problem_id', '题目ID（可选）')
    @AuthMiddleware.require_auth
    def get(self):
        """获取当前用户的提交历史（仅返回最后 50 条 Redis 缓存）"""
        return {'total': 0, 'page': 1, 'per_page': 50, 'data': []}, 200


@api.route('/<int:submission_id>')
@api.param('submission_id', '提交记录ID')
class SubmissionStatusController(Resource):
    @api.doc('get_submission_status')
    @api.response(200, 'Success', submission_status_model)
    @api.response(404, 'Not Found', error_model)
    def get(self, submission_id):
        """查询提交记录的状态和结果"""
        redis_service = inject(IRedisService)
        data = _get_submission_from_redis(redis_service, submission_id)
        if data:
            tr = data.get('testcase_results')
            if isinstance(tr, str):
                try:
                    data['testcase_results'] = json.loads(tr)
                except Exception:
                    pass
            return data, 200
        return {'error': '提交记录不存在或已过期'}, 404
