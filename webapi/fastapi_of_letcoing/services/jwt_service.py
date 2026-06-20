"""
JWT 认证服务模块

提供完整的 JWT（JSON Web Token）认证功能：
1. 生成令牌对：访问令牌（Access Token）+ 刷新令牌（Refresh Token）
2. 验证访问令牌：签名验证、过期检查、令牌类型检查、黑名单检查
3. 刷新令牌续期：使用刷新令牌获取新的访问令牌
4. 令牌撤销：将令牌加入 Redis 黑名单使其失效

使用 Redis 实现：
- 用户信息缓存（减少数据库查询）
- 刷新令牌存储（验证有效性）
- 令牌黑名单（实现登出功能）
"""

import jwt           # PyJWT 库：JWT 编码/解码
import json          # JSON 数据处理
import time          # 时间戳操作
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from interfaces.service_interfaces import IConfigService, ILoggerService, IRedisService, IJWTService
from core.di_container import Injectable
from models.auth_models import JWTToken


class JWTService(Injectable, IJWTService):
    """
    JWT 认证服务实现类

    管理 JWT 令牌的完整生命周期，包括生成、验证、刷新和撤销。
    使用 HS256（HMAC-SHA256）算法进行签名。
    通过 Redis 缓存来提升性能和实现令牌状态管理。
    """

    def __init__(self, config_service: IConfigService, logger_service: ILoggerService, redis_service: IRedisService):
        """
        初始化 JWT 服务

        Args:
            config_service: 配置服务（提供密钥、算法、过期时间等配置）
            logger_service: 日志服务
            redis_service: Redis 服务（用于缓存和黑名单）
        """
        self._config_service = config_service
        self._logger_service = logger_service
        self._redis_service = redis_service
        self._secret_key = self._config_service.get_config('JWT_SECRET_KEY', 'default-secret-key')
        self._algorithm = self._config_service.get_config('JWT_ALGORITHM', 'HS256')
        self._access_token_expire = self._config_service.get_config('JWT_ACCESS_TOKEN_EXPIRE', 3600)       # 1 小时
        self._refresh_token_expire = self._config_service.get_config('JWT_REFRESH_TOKEN_EXPIRE', 86400 * 7)  # 7 天

    def generate_tokens(self, user_info: Dict[str, Any]) -> JWTToken:
        """
        生成 JWT 令牌对（访问令牌 + 刷新令牌）

        访问令牌包含用户的基本信息（ID、用户名、邮箱、提供商），
        刷新令牌仅包含用户 ID，用于后续的令牌续期。

        Args:
            user_info: 用户信息字典（必须包含 id、username、email、provider）

        Returns:
            包含访问令牌和刷新令牌的 JWTToken 对象
        """
        now = datetime.utcnow()
        access_expire = now + timedelta(seconds=self._access_token_expire)
        refresh_expire = now + timedelta(seconds=self._refresh_token_expire)

        # 生成访问令牌（Access Token）—— 包含完整的用户信息
        access_payload = {
            'user_id': user_info['id'],
            'username': user_info.get('username', ''),
            'email': user_info.get('email', ''),
            'provider': user_info.get('provider', ''),
            'exp': access_expire,      # 过期时间
            'iat': now,                # 签发时间
            'type': 'access'           # 令牌类型：访问令牌
        }
        access_token = jwt.encode(access_payload, self._secret_key, algorithm=self._algorithm)

        # 生成刷新令牌（Refresh Token）—— 仅包含用户 ID 和过期时间
        refresh_payload = {
            'user_id': user_info['id'],
            'exp': refresh_expire,     # 过期时间
            'iat': now,                # 签发时间
            'type': 'refresh'          # 令牌类型：刷新令牌
        }
        refresh_token = jwt.encode(refresh_payload, self._secret_key, algorithm=self._algorithm)

        # 将用户信息和刷新令牌缓存到 Redis
        self._cache_user_info(user_info['id'], user_info)
        self._cache_refresh_token(user_info['id'], refresh_token)

        return JWTToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_token_expire
        )

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌的有效性

        验证流程：
        1. 解码 JWT 并验证签名
        2. 检查令牌类型是否为 "access"
        3. 检查令牌是否在黑名单中（是否已被撤销）
        4. 尝试从 Redis 缓存获取用户信息
        5. 如果缓存中没有，从令牌载荷中提取基本信息

        Args:
            token: 待验证的 JWT 访问令牌字符串

        Returns:
            用户信息字典，验证失败返回 None
        """
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])

            # 检查令牌类型是否为访问令牌
            if payload.get('type') != 'access':
                self._logger_service.warning("令牌类型不匹配")
                return None

            # 检查令牌是否已被撤销（在黑名单中）
            if self._is_token_blacklisted(token):
                self._logger_service.warning("令牌已被撤销")
                return None

            # 优先从 Redis 缓存获取用户信息（更完整）
            user_info = self._get_cached_user_info(payload['user_id'])
            if user_info:
                return user_info

            # 如果缓存中没有，从令牌载荷中提取基本信息
            return {
                'id': payload['user_id'],
                'username': payload.get('username', ''),
                'email': payload.get('email', ''),
                'provider': payload.get('provider', '')
            }

        except jwt.ExpiredSignatureError:
            self._logger_service.warning("访问令牌已过期")
            return None
        except jwt.InvalidTokenError as ex:
            self._logger_service.warning(f"无效的访问令牌: {ex}")
            return None
        except Exception as ex:
            self._logger_service.error("验证访问令牌时发生异常", ex)
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[JWTToken]:
        """
        使用刷新令牌获取新的访问令牌

        流程：
        1. 验证刷新令牌的签名和类型
        2. 检查刷新令牌是否与 Redis 中缓存的一致
        3. 获取缓存的用户信息
        4. 生成新的令牌对

        Args:
            refresh_token: 刷新令牌字符串

        Returns:
            新的 JWTToken 对象（包含新的访问令牌和刷新令牌），验证失败返回 None
        """
        try:
            payload = jwt.decode(refresh_token, self._secret_key, algorithms=[self._algorithm])

            # 检查令牌类型是否为刷新令牌
            if payload.get('type') != 'refresh':
                self._logger_service.warning("令牌类型不匹配")
                return None

            user_id = payload['user_id']

            # 检查刷新令牌是否与 Redis 中缓存的匹配
            if not self._is_valid_refresh_token(user_id, refresh_token):
                self._logger_service.warning("无效的刷新令牌")
                return None

            # 获取缓存的用户信息
            user_info = self._get_cached_user_info(user_id)
            if not user_info:
                self._logger_service.warning("用户信息不存在")
                return None

            # 生成新的令牌对（旧的刷新令牌仍然有效，因为尚未实现令牌轮换）
            return self.generate_tokens(user_info)

        except jwt.ExpiredSignatureError:
            self._logger_service.warning("刷新令牌已过期")
            return None
        except jwt.InvalidTokenError as ex:
            self._logger_service.warning(f"无效的刷新令牌: {ex}")
            return None
        except Exception as ex:
            self._logger_service.error("刷新访问令牌时发生异常", ex)
            return None

    def revoke_token(self, token: str) -> bool:
        """
        撤销访问令牌（将其加入 Redis 黑名单）

        如果令牌尚未过期，将其加入黑名单并设置与令牌剩余有效期相同的过期时间。

        Args:
            token: 要撤销的 JWT 令牌

        Returns:
            是否成功撤销（已过期的令牌也视为成功）
        """
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            exp = payload.get('exp', 0)
            remaining_time = int(exp - time.time())

            if remaining_time > 0:
                self._blacklist_token(token, remaining_time)
                return True

            return False

        except jwt.ExpiredSignatureError:
            return True  # 已过期的令牌无需撤销
        except jwt.InvalidTokenError as ex:
            self._logger_service.warning(f"无效的令牌无法撤销: {ex}")
            return False
        except Exception as ex:
            self._logger_service.error("撤销令牌时发生异常", ex)
            return False

    # ============================================================
    # Redis 缓存操作（私有方法）
    # ============================================================

    def _cache_user_info(self, user_id: str, user_info: Dict[str, Any]) -> None:
        """将用户信息缓存到 Redis，过期时间与刷新令牌一致"""
        try:
            key = f"user:{user_id}"
            self._redis_service.set(key, user_info, self._refresh_token_expire)
        except Exception as ex:
            self._logger_service.warning("缓存用户信息失败", ex)

    def _get_cached_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """从 Redis 获取缓存的用户信息"""
        try:
            key = f"user:{user_id}"
            return self._redis_service.get(key)
        except Exception as ex:
            self._logger_service.warning("获取缓存的用户信息失败", ex)
            return None

    def _cache_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """将刷新令牌缓存到 Redis，用于后续验证（使用原始字符串存储，避免 JSON 序列化开销）"""
        try:
            key = f"refresh_token:{user_id}"
            self._redis_service.set_raw(key, refresh_token, self._refresh_token_expire)
        except Exception as ex:
            self._logger_service.warning("缓存刷新令牌失败", ex)

    def _is_valid_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """检查客户端提供的刷新令牌是否与 Redis 中缓存的一致（使用原始字符串读取）"""
        try:
            key = f"refresh_token:{user_id}"
            cached_token = self._redis_service.get_raw(key)
            return cached_token == refresh_token
        except Exception as ex:
            self._logger_service.warning("检查刷新令牌失败", ex)
            return False

    def _blacklist_token(self, token: str, expire_time: int) -> None:
        """将令牌加入 Redis 黑名单，使其在剩余有效期内失效（使用原始字符串存储）"""
        try:
            key = f"blacklist:{token}"
            self._redis_service.set_raw(key, "1", expire_time)
        except Exception as ex:
            self._logger_service.warning("将令牌加入黑名单失败", ex)

    def _is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在 Redis 黑名单中"""
        try:
            key = f"blacklist:{token}"
            return self._redis_service.exists(key)
        except Exception as ex:
            self._logger_service.warning("检查令牌黑名单失败", ex)
            return False