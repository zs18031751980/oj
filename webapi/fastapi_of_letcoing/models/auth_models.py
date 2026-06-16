"""
认证相关数据模型模块

定义了认证流程中使用的所有数据结构，包括：
- JWTToken: JWT 令牌对象（访问令牌 + 刷新令牌）
- UserInfo: 用户信息模型
- LoginRequest / LoginResponse: 登录请求与响应
- TokenResponse: 令牌响应（含用户信息）
- RefreshTokenRequest: 刷新令牌请求
- AuthCallbackRequest / AuthResult: OAuth 回调请求与结果
- OIDCProviderConfig: OIDC 提供商配置
"""

from dataclasses import dataclass, field
import time
from typing import Optional, Dict, List, Any
from datetime import datetime


class JWTToken:
    """
    JWT 令牌数据模型

    封装了完整的 JWT 认证令牌信息，包括访问令牌和刷新令牌。
    访问令牌用于 API 请求的身份验证，刷新令牌用于获取新的访问令牌。
    """

    def __init__(self, access_token: str, refresh_token: str,
                 expires_in: int, token_type: str = "Bearer"):
        """
        Args:
            access_token: 访问令牌（Access Token），用于 API 请求认证
            refresh_token: 刷新令牌（Refresh Token），用于续期
            expires_in: 访问令牌的有效期（秒）
            token_type: 令牌类型，默认为 Bearer
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
        self.token_type = token_type
        self.created_at = time.time()  # 令牌创建时间戳

    def to_dict(self) -> Dict[str, Any]:
        """将令牌对象转换为字典格式（用于 API 响应序列化）"""
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': self.expires_in,
            'token_type': self.token_type
        }


@dataclass
class UserInfo:
    """
    用户信息数据模型

    标准化用户信息格式，无论用户通过何种方式登录，都统一为此格式。
    用于 JWT 令牌载荷和 API 响应中的用户数据。
    """
    id: str                        # 用户唯一标识
    username: str                  # 用户名
    email: str                     # 电子邮箱
    name: str = ""                 # 显示名称
    avatar_url: str = ""           # 头像 URL
    provider: str = ""             # 登录提供商（如 github, password）
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间

    def to_dict(self) -> Dict[str, Any]:
        """将用户信息转换为字典格式"""
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
    """OAuth 登录请求模型"""
    provider: str                            # 认证提供商名称
    redirect_uri: Optional[str] = None       # 自定义回调地址（可选）

    def to_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider,
            'redirect_uri': self.redirect_uri
        }


@dataclass
class LoginResponse:
    """OAuth 登录响应模型"""
    success: bool                             # 操作是否成功
    authorization_url: Optional[str] = None   # OAuth 授权 URL
    error: Optional[str] = None               # 错误信息

    def to_dict(self) -> Dict[str, Any]:
        result = {'success': self.success}
        if self.authorization_url:
            result['authorization_url'] = self.authorization_url
        if self.error:
            result['error'] = self.error
        return result


@dataclass
class TokenResponse:
    """
    令牌响应数据模型

    包含完整的认证信息：访问令牌、刷新令牌以及用户信息。
    在登录成功或令牌刷新成功时返回给客户端。
    """
    access_token: str                          # 访问令牌
    refresh_token: str                         # 刷新令牌
    expires_in: int                            # 访问令牌有效期（秒）
    token_type: str = "Bearer"                 # 令牌类型
    user_info: Optional[UserInfo] = None       # 用户信息（可选）

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
    refresh_token: str                         # 刷新令牌字符串

    def to_dict(self) -> Dict[str, Any]:
        return {
            'refresh_token': self.refresh_token
        }


@dataclass
class AuthCallbackRequest:
    """
    OAuth 回调请求模型

    封装了 OAuth 提供商在回调时携带的参数，
    包括授权码、状态值以及可能的错误信息。
    """
    provider: str                              # 认证提供商名称
    code: Optional[str] = None                 # 授权码（成功时返回）
    state: Optional[str] = None                # CSRF 防护状态值
    error: Optional[str] = None                # 错误代码（失败时返回）
    error_description: Optional[str] = None    # 错误描述

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
    """
    认证结果模型

    封装完整的认证结果，用于在认证流程的不同阶段传递数据。
    """
    success: bool                              # 认证是否成功
    user_info: Optional[UserInfo] = None       # 用户信息
    tokens: Optional[TokenResponse] = None     # JWT 令牌
    error: Optional[str] = None                # 错误信息

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
    """
    OIDC 提供商配置数据模型

    定义了连接 OIDC/OAuth 2.0 提供商所需的完整配置信息。
    支持标准 OIDC 发现协议（通过 server_metadata_url）和手动配置。
    """
    name: str                                  # 提供商名称
    client_id: str                             # OAuth 客户端 ID
    client_secret: str                         # OAuth 客户端密钥
    server_metadata_url: Optional[str] = None  # OIDC 发现端点（获取服务元数据）
    access_token_url: Optional[str] = None     # 令牌端点 URL（OAuth 2.0 方式）
    authorize_url: Optional[str] = None        # 授权端点 URL
    api_base_url: Optional[str] = None         # API 基础地址（用于获取用户信息）
    client_kwargs: Dict[str, Any] = field(default_factory=dict)  # 客户端额外参数（如 scope）

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