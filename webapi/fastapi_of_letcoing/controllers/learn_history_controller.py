"""
学习资源浏览记录 API 控制器模块

提供当前登录用户的学习资源浏览记录功能：
- 记录浏览行为（幂等：同一资源短时间内只保留最新一条）
- 获取最近浏览的资源列表（默认 10 条）
"""

from flask import g
from flask_restx import Namespace, Resource, fields

from middleware.auth_middleware import AuthMiddleware
from models.db_models import LearnBrowsingHistory

api = Namespace('learn-history', description='学习资源浏览记录接口')


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
class LearnHistoryController(Resource):
    @api.doc('list_learn_history')
    @AuthMiddleware.require_auth
    def get(self):
        """获取当前用户最近浏览的学习资源（默认 10 条，按浏览时间倒序）"""
        user_id = _current_user_id()
        limit = 10

        records = (
            LearnBrowsingHistory.select()
            .where(LearnBrowsingHistory.user == user_id)
            .order_by(LearnBrowsingHistory.browsed_at.desc())
            .limit(limit)
        )

        data = []
        seen = set()
        for record in records:
            if record.resource_id in seen:
                continue
            seen.add(record.resource_id)
            data.append({
                'resource_id': record.resource_id,
                'browsed_at': record.browsed_at.isoformat() if record.browsed_at else None,
            })

        return {'data': data, 'total': len(data)}, 200

    @api.doc('record_learn_history')
    @AuthMiddleware.require_auth
    def post(self):
        """记录当前用户浏览了某个学习资源"""
        user_id = _current_user_id()

        payload = api.payload or {}
        resource_id = payload.get('resource_id', '').strip()
        if not resource_id:
            return {'error': 'resource_id 不能为空'}, 400

        try:
            # 先删除该用户对该资源的旧记录，再插入新记录（保证时间最新）
            (
                LearnBrowsingHistory.delete()
                .where(
                    (LearnBrowsingHistory.user == user_id)
                    & (LearnBrowsingHistory.resource_id == resource_id)
                )
                .execute()
            )
            LearnBrowsingHistory.create(user=user_id, resource_id=resource_id)
            return {'success': True}, 201
        except Exception as e:
            return {'error': f'记录浏览失败: {e}'}, 500
