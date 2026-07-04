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
    'permission': fields.String(default='member', description='访问权限'),
    'is_published': fields.Boolean(default=True, description='是否发布'),
    'published_at': fields.String(description='发布时间'),
    'created_at': fields.String(description='创建时间'),
    'updated_at': fields.String(description='更新时间'),
})

announcement_input = api.model('AnnouncementInput', {
    'title': fields.String(required=True, description='公告标题'),
    'content': fields.String(required=True, description='Markdown 内容'),
    'permission': fields.String(default='member', description='访问权限'),
    'is_published': fields.Boolean(default=True, description='是否发布'),
})


def _require_manager() -> (dict | tuple):
    """验证请求携带的 JWT 令牌，确保用户角色为 manager（副部长/部长/社长/管理员等）"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return {'error': '请先登录'}, 401

    jwt_service = inject(IJWTService)
    user_info = jwt_service.verify_access_token(auth_header[7:])
    if not user_info:
        return {'error': '令牌无效或已过期'}, 401

    if user_info.get('role', 'member') != 'manager':
        return {'error': '权限不足，仅副部长/部长/社长/管理员可执行此操作'}, 403

    return user_info


@api.route('/')
class AnnouncementListController(Resource):
    @api.doc('list_announcements')
    @api.response(200, 'Success', [announcement_model])
    def get(self):
        announcements = Announcement.select().order_by(Announcement.created_at.desc())
        return [a.to_dict() for a in announcements], 200

    @api.expect(announcement_input)
    @api.doc('create_announcement')
    @api.response(201, 'Created', announcement_model)
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    def post(self):
        result = _require_manager()
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
        result = _require_manager()
        if isinstance(result, tuple):
            return result

        try:
            announcement = Announcement.get_by_id(announcement_id)
        except Announcement.DoesNotExist:
            return {'error': '公告不存在'}, 404

        data = request.get_json(silent=True) or {}
        if 'title' in data:
            announcement.title = data['title'].strip()
        if 'content' in data:
            announcement.content = data['content'].strip()
        if 'permission' in data:
            announcement.permission = data['permission']
        if 'is_published' in data:
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
        result = _require_manager()
        if isinstance(result, tuple):
            return result

        try:
            announcement = Announcement.get_by_id(announcement_id)
            announcement.delete_instance()
            return {'success': True}, 200
        except Announcement.DoesNotExist:
            return {'error': '公告不存在'}, 404
