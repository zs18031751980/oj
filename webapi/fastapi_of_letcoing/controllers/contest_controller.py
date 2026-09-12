from services.contest_lifecycle import transactional, lock_contest
import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from flask import g, request
from flask_restx import Namespace, Resource, fields
from models.db_models import (
    Contest, ContestParticipant, User, ContestProblem, ContestTestcase, ContestSubmission,
    ContestJudgeOutbox, ContestTeamMember, get_database,
)
from core.di_container import inject
from interfaces.service_interfaces import IJWTService, IRedisService
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware
from services.contest_lifecycle import can_delete_contest
from services.contest_outbox import dispatch_outbox_entry
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
    'freeze_time': fields.String(description='封榜时间（可选）'),
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
    data['lifecycle_state'] = contest.lifecycle_state
    data['is_frozen'] = _contest_is_frozen(contest)
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


def _contest_submission_replay(contest_id, owner, key, problem_id, language, code):
    """同一请求的重取先于额度和时间限制；同键异内容明确拒绝。"""
    if not key:
        return None
    existing = ContestSubmission.select().where(
        ContestSubmission.contest == contest_id, owner,
        ContestSubmission.contest_eligible == True,
        ContestSubmission.idempotency_key == key,
    ).first()
    if existing is None:
        return None
    if (existing.contest_problem_id != problem_id or existing.language != language or existing.code != code):
        return {'error': '幂等键已用于不同提交'}, 409
    return {'submission_id': existing.id, 'job_id': existing.job_id,
        'attempt_id': existing.attempt_id, 'status': existing.status,
        'idempotent_replay': True}, 202


def _contest_time_error(contest, received_at=None):
    """返回当前时间不在比赛设定范围内时的错误提示，否则返回 None。

    数据库 start_time/end_time 为 timestamp without time zone，按项目约定以
    Asia/Shanghai（UTC+8）墙钟存储/传输；读出时为 naive 值，这里统一当作 UTC+8
    解释再与 UTC 当前时间比较，避免被误当作 UTC 而产生时区偏移。
    """
    if contest.lifecycle_state == 'FINALIZED':
        return '比赛已结算'
    if contest.lifecycle_state in {'DRAFT', 'READY'}:
        return '比赛尚未发布'
    if contest.lifecycle_state == 'CANCELLED':
        return '比赛已取消'
    now = received_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_CST)

    def _aware(dt):
        if dt is None:
            return None
        return dt.replace(tzinfo=_CST) if dt.tzinfo is None else dt.astimezone(_CST)

    start = _aware(contest.start_time)
    end = _aware(contest.end_time)
    if start is not None and now < start:
        return '比赛尚未开始'
    if end is not None and now >= end:
        return '比赛已结束'
    return None


def _contest_status(contest):
    """基于当前时间返回实时状态，不依赖创建时写入的过期状态字段。"""
    error = _contest_time_error(contest)
    if error in ('比赛尚未发布', '比赛尚未开始'):
        return 'upcoming'
    if error in ('比赛已取消', '比赛已结束', '比赛已结算'):
        return 'past'
    return 'ongoing'


def _contest_is_frozen(contest) -> bool:
    """封榜只影响对参赛者的公开可见性，不停止判题或真实计分。"""
    if (not contest.freeze_time or contest.thawed_at
            or contest.lifecycle_state in {'DRAFT', 'READY', 'CANCELLED'}):
        return False
    freeze_time = contest.freeze_time
    if freeze_time.tzinfo is None:
        freeze_time = freeze_time.replace(tzinfo=_CST)
    else:
        freeze_time = freeze_time.astimezone(_CST)
    return datetime.now(timezone.utc) >= freeze_time


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
    data.pop('validation_error', None)
    data.pop('checker_config', None)
    data.pop('package_digest', None)
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
        'received_at': submission.received_at.isoformat() if submission.received_at else None,
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
        query = Contest.select().where(
            Contest.is_public == True,
            Contest.lifecycle_state != 'DRAFT',
            Contest.lifecycle_state != 'CANCELLED',
        )
        contests = query.order_by(Contest.start_time.desc())
        data = [_contest_to_dict(c) for c in contests]
        if status_filter:
            data = [item for item in data if item['status'] == status_filter]
        return data, 200

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
        freeze_time = _parse_dt(data.get('freeze_time'))
        if start_time and end_time and end_time <= start_time:
            return {'error': '结束时间必须晚于开始时间'}, 400
        if freeze_time and (not start_time or not end_time or not start_time < freeze_time < end_time):
            return {'error': '封榜时间必须位于开始与结束时间之间'}, 400
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
            freeze_time=freeze_time,
            lifecycle_state='DRAFT',
        )
        return _contest_to_dict(contest), 201


