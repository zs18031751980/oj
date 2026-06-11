"""
服务配置模块

集中管理依赖注入的配置。
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
    """设置依赖注入服务"""
    
    def service_configurator(container):
        # 配置服务
        container.register_singleton(IConfigService, 
                                  factory=lambda: ConfigService(app_config))
        container.register_singleton(ILoggerService,
                                  factory=lambda: LoggerService())
        container.register_singleton(IRedisService, RedisService)
        container.register_scoped(ICodeExecutionService, GlotService)
        container.register_singleton(IOIDCService, OIDCService)
        container.register_singleton(IJWTService, JWTService)
        
        # 数据库服务（依赖于ConfigService）
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
    """获取指定类型的服务实例"""
    container = get_container()
    return container.resolve(service_type)
