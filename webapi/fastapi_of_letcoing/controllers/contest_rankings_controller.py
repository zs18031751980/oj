import json
from datetime import datetime, timedelta, timezone

from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import (
    Contest, ContestParticipant, ContestProblem, ContestScoreboardSnapshot,
    ContestSubmission, User, get_database,
)
from controllers.contest_controller import _contest_is_frozen, _get_current_user
from services.contest_lifecycle import can_view_rankings
from services.contest_scoring import compute_acm_scoreboard

api = Namespace('contest_rankings', description='比赛实时排行榜接口')
_CST = timezone(timedelta(hours=8))

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
        a = a.astimezone(_CST).replace(tzinfo=None)
    if b.tzinfo is not None:
        b = b.astimezone(_CST).replace(tzinfo=None)
    try:
        return int((a - b).total_seconds() / 60)
    except Exception:
        return 0


def _compute_rankings(contest_id: int, cutoff_at=None):
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

    # ACM 走独立领域服务，保证 CE、首次 AC 和最后 AC tie-break 的规则与
    # 复判/增量榜单消费者复用同一实现。
    if mode == 'ACM':
        entries = []
        for participant in ContestParticipant.select().where(
            ContestParticipant.contest_id == contest_id
        ):
            try:
                user = User.get_by_id(participant.user_id)
                username = user.username or '匿名'
                avatar_url = user.avatar_url or ''
            except Exception:
                username = '匿名'
                avatar_url = ''
            entries.append({
                'entry_id': participant.user_id,
                'user_id': participant.user_id,
                'username': username,
                'avatar_url': avatar_url,
            })

        submissions = [
            {
                'id': submission.id,
                'entry_id': submission.user_id,
                'problem_index': submission.problem_index or '',
                'status': submission.status,
                'verdict': submission.verdict or submission.status,
                'received_at': submission.received_at or submission.submitted_at,
            }
            for submission in ContestSubmission.select().where(
                ContestSubmission.contest_id == contest_id,
                ContestSubmission.contest_eligible == True,
            )
        ]
        scored_rows = compute_acm_scoreboard(
            entries=entries,
            problem_indexes=problem_indexes,
            submissions=submissions,
            start_at=contest_start,
            penalty_minutes=penalty_minutes,
            cutoff_at=cutoff_at,
        )
        rankings = []
        for row in scored_rows:
            problem_results = []
            for problem_index in problem_indexes:
                problem = row['problems'][problem_index]
                problem_results.append({
                    'problem_index': problem_index,
                    'solved': problem['solved'],
                    'passed': 0,
                    'total': 0,
                    'score': 0,
                    'status': 'AC' if problem['solved'] else problem['status'],
                    'submissions': problem['submissions'],
                    'solve_minutes': problem['solve_minutes'],
                })
            rankings.append({
                'rank': row['rank'],
                'user_id': row['user_id'],
                'username': row['username'],
                'avatar_url': row['avatar_url'],
                'solved_count': row['solved_count'],
                'penalty': row['penalty'],
                'score': 0,
                'problems': problem_results,
            })
        return {
            'mode': mode,
            'contest_type': contest.contest_type,
            'problem_indexes': problem_indexes,
            'rankings': rankings,
        }

    # 拉取全部提交记录
    rows = list(
        ContestSubmission.select()
        .where(ContestSubmission.contest_id == contest_id)
        .order_by(ContestSubmission.submitted_at)
    )
    if cutoff_at is not None:
        rows = [row for row in rows if (row.received_at or row.submitted_at) <= cutoff_at]

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

    results.sort(key=lambda x: -x['score'])

    # 同分（OI）或同解题数且同罚时（ACM）使用并列名次，不能因 Worker 并发
    # 完成顺序不同而影响名次。
    previous_key = None
    current_rank = 0
    for position, r in enumerate(results, 1):
        ranking_key = (-r['score'],)
        if ranking_key != previous_key:
            current_rank = position
            previous_key = ranking_key
        r['rank'] = current_rank

    return {
        'mode': mode,
        'contest_type': contest.contest_type,
        'problem_indexes': problem_indexes,
        'rankings': results,
    }


def _save_public_snapshot(contest: Contest, data: dict) -> None:
    """比赛未封榜时覆盖保存公开榜；封榜后此快照成为唯一公开数据源。"""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    # PostgreSQL UPSERT 消除首次并发读榜时 get_or_create 的唯一索引竞争。
    (ContestScoreboardSnapshot.insert(
        contest=contest,
        snapshot_kind='PUBLIC_FREEZE',
        payload=payload,
        scoreboard_version=1,
    ).on_conflict(
        conflict_target=(
            ContestScoreboardSnapshot.contest,
            ContestScoreboardSnapshot.snapshot_kind,
        ),
        update={
            ContestScoreboardSnapshot.payload: payload,
            ContestScoreboardSnapshot.scoreboard_version:
                ContestScoreboardSnapshot.scoreboard_version + 1,
        },
    ).execute())


