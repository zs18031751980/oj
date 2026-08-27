from datetime import datetime

from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import (
    Contest, ContestProblem, ContestSubmission, User, get_database,
)

api = Namespace('contest_rankings', description='比赛实时排行榜接口')

contest_problem_result = api.model('ContestProblemResult', {
    'problem_index': fields.String(description='题目编号(A/B/C...)'),
    'solved': fields.Boolean(description='是否通过(ACM:全过; OI:得分>0)'),
    'passed': fields.Integer(description='通过用例数'),
    'total': fields.Integer(description='用例总数'),
    'score': fields.Integer(description='本题得分(OI)'),
    'status': fields.String(description='本题最终状态'),
    'submissions': fields.Integer(description='本题提交次数'),
    'solve_minutes': fields.Integer(description='通过该题距比赛开始的分钟数(ACM)'),
})

contest_ranking_model = api.model('ContestRanking', {
    'rank': fields.Integer(description='排名'),
    'user_id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'avatar_url': fields.String(description='头像'),
    'solved_count': fields.Integer(description='通过题目数(ACM)'),
    'penalty': fields.Integer(description='罚时(分钟, ACM)'),
    'score': fields.Integer(description='总得分(OI)'),
    'problems': fields.List(fields.Nested(contest_problem_result), description='各题结果'),
})

contest_rankings_response = api.model('ContestRankingsResponse', {
    'mode': fields.String(description='排行模式(ACM/OI)'),
    'contest_type': fields.String(description='比赛类型'),
    'problem_indexes': fields.List(fields.String, description='题目编号顺序'),
    'rankings': fields.List(fields.Nested(contest_ranking_model)),
})


def _as_datetime(v):
    """将可能为字符串/ datetime 的值统一解析为 datetime；无法解析返回 None。"""
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        except Exception:
            return None
    return None


def _wall_delta_minutes(a, b):
    """计算两个时间点的墙钟时间差（分钟），与服务器时区无关。

    数据库存储约定：start_time 与 submitted_at 均经 psycopg 的
    session timezone(Asia/Shanghai) 以「墙钟」形式落地为 naive 值，因此两者
    处于同一墙钟坐标系。直接按 naive 相减即可得到正确的「距比赛开始的时长」，
    避免 aware/naive 混用或 .timestamp() 带来的时区偏移。
    """
    a = _as_datetime(a)
    b = _as_datetime(b)
    if a is None or b is None:
        return 0
    if a.tzinfo is not None:
        a = a.replace(tzinfo=None)
    if b.tzinfo is not None:
        b = b.replace(tzinfo=None)
    try:
        return int((a - b).total_seconds() / 60)
    except Exception:
        return 0


