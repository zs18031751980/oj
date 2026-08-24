from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import Submission, User, Problem
from peewee import fn, SQL

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

# 积分规则：简单10分，中等20分，困难30分
DIFFICULTY_SCORES = {
    '简单': 10,
    '中等': 20,
    '困难': 30,
}


def _get_user_stats():
    """计算所有用户的解题统计，按难度积分"""
    # 获取每个用户 AC 的题目及其难度
    ac_query = (
        Submission.select(
            Submission.user,
            Problem.difficulty,
            fn.COUNT(fn.DISTINCT(Submission.problem)).alias('count'),
        )
        .join(Problem, on=(Submission.problem == Problem.id))
        .where(Submission.status == 'AC')
        .group_by(Submission.user, Problem.difficulty)
    )

    # 按用户聚合
    user_stats: dict[int, dict] = {}
    for row in ac_query:
        uid = row.user.id if row.user else None
        if uid is None:
            continue
        if uid not in user_stats:
            user_stats[uid] = {
                'user_id': uid,
                'username': row.user.username or '匿名',
                'avatar_url': row.user.avatar_url or '',
                'solved_count': 0,
                'rating': 0,
                'easy_count': 0,
                'medium_count': 0,
                'hard_count': 0,
            }
        diff = row.difficulty or '简单'
        cnt = row.count
        user_stats[uid]['solved_count'] += cnt
        score = DIFFICULTY_SCORES.get(diff, 10) * cnt
        user_stats[uid]['rating'] += score
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

        # 该用户 AC 的题目按难度统计
        ac_query = (
            Submission.select(
                Problem.difficulty,
                fn.COUNT(fn.DISTINCT(Submission.problem)).alias('count'),
            )
            .join(Problem, on=(Submission.problem == Problem.id))
            .where(Submission.user == user, Submission.status == 'AC')
            .group_by(Problem.difficulty)
        )

        solved_count = 0
        rating = 0
        easy_count = 0
        medium_count = 0
        hard_count = 0
        for row in ac_query:
            diff = row.difficulty or '简单'
            cnt = row.count
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