def _save_live_projection(contest: Contest, data: dict) -> None:
    """由判题完成事件推进的实时榜单投影，读榜不再全表聚合。"""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    (ContestScoreboardSnapshot.insert(
        contest=contest,
        snapshot_kind='LIVE',
        payload=payload,
        scoreboard_version=1,
    ).on_conflict(
        conflict_target=(
            ContestScoreboardSnapshot.contest,
            ContestScoreboardSnapshot.snapshot_kind,
        ),
        update={
            ContestScoreboardSnapshot.payload: payload,
            ContestScoreboardSnapshot.scoreboard_version:
                ContestScoreboardSnapshot.scoreboard_version + 1,
        },
    ).execute())


def refresh_live_projection(contest_id: int) -> None:
    """判题完成后的唯一榜单刷新入口；异常不得影响提交事实的持久化。"""
    try:
        contest = Contest.get_by_id(contest_id)
        if contest.lifecycle_state in {'CANCELLED', 'FINALIZED'}:
            return
        data = _compute_rankings(contest_id)
        if data is not None:
            _save_live_projection(contest, data)
    except Exception:
        # 投影是可从提交事实重建的读模型，失败留待下一次完成事件或读榜重建。
        return


def _load_public_snapshot(contest: Contest) -> dict | None:
    snapshot = ContestScoreboardSnapshot.select().where(
        ContestScoreboardSnapshot.contest == contest,
        ContestScoreboardSnapshot.snapshot_kind == 'PUBLIC_FREEZE',
    ).first()
    if not snapshot:
        return None


def _save_final_snapshot(contest: Contest, data: dict) -> dict:
    """最终榜只首次写入，之后永远从该不可变版本读取。"""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    (ContestScoreboardSnapshot.insert(
        contest=contest,
        snapshot_kind='FINAL',
        payload=payload,
        scoreboard_version=1,
    ).on_conflict_ignore().execute())
    snapshot = ContestScoreboardSnapshot.select().where(
        ContestScoreboardSnapshot.contest == contest,
        ContestScoreboardSnapshot.snapshot_kind == 'FINAL',
    ).get()
    return json.loads(snapshot.payload)
    try:
        return json.loads(snapshot.payload)
    except (TypeError, ValueError):
        return None


@api.route('/<int:contest_id>/rankings')
@api.param('contest_id', '比赛ID')
class ContestRankingsController(Resource):
    @api.doc('get_contest_rankings')
    @api.marshal_with(contest_rankings_response)
    def get(self, contest_id: int):
        """获取比赛实时排行榜（按比赛模式 ACM/OI 计算排名）"""
        try:
            contest = Contest.get_by_id(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        user = _get_current_user()
        is_manager = bool(user and user.role == 'manager')
        if not can_view_rankings(
            contest.lifecycle_state, is_public=contest.is_public, is_manager=is_manager,
        ):
            return {'error': '比赛不存在'}, 404
        if contest.lifecycle_state == 'FINALIZED':
            snapshot = ContestScoreboardSnapshot.select().where(
                ContestScoreboardSnapshot.contest == contest,
                ContestScoreboardSnapshot.snapshot_kind == 'FINAL',
            ).first()
            if snapshot:
                return json.loads(snapshot.payload), 200
        if _contest_is_frozen(contest) and not is_manager:
            snapshot = _load_public_snapshot(contest)
            if snapshot is not None:
                return snapshot, 200
            data = _compute_rankings(contest_id, cutoff_at=contest.freeze_time)
            _save_public_snapshot(contest, data)
            return data, 200
        live_snapshot = ContestScoreboardSnapshot.select().where(
            ContestScoreboardSnapshot.contest == contest,
            ContestScoreboardSnapshot.snapshot_kind == 'LIVE',
        ).first()
        data = json.loads(live_snapshot.payload) if live_snapshot else _compute_rankings(contest_id)
        if data is None:
            return {'error': '比赛不存在'}, 404
        if live_snapshot is None:
            _save_live_projection(contest, data)
        if not _contest_is_frozen(contest):
            _save_public_snapshot(contest, data)
        return data, 200


@api.route('/<int:contest_id>/finalize')
@api.param('contest_id', '比赛ID')
class ContestRankingsFinalizeController(Resource):
    def post(self, contest_id: int):
        """管理员在比赛结束、积压判题处理完后发布不可变最终榜。"""
        user = _get_current_user()
        if not user or user.role != 'manager':
            return {'error': '仅管理员可结算比赛'}, 403
        try:
            contest = Contest.get_by_id(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404
        if contest.lifecycle_state == 'CANCELLED':
            return {'error': '已取消比赛不能结算'}, 409
        now = datetime.now(timezone.utc)
        end_time = contest.end_time
        if end_time is not None:
            end_time = end_time.replace(tzinfo=_CST) if end_time.tzinfo is None else end_time.astimezone(_CST)
            if now < end_time:
                return {'error': '比赛尚未结束，不能结算'}, 409
        unresolved = ContestSubmission.select().where(
            ContestSubmission.contest == contest,
            ContestSubmission.status.in_(('Queued', 'Claimed', 'Compiling', 'Compiled', 'Checking', 'Running')),
        ).exists()
        if unresolved:
            return {'error': '仍有判题任务未完成，不能结算'}, 409
        data = _compute_rankings(contest_id)
        final = _save_final_snapshot(contest, data)
        contest.lifecycle_state = 'FINALIZED'
        contest.finalized_at = datetime.now(_CST).replace(tzinfo=None)
        contest.save()
        return final, 200
