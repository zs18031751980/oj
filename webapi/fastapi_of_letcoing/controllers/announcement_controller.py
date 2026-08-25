from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import Announcement
from core.di_container import inject
from interfaces.service_interfaces import IJWTService

api = Namespace('announcement', description='公告管理接口')

announcement_model = api.model('Announcement', {
    'id': fields.Integer(description='公告ID'),
    'title': fields.String(required=True, description='公告标题'),
    'content': fields.String(required=True, description='Markdown 内容'),
    'category': fields.String(default='系统公告', description='分类(系统公告/比赛公告/更新公告/活动通知)'),
    'permission': fields.String(default='member', description='访问权限'),
    'is_published': fields.Boolean(default=True, description='是否发布'),
    'published_at': fields.String(description='发布时间'),
    'created_at': fields.String(description='创建时间'),
    'updated_at': fields.String(description='更新时间'),
})

announcement_input = api.model('AnnouncementInput', {
    'title': fields.String(required=True, description='公告标题'),
    'content': fields.String(required=True, description='Markdown 内容'),
    'category': fields.String(default='系统公告', description='分类(系统公告/比赛公告/更新公告/活动通知)'),
    'permission': fields.String(default='member', description='访问权限'),
    'is_published': fields.Boolean(default=True, description='是否发布'),
})


# 允许编辑/管理公告的角色集合（仅 manager）
ANNOUNCEMENT_EDITOR_ROLES = {'manager'}


def _require_editor() -> (dict | tuple):
    """验证请求携带的 JWT 令牌，确保用户具有公告编辑权限（仅 manager）"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return {'error': '请先登录'}, 401

    jwt_service = inject(IJWTService)
    user_info = jwt_service.verify_access_token(auth_header[7:])
    if not user_info:
        return {'error': '令牌无效或已过期'}, 401

    # 从数据库获取最新角色，避免 Redis 缓存/Token 载荷中的过期数据
    try:
        from models.db_models import User
        user = User.get_by_id(int(user_info.get('id', 0)))
        if user:
            user_info['role'] = user.role
            jwt_service.refresh_cached_user(str(user.id), user_info)
    except Exception:
        pass

    if user_info.get('role', 'member') not in ANNOUNCEMENT_EDITOR_ROLES:
        return {'error': '权限不足，仅管理员可管理公告'}, 403

    return user_info


@api.route('/')
class AnnouncementListController(Resource):
    @api.doc('list_announcements')
    @api.response(200, 'Success', [announcement_model])
    def get(self):
        include_unpublished = (
            request.args.get('include_unpublished', '').strip().lower() == 'true'
        )
        if include_unpublished:
            result = _require_editor()
            if isinstance(result, tuple):
                return result
            query = Announcement.select()
        else:
            query = Announcement.select().where(Announcement.is_published == True)

        announcements = query.order_by(
            Announcement.published_at.desc(),
            Announcement.created_at.desc(),
        )
        return [a.to_dict() for a in announcements], 200

    @api.expect(announcement_input)
    @api.doc('create_announcement')
    @api.response(201, 'Created', announcement_model)
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    def post(self):
        result = _require_editor()
        if isinstance(result, tuple):
            return result

        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        if not title or not content:
            return {'error': '标题和内容不能为空'}, 400

        now = datetime.now()
        announcement = Announcement.create(
            title=title,
            content=content,
            category=data.get('category', '系统公告'),
            permission=data.get('permission', 'member'),
            is_published=data.get('is_published', True),
            created_by=result.get('id'),
            published_at=now if data.get('is_published', True) else None,
        )
        return announcement.to_dict(), 201


@api.route('/<int:announcement_id>')
class AnnouncementDetailController(Resource):
    @api.doc('get_announcement')
    @api.response(200, 'Success', announcement_model)
    @api.response(404, 'Not Found')
    def get(self, announcement_id: int):
        try:
            announcement = Announcement.get_by_id(announcement_id)
            if not announcement.is_published:
                result = _require_editor()
                if isinstance(result, tuple):
                    return {'error': '公告不存在'}, 404
            return announcement.to_dict(), 200
        except Announcement.DoesNotExist:
            return {'error': '公告不存在'}, 404

    @api.expect(announcement_input)
    @api.doc('update_announcement')
    @api.response(200, 'Success', announcement_model)
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    def put(self, announcement_id: int):
        result = _require_editor()
        if isinstance(result, tuple):
            return result

        try:
            announcement = Announcement.get_by_id(announcement_id)
        except Announcement.DoesNotExist:
            return {'error': '公告不存在'}, 404

        data = request.get_json(silent=True) or {}
        if 'title' in data:
            title = str(data['title'] or '').strip()
            if not title:
                return {'error': '标题不能为空'}, 400
            announcement.title = title
        if 'content' in data:
            content = str(data['content'] or '').strip()
            if not content:
                return {'error': '内容不能为空'}, 400
            announcement.content = content
        if 'permission' in data:
            announcement.permission = data['permission']
        if 'category' in data:
            announcement.category = data['category']
        if 'is_published' in data:
            if not isinstance(data['is_published'], bool):
                return {'error': 'is_published 必须是布尔值'}, 400
            announcement.is_published = data['is_published']
            if data['is_published'] and not announcement.published_at:
                announcement.published_at = datetime.now()

        announcement.save()
        return announcement.to_dict(), 200

    @api.doc('delete_announcement')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    def delete(self, announcement_id: int):
        result = _require_editor()
        if isinstance(result, tuple):
            return result

        try:
            announcement = Announcement.get_by_id(announcement_id)
            announcement.delete_instance()
            return {'success': True}, 200
        except Announcement.DoesNotExist:
            return {'error': '公告不存在'}, 404
