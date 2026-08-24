"""
题目收藏 API 控制器模块

提供当前登录用户的题目收藏功能：
- 收藏列表（附带题库元信息：标题、难度、标签）
- 收藏 / 取消收藏
- 收藏状态查询（题目详情页星标按钮使用）
"""

from flask import g
from flask_restx import Namespace, Resource, fields

from middleware.auth_middleware import AuthMiddleware
from models.db_models import Favorite

api = Namespace('favorites', description='题目收藏接口')

error_model = api.model('FavoriteError', {
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


def _problem_summary(problem_id):
    """从内存题库获取题目摘要信息"""
    from pages.problem_data import PROBLEMS
    pdata = PROBLEMS.get(problem_id)
    if not pdata:
        return None
    return {
        'problem_id': problem_id,
        'problem_title': pdata.get('title', f'题目 {problem_id}'),
        'difficulty': pdata.get('difficulty', '简单'),
        'tags': pdata.get('tags', []),
    }


@api.route('')
class FavoriteListController(Resource):
    @api.doc('list_favorites')
    @AuthMiddleware.require_auth
    def get(self):
        """获取当前用户的收藏题目列表（按收藏时间倒序）"""
        user_id = _current_user_id()
        favorites = (
            Favorite.select()
            .where(Favorite.user == user_id)
            .order_by(Favorite.id.desc())
        )

        data = []
        for fav in favorites:
            summary = _problem_summary(fav.problem_id)
            if not summary:
                # 题目已从题库移除，展示占位信息
                summary = {
                    'problem_id': fav.problem_id,
                    'problem_title': f'题目 {fav.problem_id}（已下架）',
                    'difficulty': None,
                    'tags': [],
                }
            summary['favorited_at'] = fav.created_at.isoformat() if fav.created_at else None
            data.append(summary)

        return {'data': data, 'total': len(data)}, 200


@api.route('/<int:problem_id>')
@api.param('problem_id', '题目ID')
class FavoriteToggleController(Resource):
    @api.doc('add_favorite')
    @api.response(201, 'Created')
    @api.response(400, 'Bad Request', error_model)
    @AuthMiddleware.require_auth
    def post(self, problem_id: int):
        """收藏指定题目（重复收藏幂等处理）"""
        user_id = _current_user_id()

        summary = _problem_summary(problem_id)
        if not summary:
            return {'error': '题目不存在'}, 404

        exists = (
            Favorite.select()
            .where((Favorite.user == user_id) & (Favorite.problem_id == problem_id))
            .exists()
        )
        if not exists:
            try:
                Favorite.create(user=user_id, problem_id=problem_id)
                return {'success': True, 'favorited': True}, 201
            except Exception as e:
                return {'error': f'收藏失败: {e}'}, 500

        return {'success': True, 'favorited': True, 'message': '已收藏过'}, 200

    @api.doc('remove_favorite')
    @api.response(200, 'Success')
    @AuthMiddleware.require_auth
    def delete(self, problem_id: int):
        """取消收藏指定题目"""
        user_id = _current_user_id()

        deleted = (
            Favorite.delete()
            .where((Favorite.user == user_id) & (Favorite.problem_id == problem_id))
            .execute()
        )

        return {'success': True, 'favorited': False, 'removed': deleted > 0}, 200


@api.route('/<int:problem_id>/status')
@api.param('problem_id', '题目ID')
class FavoriteStatusController(Resource):
    @api.doc('get_favorite_status')
    @AuthMiddleware.require_auth
    def get(self, problem_id: int):
        """查询当前用户是否收藏了指定题目"""
        user_id = _current_user_id()

        favorited = (
            Favorite.select()
            .where((Favorite.user == user_id) & (Favorite.problem_id == problem_id))
            .exists()
        )

        return {'favorited': favorited}, 200
