"""
数据库配置模块

管理 PostgreSQL 数据库的连接配置信息，包括：
- 数据库主机、端口、名称、用户名和密码
- 连接池的最大连接数和空闲超时时间
- 支持通过依赖注入容器从 ConfigService 动态读取配置
- 也支持使用默认值作为兜底方案
"""

from dataclasses import dataclass
from typing import Optional

from core.di_container import get_container          # 依赖注入容器
from interfaces.service_interfaces import IConfigService  # 配置服务接口


@dataclass
class DatabaseConfig:
    """
    数据库配置数据类

    封装了连接 PostgreSQL 所需的所有参数，以及连接池的配置。
    初始化时会尝试从 ConfigService 读取配置，如果不可用则使用默认值。
    """

    # ----- 数据库连接参数 -----
    host: str = "localhost"             # 数据库服务器地址
    port: int = 5432                    # PostgreSQL 默认端口
    database: str = "letcoding"         # 数据库名称
    username: str = "postgres"          # 数据库用户名
    password: str = ""                  # 数据库密码

    # ----- 连接池配置 -----
    max_connections: int = 20           # 连接池最大连接数
    stale_timeout: int = 300            # 空闲连接超时时间（秒）

    def __post_init__(self):
        """
        对象初始化后的回调方法

        尝试从依赖注入容器中获取 ConfigService，
        并用实际配置覆盖默认值。如果容器尚未初始化，则保留默认值。
        """
        try:
            config_service = get_container().resolve(IConfigService)
            db_config = config_service.get_database_config()

            self.host = db_config["host"]
            self.port = db_config["port"]
            self.database = db_config["database"]
            self.username = db_config["username"]
            self.password = db_config["password"]
            self.max_connections = db_config["max_connections"]
            self.stale_timeout = db_config["stale_timeout"]
        except Exception:
            # 如果依赖注入容器不可用（如数据库迁移脚本中），使用初始化时的默认值
            pass

    @property
    def database_url(self) -> str:
        """
        获取标准格式的 PostgreSQL 连接 URL

        返回格式: postgresql://username:password@host:port/database
        适用于 SQLAlchemy 等 ORM 工具的直接连接。
        """
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def to_dict(self) -> dict:
        """
        将配置转换为字典格式

        注意：出于安全考虑，返回的字典中不包含密码字段。
        """
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "max_connections": self.max_connections,
            "stale_timeout": self.stale_timeout
        }