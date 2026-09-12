"""
数据库 ORM 模型模块

使用 Peewee ORM 定义数据库表结构与操作方法。
当前仅包含 User（用户）模型，支持第三方登录用户和本地用户的持久化。

数据库连接管理：
- 支持通过 ConfigService 动态读取数据库配置
- 使用连接池（PooledPostgresqlExtDatabase）提高性能
- 提供数据库表创建、删除、连接和关闭等管理方法
"""

from datetime import datetime
from typing import Optional

from peewee import (
    Model, CharField, TextField, DateTimeField, BooleanField,
    IntegerField, BigIntegerField, ForeignKeyField, AutoField, Database, DatabaseProxy
)
from playhouse.pool import PooledPostgresqlExtDatabase

from core.db_config import DatabaseConfig
from core.db_robust import ensure_connected, sanitize_db_error, DatabaseUnavailableError


# ============================================================
# 1. 数据库连接管理
# ============================================================

# DatabaseProxy 用作模型的占位符，不依赖实际的数据库连接
# 这样在模块导入时不会创建连接，避免 DI 容器未就绪时 fallback 到 localhost
database_proxy = DatabaseProxy()

# 实际的数据库连接实例（惰性初始化）
_actual_db: Optional[PooledPostgresqlExtDatabase] = None


def _create_actual_db() -> PooledPostgresqlExtDatabase:
    from core.di_container import get_container
    from interfaces.service_interfaces import IConfigService
    service = get_container().resolve(IConfigService)
    config = service.get_database_config()
    statement_timeout = max(1000, int(service.get_config('DB_STATEMENT_TIMEOUT_MS', 15000)))
    return PooledPostgresqlExtDatabase(
        config['database'], user=config['username'], password=config['password'],
        host=config['host'], port=int(config['port']),
        max_connections=int(config['max_connections']), stale_timeout=int(config['stale_timeout']),
        timeout=int(config.get('pool_timeout', 5)), connect_timeout=5,
        sslmode=config.get('sslmode', 'prefer'),
        options=f'-c timezone=Asia/Shanghai -c statement_timeout={statement_timeout} -c lock_timeout=5000 -c idle_in_transaction_session_timeout=30000')


def init_database():
    """
    初始化数据库连接并将实际连接绑定到 DatabaseProxy

    应在 DI 容器配置完成后（setup_services 之后）调用，
    确保能通过 ConfigService 获取正确的数据库配置。
    """
    global _actual_db
    _actual_db = _create_actual_db()
    database_proxy.initialize(_actual_db)


def get_database() -> PooledPostgresqlExtDatabase:
    """
    获取实际 PostgreSQL 数据库连接池实例

    用于 create_tables()、migrate_add_role_column() 等需要
    直接操作数据库连接的管理函数。
    """
    global _actual_db
    if _actual_db is None:
        init_database()
    return _actual_db


# ============================================================
# 2. 基础模型与用户模型
# ============================================================

class BaseModel(Model):
    """
    基础 ORM 模型类

    所有数据库模型的基类，提供：
    - 自动记录创建时间（created_at）和更新时间（updated_at）
    - save() 时自动更新 updated_at 字段
    - to_dict() 方法将模型实例转换为字典
    """

    created_at = DateTimeField(default=datetime.now, verbose_name="创建时间")
    updated_at = DateTimeField(default=datetime.now, verbose_name="更新时间")

    class Meta:
        database = database_proxy

    def save(self, force_insert=False, only=None):
        """重写 save 方法，在保存时自动更新 updated_at 字段"""
        self.updated_at = datetime.now()
        return super().save(force_insert, only)

    def to_dict(self) -> dict:
        """
        将模型实例转换为字典

        datetime 类型的字段会自动转换为 ISO 格式字符串。
        ForeignKey 字段自动提取关联对象的 id，避免序列化失败。
        """
        data = {}
        for field_name in self._meta.fields.keys():
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Model):
                value = getattr(value, 'id', None)
            data[field_name] = value
        return data


class User(BaseModel):
    """
    用户 ORM 模型

    存储用户的核心信息，支持：
    - 第三方登录用户（通过 provider + provider_id 关联）
    - 本地密码登录用户（通过 password_hash 验证）
    - 用户激活/停用状态管理
    - 角色权限管理（member / staff / manager）
    """

    id = AutoField(primary_key=True, verbose_name="用户ID")
    username = CharField(max_length=50, unique=True, null=True, verbose_name="用户名")
    name = CharField(max_length=100, null=True, verbose_name="显示名称")
    email = CharField(max_length=100, unique=True, null=True, verbose_name="邮箱")
    password_hash = CharField(max_length=255, null=True, verbose_name="密码哈希")
    is_active = BooleanField(default=True, verbose_name="是否激活")
    role = CharField(max_length=20, default="member", verbose_name="生效角色")
    provider_role = CharField(max_length=20, null=True, verbose_name="提供商角色")
    local_role = CharField(max_length=20, null=True, verbose_name="显式本地角色覆盖")
    last_login = DateTimeField(null=True, verbose_name="最后登录时间")
    provider = CharField(max_length=50, null=True, verbose_name="登录提供商")
    provider_id = CharField(max_length=255, null=True, verbose_name="提供商用户ID")
    avatar_url = CharField(max_length=500, null=True, verbose_name="头像URL")
    bio = CharField(max_length=500, null=True, verbose_name="个人简介")
    theme_preference = CharField(max_length=10, null=True, default="system", verbose_name="主题偏好")

    class Meta:
        table_name = "users"  # 数据库表名

    def to_dict(self) -> dict:
        """
        转换为字典并排除敏感信息（如密码哈希）

        Returns:
            不包含 password_hash 字段的用户信息字典
        """
        data = super().to_dict()
        data.pop("password_hash", None)
        data.pop("provider_role", None)
        data.pop("local_role", None)
        return data



class AuthSession(BaseModel):
    """可撤销会话；只存刷新令牌摘要，所有时间均为 UTC。"""
    id = CharField(primary_key=True, max_length=64)
    user = ForeignKeyField(User, backref='auth_sessions', on_delete='CASCADE')
    refresh_hash = CharField(max_length=64)
    previous_refresh_hash = CharField(max_length=64, null=True)
    refresh_request_id = CharField(max_length=128, null=True)
    refresh_retry_ciphertext = TextField(null=True)
    refresh_retry_until = DateTimeField(null=True)
    expires_at = DateTimeField()
    revoked = BooleanField(default=False)

    class Meta:
        table_name = 'auth_sessions'


