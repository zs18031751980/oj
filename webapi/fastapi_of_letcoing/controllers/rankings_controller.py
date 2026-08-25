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

DIFFICULTY_SCORES = {
    '简单': 10,
    '中等': 20,
    '困难': 30,
}


def _get_user_stats():
    db = get_database()
    rows = db.execute_sql("""
        SELECT
            u.id AS user_id,
            COALESCE(u.username, '匿名') AS username,
            COALESCE(u.avatar_url, '') AS avatar_url,
            p.difficulty,
            COUNT(DISTINCT s.problem_id) AS cnt
        FROM submissions s
        JOIN users u ON s.user_id = u.id
        JOIN problems p ON s.problem_id = p.id
        WHERE s.status = 'AC'
        GROUP BY u.id, u.username, u.avatar_url, p.difficulty
    """).fetchall()

    user_stats: dict[int, dict] = {}
    for row in rows:
        uid, username, avatar_url, diff, cnt = row
        if uid not in user_stats:
            user_stats[uid] = {
                'user_id': uid,
                'username': username,
                'avatar_url': avatar_url,
                'solved_count': 0,
                'rating': 0,
                'easy_count': 0,
                'medium_count': 0,
                'hard_count': 0,
            }
        diff = diff or '简单'
        user_stats[uid]['solved_count'] += cnt
        user_stats[uid]['rating'] += DIFFICULTY_SCORES.get(diff, 10) * cnt
        if diff == '简单':
            user_stats[uid]['easy_count'] += cnt
        elif diff == '中等':
            user_stats[uid]['medium_count'] += cnt
        elif diff == '困难':
            user_stats[uid]['hard_count'] += cnt

    results = list(user_stats.values())
    results.sort(key=lambda x: x['rating'], reverse=True)

    for i, r in enumerate(results):
        r['rank'] = i + 1

    return results


@api.route('/')
class RankingsListController(Resource):
    @api.doc('get_rankings')
    def get(self):
        """获取排行榜（按积分降序）"""
        rankings = _get_user_stats()
        return rankings, 200


@api.route('/user/<int:user_id>')
class UserRankingController(Resource):
    def get(self, user_id):
        """获取用户排名详情"""
        try:
            user = User.get_by_id(user_id)
        except User.DoesNotExist:
            return {'error': '用户不存在'}, 404

        db = get_database()
        rows = db.execute_sql("""
            SELECT p.difficulty, COUNT(DISTINCT s.problem_id) AS cnt
            FROM submissions s
            JOIN problems p ON s.problem_id = p.id
            WHERE s.user_id = %s AND s.status = 'AC'
            GROUP BY p.difficulty
        """, (user_id,)).fetchall()

        solved_count = 0
        rating = 0
        easy_count = 0
        medium_count = 0
        hard_count = 0
        for diff, cnt in rows:
            diff = diff or '简单'
            solved_count += cnt
            rating += DIFFICULTY_SCORES.get(diff, 10) * cnt
            if diff == '简单':
                easy_count += cnt
            elif diff == '中等':
                medium_count += cnt
            elif diff == '困难':
                hard_count += cnt

        all_rankings = _get_user_stats()
        rank = next((r['rank'] for r in all_rankings if r['user_id'] == user.id), None)

        return {
            'user_id': user.id,
            'username': user.username or '匿名',
            'avatar_url': user.avatar_url or '',
            'solved_count': solved_count,
            'rating': rating,
            'rank': rank,
            'easy_count': easy_count,
            'medium_count': medium_count,
            'hard_count': hard_count,
        }, 200
