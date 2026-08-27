"""
管理后台 API 控制器模块

提供管理后台所需的实时数据接口：
- 仪表盘统计（用户/提交/公告计数与最近列表）
- 用户管理（分页列表、搜索筛选、启用/停用、删除）

数据来源：
- PostgreSQL（users / announcements 表）
- Redis（submission:id_counter 累计提交计数）
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from peewee import fn

from core.di_container import inject
from controllers.announcement_controller import _require_editor
from interfaces.service_interfaces import IJWTService, IRedisService
from models.db_models import (
    Announcement, Submission, User, UserCode, Favorite, ContestParticipant,
    ContestSubmission,
    Discussion, DiscussionReply, DiscussionLike, DiscussionReplyLike,
    LearnFavorite, LearnBrowsingHistory,
)

api = Namespace('admin', description='管理后台接口')

error_model = api.model('AdminStatsError', {
    'error': fields.String(description='错误信息'),
})

user_status_input = api.model('AdminUserStatusInput', {
    'is_active': fields.Boolean(required=True, description='是否启用（true=活跃 / false=停用）'),
})

# 最近列表的返回条数
RECENT_LIMIT = 5

# 允许筛选的角色
USER_ROLES = ('member', 'staff', 'manager')


def _require_manager() -> (dict | tuple):
    """验证 JWT 并确保用户角色为 manager（用户写操作仅限管理员）"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return {'error': '请先登录'}, 401

    jwt_service = inject(IJWTService)
    user_info = jwt_service.verify_access_token(auth_header[7:])
    if not user_info:
        return {'error': '令牌无效或已过期'}, 401

    try:
        user = User.get_by_id(int(user_info.get('id', 0)))
        if user:
            user_info['role'] = user.role
    except Exception:
        pass

    if user_info.get('role', 'member') != 'manager':
        return {'error': '权限不足，仅管理员可执行此操作'}, 403

    return user_info


def _user_dict(user: User) -> dict:
    """将用户 ORM 实例转换为安全的字典（不含密码哈希）"""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'provider': user.provider,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
    }


@api.route('/stats')
class AdminStatsController(Resource):
    @api.doc('get_admin_stats')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    def get(self):
        """获取管理后台仪表盘统计数据（需 manager/staff 权限）"""
        result = _require_editor()
        if isinstance(result, tuple):
            return result

        total_users = User.select().count()
        active_users = User.select().where(User.is_active == True).count()
        total_announcements = Announcement.select().count()

        recent_users = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
            }
            for user in (
                User.select().order_by(User.created_at.desc()).limit(RECENT_LIMIT)
            )
        ]

        recent_announcements = [
            {
                'id': announcement.id,
                'title': announcement.title,
                'is_published': announcement.is_published,
                'created_at': announcement.created_at.isoformat() if announcement.created_at else None,
            }
            for announcement in (
                Announcement.select().order_by(Announcement.created_at.desc()).limit(RECENT_LIMIT)
            )
        ]

        # 累计提交次数来自 Redis 原子计数器（每次提交判题自增一次）
        total_submissions = 0
        try:
            redis_service = inject(IRedisService)
            total_submissions = redis_service.get_int('submission:id_counter', 0)
        except Exception:
            total_submissions = 0

        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_submissions': total_submissions,
            'total_announcements': total_announcements,
            'recent_users': recent_users,
            'recent_announcements': recent_announcements,
        }, 200


@api.route('/users')
class AdminUserListController(Resource):
    @api.doc('list_admin_users')
    @api.param('page', '页码（默认 1）')
    @api.param('per_page', '每页数量（默认 10，最大 100）')
    @api.param('search', '搜索关键词（匹配用户名或邮箱）')
    @api.param('role', '角色筛选（member/staff/manager）')
    @api.param('status', '状态筛选（active/inactive）')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    def get(self):
        """分页获取用户列表（需 manager/staff 权限）"""
        result = _require_editor()
        if isinstance(result, tuple):
            return result

        try:
            page = max(int(request.args.get('page', 1)), 1)
            per_page = min(max(int(request.args.get('per_page', 10)), 1), 100)
        except (TypeError, ValueError):
            page, per_page = 1, 10

        search = (request.args.get('search') or '').strip()
        role = (request.args.get('role') or '').strip()
        status = (request.args.get('status') or '').strip()

        query = User.select()
        if search:
            keyword = search.lower()
            query = query.where(
                (fn.LOWER(User.username).contains(keyword))
                | (fn.LOWER(User.email).contains(keyword))
            )
        if role in USER_ROLES:
            query = query.where(User.role == role)
        if status in ('active', 'inactive'):
            query = query.where(User.is_active == (status == 'active'))

        total = query.count()
        users = query.order_by(User.created_at.desc()).paginate(page, per_page)

        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'data': [_user_dict(user) for user in users],
        }, 200


