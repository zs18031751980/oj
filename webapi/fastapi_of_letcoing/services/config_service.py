"""
配置服务实现模块

提供统一的配置访问接口，支持：
1. 从 Flask 应用配置中读取
2. 从系统环境变量中读取（作为兜底）
3. 提供数据库配置、API Token、超时时间等常用配置的快捷方法
"""

import os
from typing import Any, Optional

from interfaces.service_interfaces import IConfigService


class ConfigService(IConfigService):
    """
    配置服务实现类

    包装了 Flask 的应用配置字典和系统环境变量，
    为其他服务提供统一的配置访问入口。
    配置优先级：应用配置 > 环境变量 > 默认值
    """

    def __init__(self, app_config: Optional[dict] = None):
        """
        初始化配置服务

        Args:
            app_config: Flask 应用配置字典，通常来自 app.config
        """
        self._app_config = app_config or {}

    def get_api_token(self) -> str:
        """
        获取 Glot.io 代码执行服务的 API Token

        Returns:
            API Token 字符串，未配置时返回空字符串
        """
        return self._app_config.get('API_TOKEN', '')

    def get_timeout(self) -> int:
        """
        获取 HTTP 请求超时时间

        Returns:
            超时秒数，默认 30 秒
        """
        return int(self._app_config.get('REQUEST_TIMEOUT', '30'))

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取指定键的配置值

        搜索顺序：
        1. Flask 应用配置（app.config）
        2. 系统环境变量（os.environ）
        3. 调用方提供的默认值

        Args:
            key: 配置键名
            default: 配置不存在时的默认值

        Returns:
            配置值
        """
        return self._app_config.get(key, os.environ.get(key, default))

    def get_database_config(self) -> dict:
        """
        获取完整的数据库连接配置

        Returns:
            包含所有数据库连接参数的字典
        """
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
        """
        获取标准 PostgreSQL 连接 URL

        Returns:
            格式: postgresql://user:password@host:port/database
        """
        config = self.get_database_config()
        return f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
