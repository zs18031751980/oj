"""
服务接口和抽象基类模块

定义各种服务的抽象接口，提供可测试和可扩展的架构基础。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import os
from models.auth_models import JWTToken
from models.glot_models import CodeExecutionResponse


class IConfigService(ABC):
    """配置服务接口"""
    
    @abstractmethod
    def get_api_token(self) -> str:
        """获取API Token"""
        pass
    
    @abstractmethod
    def get_timeout(self) -> int:
        """获取请求超时时间"""
        pass
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass


class ICodeExecutionService(ABC):
    """代码执行服务接口"""
    
    @abstractmethod
    async def execute_code(self, request) -> CodeExecutionResponse:
        """执行代码"""
        pass


class ILoggerService(ABC):
    """日志服务接口"""
    
    @abstractmethod
    def info(self, message: str) -> None:
        """记录信息日志"""
        pass
    
    @abstractmethod
    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """记录错误日志"""
        pass
    
    @abstractmethod
    def warning(self, message: str) -> None:
        """记录警告日志"""
        pass
    
    @abstractmethod
    def debug(self, message: str) -> None:
        """记录调试日志"""
        pass


class IRedisService(ABC):
    """Redis 服务接口"""
    
    @abstractmethod
    def is_connected(self) -> bool:
        """检查是否连接到 Redis"""
        pass
    
    @abstractmethod
    def reconnect(self) -> bool:
        """重新连接到 Redis"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置键值对"""
        pass
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取键值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除键"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def expire(self, key: str, ttl: int) -> bool:
        """设置键的过期时间"""
        pass
    
    @abstractmethod
    def ttl(self, key: str) -> int:
        """获取键的剩余过期时间"""
        pass
    
    @abstractmethod
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        pass
    
    @abstractmethod
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """递减计数器"""
        pass
    
    @abstractmethod
    def set_add(self, key: str, *members: Any) -> bool:
        """向集合添加成员"""
        pass
    
    @abstractmethod
    def set_remove(self, key: str, *members: Any) -> bool:
        """从集合移除成员"""
        pass
    
    @abstractmethod
    def set_members(self, key: str) -> List[Any]:
        """获取集合所有成员"""
        pass
    
    @abstractmethod
    def set_is_member(self, key: str, member: Any) -> bool:
        """检查成员是否在集合中"""
        pass
    
    @abstractmethod
    def list_push(self, key: str, *values: Any) -> Optional[int]:
        """向列表左侧推送元素"""
        pass
    
    @abstractmethod
    def list_pop(self, key: str) -> Any:
        """从列表右侧弹出元素"""
        pass
    
    @abstractmethod
    def list_length(self, key: str) -> int:
        """获取列表长度"""
        pass
    
    @abstractmethod
    def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表范围内的元素"""
        pass
    
    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的所有键"""
        pass
    
    @abstractmethod
    def flushdb(self) -> bool:
        """清空当前数据库"""
        pass
    
    @abstractmethod
    def info(self) -> Optional[Dict[str, Any]]:
        """获取 Redis 服务器信息"""
        pass


class IOIDCService(ABC):
    """OIDC 认证服务接口"""
    
    @abstractmethod
    def initialize_oauth(self, app) -> None:
        """初始化 OAuth"""
        pass

    @abstractmethod
    def get_authorization_url(self, provider: str, redirect_uri: Optional[str] = None) -> Optional[str]:
        """
        获取授权URL
        
        Args:
            provider: 提供商名称 (如 'github')
            redirect_uri: 回调地址
            
        Returns:
            授权URL或None
        """
        pass

    @abstractmethod
    def get_authorization_redirect(self, provider: str, redirect_uri: str):
        """Create the browser redirect response for OAuth login."""
        pass

    @abstractmethod
    def authorize_callback(self, provider: str, redirect_uri: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        处理授权回调
        
        Args:
            provider: 提供商名称
            
        Returns:
            用户信息字典或None
        """
        pass

    @abstractmethod
    def get_supported_providers(self) -> List[str]:
        """获取支持的提供商列表"""
        pass

    @abstractmethod
    def validate_provider(self, provider: str) -> bool:
        """验证提供商是否支持"""
        pass
    @abstractmethod
    def resolve_provider_name(self, provider: str) -> Optional[str]:
        """Resolve a provider name to the configured canonical value."""
        pass


class IJWTService(ABC):
    """JWT 认证服务接口"""
    
    @abstractmethod
    def generate_tokens(self, user_info: Dict[str, Any]) -> JWTToken:
        """
        生成 JWT 令牌对
        
        Args:
            user_info: 用户信息字典
            
        Returns:
            JWT 令牌对象
        """
        pass

    @abstractmethod
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌
        
        Args:
            token: JWT 访问令牌
            
        Returns:
            用户信息或None
        """
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Optional[JWTToken]:
        """
        使用刷新令牌生成新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的JWT令牌对象或None
        """
        pass

    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """
        撤销令牌（加入黑名单）
        
        Args:
            token: 要撤销的令牌
            
        Returns:
            是否成功
        """
        pass


class IUserService(ABC):
    """用户服务接口"""
    
    @abstractmethod
    async def find_or_create_user(self, provider: str, provider_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据第三方登录信息查找或创建用户
        
        Args:
            provider: 登录提供商 (如 'github', 'oidc-provider')
            provider_id: 提供商的用户ID
            user_info: 用户信息字典
            
        Returns:
            用户信息字典
        """
        pass

    @abstractmethod
    async def get_user_with_password_hash_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名或邮箱获取包含密码哈希的用户信息

        Args:
            identifier: 用户名或邮箱

        Returns:
            用户认证信息字典或None
        """
        pass

    @abstractmethod
    async def update_user_last_login(self, user_id: int) -> bool:
        """
        更新用户最后登录时间

        Args:
            user_id: 用户ID

        Returns:
            是否更新成功
        """
        pass
