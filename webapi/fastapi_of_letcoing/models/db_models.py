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
    IntegerField, ForeignKeyField, AutoField, Database, DatabaseProxy
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
    try:
        from core.di_container import get_container
        from interfaces.service_interfaces import IConfigService

        config_service = get_container().resolve(IConfigService)
        db_config = config_service.get_database_config()

        connect_kwargs = dict(
            database=db_config["database"],
            user=db_config["username"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"],
            max_connections=db_config["max_connections"],
            stale_timeout=db_config["stale_timeout"],
            options="-c timezone=Asia/Shanghai",
        )
        # 仅在需要时使用 SSL（如 Zeabur DATABASE_URL 含 ?sslmode=require）
        if db_config.get("ssl"):
            connect_kwargs["ssl"] = True

        db = PooledPostgresqlExtDatabase(**connect_kwargs)
        print(f"[DB] 数据库连接已创建: {db_config['host']}:{db_config['port']}/{db_config['database']}"
              f"{' (ssl)' if db_config.get('ssl') else ''}")
        return db
    except Exception:
        config = DatabaseConfig()
        db = PooledPostgresqlExtDatabase(
            config.database,
            user=config.username,
            password=config.password,
            host=config.host,
            port=config.port,
            max_connections=config.max_connections,
            stale_timeout=config.stale_timeout,
            options="-c timezone=Asia/Shanghai"
        )
        print(f"[DB] 数据库连接已创建(fallback): {config.host}:{config.port}/{config.database}")
        return db


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
    role = CharField(max_length=20, default="member", verbose_name="用户角色")
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
        return data


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

    class Meta:
        table_name = "contests"


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

    class Meta:
        table_name = "contest_problems"


class ContestSubmission(BaseModel):
    """比赛提交记录（用于实时排行榜统计，按比赛模式计分）"""
    id = AutoField(primary_key=True, verbose_name="提交ID")
    contest = ForeignKeyField(Contest, backref="submissions", verbose_name="所属比赛")
    user = ForeignKeyField(User, backref="contest_submissions", verbose_name="提交用户")
    contest_problem = ForeignKeyField(ContestProblem, backref="submissions", verbose_name="所属比赛题目")
    problem_index = CharField(max_length=10, default="", verbose_name="题目编号")
    status = CharField(max_length=20, default="WA", verbose_name="结果(AC/Partial/WA)")
    passed = IntegerField(default=0, verbose_name="通过用例数")
    total = IntegerField(default=0, verbose_name="用例总数")
    score = IntegerField(default=0, verbose_name="本题得分(OI模式)")
    language = CharField(max_length=20, default="cpp", verbose_name="提交语言")
    submitted_at = DateTimeField(default=datetime.now, verbose_name="提交时间")

    class Meta:
        table_name = "contest_submissions"


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
MODELS = [User, Problem, Testcase, Submission, UserCode, Favorite, Announcement,
          Contest, ContestParticipant, Discussion, DiscussionReply,
          ContestProblem, ContestTestcase, ContestSubmission, LearnFavorite, LearnBrowsingHistory]


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
]


def _apply_migrations(db):
    """
    在已建立连接的前提下应用所有尚未执行的迁移。

    迁移记录保存在 schema_migrations 表中；若该表无法创建，
    仍会继续执行迁移（迁移语句本身幂等，可重复运行）。
    """
    try:
        db.execute_sql(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "name VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMP DEFAULT now())"
        )
    except Exception:
        pass

    applied = set()
    try:
        applied = {
            row[0]
            for row in db.execute_sql("SELECT name FROM schema_migrations").fetchall()
        }
    except Exception:
        applied = set()

    for name, sqls in _SCHEMA_MIGRATIONS:
        if name in applied:
            continue
        try:
            with db.atomic():
                for sql in sqls:
                    db.execute_sql(sql)
            try:
                db.execute_sql(
                    "INSERT INTO schema_migrations(name) VALUES (%s) "
                    "ON CONFLICT (name) DO NOTHING",
                    (name,),
                )
            except Exception:
                pass
            print(f"[DB] 迁移已应用: {name}")
        except Exception as e:
            print(f"[DB] 迁移失败(已跳过): {name}: {sanitize_db_error(str(e))}")


def run_schema_migrations():
    """
    执行所有数据库迁移。

    在连接建立（含自动重连）后应用迁移，数据库暂时不可用时安全跳过，
    不会阻塞应用启动。
    """
    db = get_database()
    try:
        with ensure_connected(db):
            _apply_migrations(db)
    except DatabaseUnavailableError as e:
        print(f"[DB] 迁移跳过(数据库不可用): {sanitize_db_error(str(e))}")


def migrate_add_role_column():
    """
    迁移入口（保留旧名以兼容既有调用）：执行全部数据库迁移。
    """
    run_schema_migrations()


def seed_problem_catalog():
    """
    将内存题库（pages.problem_data.PROBLEMS）同步到 PostgreSQL 的 problems 表。

    启动时调用，幂等：只插入缺失的题目，不更新已有记录。
    这样 submissions / favorites 等外键引用 problems 表时不会违约。
    数据库不可用时安全跳过。
    """
    from pages.problem_data import PROBLEMS

    db = get_database()
    inserted = 0
    try:
        with ensure_connected(db):
            for problem_id, pdata in PROBLEMS.items():
                try:
                    exists = Problem.select().where(Problem.id == problem_id).exists()
                    if exists:
                        continue
                    Problem.create(
                        id=problem_id,
                        title=pdata.get('title', f'题目 {problem_id}'),
                        description=pdata.get('description', ''),
                        input_desc=pdata.get('inputFormat', ''),
                        output_desc=pdata.get('outputFormat', ''),
                        difficulty=pdata.get('difficulty', '简单'),
                        time_limit=pdata.get('timeLimit', 1000),
                        memory_limit=pdata.get('memoryLimit', 256),
                        is_public=True,
                    )
                    inserted += 1
                except Exception as e:
                    print(f"[DB] 题目 {problem_id} 同步失败(已跳过): {sanitize_db_error(str(e))}")
        if inserted:
            print(f"[DB] 题库同步完成: 新增 {inserted} 道题目")
    except DatabaseUnavailableError as e:
        print(f"[DB] 题库同步跳过(数据库不可用): {sanitize_db_error(str(e))}")
