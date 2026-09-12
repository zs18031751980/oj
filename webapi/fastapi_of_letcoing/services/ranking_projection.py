"""普通排行榜的持久化投影；只有 Worker 聚合，API 只执行索引分页查询。"""
from datetime import timedelta
from werkzeug.exceptions import ServiceUnavailable
from models.db_models import User, UserJudgeStats, RankingProjectionState, get_database
from services.jwt_service import utcnow


def refresh_rankings():
    db = get_database()
    state = RankingProjectionState.get_or_none(RankingProjectionState.id == 1)
    if state and state.built_at and state.built_at > utcnow() - timedelta(seconds=30):
        return
    if not state:
        RankingProjectionState.insert(id=1).on_conflict_ignore().execute()
    with db.atomic():
        query = RankingProjectionState.select().where(RankingProjectionState.id == 1)
        if db.__class__.__name__ != 'SqliteDatabase':
            query = query.for_update('FOR UPDATE SKIP LOCKED')
        state = query.first()
        if not state or (state.built_at and state.built_at > utcnow() - timedelta(seconds=30)):
            return
        # 全量聚合限制在独立消费者；原子替换让并发读始终看到一个完整版本。
        UserJudgeStats.delete().execute()
        db.execute_sql("""
            INSERT INTO user_judge_stats
                (user_id, rank, solved_count, rating, easy_count, medium_count, hard_count, created_at, updated_at)
            WITH solved AS (
                SELECT DISTINCT s.user_id, s.problem_id, COALESCE(p.difficulty, '简单') AS difficulty
                FROM submissions s JOIN problems p ON p.id=s.problem_id WHERE s.status='AC'
            ), stats AS (
                SELECT user_id, COUNT(*) AS solved_count,
                    SUM(CASE difficulty WHEN '困难' THEN 30 WHEN '中等' THEN 20 ELSE 10 END) AS rating,
                    SUM(CASE WHEN difficulty='简单' THEN 1 ELSE 0 END) AS easy_count,
                    SUM(CASE WHEN difficulty='中等' THEN 1 ELSE 0 END) AS medium_count,
                    SUM(CASE WHEN difficulty='困难' THEN 1 ELSE 0 END) AS hard_count
                FROM solved GROUP BY user_id
            ) SELECT user_id, ROW_NUMBER() OVER (ORDER BY rating DESC, user_id),
                solved_count, rating, easy_count, medium_count, hard_count, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM stats
        """)
        state.built_at = utcnow()
        state.save(only=[RankingProjectionState.built_at])


def ranking_page(limit=30, offset=0, user_id=None):
    state = RankingProjectionState.get_or_none(RankingProjectionState.id == 1)
    if not state or not state.built_at:
        raise ServiceUnavailable('排行榜正在初始化，请稍后重试')
    query = UserJudgeStats.select(UserJudgeStats, User).join(User)
    if user_id is not None:
        query = query.where(UserJudgeStats.user == user_id)
    rows = query.order_by(UserJudgeStats.rank).limit(limit).offset(offset)
    return [{'user_id': row.user_id, 'username': row.user.username or '匿名',
             'avatar_url': row.user.avatar_url or '', 'rank': row.rank,
             'solved_count': row.solved_count, 'rating': row.rating,
             'easy_count': row.easy_count, 'medium_count': row.medium_count,
             'hard_count': row.hard_count} for row in rows]