@api.route('/<int:contest_id>')
class ContestDetailController(Resource):
    def get(self, contest_id):
        """获取比赛详情"""
        try:
            contest = Contest.get_by_id(contest_id)
            user = _get_current_user()
            is_manager = bool(user and user.role == 'manager')
            if (not contest.is_public or contest.lifecycle_state == 'DRAFT') and not is_manager:
                return {'error': '比赛不存在'}, 404
            return _contest_to_dict(contest), 200
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404

    @transactional
    def put(self, contest_id):
        """更新比赛"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role != 'manager':
            return {'error': '仅管理员可管理比赛'}, 403

        try:
            contest = lock_contest(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        if contest.lifecycle_state not in ('DRAFT', 'READY'):
            return {'error': '比赛发布后不能直接修改规则或时间'}, 409

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
        if 'freeze_time' in data:
            contest.freeze_time = _parse_dt(data['freeze_time']) if data['freeze_time'] else None
        if contest.start_time and contest.end_time and contest.end_time <= contest.start_time:
            return {'error': '结束时间必须晚于开始时间'}, 400
        if contest.freeze_time and (
            not contest.start_time
            or not contest.end_time
            or not contest.start_time < contest.freeze_time < contest.end_time
        ):
            return {'error': '封榜时间必须位于开始与结束时间之间'}, 400
        if 'penalty_time' in data:
            try:
                contest.penalty_time = int(data['penalty_time'] or 20)
            except (ValueError, TypeError):
                pass
        contest.save()
        return _contest_to_dict(contest), 200


    @transactional
    def delete(self, contest_id):
        """删除比赛"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role != 'manager':
            return {'error': '仅管理员可管理比赛'}, 403

        try:
            contest = lock_contest(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        if not can_delete_contest(contest.lifecycle_state):
            return {'error': '已发布比赛必须保留审计记录；请取消比赛，不能删除'}, 409

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
            return {'error': '服务暂时不可用'}, 503


@api.route('/<int:contest_id>/cancel')
class ContestCancelController(Resource):
    @transactional
    def post(self, contest_id):
        """取消比赛但保留题目、提交和操作痕迹，避免破坏审计链。"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role != 'manager':
            return {'error': '仅管理员可管理比赛'}, 403
        try:
            contest = lock_contest(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        if contest.lifecycle_state == 'FINALIZED':
            return {'error': '最终榜已结算，不能取消'}, 409
        contest.lifecycle_state = 'CANCELLED'
        contest.save()
        return _contest_to_dict(contest), 200


@api.route('/manage')
class ContestManageListController(Resource):
    def get(self):
        """管理员比赛工作台：包含尚未公开的草稿。"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role != 'manager':
            return {'error': '仅管理员可查看比赛工作台'}, 403
        contests = Contest.select().order_by(Contest.start_time.desc())
        return [_contest_to_dict(contest) for contest in contests], 200


@api.route('/<int:contest_id>/publish')
class ContestPublishController(Resource):
    @transactional
    def post(self, contest_id):
        """发布比赛：冻结发布版本前，必须保证每题均有可用隐藏测试数据。"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role != 'manager':
            return {'error': '仅管理员可发布比赛'}, 403
        try:
            contest = lock_contest(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        if contest.lifecycle_state not in ('DRAFT', 'READY'):
            return {'error': '比赛已发布，不能再次发布'}, 409
        if not contest.start_time or not contest.end_time:
            return {'error': '发布比赛必须设置开始和结束时间'}, 400
        problems = list(ContestProblem.select().where(ContestProblem.contest == contest))
        if not problems:
            return {'error': '发布比赛至少需要一道题目'}, 400
        for problem in problems:
            if problem.validation_status != 'VALID':
                return {'error': f'题目 {problem.problem_index} 的参考答案尚未验证通过'}, 409
            has_hidden_testcase = ContestTestcase.select().where(
                ContestTestcase.contest_problem == problem,
                ContestTestcase.is_sample == False,
            ).exists()
            if not has_hidden_testcase:
                return {'error': f'题目 {problem.problem_index} 缺少隐藏测试数据'}, 400
        from services.contest_packages import publish_package
        for problem in problems:
            problem.package_digest = publish_package(problem, user.id).digest
            problem.save(only=[ContestProblem.package_digest])
        contest.scoreboard_requested_version += 1
        contest.lifecycle_state = 'SCHEDULED'
        contest.published_at = datetime.now(_CST).replace(tzinfo=None)
        contest.save()
        return _contest_to_dict(contest), 200


@api.route('/<int:contest_id>/join')
class ContestJoinController(Resource):
    @transactional
    def post(self, contest_id):
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        try:
            contest = lock_contest(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        if ContestParticipant.select().where(ContestParticipant.contest == contest,
                ContestParticipant.user == user).exists():
            return {'success': True, 'already_joined': True}, 200
        from services.contest_operations import now, emit
        if contest.lifecycle_state not in {'SCHEDULED', 'RUNNING'} or not contest.is_public:
            return {'error': '比赛未开放报名'}, 409
        if not contest.start_time or now() >= contest.start_time:
            return {'error': '比赛开始后名单已锁定'}, 409
        ContestParticipant.create(contest=contest, user=user)
        Contest.update(scoreboard_requested_version=Contest.scoreboard_requested_version+1).where(Contest.id == contest_id).execute()
        emit(contest_id, 'entry', {'entry_id': user.id})
        return {'success': True, 'message': '报名成功'}, 201


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

        if not _require_participant(contest, user):
            return {'error': '请先参加比赛'}, 403

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

        if problem.contest_id != contest_id:
            return {'error': '题目不属于该比赛'}, 400

        data = request.get_json(silent=True) or {}
        from utils.request_validation import execution_fields
        try:
            code, language, _ = execution_fields(data, 'cpp', set(json.loads(contest.allowed_languages)))
        except ValueError as exc:
            return {'error': str(exc)}, 400

        member = ContestTeamMember.get_or_none(ContestTeamMember.contest == contest_id, ContestTeamMember.user == user.id)
        owner = (ContestSubmission.team == member.team_id) if member else (ContestSubmission.user == user.id)
        idempotency_key = request.headers.get('Idempotency-Key', '').strip() or None
        if idempotency_key and len(idempotency_key) > 128:
            return {'error': '幂等键过长'}, 400
        replay = _contest_submission_replay(contest_id, owner, idempotency_key, problem.id, language, code)
        if replay is not None:
            return replay

        redis_service = inject(IRedisService)
        job_id = uuid4().hex
        # 排行榜罚时以用户提交进入系统的时刻为准，绝不能使用 Worker 排队完成时刻。
        received_at = datetime.now(_CST).replace(tzinfo=None)
        time_error = _contest_time_error(contest, received_at)
        if time_error:
            return {'error': time_error}, 400
        submitted_at = received_at.isoformat()

        # PostgreSQL 是提交事实源：先创建记录，再把 job 放入队列。
        # 数据库不可用时直接拒绝提交，避免产生 Redis 中永久 Pending 的幽灵任务。
        try:
            with get_database().atomic():
                contest = lock_contest(contest_id)
                current_user = User.get_or_none(User.id == user.id)
                if not current_user or not current_user.is_active or not _require_participant(contest, current_user):
                    return {'error': '参赛身份已失效，请重新确认账号和报名状态'}, 403
                member = ContestTeamMember.get_or_none(ContestTeamMember.contest == contest_id, ContestTeamMember.user == user.id)
                owner = (ContestSubmission.team == member.team_id) if member else (ContestSubmission.user == user.id)
                replay = _contest_submission_replay(contest_id, owner, idempotency_key, problem_id, language, code)
                if replay is not None:
                    return replay
                time_error = _contest_time_error(contest, received_at)
                if time_error:
                    return {'error': time_error}, 409
                entry_id = member.team.captain_id if member else user.id
                # 比赛行锁已串行化本场额度检查，避免再锁全局用户行。
                problem = ContestProblem.get_by_id(problem_id)
                from services.judge_state import TERMINAL_STATES
                active = ContestSubmission.select().where(owner, ContestSubmission.contest == contest,
                    ContestSubmission.contest_eligible == True,
                    ~ContestSubmission.status.in_(list(TERMINAL_STATES))).count()
                if active >= contest.active_submission_limit:
                    return {'error': f'最多同时处理 {contest.active_submission_limit} 个比赛提交'}, 429, {'Retry-After': '5'}
                from services.contest_packages import publish_package, canonical
                import hashlib
                if not problem.package_digest:
                    problem.package_digest = publish_package(problem, user.id).digest
                    problem.save(only=[ContestProblem.package_digest])
                digest = hashlib.sha256(canonical([contest_id, entry_id, problem_id, language, code]).encode()).hexdigest()
                submission = ContestSubmission.create(
                    contest=contest,
                    user=user, team=member.team_id if member else None,
                    package_digest=problem.package_digest, request_digest=digest,
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
                    received_at=received_at,
                    contest_eligible=True,
                    submitted_at=datetime.fromisoformat(submitted_at),
                    idempotency_key=idempotency_key,
                )
                outbox = ContestJudgeOutbox.create(submission=submission)
                Contest.update(scoreboard_requested_version=Contest.scoreboard_requested_version+1).where(Contest.id == contest_id).execute()
                from services.contest_operations import emit
                emit(contest_id, 'submission', {'submission_id': submission.id, 'entry_id': entry_id}, 'jury')
        except Exception:
            # 并发重试可能由唯一幂等索引先完成写入；把它视为同一提交。
            replay = _contest_submission_replay(contest_id, owner, idempotency_key, problem_id, language, code)
            if replay is not None:
                return replay
            return {'error': '提交记录暂时无法保存，请稍后重试'}, 503
        submission_id = submission.id
        import logging
        logging.getLogger('letcoding.requests').info(
            'submission_accepted request_id=%s submission_id=%s job_id=%s attempt_id=%s',
            getattr(g, 'request_id', ''), submission_id, job_id, submission.attempt_id)

        # 数据库已持久化事实与 outbox；即时投递失败也由 Worker 后续补偿，不能丢比赛提交。
        dispatched = dispatch_outbox_entry(redis_service, outbox)
        return {
            'submission_id': submission_id,
            'job_id': job_id,
            'attempt_id': 1,
            'status': QUEUED,
            'queue_pending_retry': not dispatched,
        }, 202


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
        if submission.rejudge_of is not None or not submission.contest_eligible:
            return {'error': '提交记录不存在'}, 404
        if (
            (submission.user_id != user.id and not (
                submission.team_id and ContestTeamMember.select().where(
                    ContestTeamMember.team == submission.team_id,
                    ContestTeamMember.user == user.id).exists()))
            or submission.contest_id != contest_id
            or submission.contest_problem_id != problem_id
        ):
            return {'error': '无权访问该提交'}, 403
        result = _submission_to_result(submission)
        # 封榜保护其他队伍结果；队伍始终可以查看自己的判定。
        if 'oi' not in (submission.contest.contest_type or '').lower():
            result.update(passed=0, total=0, score=0, details=[])
        return result, 200


@api.route('/<int:contest_id>/problems')
@api.param('contest_id', '比赛ID')
class ContestProblemListPublicController(Resource):
    def get(self, contest_id: int):
        """获取比赛题目目录；仅进行中的已报名参赛者可访问。"""
        try:
            contest = Contest.get_by_id(contest_id)
            time_error = _contest_time_error(contest)
            if time_error:
                return {'error': time_error}, 403
            user = _get_current_user()
            if not user or not _require_participant(contest, user):
                return {'error': '请先参加比赛'}, 403
            problems = ContestProblem.select().where(
                ContestProblem.contest_id == contest_id
            ).order_by(ContestProblem.problem_index)
            return [_public_problem_data(p) for p in problems], 200
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        except Exception as e:
            return {'error': '服务暂时不可用'}, 503


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
            member = ContestTeamMember.get_or_none(ContestTeamMember.contest == contest_id, ContestTeamMember.user == user.id)
            owner = (ContestSubmission.team == member.team_id) if member else (ContestSubmission.user == user.id)
            subs = (ContestSubmission.select(ContestSubmission.contest_problem, ContestSubmission.status)
                .where(ContestSubmission.contest == contest_id, owner, ContestSubmission.contest_eligible == True)
                .order_by(ContestSubmission.received_at.desc(), ContestSubmission.id.desc()))
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
            return {'error': '服务暂时不可用'}, 503


@api.route('/problems/<int:problem_id>')
@api.param('problem_id', '比赛题目ID')
class ContestProblemByIdPublicController(Resource):
    def get(self, problem_id: int):
        """废弃无比赛上下文的题目读取接口，避免绕过时间与报名校验。"""
        return {'error': '请通过比赛题目地址访问'}, 410
