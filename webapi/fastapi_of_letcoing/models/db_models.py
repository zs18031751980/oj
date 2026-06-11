"""
数据库模型文件
使用 Peewee ORM 定义的数据库模型
"""
from datetime import datetime
from typing import Optional

from peewee import (
    Model, CharField, TextField, DateTimeField, BooleanField,
    IntegerField, ForeignKeyField, AutoField, Database
)
from playhouse.pool import PooledPostgresqlExtDatabase

from core.db_config import DatabaseConfig


# 数据库连接实例
database: Optional[PooledPostgresqlExtDatabase] = None


def get_database() -> PooledPostgresqlExtDatabase:
    """获取数据库连接实例"""
    global database
    if database is None:
        try:
            # 尝试使用 ConfigService
            from core.di_container import get_container
            from interfaces.service_interfaces import IConfigService
            
            config_service = get_container().resolve(IConfigService)
            db_config = config_service.get_database_config()
            
            database = PooledPostgresqlExtDatabase(
                db_config["database"],
                user=db_config["username"],
                password=db_config["password"],
                host=db_config["host"],
                port=db_config["port"],
                max_connections=db_config["max_connections"],
                stale_timeout=db_config["stale_timeout"]
            )
        except Exception:
            # 回退到 DatabaseConfig
            config = DatabaseConfig()
            database = PooledPostgresqlExtDatabase(
                config.database,
                user=config.username,
                password=config.password,
                host=config.host,
                port=config.port,
                max_connections=config.max_connections,
                stale_timeout=config.stale_timeout
            )
    return database


class BaseModel(Model):
    """基础模型类"""
    
    created_at = DateTimeField(default=datetime.now, verbose_name="创建时间")
    updated_at = DateTimeField(default=datetime.now, verbose_name="更新时间")
    
    class Meta:
        database = get_database()
    
    def save(self, force_insert=False, only=None):
        """保存时更新 updated_at 字段"""
        self.updated_at = datetime.now()
        return super().save(force_insert, only)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = {}
        for field_name in self._meta.fields.keys():
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                value = value.isoformat()
            data[field_name] = value
        return data


class User(BaseModel):
    """用户模型"""
    
    id = AutoField(primary_key=True, verbose_name="用户ID")
    username = CharField(max_length=50, unique=True, null=True, verbose_name="用户名")
    email = CharField(max_length=100, unique=True, null=True, verbose_name="邮箱")
    password_hash = CharField(max_length=255, null=True, verbose_name="密码")
    is_active = BooleanField(default=True, verbose_name="是否激活")
    last_login = DateTimeField(null=True, verbose_name="最后登录时间")
    provider = CharField(max_length=50, null=True, verbose_name="登录提供商")
    provider_id = CharField(max_length=255, null=True, verbose_name="提供商用户ID")
    avatar_url = CharField(max_length=500, null=True, verbose_name="头像URL")
    
    class Meta:
        table_name = "users"
    
    def to_dict(self) -> dict:
        """转换为字典，排除敏感信息"""
        data = super().to_dict()
        data.pop("password_hash", None)
        return data

# 模型列表
MODELS = [User]


def create_tables():
    """创建所有表"""
    db = get_database()
    db.create_tables(MODELS, safe=True)


def drop_tables():
    """删除所有表"""
    db = get_database()
    db.drop_tables(MODELS, safe=True)


def connect_database():
    """连接数据库"""
    db = get_database()
    if not db.is_connection_usable():
        db.connect()


def close_database():
    """关闭数据库连接"""
    db = get_database()
    if not db.is_closed():
        db.close()
