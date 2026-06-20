"""
Redis 缓存服务模块

提供统一的 Redis 操作接口，支持以下功能：
1. 缓存管理：键值对存储、过期时间管理
2. 会话管理：用户会话（Session）的持久化
3. 速率限制：基于计数器的频率控制（配合 RateLimitMiddleware）
4. 数据结构：字符串、集合（Set）、列表（List）
5. 令牌管理：JWT 令牌的缓存和黑名单存储

所有存储的值自动进行 JSON 序列化/反序列化，支持复杂数据结构。
"""

import redis           # Redis Python 客户端
import json            # JSON 序列化/反序列化
import time            # 时间戳操作
from typing import Optional, Any, Dict, List, Union
from datetime import timedelta
from interfaces.service_interfaces import IConfigService, ILoggerService, IRedisService
from core.di_container import Injectable


class RedisService(IRedisService, Injectable):
    """
    Redis 服务实现类

    封装 redis-py 库，提供易用的接口。
    所有值在存储时自动序列化为 JSON，读取时自动反序列化。
    连接丢失时不会抛出异常，而是返回默认值，确保 Redis 不可用时服务仍可降级运行。
    """

    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        """
        初始化 Redis 服务

        Args:
            config_service: 配置服务（读取 Redis 连接参数）
            logger_service: 日志服务
        """
        self._config_service = config_service
        self._logger_service = logger_service
        self._client = None
        self._connected = False
        self._connect()

    def _connect(self) -> bool:
        """
        连接到 Redis 服务器

        从配置中读取 Redis 连接参数，建立连接并测试连通性。

        Returns:
            是否连接成功
        """
        try:
            redis_host = self._config_service.get_config('REDIS_HOST', 'localhost')
            redis_port = self._config_service.get_config('REDIS_PORT', 6379)
            redis_db = self._config_service.get_config('REDIS_DB', 0)
            redis_password = self._config_service.get_config('REDIS_PASSWORD')
            redis_timeout = self._config_service.get_config('REDIS_TIMEOUT', 5)

            self._client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,          # 自动解码响应为字符串
                socket_timeout=redis_timeout,    # Socket 超时
                socket_connect_timeout=redis_timeout  # 连接超时
            )

            # 通过 ping 测试连接
            self._client.ping()
            self._connected = True
            self._logger_service.info(f"Redis 连接成功: {redis_host}:{redis_port}")
            return True

        except Exception as ex:
            self._connected = False
            self._logger_service.error("Redis 连接失败", ex)
            self._client = None
            return False

    # ============================================================
    # 连接管理
    # ============================================================

    def is_connected(self) -> bool:
        """检查当前是否与 Redis 服务器保持连接"""
        return self._connected and self._client is not None

    def reconnect(self) -> bool:
        """重新连接到 Redis 服务器"""
        return self._connect()

    # ============================================================
    # 键值对操作（核心数据操作）
    # ============================================================

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置键值对

        Args:
            key: 键名
            value: 值（支持任意可 JSON 序列化的类型）
            ttl: 过期时间（秒），不设置则持久化存储

        Returns:
            是否设置成功
        """
        if not self.is_connected():
            return False

        try:
            serialized_value = json.dumps(value, ensure_ascii=False)

            if ttl:
                return self._client.setex(key, ttl, serialized_value)
            else:
                return self._client.set(key, serialized_value)

        except Exception as ex:
            self._logger_service.error(f"Redis 设置失败: {key}", ex)
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取键对应的值

        Args:
            key: 键名
            default: 键不存在时返回的默认值

        Returns:
            自动反序列化后的值，键不存在返回 default
        """
        if not self.is_connected():
            return default

        try:
            value = self._client.get(key)
            if value is None:
                return default

            return json.loads(value)

        except (json.JSONDecodeError, Exception) as ex:
            self._logger_service.error(f"Redis 获取失败: {key}", ex)
            return default

    def delete(self, key: str) -> bool:
        """删除指定的键"""
        if not self.is_connected():
            return False

        try:
            return self._client.delete(key) > 0
        except Exception as ex:
            self._logger_service.error(f"Redis 删除失败: {key}", ex)
            return False

    def exists(self, key: str) -> bool:
        """检查指定的键是否存在"""
        if not self.is_connected():
            return False

        try:
            return self._client.exists(key) > 0
        except Exception as ex:
            self._logger_service.error(f"Redis 检查存在性失败: {key}", ex)
            return False

    # ============================================================
    # 过期时间管理
    # ============================================================

    def expire(self, key: str, ttl: int) -> bool:
        """
        为指定键设置过期时间

        Args:
            key: 键名
            ttl: 过期时间（秒）
        """
        if not self.is_connected():
            return False

        try:
            return self._client.expire(key, ttl)
        except Exception as ex:
            self._logger_service.error(f"Redis 设置过期时间失败: {key}", ex)
            return False

    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间

        Returns:
            剩余秒数（>0），-1 表示永不过期，-2 表示键不存在
        """
        if not self.is_connected():
            return -2

        try:
            return self._client.ttl(key)
        except Exception as ex:
            self._logger_service.error(f"Redis 获取TTL失败: {key}", ex)
            return -2

    def set_raw(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置键为原始字符串值（不进行 JSON 序列化）

        用于存储简单字符串值（黑名单标记、刷新令牌等），避免 JSON 序列化开销。

        Args:
            key: 键名
            value: 值（自动转换为字符串）
            ttl: 过期时间（秒），不设置则持久化存储
        """
        if not self.is_connected():
            return False

        try:
            str_value = str(value)
            if ttl:
                return self._client.setex(key, ttl, str_value)
            else:
                return self._client.set(key, str_value)
        except Exception as ex:
            self._logger_service.error(f"Redis 设置原始值失败: {key}", ex)
            return False

    def get_raw(self, key: str) -> Optional[str]:
        """
        获取键对应的原始字符串值（不进行 JSON 反序列化）

        用于计数器和简单字符串值的读取，避免 JSON 解析开销。
        """
        if not self.is_connected():
            return None

        try:
            return self._client.get(key)
        except Exception as ex:
            self._logger_service.error(f"Redis 获取原始值失败: {key}", ex)
            return None

    def get_int(self, key: str, default: int = 0) -> int:
        """
        获取键对应的整数值

        用于计数器读取，避免 JSON 解析开销。
        """
        if not self.is_connected():
            return default

        try:
            value = self._client.get(key)
            return int(value) if value is not None else default
        except (ValueError, Exception) as ex:
            self._logger_service.error(f"Redis 获取整数值失败: {key}", ex)
            return default

    def rate_limit_check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        原子化频率限制检查

        使用 INCR + EXPIRE 组合实现高效且原子化的计数和过期设置。
        在单个原子操作中递增计数器，并在首次请求时设置过期时间。

        Returns:
            True 表示允许请求，False 表示超出限制
        """
        if not self.is_connected():
            return True

        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            results = pipe.execute()
            count = int(results[0])
            ttl_val = int(results[1])

            if ttl_val < 0:
                self._client.expire(key, window_seconds)

            return count <= max_requests
        except Exception as ex:
            self._logger_service.error(f"Redis 频率限制检查失败: {key}", ex)
            return True

    # ============================================================
    # 计数器操作（原子操作）
    # ============================================================

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        原子递增计数器

        Args:
            key: 键名
            amount: 递增数量（默认 1）

        Returns:
            递增后的数值，失败返回 None
        """
        if not self.is_connected():
            return None

        try:
            return self._client.incrby(key, amount)
        except Exception as ex:
            self._logger_service.error(f"Redis 递增失败: {key}", ex)
            return None

    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        原子递减计数器

        Args:
            key: 键名
            amount: 递减数量（默认 1）

        Returns:
            递减后的数值，失败返回 None
        """
        if not self.is_connected():
            return None

        try:
            return self._client.decrby(key, amount)
        except Exception as ex:
            self._logger_service.error(f"Redis 递减失败: {key}", ex)
            return None

    # ============================================================
    # 集合（Set）操作
    # ============================================================

    def set_add(self, key: str, *members: Any) -> bool:
        """向集合中添加一个或多个成员（成员自动 JSON 序列化）"""
        if not self.is_connected():
            return False

        try:
            serialized_members = [json.dumps(member, ensure_ascii=False) for member in members]
            return self._client.sadd(key, *serialized_members) > 0
        except Exception as ex:
            self._logger_service.error(f"Redis 集合添加失败: {key}", ex)
            return False

    def set_remove(self, key: str, *members: Any) -> bool:
        """从集合中移除一个或多个成员"""
        if not self.is_connected():
            return False

        try:
            serialized_members = [json.dumps(member, ensure_ascii=False) for member in members]
            return self._client.srem(key, *serialized_members) > 0
        except Exception as ex:
            self._logger_service.error(f"Redis 集合移除失败: {key}", ex)
            return False

    def set_members(self, key: str) -> List[Any]:
        """获取集合中的所有成员（自动反序列化）"""
        if not self.is_connected():
            return []

        try:
            members = self._client.smembers(key)
            return [json.loads(member) for member in members]
        except Exception as ex:
            self._logger_service.error(f"Redis 获取集合成员失败: {key}", ex)
            return []

    def set_is_member(self, key: str, member: Any) -> bool:
        """检查指定成员是否在集合中"""
        if not self.is_connected():
            return False

        try:
            serialized_member = json.dumps(member, ensure_ascii=False)
            return self._client.sismember(key, serialized_member)
        except Exception as ex:
            self._logger_service.error(f"Redis 检查集合成员失败: {key}", ex)
            return False

    # ============================================================
    # 列表（List）操作
    # ============================================================

    def list_push(self, key: str, *values: Any) -> Optional[int]:
        """向列表左侧推入元素（元素自动 JSON 序列化），返回推入后的列表长度"""
        if not self.is_connected():
            return None

        try:
            serialized_values = [json.dumps(value, ensure_ascii=False) for value in values]
            return self._client.lpush(key, *serialized_values)
        except Exception as ex:
            self._logger_service.error(f"Redis 列表推送失败: {key}", ex)
            return None

    def list_pop(self, key: str) -> Any:
        """从列表右侧弹出元素（自动反序列化）"""
        if not self.is_connected():
            return None

        try:
            value = self._client.rpop(key)
            return json.loads(value) if value else None
        except Exception as ex:
            self._logger_service.error(f"Redis 列表弹出失败: {key}", ex)
            return None

    def list_length(self, key: str) -> int:
        """获取列表长度"""
        if not self.is_connected():
            return 0

        try:
            return self._client.llen(key)
        except Exception as ex:
            self._logger_service.error(f"Redis 获取列表长度失败: {key}", ex)
            return 0

    def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表中指定范围的元素（end=-1 表示到末尾）"""
        if not self.is_connected():
            return []

        try:
            values = self._client.lrange(key, start, end)
            return [json.loads(value) for value in values]
        except Exception as ex:
            self._logger_service.error(f"Redis 获取列表范围失败: {key}", ex)
            return []

    # ============================================================
    # 键管理与服务器信息
    # ============================================================

    def keys(self, pattern: str = "*") -> List[str]:
        """
        查找所有匹配指定模式的键

        Args:
            pattern: 匹配模式，支持通配符（如 user:*、rate_limit:*）

        Returns:
            匹配的键名列表
        """
        if not self.is_connected():
            return []

        try:
            return self._client.keys(pattern)
        except Exception as ex:
            self._logger_service.error(f"Redis 获取键列表失败: {pattern}", ex)
            return []

    def flushdb(self) -> bool:
        """清空当前数据库（谨慎使用！会删除所有数据）"""
        if not self.is_connected():
            return False

        try:
            return self._client.flushdb()
        except Exception as ex:
            self._logger_service.error("Redis 清空数据库失败", ex)
            return False

    def info(self) -> Optional[Dict[str, Any]]:
        """获取 Redis 服务器的信息与统计"""
        if not self.is_connected():
            return None

        try:
            return self._client.info()
        except Exception as ex:
            self._logger_service.error("Redis 获取服务器信息失败", ex)
            return None