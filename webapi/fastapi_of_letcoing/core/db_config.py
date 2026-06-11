"""
数据库配置文件
PostgreSQL 数据库连接配置管理
"""
from dataclasses import dataclass
from typing import Optional

from core.di_container import get_container
from interfaces.service_interfaces import IConfigService


@dataclass
class DatabaseConfig:
    """数据库配置类"""
    
    # 数据库连接参数
    host: str = "localhost"
    port: int = 5432
    database: str = "letcoding"
    username: str = "postgres"
    password: str = ""
    
    # 连接池配置
    max_connections: int = 20
    stale_timeout: int = 300
    
    def __post_init__(self):
        """初始化时从 ConfigService 读取配置"""
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
            # 如果依赖注入不可用，使用默认值
            pass
    
    @property
    def database_url(self) -> str:
        """获取数据库连接 URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "max_connections": self.max_connections,
            "stale_timeout": self.stale_timeout
        }