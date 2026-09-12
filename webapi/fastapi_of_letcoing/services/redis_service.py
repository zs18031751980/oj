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
import hashlib
import threading
from uuid import uuid4
import time            # 时间戳操作
from typing import Optional, Any, Dict, List, Union
from datetime import timedelta
from interfaces.service_interfaces import IConfigService, ILoggerService, IRedisService
from core.di_container import Injectable

_JOB_LEASE_SECONDS = 300


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
        self._reconnect_lock = threading.Lock()
        self._next_reconnect = 0.0
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

            # 兼容 Zeabur 等平台：若提供了 REDIS_URL 则优先解析（覆盖单项配置）
            redis_url = self._config_service.get_config('REDIS_URL')
            if redis_url:
                self._client = redis.Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=redis_timeout,
                    socket_connect_timeout=redis_timeout,
                )
            else:
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
            self._next_reconnect = time.monotonic() + 5
            self._connected = False
            self._logger_service.error("Redis 连接失败", ex)
            self._client = None
            return False

    # ============================================================
    # 连接管理
    # ============================================================

    def is_connected(self) -> bool:
        """检查当前是否与 Redis 服务器保持连接"""
        if self._client is None and time.monotonic() >= self._next_reconnect:
            if self._reconnect_lock.acquire(blocking=False):
                try:
                    self._connect()
                finally:
                    self._reconnect_lock.release()
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
            raise ConnectionError('Redis unavailable')
        count = self._client.eval("""
            local count = redis.call('INCR', KEYS[1])
            if redis.call('TTL', KEYS[1]) < 0 then
                redis.call('EXPIRE', KEYS[1], ARGV[1])
            end
            return count
        """, 1, key, window_seconds)
        return int(count) <= max_requests

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

    def list_claim(self, key: str, processing_key: str) -> Any:
        """原子认领，投递身份与业务 payload 分离，兼容旧队列消息。"""
        if not self.is_connected():
            return None
        delivery = uuid4().hex
        receipt = self._client.eval("""
            local raw
            if KEYS[1] == 'contest_judge_queue' then
                local candidates = redis.call('LRANGE', KEYS[1], -1000, -1)
                local lowest = math.huge
                for i = #candidates, 1, -1 do
                    local ok, item = pcall(cjson.decode, candidates[i])
                    if ok and type(item) == 'table' then
                        local payload = item._delivery and item.payload or item
                        if type(payload) == 'table' then
                            local group = tostring(payload.contest_id) .. ':' .. tostring(payload.entry_id or payload.user_id)
                            local score = tonumber(redis.call('HGET', KEYS[1] .. ':fair', group)) or 0
                            if score < lowest then lowest = score; raw = candidates[i] end
                        end
                    end
                end
                if raw then
                    redis.call('LREM', KEYS[1], -1, raw)
                    local item = cjson.decode(raw)
                    local payload = item._delivery and item.payload or item
                    local group = tostring(payload.contest_id) .. ':' .. tostring(payload.entry_id or payload.user_id)
                    local tick = redis.call('HINCRBY', KEYS[1] .. ':fair', '_tick', 1)
                    redis.call('HSET', KEYS[1] .. ':fair', group, tick)
                    redis.call('EXPIRE', KEYS[1] .. ':fair', 86400)
                else raw = redis.call('RPOP', KEYS[1]) end
            else raw = redis.call('RPOP', KEYS[1]) end
            if not raw then return nil end
            local ok, item = pcall(cjson.decode, raw)
            if not ok or type(item) ~= 'table' then
                redis.call('LPUSH', KEYS[1] .. ':dead', raw)
                return nil
            end
            local payload = item
            local attempts = 0
            if item._delivery then payload = item.payload; attempts = tonumber(item.attempts) or 0 end
            if type(payload) ~= 'table' then
                redis.call('LPUSH', KEYS[1] .. ':dead', raw); return nil
            end
            local receipt = cjson.encode({_delivery=true, payload=payload,
                attempts=attempts+1, delivery_id=ARGV[1]})
            redis.call('LPUSH', KEYS[2], receipt)
            redis.call('SET', KEYS[3], ARGV[1], 'EX', ARGV[2])
            return receipt
        """, 3, key, processing_key, f'judge:lease:{processing_key}:{delivery}',
            delivery, _JOB_LEASE_SECONDS)
        if receipt is None:
            return None
        item = json.loads(receipt)
        return {'payload': item['payload'], 'receipt': receipt, 'attempts': item['attempts']}

    def list_ack(self, processing_key: str, receipt: str) -> bool:
        if not self.is_connected():
            return False
        return bool(self._client.eval("""
            if not redis.call('GET', KEYS[2]) then return 0 end
            local n = redis.call('LREM', KEYS[1], 1, ARGV[1])
            redis.call('DEL', KEYS[2])
            return n
        """, 2, processing_key, self._lease_key(processing_key, receipt), receipt))

    def list_renew(self, processing_key: str, receipt: str) -> bool:
        if not self.is_connected():
            return False
        return bool(self._client.eval("""
            if not redis.call('GET', KEYS[1]) then return 0 end
            return redis.call('EXPIRE', KEYS[1], ARGV[1])
        """, 1, self._lease_key(processing_key, receipt), _JOB_LEASE_SECONDS))

    def list_nack(self, key, processing_key, receipt):
        if not self.is_connected():
            return False
        return bool(self._client.eval("""
            if not redis.call('GET', KEYS[2]) then return 0 end
            if redis.call('LREM', KEYS[1], 1, ARGV[1]) == 0 then return 0 end
            redis.call('DEL', KEYS[2])
            local item = cjson.decode(ARGV[1])
            if item.attempts >= 5 then
                redis.call('LPUSH', KEYS[3] .. ':dead', ARGV[1])
            else
                local clock = redis.call('TIME')
                redis.call('ZADD', KEYS[3] .. ':retry', tonumber(clock[1]) + math.min(60, 2 ^ item.attempts), ARGV[1])
            end
            return 1
        """, 3, processing_key, self._lease_key(processing_key, receipt), key, receipt))

    def archive_dead(self, key, receipt):
        return bool(self._client.eval("""
            if redis.call('LREM', KEYS[1], 1, ARGV[1]) == 0 then return 0 end
            redis.call('LPUSH', KEYS[2], ARGV[1])
            redis.call('LTRIM', KEYS[2], 0, 999)
            return 1
        """, 2, key + ':dead', key + ':dead:archive', receipt))

    def list_retry_due(self, key):
        if not self.is_connected():
            return 0
        return int(self._client.eval("""
            local clock = redis.call('TIME')
            local count = 0
            for _, item in ipairs(redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', clock[1], 'LIMIT', 0, 100)) do
                if redis.call('LLEN', KEYS[2]) >= 1000 then break end
                if redis.call('ZREM', KEYS[1], item) == 1 then
                    redis.call('LPUSH', KEYS[2], item); count = count + 1
                end
            end
            return count
        """, 2, key + ':retry', key))

    def list_recover(self, processing_key: str, key: str) -> int:
        if not self.is_connected():
            return 0
        return int(self._client.eval("""
            local count = 0
            for _, receipt in ipairs(redis.call('LRANGE', KEYS[1], 0, -1)) do
                local ok, item = pcall(cjson.decode, receipt)
                ok = ok and type(item) == 'table'
                local lease = ok and item.delivery_id and
                    ('judge:lease:' .. KEYS[1] .. ':' .. item.delivery_id) or ''
                if not redis.call('GET', lease) then
                    if redis.call('LREM', KEYS[1], 1, receipt) == 1 then
                        local target = KEYS[2]
                        if not ok or (tonumber(item.attempts) or 0) >= tonumber(ARGV[1]) then
                            target = target .. ':dead'
                        end
                        redis.call('LPUSH', target, receipt)
                        count = count + 1
                    end
                end
            end
            return count
        """, 2, processing_key, key, 5))

    @staticmethod
    def _lease_key(processing_key: str, receipt: str) -> str:
        delivery = json.loads(receipt).get('delivery_id')
        return f'judge:lease:{processing_key}:{delivery}'

    def enqueue_with_state(self, state_key: str, state: Any, ttl: int, queue_key: str, task: Any) -> bool:
        """通过 Redis 事务原子完成“提交已接收 + 任务入队”。"""
        if not self.is_connected():
            return False
        job_id = task.get('job_id') or uuid4().hex
        try:
            return bool(self._client.eval("""
                if redis.call('EXISTS', KEYS[3]) == 1 then return 1 end
                if redis.call('LLEN', KEYS[2]) >= 1000 then return 0 end
                redis.call('SET', KEYS[3], '1', 'EX', 604800)
                redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
                redis.call('LPUSH', KEYS[2], ARGV[3])
                return 1
            """, 3, state_key, queue_key, f'judge:enqueued:{queue_key}:{job_id}',
                json.dumps(state), ttl, json.dumps(task)))
        except Exception:
            return False

    def acquire_execution_slot(self, subject):
        if not self.is_connected():
            raise ConnectionError('Redis unavailable')
        token = uuid4().hex
        allowed = self._client.eval("""
            local clock = redis.call('TIME')
            local now = tonumber(clock[1])
            for _, key in ipairs(KEYS) do redis.call('ZREMRANGEBYSCORE', key, '-inf', now) end
            if redis.call('ZCARD', KEYS[1]) >= 16 or redis.call('ZCARD', KEYS[2]) >= 2 then return 0 end
            for _, key in ipairs(KEYS) do
                redis.call('ZADD', key, now + 60, ARGV[1]); redis.call('EXPIRE', key, 65)
            end
            return 1
        """, 2, 'execution:global', f'execution:{subject}', token)
        return token if allowed else None

    def release_execution_slot(self, subject, token):
        if self.is_connected():
            with self._client.pipeline() as pipe:
                pipe.zrem('execution:global', token)
                pipe.zrem(f'execution:{subject}', token)
                pipe.execute()

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
