"""
服务配置模块

集中管理所有依赖注入服务的注册配置。
在应用启动时由 main.py 调用 setup_services()，完成所有服务的注册。

注册的服务清单：
- IConfigService -> ConfigService（单例）：应用配置管理
- ILoggerService -> LoggerService（单例）：日志记录
- IRedisService -> RedisService（单例）：Redis 缓存
- ICodeExecutionService -> GlotService（作用域）：代码执行
- IOIDCService -> OIDCService（单例）：OAuth/OIDC 认证
- IJWTService -> JWTService（单例）：JWT 令牌管理
- DatabaseService（单例）：数据库操作
- UserService / IUserService（单例）：用户管理
"""

from core.di_container import configure_services, get_container
from services.config_service import ConfigService
from services.logger_service import LoggerService
from services.glot_service import GlotService
from services.oidc_service import OIDCService
from services.jwt_service import JWTService
from services.redis_service import RedisService
from services.database_service import DatabaseService
from services.user_service import UserService
from interfaces.service_interfaces import IConfigService, ILoggerService, ICodeExecutionService, IRedisService, IOIDCService, IJWTService, IUserService


def setup_services(app_config: dict) -> None:
    """
    初始化并注册所有依赖注入服务

    在应用启动时调用，将应用配置注入到各个服务中。
    此函数定义了服务之间的依赖关系和生命周期策略。

    Args:
        app_config: Flask 应用配置字典，包含所有运行时配置
    """

    def service_configurator(container):
        """服务注册配置器，在容器中注册所有服务"""

        # ---------- 核心服务（单例） ----------
        # 配置服务：管理所有应用配置，依赖于 app_config
        container.register_singleton(IConfigService,
                                  factory=lambda: ConfigService(app_config))
        # 日志服务：提供统一的日志记录接口
        container.register_singleton(ILoggerService,
                                  factory=lambda: LoggerService())
        # Redis 服务：缓存、会话管理和速率限制
        container.register_singleton(IRedisService, RedisService)
        # OIDC/OAuth 认证服务：管理第三方登录
        container.register_singleton(IOIDCService, OIDCService)
        # JWT 令牌服务：生成、验证和撤销令牌
        container.register_singleton(IJWTService, JWTService)

        # ---------- 作用域服务 ----------
        # 代码执行服务：每次请求独立实例，避免状态污染
        container.register_scoped(ICodeExecutionService, GlotService)

        # ---------- 数据库服务（单例，使用工厂延迟初始化） ----------
        # DatabaseService 和 UserService 依赖 ConfigService，使用工厂延迟创建
        def create_database_service():
            config_service = container.resolve(IConfigService)
            return DatabaseService(config_service)

        def create_user_service():
            config_service = container.resolve(IConfigService)
            return UserService(config_service)

        container.register_singleton(DatabaseService, factory=create_database_service)
        container.register_singleton(UserService, factory=create_user_service)
        container.register_singleton(IUserService, factory=create_user_service)

    configure_services(service_configurator)


def get_service(service_type):
    """
    从全局容器中获取指定类型的服务实例

    便捷函数，等价于 get_container().resolve(service_type)

    Args:
        service_type: 要获取的服务类型（接口类）

    Returns:
        服务实例
    """
    container = get_container()
    return container.resolve(service_type)
