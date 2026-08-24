"""
学习资源收藏 API 控制器模块

提供当前登录用户的学习资源收藏功能：
- 收藏列表
- 收藏 / 取消收藏
- 收藏状态查询
"""

from flask import g
from flask_restx import Namespace, Resource, fields

from middleware.auth_middleware import AuthMiddleware
from models.db_models import LearnFavorite

api = Namespace('learn-favorites', description='学习资源收藏接口')

error_model = api.model('LearnFavoriteError', {
    'error': fields.String(description='错误信息'),
})


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
class LearnFavoriteListController(Resource):
    @api.doc('list_learn_favorites')
    @AuthMiddleware.require_auth
    def get(self):
        """获取当前用户的学习资源收藏列表（按收藏时间倒序）"""
        user_id = _current_user_id()
        favorites = (
            LearnFavorite.select()
            .where(LearnFavorite.user == user_id)
            .order_by(LearnFavorite.id.desc())
        )

        data = []
        for fav in favorites:
            data.append({
                'resource_id': fav.resource_id,
                'favorited_at': fav.created_at.isoformat() if fav.created_at else None,
            })

        return {'data': data, 'total': len(data)}, 200


@api.route('/<string:resource_id>')
@api.param('resource_id', '资源ID')
class LearnFavoriteToggleController(Resource):
    @api.doc('add_learn_favorite')
    @api.response(201, 'Created')
    @api.response(400, 'Bad Request', error_model)
    @AuthMiddleware.require_auth
    def post(self, resource_id: str):
        """收藏指定学习资源（重复收藏幂等处理）"""
        user_id = _current_user_id()

        exists = (
            LearnFavorite.select()
            .where((LearnFavorite.user == user_id) & (LearnFavorite.resource_id == resource_id))
            .exists()
        )
        if not exists:
            try:
                LearnFavorite.create(user=user_id, resource_id=resource_id)
                return {'success': True, 'favorited': True}, 201
            except Exception as e:
                return {'error': f'收藏失败: {e}'}, 500

        return {'success': True, 'favorited': True, 'message': '已收藏过'}, 200

    @api.doc('remove_learn_favorite')
    @api.response(200, 'Success')
    @AuthMiddleware.require_auth
    def delete(self, resource_id: str):
        """取消收藏指定学习资源"""
        user_id = _current_user_id()

        deleted = (
            LearnFavorite.delete()
            .where((LearnFavorite.user == user_id) & (LearnFavorite.resource_id == resource_id))
            .execute()
        )

        return {'success': True, 'favorited': False, 'removed': deleted > 0}, 200


@api.route('/<string:resource_id>/status')
@api.param('resource_id', '资源ID')
class LearnFavoriteStatusController(Resource):
    @api.doc('get_learn_favorite_status')
    @AuthMiddleware.require_auth
    def get(self, resource_id: str):
        """查询当前用户是否收藏了指定学习资源"""
        user_id = _current_user_id()

        favorited = (
            LearnFavorite.select()
            .where((LearnFavorite.user == user_id) & (LearnFavorite.resource_id == resource_id))
            .exists()
        )

        return {'favorited': favorited}, 200
