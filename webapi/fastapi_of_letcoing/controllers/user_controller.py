"""
用户资料 API 控制器模块

提供当前登录用户的资料管理接口，包括：
- 获取当前用户资料 (GET /users/me)
- 更新当前用户资料 (PATCH /users/me)
- 上传/更新头像 (POST /users/me/avatar)
"""

import os
import uuid
from datetime import datetime

from flask import request
from flask_restx import Namespace, Resource, fields

from core.di_container import inject
from interfaces.service_interfaces import IJWTService
from models.db_models import User


# ============================================================
# 1. API 命名空间与请求/响应模型定义
# ============================================================

api = Namespace('users', description='用户资料管理接口')

# ---------- 请求模型 ----------

# 更新用户资料请求模型
profile_update_model = api.model('ProfileUpdate', {
    'name': fields.String(description='显示名称'),
    'email': fields.String(description='邮箱'),
    'bio': fields.String(description='个人简介'),
})

# ---------- 响应模型 ----------

user_info_model = api.model('UserInfo', {
    'id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'email': fields.String(description='邮箱'),
    'name': fields.String(description='显示名称'),
    'avatar_url': fields.String(description='头像URL'),
    'bio': fields.String(description='个人简介'),
    'role': fields.String(description='用户角色'),
    'is_active': fields.Boolean(description='是否激活'),
    'created_at': fields.String(description='注册时间'),
})


# ============================================================
# 2. 辅助函数
# ============================================================

def _get_current_user():
    """从 JWT 获取当前登录用户，未登录返回 None"""
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


def _user_to_dict(user: User) -> dict:
    """将 User 模型转换为前端可用的字典格式"""
    data = {
        'id': str(user.id),
        'username': user.username or '',
        'email': user.email or '',
        'name': getattr(user, 'name', None) or user.username or '',
        'avatar_url': user.avatar_url or '',
        'bio': getattr(user, 'bio', '') or '',
        'provider': user.provider or '',
        'role': user.role or 'member',
        'is_active': user.is_active,
        'theme_preference': user.theme_preference or 'system',
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
    }
    return data


# ============================================================
# 3. API 端点
# ============================================================

@api.route('/me')
class UserProfileController(Resource):
    """当前用户资料管理"""

    @api.doc('get_profile')
    @api.response(200, 'Success', user_info_model)
    @api.response(401, 'Unauthorized')
    def get(self):
        """获取当前登录用户的资料"""
        user = _get_current_user()
        if not user:
            return {'error': '未登录或令牌无效'}, 401
        return _user_to_dict(user), 200

    @api.doc('update_profile')
    @api.expect(profile_update_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    def patch(self):
        """更新当前登录用户的资料（昵称、邮箱、个人简介）"""
        user = _get_current_user()
        if not user:
            return {'error': '未登录或令牌无效'}, 401

        data = request.get_json(silent=True) or {}

        # 更新 name 字段（映射到 User.name 或 username）
        if 'name' in data:
            new_name = (data['name'] or '').strip()
            if hasattr(user, 'name'):
                user.name = new_name
            elif new_name:
                # 如果 User 模型没有 name 字段，更新 username
                user.username = new_name

        # 更新 email
        if 'email' in data:
            new_email = (data['email'] or '').strip()
            if new_email:
                # 检查邮箱是否已被其他用户使用
                existing = User.select().where(
                    (User.email == new_email) & (User.id != user.id)
                ).first()
                if existing:
                    return {'error': '该邮箱已被其他用户使用'}, 400
                user.email = new_email

        # 更新 bio（如果 User 模型有该字段）
        if 'bio' in data and hasattr(user, 'bio'):
            user.bio = data['bio']

        user.save()

        # 刷新 JWT 中的用户信息
        try:
            jwt_service = inject(IJWTService)
            user_info = jwt_service.verify_access_token(
                request.headers.get('Authorization', '')[7:]
            )
            if user_info:
                user_info['username'] = user.username
                user_info['email'] = user.email
                jwt_service.refresh_cached_user(str(user.id), user_info)
        except Exception:
            pass

        return {'success': True, 'user_info': _user_to_dict(user)}, 200


# 头像文件保存目录（相对于项目根目录）
_AVATAR_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'avatars')


@api.route('/me/avatar')
class UserAvatarController(Resource):
    """头像上传"""

    @api.doc('upload_avatar')
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request')
    @api.response(401, 'Unauthorized')
    def post(self):
        """上传或更新当前用户的头像图片"""
        user = _get_current_user()
        if not user:
            return {'error': '未登录或令牌无效'}, 401

        if 'avatar' not in request.files:
            return {'error': '未找到上传文件'}, 400

        file = request.files['avatar']
        if not file.filename:
            return {'error': '文件名为空'}, 400

        # 验证文件类型
        allowed_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        if file.content_type not in allowed_types:
            return {'error': '仅支持 JPG/PNG/GIF/WebP 格式'}, 400

        # 验证文件大小（2MB）
        file_data = file.read()
        if len(file_data) > 2 * 1024 * 1024:
            return {'error': '图片大小不能超过 2MB'}, 400

        # 生成唯一文件名
        ext = os.path.splitext(file.filename)[1].lower() or '.png'
        filename = f"{uuid.uuid4().hex}{ext}"

        # 确保目录存在
        os.makedirs(_AVATAR_DIR, exist_ok=True)

        # 保存文件
        filepath = os.path.join(_AVATAR_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(file_data)

        # 构建访问 URL
        avatar_url = f"/uploads/avatars/{filename}"

        # 更新用户头像
        user.avatar_url = avatar_url
        user.save()

        # 刷新 JWT 中的用户信息
        try:
            jwt_service = inject(IJWTService)
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                user_info = jwt_service.verify_access_token(auth_header[7:])
                if user_info:
                    user_info['avatar_url'] = avatar_url
                    jwt_service.refresh_cached_user(str(user.id), user_info)
        except Exception:
            pass

        return {'success': True, 'avatar_url': avatar_url}, 200