@api.route('/users/<int:user_id>/status')
@api.param('user_id', '用户ID')
class AdminUserStatusController(Resource):
    @api.doc('update_admin_user_status')
    @api.expect(user_status_input)
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    def patch(self, user_id: int):
        """启用/停用指定用户（仅 manager）"""
        result = _require_manager()
        if isinstance(result, tuple):
            return result

        data = request.get_json(silent=True) or {}
        is_active = data.get('is_active')
        if not isinstance(is_active, bool):
            return {'error': 'is_active 必须为布尔值'}, 400

        updated = (
            User.update(is_active=is_active, updated_at=fn.NOW())
            .where(User.id == user_id)
            .execute()
        )
        if not updated:
            return {'error': '用户不存在'}, 404

        return {'success': True, 'id': user_id, 'is_active': is_active}, 200


@api.route('/users/<int:user_id>')
@api.param('user_id', '用户ID')
class AdminUserDetailController(Resource):
    @api.doc('delete_admin_user')
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    def delete(self, user_id: int):
        """删除指定用户及其关联数据（仅 manager）"""
        result = _require_manager()
        if isinstance(result, tuple):
            return result

        # 禁止删除当前登录账号
        if str(user_id) == str(result.get('id', '')):
            return {'error': '不能删除当前登录账号'}, 400

        try:
            user = User.get_by_id(user_id)
        except User.DoesNotExist:
            return {'error': '用户不存在'}, 404

        try:
            # 清理所有引用该用户的关联数据，避免外键约束冲突
            # 1) 讨论区：先删点赞/回复，再删讨论本身
            user_reply_ids = [
                r.id for r in DiscussionReply.select(DiscussionReply.id).where(
                    DiscussionReply.author == user
                )
            ]
            if user_reply_ids:
                DiscussionReplyLike.delete().where(
                    DiscussionReplyLike.reply.in_(user_reply_ids)
                ).execute()
                DiscussionReply.delete().where(
                    DiscussionReply.id.in_(user_reply_ids)
                ).execute()
            user_disc_ids = [
                d.id for d in Discussion.select(Discussion.id).where(
                    Discussion.author == user
                )
            ]
            if user_disc_ids:
                disc_reply_ids = [
                    r.id for r in DiscussionReply.select(DiscussionReply.id).where(
                        DiscussionReply.discussion.in_(user_disc_ids)
                    )
                ]
                if disc_reply_ids:
                    DiscussionReplyLike.delete().where(
                        DiscussionReplyLike.reply.in_(disc_reply_ids)
                    ).execute()
                    DiscussionReply.delete().where(
                        DiscussionReply.id.in_(disc_reply_ids)
                    ).execute()
                DiscussionLike.delete().where(
                    DiscussionLike.discussion.in_(user_disc_ids)
                ).execute()
                Discussion.delete().where(Discussion.id.in_(user_disc_ids)).execute()
            DiscussionLike.delete().where(DiscussionLike.user == user).execute()
            DiscussionReplyLike.delete().where(DiscussionReplyLike.user == user).execute()

            # 2) 题目收藏、比赛参与、学习数据
            Favorite.delete().where(Favorite.user == user).execute()
            ContestParticipant.delete().where(ContestParticipant.user == user).execute()
            LearnFavorite.delete().where(LearnFavorite.user == user).execute()
            LearnBrowsingHistory.delete().where(
                LearnBrowsingHistory.user == user
            ).execute()

            # 3) 用户代码、提交记录解除关联
            UserCode.delete().where(UserCode.user == user).execute()
            # 比赛提交记录（user 外键非空，无法置空，必须随用户删除）
            ContestSubmission.delete().where(ContestSubmission.user == user).execute()
            Submission.update(user=None).where(Submission.user == user).execute()

            user.delete_instance()
            return {'success': True, 'id': user_id}, 200
        except Exception as exc:
            return {'error': f'删除用户失败: {exc}'}, 500
