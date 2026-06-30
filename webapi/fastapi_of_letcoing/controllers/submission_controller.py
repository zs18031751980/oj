"""
提交判题 API 控制器模块

提供题目提交、判题状态查询、提交历史等接口。
判题流程异步化：提交 -> Redis队列 -> Worker处理 -> 结果可查询。
"""

from flask import g, request
from flask_restx import Namespace, Resource, fields

from core.di_container import inject
from interfaces.service_interfaces import IRedisService
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware
from models.db_models import Submission, Problem, Testcase, User

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


def _get_or_create_problem(problem_id: int):
    """从数据库查询题目，不存在则从内存数据创建"""
    from peewee import OperationalError
    from pages.problem_data import PROBLEMS
    pdata = PROBLEMS.get(problem_id)
    if not pdata:
        return None
    try:
        problem, created = Problem.get_or_create(
            id=problem_id,
            defaults=dict(
                title=pdata["title"],
                description=pdata["description"],
                input_desc=pdata.get("inputFormat", ""),
                output_desc=pdata.get("outputFormat", ""),
                difficulty=pdata.get("difficulty", "简单"),
                time_limit=pdata.get("timeLimit", 1000),
                memory_limit=pdata.get("memoryLimit", 256),
                is_public=True,
            ),
        )
        if created:
            for idx, tc in enumerate(pdata.get("testCases", [])):
                Testcase.create(
                    problem=problem,
                    input_data=tc["input"],
                    output_data=tc["output"],
                    is_sample=False,
                    sort_order=idx,
                )
            for idx, sc in enumerate(pdata.get("samples", [])):
                Testcase.create(
                    problem=problem,
                    input_data=sc["input"],
                    output_data=sc["output"],
                    is_sample=True,
                    sort_order=idx,
                )
        return problem
    except OperationalError:
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
        model = request.get_json(silent=True) or {}
        problem_id = model.get('problem_id')
        code = str(model.get('code', ''))
        language = str(model.get('language', 'cpp'))

        if not problem_id:
            return {'error': '题目ID不能为空'}, 400
        if not code.strip():
            return {'error': '代码不能为空'}, 400

        current_user = getattr(g, 'current_user', None)
        user = None
        if current_user:
            try:
                user = User.get_by_id(int(current_user['id']))
            except Exception:
                pass

        from pages.problem_data import PROBLEMS
        pdata = PROBLEMS.get(problem_id)
        testcase_list = pdata.get("testCases", []) if pdata else []

        problem = _get_or_create_problem(problem_id)
        pid = problem.id if problem and hasattr(problem, 'id') else problem_id
        try:
            submission = Submission.create(
                user=user,
                problem=pid,
                code=code,
                language=language,
                status=Submission.PENDING,
            )
            sid = submission.id
        except Exception:
            sid = None

        redis_service = inject(IRedisService)
        redis_service.list_push('judge_queue', {
            'submission_id': sid,
            'problem_id': problem_id,
            'code': code,
            'language': language,
            'testcases': testcase_list,
        })

        if sid:
            try:
                return Submission.get_by_id(sid).to_dict(), 201
            except Exception:
                pass
        return {'id': sid, 'status': 'Pending', 'problem_id': problem_id}, 201

    @api.doc('list_submissions')
    @api.param('problem_id', '题目ID（可选）')
    @api.param('page', '页码（默认1）')
    @api.param('per_page', '每页条数（默认20）')
    @AuthMiddleware.require_auth
    def get(self):
        """获取当前用户的提交历史"""
        current_user = getattr(g, 'current_user', None)
        if not current_user:
            return {'error': '未登录'}, 401

        problem_id = request.args.get('problem_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = Submission.select().where(Submission.user == current_user['id'])
        if problem_id:
            query = query.where(Submission.problem == problem_id)
        query = query.order_by(Submission.created_at.desc())
        total = query.count()
        submissions = query.paginate(page, per_page)

        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'data': [s.to_dict() for s in submissions],
        }, 200


@api.route('/<int:submission_id>')
@api.param('submission_id', '提交记录ID')
class SubmissionStatusController(Resource):
    @api.doc('get_submission_status')
    @api.response(200, 'Success', submission_status_model)
    @api.response(404, 'Not Found', error_model)
    def get(self, submission_id):
        """查询提交记录的状态和结果"""
        try:
            submission = Submission.get_by_id(submission_id)
        except Submission.DoesNotExist:
            return {'error': '提交记录不存在'}, 404
        return submission.to_dict(), 200
