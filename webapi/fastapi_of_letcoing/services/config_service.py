"""
配置服务实现

提供配置管理功能，支持环境变量和应用配置。
"""

import os
from typing import Any, Optional

from interfaces.service_interfaces import IConfigService


class ConfigService(IConfigService):
    """配置服务实现"""

    def __init__(self, app_config: Optional[dict] = None):
        """
        初始化配置服务

        Args:
            app_config: Flask应用配置字典
        """
        self._app_config = app_config or {}

    def get_api_token(self) -> str:
        """获取API Token"""
        return self._app_config.get('API_TOKEN', '')

    def get_timeout(self) -> int:
        """获取请求超时时间"""
        return int(self._app_config.get('REQUEST_TIMEOUT', '30'))

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._app_config.get(key, os.environ.get(key, default))

    def get_database_config(self) -> dict:
        """获取数据库配置"""
        return {
            "host": self.get_config("DB_HOST", "localhost"),
            "port": self.get_config("DB_PORT", 5432),
            "database": self.get_config("DB_NAME", "letcoding"),
            "username": self.get_config("DB_USER", "postgres"),
            "password": self.get_config("DB_PASSWORD", ""),
            "max_connections": self.get_config("DB_MAX_CONNECTIONS", 20),
            "stale_timeout": self.get_config("DB_STALE_TIMEOUT", 300),
        }

    def get_database_url(self) -> str:
        """获取数据库连接 URL"""
        config = self.get_database_config()
        return f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
