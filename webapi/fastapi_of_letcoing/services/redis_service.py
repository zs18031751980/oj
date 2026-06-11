"""
Redis 缓存服务

提供统一的 Redis 操作接口，支持缓存、会话管理和速率限制等功能
"""

import redis
import json
import time
from typing import Optional, Any, Dict, List, Union
from datetime import timedelta
from interfaces.service_interfaces import IConfigService, ILoggerService, IRedisService
from core.di_container import Injectable


class RedisService(IRedisService, Injectable):
    """Redis 服务实现类"""
    
    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        self._config_service = config_service
        self._logger_service = logger_service
        self._client = None
        self._connected = False
        self._connect()
    
    def _connect(self) -> bool:
        """连接到 Redis 服务器"""
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
                decode_responses=True,
                socket_timeout=redis_timeout,
                socket_connect_timeout=redis_timeout
            )
            
            # 测试连接
            self._client.ping()
            self._connected = True
            self._logger_service.info(f"Redis 连接成功: {redis_host}:{redis_port}")
            return True
            
        except Exception as ex:
            self._connected = False
            self._logger_service.error("Redis 连接失败", ex)
            self._client = None
            return False
    
    def is_connected(self) -> bool:
        """检查是否连接到 Redis"""
        return self._connected and self._client is not None
    
    def reconnect(self) -> bool:
        """重新连接到 Redis"""
        return self._connect()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置键值对
        
        Args:
            key: 键名
            value: 值（会自动序列化为JSON字符串）
            ttl: 过期时间（秒）
            
        Returns:
            是否成功
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
        获取键值
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            值（自动反序列化JSON）或默认值
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
        """
        删除键
        
        Args:
            key: 键名
            
        Returns:
            是否成功
        """
        if not self.is_connected():
            return False
        
        try:
            return self._client.delete(key) > 0
        except Exception as ex:
            self._logger_service.error(f"Redis 删除失败: {key}", ex)
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键名
            
        Returns:
            是否存在
        """
        if not self.is_connected():
            return False
        
        try:
            return self._client.exists(key) > 0
        except Exception as ex:
            self._logger_service.error(f"Redis 检查存在性失败: {key}", ex)
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 键名
            ttl: 过期时间（秒）
            
        Returns:
            是否成功
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
        获取键的剩余过期时间
        
        Args:
            key: 键名
            
        Returns:
            剩余时间（秒），-1表示永不过期，-2表示键不存在
        """
        if not self.is_connected():
            return -2
        
        try:
            return self._client.ttl(key)
        except Exception as ex:
            self._logger_service.error(f"Redis 获取TTL失败: {key}", ex)
            return -2
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递增计数器
        
        Args:
            key: 键名
            amount: 递增量
            
        Returns:
            递增后的值，失败返回None
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
        递减计数器
        
        Args:
            key: 键名
            amount: 递减量
            
        Returns:
            递减后的值，失败返回None
        """
        if not self.is_connected():
            return None
        
        try:
            return self._client.decrby(key, amount)
        except Exception as ex:
            self._logger_service.error(f"Redis 递减失败: {key}", ex)
            return None
    
    def set_add(self, key: str, *members: Any) -> bool:
        """
        向集合添加成员
        
        Args:
            key: 集合键名
            members: 成员列表
            
        Returns:
            是否成功
        """
        if not self.is_connected():
            return False
        
        try:
            serialized_members = [json.dumps(member, ensure_ascii=False) for member in members]
            return self._client.sadd(key, *serialized_members) > 0
        except Exception as ex:
            self._logger_service.error(f"Redis 集合添加失败: {key}", ex)
            return False
    
    def set_remove(self, key: str, *members: Any) -> bool:
        """
        从集合移除成员
        
        Args:
            key: 集合键名
            members: 成员列表
            
        Returns:
            是否成功
        """
        if not self.is_connected():
            return False
        
        try:
            serialized_members = [json.dumps(member, ensure_ascii=False) for member in members]
            return self._client.srem(key, *serialized_members) > 0
        except Exception as ex:
            self._logger_service.error(f"Redis 集合移除失败: {key}", ex)
            return False
    
    def set_members(self, key: str) -> List[Any]:
        """
        获取集合所有成员
        
        Args:
            key: 集合键名
            
        Returns:
            成员列表
        """
        if not self.is_connected():
            return []
        
        try:
            members = self._client.smembers(key)
            return [json.loads(member) for member in members]
        except Exception as ex:
            self._logger_service.error(f"Redis 获取集合成员失败: {key}", ex)
            return []
    
    def set_is_member(self, key: str, member: Any) -> bool:
        """
        检查成员是否在集合中
        
        Args:
            key: 集合键名
            member: 成员
            
        Returns:
            是否在集合中
        """
        if not self.is_connected():
            return False
        
        try:
            serialized_member = json.dumps(member, ensure_ascii=False)
            return self._client.sismember(key, serialized_member)
        except Exception as ex:
            self._logger_service.error(f"Redis 检查集合成员失败: {key}", ex)
            return False
    
    def list_push(self, key: str, *values: Any) -> Optional[int]:
        """
        向列表左侧推送元素
        
        Args:
            key: 列表键名
            values: 值列表
            
        Returns:
            推送后的列表长度，失败返回None
        """
        if not self.is_connected():
            return None
        
        try:
            serialized_values = [json.dumps(value, ensure_ascii=False) for value in values]
            return self._client.lpush(key, *serialized_values)
        except Exception as ex:
            self._logger_service.error(f"Redis 列表推送失败: {key}", ex)
            return None
    
    def list_pop(self, key: str) -> Any:
        """
        从列表右侧弹出元素
        
        Args:
            key: 列表键名
            
        Returns:
            弹出的元素，失败返回None
        """
        if not self.is_connected():
            return None
        
        try:
            value = self._client.rpop(key)
            return json.loads(value) if value else None
        except Exception as ex:
            self._logger_service.error(f"Redis 列表弹出失败: {key}", ex)
            return None
    
    def list_length(self, key: str) -> int:
        """
        获取列表长度
        
        Args:
            key: 列表键名
            
        Returns:
            列表长度
        """
        if not self.is_connected():
            return 0
        
        try:
            return self._client.llen(key)
        except Exception as ex:
            self._logger_service.error(f"Redis 获取列表长度失败: {key}", ex)
            return 0
    
    def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        获取列表范围内的元素
        
        Args:
            key: 列表键名
            start: 起始索引
            end: 结束索引
            
        Returns:
            元素列表
        """
        if not self.is_connected():
            return []
        
        try:
            values = self._client.lrange(key, start, end)
            return [json.loads(value) for value in values]
        except Exception as ex:
            self._logger_service.error(f"Redis 获取列表范围失败: {key}", ex)
            return []
    
    def keys(self, pattern: str = "*") -> List[str]:
        """
        获取匹配模式的所有键
        
        Args:
            pattern: 匹配模式
            
        Returns:
            键列表
        """
        if not self.is_connected():
            return []
        
        try:
            return self._client.keys(pattern)
        except Exception as ex:
            self._logger_service.error(f"Redis 获取键列表失败: {pattern}", ex)
            return []
    
    def flushdb(self) -> bool:
        """
        清空当前数据库
        
        Returns:
            是否成功
        """
        if not self.is_connected():
            return False
        
        try:
            return self._client.flushdb()
        except Exception as ex:
            self._logger_service.error("Redis 清空数据库失败", ex)
            return False
    
    def info(self) -> Optional[Dict[str, Any]]:
        """
        获取 Redis 服务器信息
        
        Returns:
            服务器信息字典
        """
        if not self.is_connected():
            return None
        
        try:
            return self._client.info()
        except Exception as ex:
            self._logger_service.error("Redis 获取服务器信息失败", ex)
            return None