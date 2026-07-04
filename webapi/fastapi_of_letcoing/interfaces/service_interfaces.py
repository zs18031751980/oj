"""
服务接口与抽象基类模块

该模块定义了所有核心服务的抽象接口（契约），
通过 Python 的 ABC（Abstract Base Class）机制实现。
这种设计模式带来的好处：
1. 接口与实现分离：业务逻辑依赖接口而非具体实现
2. 易于测试：可以轻松创建 Mock/Stub 实现
3. 灵活扩展：可以替换任意的服务实现而不影响调用方

定义的接口：
- IConfigService: 应用配置管理
- ICodeExecutionService: 远程代码执行
- ILoggerService: 日志记录
- IRedisService: Redis 缓存操作
- IOIDCService: OAuth/OIDC 第三方登录
- IJWTService: JWT 令牌管理
- IUserService: 用户数据管理
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import os
from models.auth_models import JWTToken
from models.glot_models import CodeExecutionResponse


class IConfigService(ABC):
    """
    配置服务接口

    提供统一的配置访问方式，支持从应用配置和环境变量中读取配置。
    所有服务的配置都应该通过此接口获取。
    """

    @abstractmethod
    def get_api_token(self) -> str:
        """获取用于 Glot.io 代码执行服务的 API Token"""
        pass

    @abstractmethod
    def get_timeout(self) -> int:
        """获取 HTTP 请求的超时时间（秒）"""
        pass

    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取指定配置键的值

        Args:
            key: 配置键名
            default: 配置不存在时返回的默认值

        Returns:
            配置值（可能是字符串、数字、字典等）
        """
        pass


class ICodeExecutionService(ABC):
    """
    代码执行服务接口

    定义远程代码执行的能力，支持多种编程语言。
    当前实现使用 Glot.io API 作为后端执行引擎。
    """

    @abstractmethod
    async def execute_code(self, request) -> CodeExecutionResponse:
        """
        异步执行代码

        Args:
            request: 代码执行请求对象（包含源代码、语言和标准输入）

        Returns:
            CodeExecutionResponse 对象（包含标准输出、错误输出和执行状态）
        """
        pass