class UserJudgeStats(BaseModel):
    user = ForeignKeyField(User, primary_key=True, on_delete='CASCADE')
    rank = IntegerField(index=True)
    solved_count = IntegerField(default=0)
    rating = IntegerField(default=0)
    easy_count = IntegerField(default=0)
    medium_count = IntegerField(default=0)
    hard_count = IntegerField(default=0)

    class Meta:
        table_name = 'user_judge_stats'


class RankingProjectionState(BaseModel):
    id = IntegerField(primary_key=True, default=1)
    built_at = DateTimeField(null=True)

    class Meta:
        table_name = 'ranking_projection_state'


class OAuthGrant(BaseModel):
    id = CharField(primary_key=True, max_length=64)
    user = ForeignKeyField(User, on_delete='CASCADE')
    binding_hash = CharField(max_length=64)
    expires_at = DateTimeField()

    class Meta:
        table_name = 'oauth_grants'

# ============================================================
# 3. 题目、测试用例、提交记录模型
# ============================================================

class Problem(BaseModel):
    """题目 ORM 模型"""
    id = AutoField(primary_key=True, verbose_name="题目ID")
    title = CharField(max_length=200, verbose_name="题目标题")
    description = TextField(verbose_name="题目描述")
    input_desc = TextField(default="", verbose_name="输入格式描述")
    output_desc = TextField(default="", verbose_name="输出格式描述")
    difficulty = CharField(max_length=20, default="简单", verbose_name="难度")
    time_limit = IntegerField(default=1000, verbose_name="时间限制(ms)")
    memory_limit = IntegerField(default=256, verbose_name="内存限制(MB)")
    created_by = IntegerField(null=True, verbose_name="创建者用户ID")
    is_public = BooleanField(default=True, verbose_name="是否公开")

    class Meta:
        table_name = "problems"


class Testcase(BaseModel):
    """测试用例 ORM 模型"""
    id = AutoField(primary_key=True)
    problem = ForeignKeyField(Problem, backref="testcases", verbose_name="所属题目")
    input_data = TextField(verbose_name="输入数据")
    output_data = TextField(verbose_name="期望输出")
    is_sample = BooleanField(default=False, verbose_name="是否为样例")
    sort_order = IntegerField(default=0, verbose_name="排序序号")

    class Meta:
        table_name = "testcases"


class UserCode(BaseModel):
    """用户代码存储模型（每个用户每题每语言最多存一份，最多5题）"""
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref="user_codes", verbose_name="用户")
    problem_id = IntegerField(verbose_name="题目ID")
    language = CharField(max_length=50, verbose_name="编程语言")
    code = TextField(verbose_name="用户代码")

    class Meta:
        table_name = "user_codes"
        indexes = (
            (('user', 'problem_id', 'language'), True),
        )

    def to_dict(self) -> dict:
        data = super().to_dict()
        if 'user' in data and not isinstance(data['user'], (int, str)):
            data['user'] = getattr(data['user'], 'id', None)
        return data


class Submission(BaseModel):
    """提交记录 ORM 模型"""
    PENDING = "Pending"
    RUNNING = "Running"
    AC = "AC"
    WA = "WA"
    TLE = "TLE"
    RE = "RE"
    CE = "CE"

    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref="submissions", null=True, verbose_name="提交用户")
    problem = ForeignKeyField(Problem, backref="submissions", verbose_name="所属题目")
    code = TextField(verbose_name="提交代码")
    language = CharField(max_length=50, verbose_name="编程语言")
    status = CharField(max_length=20, default=PENDING, verbose_name="判题状态")
    time_used = IntegerField(null=True, verbose_name="运行时间(ms)")
    memory_used = IntegerField(null=True, verbose_name="内存消耗(KB)")
    testcase_results = TextField(null=True, verbose_name="各测试点结果(JSON)")
    fail_testcase_index = IntegerField(null=True, verbose_name="首个失败测试点索引")

    job_id = CharField(max_length=64, null=True, unique=True)
    attempt_id = IntegerField(default=0)
    idempotency_key = CharField(max_length=128, null=True)

    class Meta:
        table_name = "submissions"

    def to_dict(self) -> dict:
        data = super().to_dict()
        if isinstance(data.get("testcase_results"), str):
            try:
                import json
                data["testcase_results"] = json.loads(data["testcase_results"])
            except Exception:
                pass
        related_fields = {'user', 'problem'}
        for fk in related_fields:
            val = data.get(fk)
            if val is not None and not isinstance(val, (int, str)):
                data[fk] = getattr(val, 'id', None)
        return data



class Announcement(BaseModel):
    """公告 ORM 模型
    存储公告的标题、内容、权限等信息，支持发布和管理
    """
    id = AutoField(primary_key=True, verbose_name="公告ID")
    title = CharField(max_length=200, verbose_name="公告标题")
    content = TextField(verbose_name="Markdown 内容")
    category = CharField(max_length=50, default="系统公告", verbose_name="分类(系统公告/比赛公告/更新公告/活动通知)")
    permission = CharField(max_length=20, default="member", verbose_name="访问权限")
    created_by = CharField(max_length=50, null=True, verbose_name="创建者ID")
    is_published = BooleanField(default=True, verbose_name="是否发布")
    published_at = DateTimeField(null=True, verbose_name="发布时间")

    class Meta:
        table_name = "announcements"

    def to_dict(self) -> dict:
        data = super().to_dict()
        related_fields = {'created_by'}
        for fk in related_fields:
            val = data.get(fk)
            if val is not None and not isinstance(val, (int, str)):
                data[fk] = getattr(val, 'id', None)
        return data

class Favorite(BaseModel):
    """题目收藏模型（每个用户每道题最多收藏一次）"""
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref="favorites", verbose_name="用户")
    problem_id = IntegerField(verbose_name="题目ID")

    class Meta:
        table_name = "favorites"
        indexes = (
            (('user', 'problem_id'), True),
        )


