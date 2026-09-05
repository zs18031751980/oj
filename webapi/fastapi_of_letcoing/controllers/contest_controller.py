import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import Contest, ContestParticipant, User, ContestProblem, ContestTestcase, ContestSubmission
from core.di_container import inject
from interfaces.service_interfaces import IJWTService, IRedisService
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware
from services.judge_state import QUEUED

api = Namespace('contests', description='比赛管理接口')

SUPPORTED_CONTEST_MODES = {'ACM', 'OI'}

contest_model = api.model('Contest', {
    'id': fields.Integer(description='比赛ID'),
    'title': fields.String(description='比赛标题'),
    'description': fields.String(description='比赛描述'),
    'contest_type': fields.String(description='比赛类型'),
    'status': fields.String(description='状态'),
    'start_time': fields.String(description='开始时间'),
    'end_time': fields.String(description='结束时间'),
    'participants_count': fields.Integer(description='参与人数'),
    'created_at': fields.String(description='创建时间'),
})

contest_input = api.model('ContestInput', {
    'title': fields.String(required=True, description='比赛名称'),
    'description': fields.String(required=True, description='比赛简介'),
    'contest_type': fields.String(default='ACM', description='比赛类型'),
    'start_time': fields.String(description='开始时间'),
    'end_time': fields.String(description='结束时间'),
    'penalty_time': fields.Integer(default=20, description='罚时(分钟, ACM 模式)'),
})