class ILoggerService(ABC):
    """
    日志服务接口

    提供不同级别的日志记录能力，包括信息、错误、警告和调试级别。
    所有日志输出统一格式，便于监控和故障排查。
    """

    @abstractmethod
    def info(self, message: str) -> None:
        """记录信息级别的日志，用于正常的操作记录"""
        pass

    @abstractmethod
    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        记录错误级别的日志

        Args:
            message: 错误描述
            exception: 关联的异常对象（可选），会记录完整的堆栈信息
        """
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """记录警告级别的日志，用于需要注意但不致命的异常情况"""
        pass

    @abstractmethod
    def debug(self, message: str) -> None:
        """记录调试级别的日志，用于开发和排查问题时的详细信息"""
        pass


class IRedisService(ABC):
    """
    Redis 缓存服务接口

    提供完整的 Redis 数据结构操作能力，支持：
    - 键值对操作（set / get / delete / exists）
    - 过期时间管理（expire / ttl）
    - 计数器（increment / decrement）
    - 集合操作（Set）
    - 列表操作（List）
    - 键管理（keys / flushdb）
    - 服务器信息（info）
    """

    @abstractmethod
    def is_connected(self) -> bool:
        """检查当前是否与 Redis 服务器保持连接"""
        pass

    @abstractmethod
    def reconnect(self) -> bool:
        """
        重新连接到 Redis 服务器

        在连接断开时尝试重新建立连接。
        Returns:
            是否重新连接成功
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置键值对

        Args:
            key: 键名
            value: 值（会被序列化为 JSON 字符串存储）
            ttl: 过期时间，单位秒（可选）

        Returns:
            是否设置成功
        """
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        根据键名获取存储的值

        Args:
            key: 键名
            default: 键不存在时返回的默认值

        Returns:
            反序列化后的值，或默认值
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除指定的键，成功返回 True"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查指定的键是否存在于 Redis 中"""
        pass

    @abstractmethod
    def expire(self, key: str, ttl: int) -> bool:
        """
        为指定的键设置过期时间

        Args:
            key: 键名
            ttl: 过期时间，单位秒
        """
        pass

    @abstractmethod
    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间

        Returns:
            >0: 剩余秒数
            -1: 键存在但无过期时间
            -2: 键不存在
        """
        pass

    @abstractmethod
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        对键存储的数值进行递增操作（原子操作）

        Args:
            key: 键名
            amount: 递增量（默认 1）

        Returns:
            递增后的数值，失败返回 None
        """
        pass

    @abstractmethod
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        对键存储的数值进行递减操作（原子操作）

        Args:
            key: 键名
            amount: 递减量（默认 1）

        Returns:
            递减后的数值，失败返回 None
        """
        pass

    @abstractmethod
    def set_add(self, key: str, *members: Any) -> bool:
        """向集合（Set）中添加一个或多个成员"""
        pass

    @abstractmethod
    def set_remove(self, key: str, *members: Any) -> bool:
        """从集合（Set）中移除一个或多个成员"""
        pass

    @abstractmethod
    def set_members(self, key: str) -> List[Any]:
        """获取集合（Set）中的所有成员"""
        pass

    @abstractmethod
    def set_is_member(self, key: str, member: Any) -> bool:
        """检查指定成员是否存在于集合（Set）中"""
        pass

    @abstractmethod
    def list_push(self, key: str, *values: Any) -> Optional[int]:
        """
        向列表（List）的左侧推入一个或多个元素

        Returns:
            推入后的列表长度，失败返回 None
        """
        pass

    @abstractmethod
    def list_pop(self, key: str) -> Any:
        """从列表（List）的右侧弹出一个元素"""
        pass

    @abstractmethod
    def list_length(self, key: str) -> int:
        """获取列表（List）的长度"""
        pass

    @abstractmethod
    def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        获取列表（List）中指定范围内的元素

        Args:
            start: 起始索引（从 0 开始）
            end: 结束索引（-1 表示最后一个元素）
        """
        pass

    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """
        查找所有匹配指定模式的键

        Args:
            pattern: 匹配模式，支持通配符（如 user:*）

        Returns:
            匹配的键名列表
        """
        pass

    @abstractmethod
    def flushdb(self) -> bool:
        """清空当前 Redis 数据库中的所有数据（慎用）"""
        pass

    @abstractmethod
    def info(self) -> Optional[Dict[str, Any]]:
        """获取 Redis 服务器的信息和统计数据"""
        pass


