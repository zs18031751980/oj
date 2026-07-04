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

        return PooledPostgresqlExtDatabase(
            db_config["database"],
            user=db_config["username"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"],
            max_connections=db_config["max_connections"],
            stale_timeout=db_config["stale_timeout"]
        )
    except Exception:
        config = DatabaseConfig()
        return PooledPostgresqlExtDatabase(
            config.database,
            user=config.username,
            password=config.password,
            host=config.host,
            port=config.port,
            max_connections=config.max_connections,
            stale_timeout=config.stale_timeout
        )


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
        """
        data = {}
        for field_name in self._meta.fields.keys():
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                value = value.isoformat()
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
    email = CharField(max_length=100, unique=True, null=True, verbose_name="邮箱")
    password_hash = CharField(max_length=255, null=True, verbose_name="密码哈希")
    is_active = BooleanField(default=True, verbose_name="是否激活")
    role = CharField(max_length=20, default="member", verbose_name="用户角色")
    last_login = DateTimeField(null=True, verbose_name="最后登录时间")
    provider = CharField(max_length=50, null=True, verbose_name="登录提供商")
    provider_id = CharField(max_length=255, null=True, verbose_name="提供商用户ID")
    avatar_url = CharField(max_length=500, null=True, verbose_name="头像URL")
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

# ============================================================
# 4. 表管理与数据库维护方法
# ============================================================

# 所有已注册模型的列表（用于表创建和删除操作）
MODELS = [User, Problem, Testcase, Submission, UserCode, Announcement]


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


def migrate_add_role_column():
    """
    迁移：为已有 users 表添加缺失的列并修复约束（如果尚不存在）

    兼容已有数据库：如果 users 表在相关列加入之前已创建，
    此函数通过执行 PostgreSQL 的 ALTER TABLE 来安全地添加缺失的列并修复约束。
    """
    db = get_database()
    migrations = [
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
    ]
    for sql in migrations:
        try:
            db.execute_sql(sql)
        except Exception:
            pass