def _get_current_user():
    """从 JWT 获取当前用户"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    jwt_service = inject(IJWTService)
    user_info = jwt_service.verify_access_token(auth_header[7:])
    if not user_info:
        return None
    try:
        return User.get_by_id(int(user_info.get('id', 0)))
    except Exception:
        return None


def _contest_to_dict(contest):
    """转换比赛为字典，包含参与人数"""
    data = contest.to_dict()
    data['status'] = _contest_status(contest)
    data['participants_count'] = ContestParticipant.select().where(
        ContestParticipant.contest == contest
    ).count()
    return data


_CST = timezone(timedelta(hours=8))


def _parse_dt(value):
    """将 ISO 时间字符串解析为 aware datetime（Asia/Shanghai UTC+8 墙钟）。

    约定数据库中的 start_time/end_time 以 Asia/Shanghai（UTC+8）墙钟存储：
    无时区的输入（如前端 datetime-local 的 "YYYY-MM-DDTHH:MM"）直接按 UTC+8
    解释，带时区的输入则统一换算到 UTC+8，使「传入墙钟 == 存储墙钟 == 读回墙钟」，
    消除重复编辑保存时的逐次 +8h 偏移。连接已强制 session timezone=Asia/Shanghai，
    因此 psycopg 会按该时区将 aware 值落地为墙钟。
    """
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_CST)
        else:
            dt = dt.astimezone(_CST)
        return dt
    except Exception:
        return None


def _contest_time_error(contest):
    """返回当前时间不在比赛设定范围内时的错误提示，否则返回 None。

    数据库 start_time/end_time 为 timestamp without time zone，按项目约定以
    Asia/Shanghai（UTC+8）墙钟存储/传输；读出时为 naive 值，这里统一当作 UTC+8
    解释再与 UTC 当前时间比较，避免被误当作 UTC 而产生时区偏移。
    """
    now = datetime.now(timezone.utc)

    def _aware(dt):
        if dt is None:
            return None
        return dt.replace(tzinfo=_CST) if dt.tzinfo is None else dt.astimezone(_CST)

    start = _aware(contest.start_time)
    end = _aware(contest.end_time)
    if start is not None and now < start:
        return '比赛尚未开始'
    if end is not None and now > end:
        return '比赛已结束'
    return None


def _contest_status(contest):
    """基于当前时间返回实时状态，不依赖创建时写入的过期状态字段。"""
    error = _contest_time_error(contest)
    if error == '比赛尚未开始':
        return 'upcoming'
    if error == '比赛已结束':
        return 'past'
    return 'ongoing'


def _require_participant(contest, user):
    """比赛中的题目与提交只允许已报名参赛者访问。"""
    return ContestParticipant.select().where(
        ContestParticipant.contest == contest,
        ContestParticipant.user == user,
    ).exists()


def _public_problem_data(problem):
    """对参赛者返回题面，不暴露参考答案或任何隐藏测试数据。"""
    data = problem.to_dict()
    data.pop('correct_answer', None)
    return data


def _safe_submission_result(result):
    """移除隐藏测试数据，保留前端展示判题状态所需的最小信息。"""
    safe = dict(result)
    details = safe.get('details')
    if isinstance(details, list):
        safe['details'] = [
            {
                'passed': bool(item.get('passed')),
                'status': item.get('status', 'Error'),
                'time_used': item.get('time_used', 0),
            }
            for item in details if isinstance(item, dict)
        ]
    return safe


def _submission_to_result(submission):
    """将数据库提交转换为不包含源代码和隐藏测试数据的轮询响应。"""
    data = {
        'id': submission.id,
        'submission_id': submission.id,
        'contest_id': submission.contest_id,
        'problem_id': submission.contest_problem_id,
        'user_id': submission.user_id,
        'status': submission.status,
        'verdict': submission.verdict or submission.status,
        'passed': submission.passed,
        'total': submission.total,
        'score': submission.score,
        'language': submission.language,
        'attempt_id': submission.attempt_id,
        'job_id': submission.job_id,
        'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
        'queued_at': submission.queued_at.isoformat() if submission.queued_at else None,
        'judge_started_at': submission.judge_started_at.isoformat() if submission.judge_started_at else None,
        'finished_at': submission.finished_at.isoformat() if submission.finished_at else None,
        'cpu_time': submission.cpu_time,
        'wall_time': submission.wall_time,
        'memory': submission.memory,
        'output_size': submission.output_size,
        'error_message': submission.error_message,
    }
    if submission.testcase_results:
        try:
            data['details'] = json.loads(submission.testcase_results)
        except (TypeError, ValueError):
            data['details'] = []
    else:
        data['details'] = []
    return _safe_submission_result(data)


@api.route('/')
class ContestListController(Resource):
    @api.doc('list_contests')
    @api.param('status', '筛选状态(upcoming/ongoing/past)')
    def get(self):
        """获取比赛列表"""
        status_filter = request.args.get('status', '').strip()
        query = Contest.select().where(Contest.is_public == True)
        if status_filter:
            query = query.where(Contest.status == status_filter)
        contests = query.order_by(Contest.start_time.desc())
        return [_contest_to_dict(c) for c in contests], 200

    @api.expect(contest_input)
    def post(self):
        """创建比赛（需登录）"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role != 'manager':
            return {'error': '仅管理员可管理比赛'}, 403

        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        if not title:
            return {'error': '比赛名称不能为空'}, 400

        description = data.get('description', '').strip()
        if not description:
            return {'error': '比赛简介不能为空'}, 400

        start_time = _parse_dt(data.get('start_time'))
        end_time = _parse_dt(data.get('end_time'))
        if start_time and end_time and end_time <= start_time:
            return {'error': '结束时间必须晚于开始时间'}, 400
        contest_type = str(data.get('contest_type', 'ACM')).upper()
        if contest_type not in SUPPORTED_CONTEST_MODES:
            return {'error': '比赛模式仅支持 ACM 或 OI'}, 400

        # 自动推断状态（与 _contest_time_error 一致，使用 UTC now）
        now = datetime.now(timezone.utc)
        status = 'upcoming'
        if start_time and end_time:
            if now < start_time:
                status = 'upcoming'
            elif now > end_time:
                status = 'past'
            else:
                status = 'ongoing'

        contest = Contest.create(
            title=title,
            description=description,
            contest_type=contest_type,
            status=status,
            start_time=start_time,
            end_time=end_time,
            created_by=user.id,
            penalty_time=int(data.get('penalty_time', 20) or 20),
        )
        return _contest_to_dict(contest), 201