class Contest(BaseModel):
    """比赛 ORM 模型"""
    id = AutoField(primary_key=True, verbose_name="比赛ID")
    title = CharField(max_length=200, verbose_name="比赛标题")
    description = TextField(default="", verbose_name="比赛描述")
    contest_type = CharField(max_length=50, default="ACM", verbose_name="比赛类型(ACM/周赛/决赛)")
    status = CharField(max_length=20, default="upcoming", verbose_name="状态(upcoming/ongoing/past)")
    start_time = DateTimeField(null=True, verbose_name="开始时间")
    end_time = DateTimeField(null=True, verbose_name="结束时间")
    created_by = IntegerField(null=True, verbose_name="创建者ID")
    is_public = BooleanField(default=True, verbose_name="是否公开")
    penalty_time = IntegerField(default=20, verbose_name="罚时(分钟, ACM 模式)")
    lifecycle_state = CharField(max_length=20, default="DRAFT", verbose_name="生命周期状态")
    freeze_time = DateTimeField(null=True, verbose_name="封榜时间")
    published_at = DateTimeField(null=True, verbose_name="发布时间")
    finalized_at = DateTimeField(null=True, verbose_name="最终榜发布时间")
    thawed_at = DateTimeField(null=True)
    final_revision = IntegerField(default=0)
    rules_version = CharField(default='acm-2026-v1')
    allowed_languages = TextField(default='["cpp","python","java","go","javascript"]')
    active_submission_limit = IntegerField(default=3)

    scoreboard_requested_version = IntegerField(default=0)

    class Meta:
        table_name = "contests"


class ContestRole(BaseModel):
    contest = ForeignKeyField(Contest)
    user = ForeignKeyField(User)
    role = CharField()
    class Meta:
        indexes = ((('contest', 'user'), True),)


class ContestTeam(BaseModel):
    contest = ForeignKeyField(Contest)
    captain = ForeignKeyField(User)
    name = CharField(max_length=120)
    class Meta:
        indexes = ((('contest', 'captain'), True), (('contest', 'name'), True))


class ContestTeamMember(BaseModel):
    contest = ForeignKeyField(Contest)
    team = ForeignKeyField(ContestTeam)
    user = ForeignKeyField(User)
    class Meta:
        indexes = ((('contest', 'user'), True),)


class ContestParticipant(BaseModel):
    """比赛参与记录"""
    id = AutoField(primary_key=True)
    contest = ForeignKeyField(Contest, backref="participants", verbose_name="所属比赛")
    user = ForeignKeyField(User, backref="contest_participations", verbose_name="参与用户")
    score = IntegerField(default=0, verbose_name="得分")
    rank = IntegerField(null=True, verbose_name="排名")

    class Meta:
        table_name = "contest_participants"
        indexes = (
            (('contest', 'user'), True),
        )


class Discussion(BaseModel):
    """讨论区 ORM 模型"""
    id = AutoField(primary_key=True, verbose_name="讨论ID")
    title = CharField(max_length=200, verbose_name="讨论标题")
    content = TextField(verbose_name="讨论内容(Markdown)")
    author = ForeignKeyField(User, backref="discussions", verbose_name="作者")
    category = CharField(max_length=50, default="全部", verbose_name="分类(全部/问答/分享/闲聊)")
    tags = CharField(max_length=500, null=True, verbose_name="标签(逗号分隔)")
    reply_count = IntegerField(default=0, verbose_name="回复数")
    like_count = IntegerField(default=0, verbose_name="点赞数")
    view_count = IntegerField(default=0, verbose_name="浏览数")
    is_pinned = BooleanField(default=False, verbose_name="是否置顶")
    is_closed = BooleanField(default=False, verbose_name="是否关闭")

    class Meta:
        table_name = "discussions"


class DiscussionLike(BaseModel):
    """讨论点赞记录"""
    id = AutoField(primary_key=True)
    discussion = ForeignKeyField(Discussion, backref="likes", verbose_name="所属讨论")
    user = ForeignKeyField(User, backref="discussion_likes", verbose_name="点赞用户")

    class Meta:
        table_name = "discussion_likes"
        indexes = (
            (('discussion', 'user'), True),
        )


class DiscussionReply(BaseModel):
    """讨论回复"""
    id = AutoField(primary_key=True)
    discussion = ForeignKeyField(Discussion, backref="replies", verbose_name="所属讨论")
    author = ForeignKeyField(User, backref="discussion_replies", verbose_name="回复者")
    content = TextField(verbose_name="回复内容(Markdown)")
    like_count = IntegerField(default=0, verbose_name="点赞数")

    class Meta:
        table_name = "discussion_replies"


class DiscussionReplyLike(BaseModel):
    """讨论回复点赞记录"""
    id = AutoField(primary_key=True)
    reply = ForeignKeyField(DiscussionReply, backref="likes", verbose_name="所属回复")
    user = ForeignKeyField(User, backref="reply_likes", verbose_name="点赞用户")

    class Meta:
        table_name = "discussion_reply_likes"
        indexes = (
            (('reply', 'user'), True),
        )


class ContestProblem(BaseModel):
    """比赛题目"""
    id = AutoField(primary_key=True, verbose_name="比赛题目ID")
    contest = ForeignKeyField(Contest, backref="contest_problems", verbose_name="所属比赛")
    problem_index = CharField(max_length=10, verbose_name="题目编号(A/B/C...)")
    title = CharField(max_length=200, verbose_name="题目标题")
    description = TextField(verbose_name="题目描述(Markdown)")
    input_desc = TextField(default="", verbose_name="输入格式")
    output_desc = TextField(default="", verbose_name="输出格式")
    correct_answer = TextField(verbose_name="正确答案(参考代码)")
    time_limit = IntegerField(default=1000, verbose_name="时间限制(ms)")
    memory_limit = IntegerField(default=256, verbose_name="内存限制(MB)")
    difficulty = CharField(max_length=20, default="中等", verbose_name="难度")
    language = CharField(max_length=20, default="cpp", verbose_name="参考代码语言")
    samples = TextField(default="[]", verbose_name="样例输入输出(JSON)")
    score = IntegerField(default=100, verbose_name="题目满分(OI模式计分用)")
    sort_order = IntegerField(default=0, verbose_name="排序序号")

    validation_version = IntegerField(default=1)
    validation_status = CharField(max_length=20, default='PENDING')
    validation_error = TextField(null=True)
    checker_config = TextField(default='{"checker":"text"}')
    package_digest = CharField(max_length=64, null=True)

    class Meta:
        table_name = "contest_problems"