class IOIDCService(ABC):
    """
    OIDC/OAuth 认证服务接口

    管理第三方登录提供商（如 GitHub、Google 等）的 OAuth 认证流程。
    支持标准的 OIDC（OpenID Connect）协议和 OAuth 2.0 协议。
    """

    @abstractmethod
    def initialize_oauth(self, app) -> None:
        """
        初始化 OAuth 认证服务

        在应用启动时调用，注册所有已配置的 OAuth 提供商。
        包括内置的 GitHub OAuth 和自定义 OIDC 提供商。

        Args:
            app: Flask 应用实例
        """
        pass

    @abstractmethod
    def get_authorization_url(self, provider: str, redirect_uri: Optional[str] = None) -> Optional[str]:
        """
        获取 OAuth 授权 URL（供 API 客户端使用）

        API 客户端可以通过此 URL 引导用户跳转到第三方登录页面。

        Args:
            provider: 提供商名称（如 'github'）
            redirect_uri: 登录成功后的回调地址（可选）

        Returns:
            OAuth 授权 URL，失败返回 None
        """
        pass

    @abstractmethod
    def get_authorization_redirect(self, provider: str, redirect_uri: str):
        """
        创建浏览器重定向响应（供浏览器使用）

        直接返回 Flask 重定向响应，浏览器接收到后会自动跳转到第三方登录页面。

        Args:
            provider: 提供商名称
            redirect_uri: 登录成功后的回调地址

        Returns:
            Flask 重定向响应对象
        """
        pass

    @abstractmethod
    def authorize_callback(self, provider: str, redirect_uri: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        处理 OAuth 授权回调

        接收第三方提供商回调的授权码（code），向提供商交换访问令牌，
        然后获取用户信息。

        Args:
            provider: 提供商名称
            redirect_uri: 回调地址（应与授权时使用的地址一致）

        Returns:
            包含 token 和 user_info 的字典，失败返回 None
        """
        pass

    @abstractmethod
    def get_supported_providers(self) -> List[str]:
        """获取当前已配置的所有认证提供商名称列表"""
        pass

    @abstractmethod
    def validate_provider(self, provider: str) -> bool:
        """检查指定的提供商是否已配置且受支持"""
        pass

    @abstractmethod
    def resolve_provider_name(self, provider: str) -> Optional[str]:
        """
        将提供商名称解析为配置中的规范名称（大小写不敏感匹配）

        Args:
            provider: 用户传入的提供商名称（可能大小写不一致）

        Returns:
            配置中的规范名称，未找到返回 None
        """
        pass


class IJWTService(ABC):
    """
    JWT 认证服务接口

    负责 JWT（JSON Web Token）的完整生命周期管理：
    - 生成访问令牌（Access Token）和刷新令牌（Refresh Token）
    - 验证访问令牌的有效性
    - 使用刷新令牌续期
    - 撤销令牌（加入黑名单）
    - 使用 Redis 缓存令牌和用户信息
    """

    @abstractmethod
    def generate_tokens(self, user_info: Dict[str, Any]) -> JWTToken:
        """
        生成 JWT 令牌对（访问令牌 + 刷新令牌）

        Args:
            user_info: 用户信息字典（必须包含 id、username、email 等字段）

        Returns:
            JWT 令牌对象，包含 access_token 和 refresh_token
        """
        pass

    @abstractmethod
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌的有效性

        执行以下验证：
        1. 签名验证
        2. 过期时间检查
        3. 令牌类型检查（必须为 access 类型）
        4. 黑名单检查

        Args:
            token: JWT 访问令牌字符串

        Returns:
            令牌中的用户信息字典，验证失败返回 None
        """
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Optional[JWTToken]:
        """
        使用刷新令牌获取新的访问令牌

        验证刷新令牌的有效性后，生成新的令牌对。
        旧的刷新令牌仍然有效（轮换策略由实现决定）。

        Args:
            refresh_token: 刷新令牌字符串

        Returns:
            新的 JWT 令牌对象，验证失败返回 None
        """
        pass

    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """
        撤销指定的访问令牌

        将令牌加入 Redis 黑名单，使其在剩余有效期内失效。

        Args:
            token: 要撤销的 JWT 令牌

        Returns:
            是否成功撤销
        """
        pass

    @abstractmethod
    def refresh_cached_user(self, user_id: str, user_info: Dict[str, Any]) -> None:
        """
        更新 Redis 中缓存的用户信息

        当用户修改个人设置（如主题偏好）后，调用此方法更新缓存，
        避免下次令牌验证时返回过期数据。

        Args:
            user_id: 用户 ID
            user_info: 更新后的用户信息字典
        """
        pass


class IUserService(ABC):
    """
    用户服务接口

    管理用户的持久化存储，支持：
    - 第三方登录用户的查找和创建
    - 本地用户名/邮箱密码登录
    - 用户信息的查询和更新
    """

    @abstractmethod
    async def find_or_create_user(self, provider: str, provider_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据第三方登录信息查找或创建用户

        如果用户已存在则更新信息，否则创建新用户。

        Args:
            provider: 登录提供商（如 'github'）
            provider_id: 提供商侧的用户唯一标识
            user_info: 来自提供商的用户信息

        Returns:
            用户信息字典（统一格式）
        """
        pass

    @abstractmethod
    async def get_user_with_password_hash_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名或邮箱获取包含密码哈希的用户认证信息

        用于本地密码登录时验证用户身份。

        Args:
            identifier: 用户名或邮箱地址

        Returns:
            包含密码哈希的用户信息字典，用户不存在返回 None
        """
        pass

    @abstractmethod
    async def update_user_last_login(self, user_id: int) -> bool:
        """
        更新用户的最后登录时间

        Args:
            user_id: 用户 ID

        Returns:
            是否更新成功
        """
        pass
