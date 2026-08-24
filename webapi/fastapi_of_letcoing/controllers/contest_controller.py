from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import Contest, ContestParticipant, User
from core.di_container import inject
from interfaces.service_interfaces import IJWTService

api = Namespace('contests', description='比赛管理接口')

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
    'title': fields.String(required=True, description='比赛标题'),
    'description': fields.String(description='比赛描述'),
    'contest_type': fields.String(default='ACM', description='比赛类型'),
    'start_time': fields.String(description='开始时间'),
    'end_time': fields.String(description='结束时间'),
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
    data['participants_count'] = ContestParticipant.select().where(
        ContestParticipant.contest == contest
    ).count()
    return data


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
        if user.role not in ('manager', 'staff'):
            return {'error': '权限不足'}, 403

        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        if not title:
            return {'error': '标题不能为空'}, 400

        start_time = None
        end_time = None
        if data.get('start_time'):
            try:
                start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            except Exception:
                pass
        if data.get('end_time'):
            try:
                end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            except Exception:
                pass

        # 自动推断状态
        now = datetime.now()
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
            description=data.get('description', ''),
            contest_type=data.get('contest_type', 'ACM'),
            status=status,
            start_time=start_time,
            end_time=end_time,
            created_by=user.id,
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
        if user.role not in ('manager', 'staff'):
            return {'error': '权限不足'}, 403

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
            contest.contest_type = data['contest_type']
        if 'status' in data:
            contest.status = data['status']
        if 'start_time' in data and data['start_time']:
            try:
                contest.start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            except Exception:
                pass
        if 'end_time' in data and data['end_time']:
            try:
                contest.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            except Exception:
                pass
        contest.save()
        return _contest_to_dict(contest), 200

    def delete(self, contest_id):
        """删除比赛"""
        user = _get_current_user()
        if not user:
            return {'error': '请先登录'}, 401
        if user.role not in ('manager', 'staff'):
            return {'error': '权限不足'}, 403

        try:
            contest = Contest.get_by_id(contest_id)
            contest.delete_instance()
            return {'success': True}, 200
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404


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

        if contest.status == 'past':
            return {'error': '比赛已结束'}, 400

        exists = ContestParticipant.select().where(
            ContestParticipant.contest == contest,
            ContestParticipant.user == user,
        ).exists()
        if exists:
            return {'error': '已参加该比赛'}, 400

        ContestParticipant.create(
            contest=contest,
            user=user,
        )
        return {'success': True, 'message': '已参加比赛'}, 201