class ContestPackage(BaseModel):
    digest = CharField(primary_key=True, max_length=64)
    problem = ForeignKeyField(ContestProblem)
    payload = TextField()
    actor_id = IntegerField(null=True)
    validation_state = CharField(default='VALID')
    validation_error = TextField(null=True)


class RejudgeBatch(BaseModel):
    contest = ForeignKeyField(Contest)
    actor = ForeignKeyField(User)
    reason = TextField()
    state = CharField(default='PENDING')
    reviewed_by = IntegerField(null=True)


class ContestSubmission(BaseModel):
    """比赛提交记录（用于实时排行榜统计，按比赛模式计分）"""
    id = AutoField(primary_key=True, verbose_name="提交ID")
    contest = ForeignKeyField(Contest, backref="submissions", verbose_name="所属比赛")
    user = ForeignKeyField(User, backref="contest_submissions", verbose_name="提交用户")
    contest_problem = ForeignKeyField(ContestProblem, backref="submissions", verbose_name="所属比赛题目")
    problem_index = CharField(max_length=10, default="", verbose_name="题目编号")
    status = CharField(max_length=32, default="Pending", verbose_name="判题状态")
    verdict = CharField(max_length=32, null=True, verbose_name="最终判定")
    passed = IntegerField(default=0, verbose_name="通过用例数")
    total = IntegerField(default=0, verbose_name="用例总数")
    score = IntegerField(default=0, verbose_name="本题得分(OI模式)")
    language = CharField(max_length=20, default="cpp", verbose_name="提交语言")
    code = TextField(default="", verbose_name="提交源代码(审计/复判用)")
    judge_submission_id = CharField(max_length=64, null=True, unique=True, verbose_name="异步判题任务ID")
    job_id = CharField(max_length=64, null=True, unique=True, verbose_name="判题任务ID")
    attempt_id = IntegerField(default=1, verbose_name="判题尝试编号")
    worker_id = CharField(max_length=128, null=True, verbose_name="判题Worker")
    queued_at = DateTimeField(null=True, verbose_name="入队时间")
    judge_started_at = DateTimeField(null=True, verbose_name="开始判题时间")
    compile_started_at = DateTimeField(null=True, verbose_name="开始编译时间")
    compile_finished_at = DateTimeField(null=True, verbose_name="编译完成时间")
    execution_started_at = DateTimeField(null=True, verbose_name="开始执行时间")
    execution_finished_at = DateTimeField(null=True, verbose_name="执行完成时间")
    checked_at = DateTimeField(null=True, verbose_name="检查完成时间")
    finished_at = DateTimeField(null=True, verbose_name="判题完成时间")
    cpu_time = IntegerField(null=True, verbose_name="CPU时间(ms)")
    wall_time = IntegerField(null=True, verbose_name="墙钟时间(ms)")
    memory = BigIntegerField(null=True, verbose_name="峰值内存(bytes)")
    output_size = BigIntegerField(null=True, verbose_name="输出大小(bytes)")
    exit_code = IntegerField(null=True, verbose_name="退出码")
    signal = IntegerField(null=True, verbose_name="终止信号")
    testcase_results = TextField(null=True)
    error_message = TextField(null=True, verbose_name="判题错误信息")
    idempotency_key = CharField(max_length=128, null=True, verbose_name="提交幂等键")
    received_at = DateTimeField(null=True, verbose_name="服务端受理时间")
    team = ForeignKeyField(ContestTeam, null=True)
    package_digest = CharField(max_length=64, null=True)
    rejudge_batch = ForeignKeyField(RejudgeBatch, null=True)
    rejudge_of = IntegerField(null=True)
    rejudge_base_attempt = IntegerField(null=True)
    request_digest = CharField(max_length=64, null=True)
    contest_eligible = BooleanField(default=True, verbose_name="是否计入比赛成绩")
    submitted_at = DateTimeField(default=datetime.now, verbose_name="提交时间")

    class Meta:
        table_name = "contest_submissions"
        indexes = ((('contest', 'user', 'idempotency_key'), True),
                   (('contest', 'team', 'idempotency_key'), True))


class Judgement(BaseModel):
    submission = ForeignKeyField(ContestSubmission)
    attempt_id = IntegerField()
    status = CharField()
    payload = TextField()
    package_digest = CharField(max_length=64, null=True)
    batch_id = IntegerField(null=True)


class ContestAudit(BaseModel):
    contest = ForeignKeyField(Contest)
    actor = ForeignKeyField(User)
    action = CharField()
    reason = TextField()
    payload = TextField(default='{}')


class ContestEvent(BaseModel):
    contest = ForeignKeyField(Contest)
    kind = CharField()
    audience = CharField(default='jury')
    recipient_id = IntegerField(null=True)
    payload = TextField()
    class Meta:
        indexes = ((('contest', 'id'), False),)


class ContestClarification(BaseModel):
    contest = ForeignKeyField(Contest)
    author = ForeignKeyField(User)
    question = TextField()
    answer = TextField(null=True)
    claimed_by = IntegerField(null=True)
    answered_by = IntegerField(null=True)
    broadcast = BooleanField(default=False)


class ContestScoreboardSnapshot(BaseModel):
    """封榜与最终榜的不可变公开快照。"""
    id = AutoField(primary_key=True)
    contest = ForeignKeyField(Contest, backref="scoreboard_snapshots")
    snapshot_kind = CharField(max_length=20, verbose_name="PUBLIC_FREEZE/FINAL")
    payload = TextField(verbose_name="排行榜 JSON")
    scoreboard_version = IntegerField(default=0)
    event_cursor = BigIntegerField(default=0)

    class Meta:
        table_name = "contest_scoreboard_snapshots"
        indexes = ((('contest', 'snapshot_kind'), True),)


class ContestJudgeOutbox(BaseModel):
    """数据库事实与 Redis 队列之间的可靠投递记录。"""
    id = AutoField(primary_key=True)
    submission = ForeignKeyField(ContestSubmission, backref="outbox", unique=True, on_delete="CASCADE")
    state = CharField(max_length=20, default="PENDING")
    dispatch_attempts = IntegerField(default=0)
    last_error = TextField(null=True)
    dispatched_at = DateTimeField(null=True)

    class Meta:
        table_name = "contest_judge_outbox"


