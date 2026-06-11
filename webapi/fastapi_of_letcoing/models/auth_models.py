"""
认证相关的数据模型
"""

from dataclasses import dataclass, field
import time
from typing import Optional, Dict, List, Any
from datetime import datetime

class JWTToken:
    """JWT 令牌数据模型"""
    
    def __init__(self, access_token: str, refresh_token: str, 
                 expires_in: int, token_type: str = "Bearer"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
        self.token_type = token_type
        self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': self.expires_in,
            'token_type': self.token_type
        }

@dataclass
class UserInfo:
    """用户信息模型"""
    id: str
    username: str
    email: str
    name: str = ""
    avatar_url: str = ""
    provider: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'avatar_url': self.avatar_url,
            'provider': self.provider,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class LoginRequest:
    """登录请求模型"""
    provider: str
    redirect_uri: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider,
            'redirect_uri': self.redirect_uri
        }


@dataclass
class LoginResponse:
    """登录响应模型"""
    success: bool
    authorization_url: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'success': self.success}
        if self.authorization_url:
            result['authorization_url'] = self.authorization_url
        if self.error:
            result['error'] = self.error
        return result


@dataclass
class TokenResponse:
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    user_info: Optional[UserInfo] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': self.expires_in,
            'token_type': self.token_type
        }
        if self.user_info:
            result['user_info'] = self.user_info.to_dict()
        return result


@dataclass
class RefreshTokenRequest:
    """刷新令牌请求模型"""
    refresh_token: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'refresh_token': self.refresh_token
        }


@dataclass
class AuthCallbackRequest:
    """认证回调请求模型"""
    provider: str
    code: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'provider': self.provider}
        if self.code:
            result['code'] = self.code
        if self.state:
            result['state'] = self.state
        if self.error:
            result['error'] = self.error
        if self.error_description:
            result['error_description'] = self.error_description
        return result


@dataclass
class AuthResult:
    """认证结果模型"""
    success: bool
    user_info: Optional[UserInfo] = None
    tokens: Optional[TokenResponse] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'success': self.success}
        if self.user_info:
            result['user_info'] = self.user_info.to_dict()
        if self.tokens:
            result['tokens'] = self.tokens.to_dict()
        if self.error:
            result['error'] = self.error
        return result


@dataclass
class OIDCProviderConfig:
    """OIDC 提供商配置模型"""
    name: str
    client_id: str
    client_secret: str
    server_metadata_url: Optional[str] = None
    access_token_url: Optional[str] = None
    authorize_url: Optional[str] = None
    api_base_url: Optional[str] = None
    client_kwargs: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'name': self.name,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        if self.server_metadata_url:
            result['server_metadata_url'] = self.server_metadata_url
        if self.access_token_url:
            result['access_token_url'] = self.access_token_url
        if self.authorize_url:
            result['authorize_url'] = self.authorize_url
        if self.api_base_url:
            result['api_base_url'] = self.api_base_url
        if self.client_kwargs:
            result['client_kwargs'] = self.client_kwargs
        return result