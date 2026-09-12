from flask import request, g
from flask_restx import Namespace, Resource, fields
from models.db_models import Submission, User, Problem, get_database

api = Namespace('rankings', description='排行榜接口')

ranking_model = api.model('Ranking', {
    'rank': fields.Integer(description='排名'),
    'user_id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'avatar_url': fields.String(description='头像'),
    'solved_count': fields.Integer(description='解题数'),
    'rating': fields.Integer(description='积分'),
    'easy_count': fields.Integer(description='简单题数'),
    'medium_count': fields.Integer(description='中等题数'),
    'hard_count': fields.Integer(description='困难题数'),
})

from services.ranking_projection import ranking_page


@api.route('/')
class RankingsListController(Resource):
    def get(self):
        try:
            offset = max(0, int(request.args.get('offset', 0)))
            limit = min(1000, max(1, int(request.args.get('limit', 1000))))
        except ValueError:
            return {'error': '分页参数无效'}, 400
        return ranking_page(limit, offset), 200


@api.route('/user/<int:user_id>')
class UserRankingController(Resource):
    def get(self, user_id):
        user = User.get_or_none(User.id == user_id)
        if not user:
            return {'error': '用户不存在'}, 404
        rows = ranking_page(1, 0, user_id)
        return (rows[0] if rows else {'user_id': user.id, 'username': user.username,
            'avatar_url': user.avatar_url or '', 'rank': None, 'solved_count': 0,
            'rating': 0, 'easy_count': 0, 'medium_count': 0, 'hard_count': 0}), 200