class SubmissionOutbox(BaseModel):
    submission = ForeignKeyField(Submission, backref='outbox', unique=True, on_delete='CASCADE')
    state = CharField(max_length=20, default='PENDING', index=True)
    dispatch_attempts = IntegerField(default=0)
    last_error = TextField(null=True)
    dispatched_at = DateTimeField(null=True)

    class Meta:
        table_name = 'submission_outbox'


class ReferenceValidationJob(BaseModel):
    id = CharField(primary_key=True, max_length=64)
    problem = ForeignKeyField(ContestProblem, on_delete='CASCADE')
    version = IntegerField()
    state = CharField(max_length=20, default='PENDING', index=True)

    class Meta:
        table_name = 'reference_validation_jobs'


class ContestTestcase(BaseModel):
    """比赛题目测试用例"""
    id = AutoField(primary_key=True)
    contest_problem = ForeignKeyField(ContestProblem, backref="testcases", verbose_name="所属比赛题目")
    input_data = TextField(verbose_name="输入数据")
    expected_output = TextField(verbose_name="期望输出")
    is_sample = BooleanField(default=False, verbose_name="是否为样例")
    sort_order = IntegerField(default=0, verbose_name="排序序号")

    class Meta:
        table_name = "contest_testcases"


class LearnFavorite(BaseModel):
    """学习资源收藏模型（每个用户每个资源最多收藏一次）"""
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref="learn_favorites", verbose_name="用户")
    resource_id = CharField(max_length=100, verbose_name="资源ID")

    class Meta:
        table_name = "learn_favorites"
        indexes = (
            (('user', 'resource_id'), True),
        )


class LearnBrowsingHistory(BaseModel):
    """学习资源浏览记录模型"""
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref="learn_history", verbose_name="用户")
    resource_id = CharField(max_length=100, verbose_name="资源ID")
    browsed_at = DateTimeField(default=datetime.now, verbose_name="浏览时间")

    class Meta:
        table_name = "learn_browsing_history"
        indexes = (
            (('user', 'resource_id'), False),
        )


# ============================================================
# 4. 表管理与数据库维护方法
# ============================================================

# 所有已注册模型的列表（用于表创建和删除操作）
MODELS = [User, UserJudgeStats, RankingProjectionState, AuthSession, OAuthGrant, Problem, Testcase, Submission, UserCode, Favorite, Announcement,
          Contest, ContestRole, ContestTeam, ContestTeamMember, ContestParticipant, Discussion, DiscussionReply, DiscussionLike, DiscussionReplyLike,
          ContestProblem, ContestTestcase, ContestPackage, RejudgeBatch, ContestSubmission, Judgement,
          ContestAudit, ContestEvent, ContestClarification, ContestScoreboardSnapshot,
          ContestJudgeOutbox, SubmissionOutbox, ReferenceValidationJob, LearnFavorite, LearnBrowsingHistory]


def create_tables():
    """在数据库中创建所有未存在的表（safe=True 表示如果已存在则跳过）"""
    db = get_database()
    db.create_tables(MODELS, safe=True)


def drop_tables():
    """删除所有已存在的表（谨慎使用，会丢失数据）"""
    db = get_database()
    db.drop_tables(MODELS, safe=True)


def connect_database():
    """建立数据库连接（如果当前没有可用连接）"""
    db = get_database()
    if not db.is_connection_usable():
        db.connect()


def close_database():
    """关闭数据库连接（如果当前是打开状态）"""
    db = get_database()
    if not db.is_closed():
        db.close()