def _compute_rankings(contest_id: int):
    """根据比赛模式计算实时排行榜"""
    try:
        contest = Contest.get_by_id(contest_id)
    except Contest.DoesNotExist:
        return None

    mode = 'OI' if 'oi' in (contest.contest_type or '').lower() else 'ACM'
    # ACM 模式罚时：每道已解题的罚时 = 该题首次 AC 用时(分钟) + 此前失败次数 * 罚时(分钟)
    penalty_minutes = int(getattr(contest, 'penalty_time', 20) or 20)

    # 题目顺序（用于列展示）
    problems = list(
        ContestProblem.select()
        .where(ContestProblem.contest_id == contest_id)
        .order_by(ContestProblem.sort_order, ContestProblem.problem_index)
    )
    problem_indexes = [p.problem_index for p in problems]

    # 比赛开始时间（用于计算每题通过时刻距开始的时间段）
    contest_start = contest.start_time

    # 拉取全部提交记录
    rows = list(
        ContestSubmission.select()
        .where(ContestSubmission.contest_id == contest_id)
        .order_by(ContestSubmission.submitted_at)
    )

    # 按 (user_id, problem_index) 聚合
    user_stats: dict[int, dict] = {}
    for sub in rows:
        uid = sub.user.id if hasattr(sub.user, 'id') else sub.user
        if uid not in user_stats:
            user_stats[uid] = {
                'problems': {},  # index -> {best_score, ac(bool), ac_time, attempts, passed, total, status}
                'penalty': 0,
                'solved': 0,
                'score': 0,
            }
        pidx = sub.problem_index or ''
        st = user_stats[uid]['problems'].setdefault(pidx, {
            'best_score': 0,
            'ac': False,
            'ac_time': None,
            'attempts': 0,
            'passed': 0,
            'total': sub.total,
            'status': sub.status,
            'solve_minutes': 0,
        })
        st['attempts'] += 1
        st['total'] = sub.total
        st['status'] = sub.status
        st['passed'] = max(st['passed'], sub.passed)

        is_ac = sub.status == 'AC'
        sub_score = sub.score or 0

        if mode == 'ACM':
            if is_ac and not st['ac']:
                st['ac'] = True
                st['ac_time'] = sub.submitted_at
                # 首次 AC 距比赛开始的分钟数（时间段）
                failed_before = st['attempts'] - 1  # 本次之前的提交均为未通过
                ac_minutes = _wall_delta_minutes(sub.submitted_at, contest_start)
                st['solve_minutes'] = max(ac_minutes, 0)
                # 本题贡献 = 通过用时 + 未通过次数 * 罚时
                st['penalty_contrib'] = st['solve_minutes'] + failed_before * penalty_minutes
        else:
            # OI: 取最高分
            if sub_score > st['best_score']:
                st['best_score'] = sub_score
            if st['best_score'] > 0:
                st['ac'] = True

    # 汇总
    results = []
    for uid, st in user_stats.items():
        try:
            user = User.get_by_id(uid)
            username = user.username or '匿名'
            avatar_url = user.avatar_url or ''
        except Exception:
            username = '匿名'
            avatar_url = ''

        penalty = 0
        solved = 0
        score = 0
        problem_results = []
        for pidx in problem_indexes:
            p = st['problems'].get(pidx)
            if p is None:
                problem_results.append({
                    'problem_index': pidx,
                    'solved': False,
                    'passed': 0,
                    'total': 0,
                    'score': 0,
                    'status': '—',
                    'submissions': 0,
                    'solve_minutes': None,
                })
                continue
            if mode == 'ACM':
                if p['ac']:
                    solved += 1
                    penalty += p.get('penalty_contrib', 0)
                problem_results.append({
                    'problem_index': pidx,
                    'solved': p['ac'],
                    'passed': p['passed'],
                    'total': p['total'],
                    'score': 0,
                    'status': 'AC' if p['ac'] else p['status'],
                    'submissions': p['attempts'],
                    'solve_minutes': p.get('solve_minutes', 0) if p['ac'] else None,
                })
            else:
                score += p['best_score']
                problem_results.append({
                    'problem_index': pidx,
                    'solved': p['best_score'] > 0,
                    'passed': p['passed'],
                    'total': p['total'],
                    'score': p['best_score'],
                    'status': p['status'],
                    'submissions': p['attempts'],
                })

        results.append({
            'user_id': uid,
            'username': username,
            'avatar_url': avatar_url,
            'solved_count': solved,
            'penalty': penalty,
            'score': score,
            'problems': problem_results,
        })

    if mode == 'ACM':
        results.sort(key=lambda x: (-x['solved_count'], x['penalty']))
    else:
        results.sort(key=lambda x: -x['score'])

    for i, r in enumerate(results, 1):
        r['rank'] = i

    return {
        'mode': mode,
        'contest_type': contest.contest_type,
        'problem_indexes': problem_indexes,
        'rankings': results,
    }


@api.route('/<int:contest_id>/rankings')
@api.param('contest_id', '比赛ID')
class ContestRankingsController(Resource):
    @api.doc('get_contest_rankings')
    @api.marshal_with(contest_rankings_response)
    def get(self, contest_id: int):
        """获取比赛实时排行榜（按比赛模式 ACM/OI 计算排名）"""
        data = _compute_rankings(contest_id)
        if data is None:
            return {'error': '比赛不存在'}, 404
        return data, 200
