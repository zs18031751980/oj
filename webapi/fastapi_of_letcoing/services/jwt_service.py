"""
JWT 认证服务

提供 JWT 令牌生成、验证和缓存功能（使用独立的 Redis 服务）
"""

import jwt
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from interfaces.service_interfaces import IConfigService, ILoggerService, IRedisService, IJWTService
from core.di_container import Injectable
from models.auth_models import JWTToken


class JWTService(Injectable, IJWTService):
    """JWT 认证服务"""
    
    def __init__(self, config_service: IConfigService, logger_service: ILoggerService, redis_service: IRedisService):
        self._config_service = config_service
        self._logger_service = logger_service
        self._redis_service = redis_service
        self._secret_key = self._config_service.get_config('JWT_SECRET_KEY', 'default-secret-key')
        self._algorithm = self._config_service.get_config('JWT_ALGORITHM', 'HS256')
        self._access_token_expire = self._config_service.get_config('JWT_ACCESS_TOKEN_EXPIRE', 3600)  # 1小时
        self._refresh_token_expire = self._config_service.get_config('JWT_REFRESH_TOKEN_EXPIRE', 86400 * 7)  # 7天
    

    
    def generate_tokens(self, user_info: Dict[str, Any]) -> JWTToken:
        """
        生成 JWT 令牌对
        
        Args:
            user_info: 用户信息字典
            
        Returns:
            JWT 令牌对象
        """
        now = datetime.utcnow()
        access_expire = now + timedelta(seconds=self._access_token_expire)
        refresh_expire = now + timedelta(seconds=self._refresh_token_expire)
        
        # 生成访问令牌
        access_payload = {
            'user_id': user_info['id'],
            'username': user_info.get('username', ''),
            'email': user_info.get('email', ''),
            'provider': user_info.get('provider', ''),
            'exp': access_expire,
            'iat': now,
            'type': 'access'
        }
        
        access_token = jwt.encode(access_payload, self._secret_key, algorithm=self._algorithm)
        
        # 生成刷新令牌
        refresh_payload = {
            'user_id': user_info['id'],
            'exp': refresh_expire,
            'iat': now,
            'type': 'refresh'
        }
        
        refresh_token = jwt.encode(refresh_payload, self._secret_key, algorithm=self._algorithm)
        
        # 缓存用户信息
        self._cache_user_info(user_info['id'], user_info)
        
        # 缓存刷新令牌
        self._cache_refresh_token(user_info['id'], refresh_token)
        
        return JWTToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_token_expire
        )
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌
        
        Args:
            token: JWT 访问令牌
            
        Returns:
            用户信息或None
        """
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            
            # 检查令牌类型
            if payload.get('type') != 'access':
                self._logger_service.warning("令牌类型不匹配")
                return None
            
            # 检查是否在黑名单中
            if self._is_token_blacklisted(token):
                self._logger_service.warning("令牌已被撤销")
                return None
            
            # 从缓存获取用户信息
            user_info = self._get_cached_user_info(payload['user_id'])
            if user_info:
                return user_info
            
            # 如果缓存中没有，返回基本信息
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
        使用刷新令牌生成新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的JWT令牌对象或None
        """
        try:
            payload = jwt.decode(refresh_token, self._secret_key, algorithms=[self._algorithm])
            
            # 检查令牌类型
            if payload.get('type') != 'refresh':
                self._logger_service.warning("令牌类型不匹配")
                return None
            
            user_id = payload['user_id']
            
            # 检查刷新令牌是否有效
            if not self._is_valid_refresh_token(user_id, refresh_token):
                self._logger_service.warning("无效的刷新令牌")
                return None
            
            # 获取用户信息
            user_info = self._get_cached_user_info(user_id)
            if not user_info:
                self._logger_service.warning("用户信息不存在")
                return None
            
            # 生成新的令牌对
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
        撤销令牌（加入黑名单）
        
        Args:
            token: 要撤销的令牌
            
        Returns:
            是否成功
        """
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            exp = payload.get('exp', 0)
            remaining_time = int(exp - time.time())
            
            if remaining_time > 0:
                # 将令牌加入黑名单
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
    
    def _cache_user_info(self, user_id: str, user_info: Dict[str, Any]) -> None:
        """缓存用户信息"""
        try:
            key = f"user:{user_id}"
            self._redis_service.set(key, user_info, self._refresh_token_expire)
        except Exception as ex:
            self._logger_service.warning("缓存用户信息失败", ex)
    
    def _get_cached_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的用户信息"""
        try:
            key = f"user:{user_id}"
            return self._redis_service.get(key)
        except Exception as ex:
            self._logger_service.warning("获取缓存的用户信息失败", ex)
            return None
    
    def _cache_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """缓存刷新令牌"""
        try:
            key = f"refresh_token:{user_id}"
            self._redis_service.set(key, refresh_token, self._refresh_token_expire)
        except Exception as ex:
            self._logger_service.warning("缓存刷新令牌失败", ex)
    
    def _is_valid_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """检查刷新令牌是否有效"""
        try:
            key = f"refresh_token:{user_id}"
            cached_token = self._redis_service.get(key)
            return cached_token == refresh_token
        except Exception as ex:
            self._logger_service.warning("检查刷新令牌失败", ex)
            return False
    
    def _blacklist_token(self, token: str, expire_time: int) -> None:
        """将令牌加入黑名单"""
        try:
            key = f"blacklist:{token}"
            self._redis_service.set(key, "1", expire_time)
        except Exception as ex:
            self._logger_service.warning("将令牌加入黑名单失败", ex)
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        try:
            key = f"blacklist:{token}"
            return self._redis_service.exists(key)
        except Exception as ex:
            self._logger_service.warning("检查令牌黑名单失败", ex)
            return False