# 已登记的数据库迁移（按执行顺序）。每条迁移都是幂等的（使用 IF NOT EXISTS 等）。
# 新增迁移时在此追加即可，无需手动维护版本号（由 schema_migrations 表记录）。
_SCHEMA_MIGRATIONS = [
    (
        "0001_users_role_oauth_columns",
        [
            # 添加缺失的列
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'member';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider VARCHAR(50);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_id VARCHAR(255);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS theme_preference VARCHAR(10) DEFAULT 'system';",
            # 修复旧表的列约束（兼容 OAuth 用户无需密码的场景）
            "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;",
            "ALTER TABLE users ALTER COLUMN is_active SET DEFAULT true;",
            "ALTER TABLE users ALTER COLUMN created_at SET DEFAULT now();",
            "ALTER TABLE users ALTER COLUMN updated_at SET DEFAULT now();",
        ],
    ),
    (
        "0002_contests_discussions_tables",
        [
            # contests 表
            "CREATE TABLE IF NOT EXISTS contests ("
            "id SERIAL PRIMARY KEY, "
            "title VARCHAR(200) NOT NULL, "
            "description TEXT DEFAULT '', "
            "contest_type VARCHAR(50) DEFAULT 'ACM', "
            "status VARCHAR(20) DEFAULT 'upcoming', "
            "start_time TIMESTAMP, "
            "end_time TIMESTAMP, "
            "created_by INTEGER, "
            "is_public BOOLEAN DEFAULT true, "
            "created_at TIMESTAMP DEFAULT now(), "
            "updated_at TIMESTAMP DEFAULT now());",
            # contest_participants 表
            "CREATE TABLE IF NOT EXISTS contest_participants ("
            "id SERIAL PRIMARY KEY, "
            "contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE, "
            "user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, "
            "score INTEGER DEFAULT 0, "
            "rank INTEGER, "
            "created_at TIMESTAMP DEFAULT now(), "
            "updated_at TIMESTAMP DEFAULT now(), "
            "UNIQUE(contest_id, user_id));",
            # discussions 表
            "CREATE TABLE IF NOT EXISTS discussions ("
            "id SERIAL PRIMARY KEY, "
            "title VARCHAR(200) NOT NULL, "
            "content TEXT NOT NULL, "
            "author_id INTEGER REFERENCES users(id) ON DELETE SET NULL, "
            "category VARCHAR(50) DEFAULT '全部', "
            "tags VARCHAR(500), "
            "reply_count INTEGER DEFAULT 0, "
            "is_pinned BOOLEAN DEFAULT false, "
            "is_closed BOOLEAN DEFAULT false, "
            "created_at TIMESTAMP DEFAULT now(), "
            "updated_at TIMESTAMP DEFAULT now());",
            # discussion_replies 表
            "CREATE TABLE IF NOT EXISTS discussion_replies ("
            "id SERIAL PRIMARY KEY, "
            "discussion_id INTEGER REFERENCES discussions(id) ON DELETE CASCADE, "
            "author_id INTEGER REFERENCES users(id) ON DELETE SET NULL, "
            "content TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT now(), "
            "updated_at TIMESTAMP DEFAULT now());",
        ],
    ),
        (
            "0003_contest_problems_testcases",
            [
            # contest_problems 表
            "CREATE TABLE IF NOT EXISTS contest_problems ("
            "id SERIAL PRIMARY KEY, "
            "contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE, "
            "problem_index VARCHAR(10) NOT NULL, "
            "title VARCHAR(200) NOT NULL, "
            "description TEXT NOT NULL, "
            "input_desc TEXT DEFAULT '', "
            "output_desc TEXT DEFAULT '', "
            "correct_answer TEXT NOT NULL, "
            "time_limit INTEGER DEFAULT 1000, "
            "memory_limit INTEGER DEFAULT 256, "
            "difficulty VARCHAR(20) DEFAULT '中等', "
            "sort_order INTEGER DEFAULT 0, "
            "created_at TIMESTAMP DEFAULT now(), "
            "updated_at TIMESTAMP DEFAULT now());",
            # contest_testcases 表
            "CREATE TABLE IF NOT EXISTS contest_testcases ("
            "id SERIAL PRIMARY KEY, "
            "contest_problem_id INTEGER REFERENCES contest_problems(id) ON DELETE CASCADE, "
            "input_data TEXT NOT NULL, "
            "expected_output TEXT NOT NULL, "
            "is_sample BOOLEAN DEFAULT false, "
            "sort_order INTEGER DEFAULT 0, "
            "created_at TIMESTAMP DEFAULT now(), "
            "updated_at TIMESTAMP DEFAULT now());",
        ],
    ),
    (
        "0004_discussion_likes_and_hotness",
        [
            # discussions 表新增 like_count, view_count 字段
            "ALTER TABLE discussions ADD COLUMN IF NOT EXISTS like_count INTEGER DEFAULT 0;",
            "ALTER TABLE discussions ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;",
            # discussion_replies 表新增 like_count 字段
            "ALTER TABLE discussion_replies ADD COLUMN IF NOT EXISTS like_count INTEGER DEFAULT 0;",
            # discussion_likes 表（点赞记录）
            "CREATE TABLE IF NOT EXISTS discussion_likes ("
            "id SERIAL PRIMARY KEY, "
            "discussion_id INTEGER REFERENCES discussions(id) ON DELETE CASCADE, "
            "user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, "
            "created_at TIMESTAMP DEFAULT now(), "
            "UNIQUE(discussion_id, user_id));",
            # discussion_reply_likes 表（回复点赞记录）
            "CREATE TABLE IF NOT EXISTS discussion_reply_likes ("
            "id SERIAL PRIMARY KEY, "
            "reply_id INTEGER REFERENCES discussion_replies(id) ON DELETE CASCADE, "
            "user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, "
            "created_at TIMESTAMP DEFAULT now(), "
            "UNIQUE(reply_id, user_id));",
        ],
    ),
    (
        "0004_learn_favorites_history_tables",
        [
            "CREATE TABLE IF NOT EXISTS learn_favorites ("
            "id SERIAL PRIMARY KEY, "
            "user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, "
            "resource_id VARCHAR(100) NOT NULL, "
            "created_at TIMESTAMP DEFAULT now(), "
            "UNIQUE(user_id, resource_id));",
            "CREATE TABLE IF NOT EXISTS learn_browsing_history ("
            "id SERIAL PRIMARY KEY, "
            "user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, "
            "resource_id VARCHAR(100) NOT NULL, "
            "browsed_at TIMESTAMP DEFAULT now());",
            "CREATE INDEX IF NOT EXISTS idx_learn_history_user "
            "ON learn_browsing_history(user_id, browsed_at DESC);",
        ],
    ),
    (
        "0005_user_name_bio_columns",
        [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(100);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(500);",
        ],
    ),
    (
        "0006_announcement_category",
        [
            "ALTER TABLE announcements ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT '系统公告';",
        ],
    ),
    (
        "0007_like_tables_updated_at",
        [
            "ALTER TABLE discussion_likes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now();",
            "ALTER TABLE discussion_reply_likes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now();",
        ],
    ),
    (
        "0008_contest_problem_samples_language",
        [
            "ALTER TABLE contest_problems ADD COLUMN IF NOT EXISTS language VARCHAR(20) DEFAULT 'cpp';",
            "ALTER TABLE contest_problems ADD COLUMN IF NOT EXISTS samples TEXT DEFAULT '[]';",
        ],
    ),
    (
        "0009_contest_submissions_and_score",
        [
            # contest_problems 增加满分字段（OI 模式计分用）
            "ALTER TABLE contest_problems ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 100;",
            # contest_submissions 表（实时排行榜数据源）
            "CREATE TABLE IF NOT EXISTS contest_submissions ("
            "id SERIAL PRIMARY KEY, "
            "contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE, "
            "user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, "
            "contest_problem_id INTEGER REFERENCES contest_problems(id) ON DELETE CASCADE, "
            "problem_index VARCHAR(10) DEFAULT '', "
            "status VARCHAR(20) DEFAULT 'WA', "
            "passed INTEGER DEFAULT 0, "
            "total INTEGER DEFAULT 0, "
            "score INTEGER DEFAULT 0, "
            "language VARCHAR(20) DEFAULT 'cpp', "
            "submitted_at TIMESTAMP DEFAULT now(), "
            "created_at TIMESTAMP DEFAULT now());",
            "CREATE INDEX IF NOT EXISTS idx_contest_submissions_contest "
            "ON contest_submissions(contest_id, user_id);",
        ],
    ),
    (
        "0010_contest_penalty_time",
        [
            # 比赛增加可配置的罚时（分钟），用于 ACM 模式排行榜罚时计算
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS penalty_time INTEGER DEFAULT 20;",
        ],
    ),
    (
        "0011_contest_submission_code",
        [
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS code TEXT DEFAULT '';",
        ],
    ),
    (
        "0012_contest_submission_idempotency",
        [
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS judge_submission_id VARCHAR(64);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_contest_submissions_judge_submission_id "
            "ON contest_submissions(judge_submission_id) WHERE judge_submission_id IS NOT NULL;",
        ],
    ),
    (
        "0013_contest_judge_lifecycle",
        [
            # 0012 在部分旧环境中已登记但列未成功创建，继续幂等补齐。
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS judge_submission_id VARCHAR(64);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_contest_submissions_judge_submission_id "
            "ON contest_submissions(judge_submission_id) WHERE judge_submission_id IS NOT NULL;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS verdict VARCHAR(32);",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS job_id VARCHAR(64);",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS attempt_id INTEGER DEFAULT 1;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS worker_id VARCHAR(128);",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS queued_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS judge_started_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS compile_started_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS compile_finished_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS execution_started_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS execution_finished_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS checked_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS finished_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS cpu_time INTEGER;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS wall_time INTEGER;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS memory BIGINT;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS output_size BIGINT;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS exit_code INTEGER;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS signal INTEGER;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS error_message TEXT;",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_contest_submissions_job_id "
            "ON contest_submissions(job_id) WHERE job_id IS NOT NULL;",
            "CREATE INDEX IF NOT EXISTS idx_contest_submissions_status "
            "ON contest_submissions(contest_id, status, submitted_at);",
        ],
    ),
    (
        "0014_contest_submission_facts",
        [
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128);",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS received_at TIMESTAMP;",
            "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS contest_eligible BOOLEAN DEFAULT true;",
            "UPDATE contest_submissions SET received_at = submitted_at WHERE received_at IS NULL;",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_contest_submissions_idempotency "
            "ON contest_submissions(contest_id, user_id, idempotency_key) "
            "WHERE idempotency_key IS NOT NULL;",
            "CREATE INDEX IF NOT EXISTS idx_contest_submissions_scoreboard "
            "ON contest_submissions(contest_id, user_id, contest_problem_id, received_at);",
        ],
    ),
    (
        "0015_contest_lifecycle_and_snapshots",
        [
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS lifecycle_state VARCHAR(20) DEFAULT 'DRAFT';",
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS freeze_time TIMESTAMP;",
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS published_at TIMESTAMP;",
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS finalized_at TIMESTAMP;",
            "UPDATE contests SET lifecycle_state = CASE "
            "WHEN status = 'past' THEN 'FINALIZED' "
            "WHEN status IN ('upcoming', 'ongoing') THEN 'SCHEDULED' "
            "ELSE lifecycle_state END WHERE lifecycle_state = 'DRAFT';",
            "CREATE TABLE IF NOT EXISTS contest_scoreboard_snapshots ("
            "id SERIAL PRIMARY KEY, contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE, "
            "snapshot_kind VARCHAR(20) NOT NULL, payload TEXT NOT NULL, scoreboard_version INTEGER DEFAULT 0, "
            "created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now());",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_contest_scoreboard_snapshot_kind "
            "ON contest_scoreboard_snapshots(contest_id, snapshot_kind);",
        ],
    ),
    (
        "0016_contest_judge_outbox",
        [
            "CREATE TABLE IF NOT EXISTS contest_judge_outbox ("
            "id SERIAL PRIMARY KEY, submission_id INTEGER NOT NULL UNIQUE REFERENCES contest_submissions(id) ON DELETE CASCADE, "
            "state VARCHAR(20) NOT NULL DEFAULT 'PENDING', dispatch_attempts INTEGER NOT NULL DEFAULT 0, "
            "last_error TEXT, dispatched_at TIMESTAMP, created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now());",
            "CREATE INDEX IF NOT EXISTS idx_contest_judge_outbox_pending "
            "ON contest_judge_outbox(state, created_at) WHERE state = 'PENDING';",
        ],
    ),
    ('0017_backend_hardening', [
        "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS testcase_results TEXT;",
        "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS job_id VARCHAR(64);",
        "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS attempt_id INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128);",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_submission_job ON submissions(job_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_submission_idempotency ON submissions(user_id, idempotency_key) WHERE idempotency_key IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_submission_history ON submissions(user_id, id DESC);",
        "CREATE INDEX IF NOT EXISTS idx_submission_accepted ON submissions(user_id, problem_id) WHERE status = 'AC';",
        "ALTER TABLE contests ADD COLUMN IF NOT EXISTS scoreboard_requested_version INTEGER NOT NULL DEFAULT 0;",
        "UPDATE contests SET scoreboard_requested_version = COALESCE((SELECT MAX(scoreboard_version) FROM contest_scoreboard_snapshots s WHERE s.contest_id=contests.id), 0) + 1;",
        "ALTER TABLE contest_problems ADD COLUMN IF NOT EXISTS validation_version INTEGER NOT NULL DEFAULT 1;",
        "ALTER TABLE contest_problems ADD COLUMN IF NOT EXISTS validation_status VARCHAR(20) NOT NULL DEFAULT 'PENDING';",
        "ALTER TABLE contest_problems ADD COLUMN IF NOT EXISTS validation_error TEXT;",
        # 已发布比赛不改变判题规则；草稿在部署后安排验证。
        "UPDATE contest_problems SET validation_status='VALID' WHERE contest_id IN (SELECT id FROM contests WHERE lifecycle_state NOT IN ('DRAFT', 'READY'));",
        "UPDATE submissions SET status='SystemError' WHERE job_id IS NULL AND status IN ('Pending', 'Running');",
        "CREATE INDEX IF NOT EXISTS idx_contest_submission_board ON contest_submissions(contest_id, user_id, problem_index, received_at) WHERE contest_eligible=true;",
        "ALTER TABLE contest_judge_outbox DROP CONSTRAINT IF EXISTS contest_judge_outbox_submission_id_fkey;",
        "ALTER TABLE contest_judge_outbox ADD CONSTRAINT contest_judge_outbox_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES contest_submissions(id) ON DELETE CASCADE;",
    ]),
    ('0018_browser_sessions', [
        "ALTER TABLE auth_sessions ADD COLUMN IF NOT EXISTS previous_refresh_hash VARCHAR(64);",
        "ALTER TABLE auth_sessions ADD COLUMN IF NOT EXISTS refresh_request_id VARCHAR(128);",
        "ALTER TABLE auth_sessions ADD COLUMN IF NOT EXISTS refresh_retry_ciphertext TEXT;",
        "ALTER TABLE auth_sessions ADD COLUMN IF NOT EXISTS refresh_retry_until TIMESTAMP;",
        "CREATE INDEX IF NOT EXISTS idx_discussion_reply_page ON discussion_replies(discussion_id, created_at, id);",
        "CREATE INDEX IF NOT EXISTS idx_discussion_category ON discussions(category, is_pinned, created_at);",
    ]),
    ('0019_role_authority_and_freeze', [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_role VARCHAR(20);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS local_role VARCHAR(20);",
        # 旧版本曾在未封榜时写入该派生缓存；只清理可重建快照，保留正式最终榜。
        "DELETE FROM contest_scoreboard_snapshots WHERE snapshot_kind='PUBLIC_FREEZE';",
    ]),

    ('0020_acm_control', [
        "ALTER TABLE contests ADD COLUMN IF NOT EXISTS thawed_at TIMESTAMP;",
        "ALTER TABLE contests ADD COLUMN IF NOT EXISTS final_revision INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE contest_scoreboard_snapshots ADD COLUMN IF NOT EXISTS event_cursor BIGINT NOT NULL DEFAULT 0;",
        "ALTER TABLE contests ADD COLUMN IF NOT EXISTS rules_version VARCHAR(255) NOT NULL DEFAULT 'acm-2026-v1';",
        "ALTER TABLE contests ADD COLUMN IF NOT EXISTS allowed_languages TEXT NOT NULL DEFAULT '[\"cpp\",\"python\",\"java\",\"go\",\"javascript\"]';",
        "ALTER TABLE contests ADD COLUMN IF NOT EXISTS active_submission_limit INTEGER NOT NULL DEFAULT 3;",
        "ALTER TABLE contest_problems ADD COLUMN IF NOT EXISTS checker_config TEXT NOT NULL DEFAULT '{\"checker\":\"text\"}';",
        "ALTER TABLE contest_problems ADD COLUMN IF NOT EXISTS package_digest VARCHAR(64);",
        "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS team_id INTEGER REFERENCES contestteam(id);",
        "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS package_digest VARCHAR(64);",
        "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS rejudge_batch_id INTEGER REFERENCES rejudgebatch(id);",
        "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS rejudge_of INTEGER;",
        "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS rejudge_base_attempt INTEGER;",
        "ALTER TABLE contest_submissions ADD COLUMN IF NOT EXISTS request_digest VARCHAR(64);",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_contest_team_idempotency ON contest_submissions(contest_id, team_id, idempotency_key) WHERE team_id IS NOT NULL AND idempotency_key IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_contest_rejudge ON contest_submissions(rejudge_batch_id, rejudge_of);",
        "CREATE INDEX IF NOT EXISTS idx_contest_waiting ON contest_submissions(received_at) WHERE contest_eligible AND status IN ('Pending', 'Queued');",
        "CREATE INDEX IF NOT EXISTS idx_contest_finished ON contest_submissions(finished_at DESC) WHERE contest_eligible;",
        "UPDATE contests SET thawed_at=COALESCE(finalized_at,end_time) WHERE lifecycle_state='FINALIZED' AND thawed_at IS NULL;",
        "UPDATE contests SET scoreboard_requested_version=GREATEST(scoreboard_requested_version,COALESCE((SELECT MAX(s.scoreboard_version) FROM contest_scoreboard_snapshots s WHERE s.contest_id=contests.id),0))+1 WHERE lifecycle_state NOT IN ('FINALIZED','CANCELLED');",
        "DELETE FROM contest_scoreboard_snapshots WHERE snapshot_kind='PUBLIC_FREEZE';",
    ]),
]