@api.route('/<int:contest_id>')
class ContestDetailController(Resource):
    def get(self, contest_id):
        """获取比赛详情"""
        try:
            contest = Contest.get_by_id(contest_id)
            return _contest_to_dict(contest), 200
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404

    def put(self, contest_id):
        """更新比赛"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role != 'manager':
            return {'error': '仅管理员可管理比赛'}, 403

        try:
            contest = Contest.get_by_id(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404

        data = request.get_json(silent=True) or {}
        if 'title' in data:
            contest.title = str(data['title'] or '').strip() or contest.title
        if 'description' in data:
            contest.description = data['description']
        if 'contest_type' in data:
            contest_type = str(data['contest_type']).upper()
            if contest_type not in SUPPORTED_CONTEST_MODES:
                return {'error': '比赛模式仅支持 ACM 或 OI'}, 400
            contest.contest_type = contest_type
        if 'status' in data:
            contest.status = data['status']
        if 'start_time' in data and data['start_time']:
            parsed = _parse_dt(data['start_time'])
            if parsed is not None:
                contest.start_time = parsed
        if 'end_time' in data and data['end_time']:
            parsed = _parse_dt(data['end_time'])
            if parsed is not None:
                contest.end_time = parsed
        if contest.start_time and contest.end_time and contest.end_time <= contest.start_time:
            return {'error': '结束时间必须晚于开始时间'}, 400
        if 'penalty_time' in data:
            try:
                contest.penalty_time = int(data['penalty_time'] or 20)
            except (ValueError, TypeError):
                pass
        contest.save()
        return _contest_to_dict(contest), 200

    def delete(self, contest_id):
        """删除比赛"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role != 'manager':
            return {'error': '仅管理员可管理比赛'}, 403

        try:
            contest = Contest.get_by_id(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404

        try:
            # 先显式级联删除依赖数据，避免外键约束冲突
            # 比赛提交记录同时引用 contest 与 contest_problem（均为非空外键），
            # 必须在删除题目/比赛前清理，否则会因外键约束导致删除失败。
            ContestSubmission.delete().where(
                ContestSubmission.contest == contest
            ).execute()
            problem_ids = [
                cp.id
                for cp in ContestProblem.select(ContestProblem.id).where(
                    ContestProblem.contest == contest
                )
            ]
            if problem_ids:
                ContestTestcase.delete().where(
                    ContestTestcase.contest_problem.in_(problem_ids)
                ).execute()
                ContestProblem.delete().where(
                    ContestProblem.contest == contest
                ).execute()
            ContestParticipant.delete().where(
                ContestParticipant.contest == contest
            ).execute()
            contest.delete_instance()
            return {'success': True}, 200
        except Exception as exc:
            return {'error': f'删除失败: {exc}'}, 500


@api.route('/<int:contest_id>/join')
class ContestJoinController(Resource):
    def post(self, contest_id):
        """参加比赛"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401

        try:
            contest = Contest.get_by_id(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404

        time_error = _contest_time_error(contest)
        if time_error:
            return {'error': time_error}, 400

        exists = ContestParticipant.select().where(
            ContestParticipant.contest == contest,
            ContestParticipant.user == user,
        ).exists()
        if exists:
            return {'success': True, 'message': '已参加比赛', 'already_joined': True}, 200

        try:
            ContestParticipant.create(contest=contest, user=user)
        except Exception:
            # 并发报名时唯一索引可能先于本次请求写入；按幂等成功处理。
            return {'success': True, 'message': '已参加比赛', 'already_joined': True}, 200
        return {'success': True, 'message': '已参加比赛'}, 201


@api.route('/<int:contest_id>/problems/<int:problem_id>/submit')
@api.param('contest_id', '比赛ID')
@api.param('problem_id', '比赛题目ID')
class ContestProblemSubmitController(Resource):
    @AuthMiddleware.require_auth
    @RateLimitMiddleware.rate_limit(max_requests=12, window_seconds=60)
    def post(self, contest_id: int, problem_id: int):
        """提交比赛题目代码进行判题（异步入队，返回 submission_id 供轮询）"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401

        try:
            contest = Contest.get_by_id(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404

        time_error = _contest_time_error(contest)
        if time_error:
            return {'error': time_error}, 400
        if not _require_participant(contest, user):
            return {'error': '请先参加比赛'}, 403

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

        if problem.contest_id != contest_id:
            return {'error': '题目不属于该比赛'}, 400

        data = request.get_json(silent=True) or {}
        code = str(data.get('code', ''))
        language = str(data.get('language', 'cpp') or 'cpp')
        if not code.strip():
            return {'error': '代码不能为空'}, 400

        redis_service = inject(IRedisService)
        job_id = uuid4().hex
        # 排行榜罚时以用户提交进入系统的时刻为准，绝不能使用 Worker 排队完成时刻。
        submitted_at = datetime.now(_CST).replace(tzinfo=None).isoformat()

        # PostgreSQL 是提交事实源：先创建记录，再把 job 放入队列。
        # 数据库不可用时直接拒绝提交，避免产生 Redis 中永久 Pending 的幽灵任务。
        try:
            submission = ContestSubmission.create(
                contest=contest,
                user=user,
                contest_problem=problem,
                problem_index=problem.problem_index or '',
                status=QUEUED,
                verdict=None,
                language=language,
                code=code,
                judge_submission_id=job_id,
                job_id=job_id,
                attempt_id=1,
                queued_at=datetime.fromisoformat(submitted_at),
                submitted_at=datetime.fromisoformat(submitted_at),
            )
        except Exception:
            return {'error': '提交记录暂时无法保存，请稍后重试'}, 503
        submission_id = submission.id

        # 状态与任务必须原子写入：若进程在两条独立 Redis 命令之间退出，用户会看到
        # 永久 Pending 或 Worker 收到没有状态的任务。事务确保二者同时成功或同时失败。
        if not redis_service.enqueue_with_state(
            f'contest_submission:{submission_id}',
            {
                'problem_id': problem_id,
                'contest_id': contest_id,
                'user_id': user.id,
                'status': QUEUED,
                'attempt_id': 1,
                'job_id': job_id,
                'passed': 0,
                'total': 0,
                'details': [],
            },
            3600,
            'contest_judge_queue',
            {
                'submission_id': submission_id,
                'job_id': job_id,
                'attempt_id': 1,
                'contest_id': contest_id,
                'problem_id': problem_id,
                'user_id': user.id,
                'language': language,
                'submitted_at': submitted_at,
            },
        ):
            # 队列不可用时不能留下不可判题的数据库记录，标记为系统错误供审计。
            ContestSubmission.update(
                status='SystemError',
                verdict='SystemError',
                error_message='判题队列不可用',
                finished_at=datetime.now(_CST).replace(tzinfo=None),
            ).where(ContestSubmission.id == submission_id).execute()
            return {'error': '判题队列暂不可用，请稍后重试'}, 503

        return {'submission_id': submission_id, 'job_id': job_id, 'attempt_id': 1, 'status': QUEUED}, 202


@api.route('/<int:contest_id>/problems/<int:problem_id>/submission/<int:submission_id>')
@api.param('contest_id', '比赛ID')
@api.param('problem_id', '比赛题目ID')
@api.param('submission_id', '提交记录ID')
class ContestProblemSubmissionResultController(Resource):
    def get(self, contest_id: int, problem_id: int, submission_id: int):
        """轮询比赛题目判题结果"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        try:
            submission = ContestSubmission.get_by_id(submission_id)
        except ContestSubmission.DoesNotExist:
            return {'error': '提交记录不存在'}, 404
        if (
            submission.user_id != user.id
            or submission.contest_id != contest_id
            or submission.contest_problem_id != problem_id
        ):
            return {'error': '无权访问该提交'}, 403
        return _submission_to_result(submission), 200


@api.route('/<int:contest_id>/problems')
@api.param('contest_id', '比赛ID')
class ContestProblemListPublicController(Resource):
    def get(self, contest_id: int):
        """获取比赛题目列表（公开接口）"""
        try:
            problems = ContestProblem.select().where(
                ContestProblem.contest_id == contest_id
            ).order_by(ContestProblem.problem_index)
            return [_public_problem_data(p) for p in problems], 200
        except Exception as e:
            return {'error': str(e)}, 500


@api.route('/<int:contest_id>/statuses')
@api.param('contest_id', '比赛ID')
class ContestProblemStatusesController(Resource):
    def get(self, contest_id: int):
        """获取当前用户在该比赛各题的最新判题状态（用于题目列表着色）"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        try:
            contest = Contest.get_by_id(contest_id)
            if not _require_participant(contest, user):
                return {'error': '请先参加比赛'}, 403
            subs = (
                ContestSubmission.select()
                .where(
                    ContestSubmission.contest == contest_id,
                    ContestSubmission.user == user,
                )
                .order_by(ContestSubmission.submitted_at.desc())
            )
            best: dict = {}
            for s in subs:
                pid = s.contest_problem_id
                if pid not in best:
                    best[pid] = {'status': s.status, 'solved': s.status == 'AC'}
                elif not best[pid]['solved'] and s.status == 'AC':
                    best[pid] = {'status': 'AC', 'solved': True}
            return best, 200
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        except Exception:
            return {}, 200


@api.route('/<int:contest_id>/problems/<int:problem_id>')
@api.param('contest_id', '比赛ID')
@api.param('problem_id', '比赛题目ID')
class ContestProblemDetailPublicController(Resource):
    def get(self, contest_id: int, problem_id: int):
        """获取单个比赛题目详情（公开接口，不含测试用例和答案）"""
        try:
            problem = ContestProblem.get_by_id(problem_id)
            if not problem or problem.contest_id != contest_id:
                return {'error': '题目不存在'}, 404
            contest = Contest.get_by_id(contest_id)
            time_error = _contest_time_error(contest)
            if time_error:
                return {'error': time_error}, 403
            user = _get_current_user()
            if not user or not _require_participant(contest, user):
                return {'error': '请先参加比赛'}, 403
            return _public_problem_data(problem), 200
        except Exception as e:
            return {'error': str(e)}, 500


@api.route('/problems/<int:problem_id>')
@api.param('problem_id', '比赛题目ID')
class ContestProblemByIdPublicController(Resource):
    def get(self, problem_id: int):
        """废弃无比赛上下文的题目读取接口，避免绕过时间与报名校验。"""
        return {'error': '请通过比赛题目地址访问'}, 410