def _apply_migrations(db):
    """
    在已建立连接的前提下应用所有尚未执行的迁移。

    迁移记录保存在 schema_migrations 表中；若该表无法创建，
    仍会继续执行迁移（迁移语句本身幂等，可重复运行）。
    """
    db.execute_sql("CREATE TABLE IF NOT EXISTS schema_migrations (name VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMP DEFAULT now())")
    applied = {row[0] for row in db.execute_sql('SELECT name FROM schema_migrations').fetchall()}
    for name, sqls in _SCHEMA_MIGRATIONS:
        if name in applied:
            continue
        with db.atomic():
            for sql in sqls:
                db.execute_sql(sql)
            db.execute_sql('INSERT INTO schema_migrations(name) VALUES (%s)', (name,))


def run_schema_migrations():
    """显式部署步骤：互斥迁移，任意错误立即失败，迁移记录与 DDL 同事务。"""
    db = get_database()
    with db.connection_context():
        db.execute_sql('SELECT pg_advisory_lock(735194002)')
        try:
            for model in MODELS:
                if not model.table_exists():
                    model.create_table()
            _apply_migrations(db)
            # 新草稿补入持久化验证任务，重复部署不重复创建。
            from uuid import uuid4
            for problem in ContestProblem.select().where(ContestProblem.validation_status == 'PENDING'):
                if not ReferenceValidationJob.select().where(
                    (ReferenceValidationJob.problem == problem) & (ReferenceValidationJob.version == problem.validation_version)).exists():
                    ReferenceValidationJob.create(id=uuid4().hex, problem=problem, version=problem.validation_version)
        finally:
            db.execute_sql('SELECT pg_advisory_unlock(735194002)')


def migrate_add_role_column():
    """
    迁移入口（保留旧名以兼容既有调用）：执行全部数据库迁移。
    """
    run_schema_migrations()


def seed_problem_catalog():
    """显式部署步骤：幂等补齐题库；任意失败回滚并让命令非零退出。"""
    from pages.problem_data import PROBLEMS
    db = get_database()
    with db.connection_context(), db.atomic():
        for problem_id, pdata in PROBLEMS.items():
            (Problem.insert(id=problem_id,
                title=pdata.get('title', f'题目 {problem_id}'),
                description=pdata.get('description', ''),
                input_desc=pdata.get('inputFormat', ''),
                output_desc=pdata.get('outputFormat', ''),
                difficulty=pdata.get('difficulty', '简单'),
                time_limit=pdata.get('timeLimit', 1000),
                memory_limit=pdata.get('memoryLimit', 256), is_public=True)
             .on_conflict_ignore().execute())
