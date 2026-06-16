"""
依赖注入容器模块

提供轻量级的依赖注入（DI）功能，支持以下三种服务生命周期：
- SINGLETON（单例）：整个应用生命周期内只有一个实例
- TRANSIENT（瞬态）：每次解析都创建新的实例
- SCOPED（作用域）：在同一个请求作用域内共享同一实例

使用方式：
    1. 通过 register_* 方法注册服务
    2. 通过 resolve 方法解析服务实例
    3. 通过 inject 便捷函数快速获取服务
"""

import inspect
from typing import Any, Dict, Type, TypeVar, Callable, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum

T = TypeVar('T')


class ServiceLifetime(Enum):
    """服务生命周期枚举，定义了服务实例的创建和缓存策略"""
    SINGLETON = "singleton"  # 单例模式：全局唯一实例，应用启动时创建，直到应用关闭
    TRANSIENT = "transient"  # 瞬态模式：每次请求都创建新的实例，不缓存
    SCOPED = "scoped"        # 作用域模式：在每个 Flask 请求范围内共享同一实例，请求结束时清除


class ServiceDescriptor:
    """
    服务描述符

    记录一个服务的注册信息，包括：
    - 服务类型（接口/抽象类）
    - 实现类型（具体类）
    - 工厂函数（用于创建实例）
    - 预置实例（直接使用已有对象）
    - 生命周期策略

    注意：implementation_type、factory、instance 三者只能且必须提供一个。
    """

    def __init__(
        self,
        service_type: Type,
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ):
        self.service_type = service_type          # 服务接口/抽象类类型
        self.implementation_type = implementation_type  # 具体实现类型
        self.factory = factory                    # 工厂函数（延迟创建实例）
        self.instance = instance                  # 预置的实例对象
        self.lifetime = lifetime                  # 生命周期策略

        # 验证：只能提供 implementation_type、factory、instance 中的一个
        if sum(bool(x) for x in [implementation_type, factory, instance]) != 1:
            raise ValueError("必须且只能提供 implementation_type, factory, 或 instance 中的一个")


class DIContainer:
    """
    依赖注入容器

    核心功能：
    - 服务注册：支持单例、瞬态、作用域三种注册方式
    - 服务解析：根据类型自动解析依赖关系，支持构造函数注入
    - 生命周期管理：自动缓存单例和作用域实例，提供 clear_scope 方法
    """

    def __init__(self):
        # 存储所有注册的服务描述符，键为服务类型（接口类）
        self._services: Dict[Type, ServiceDescriptor] = {}
        # 缓存单例实例，首次解析后缓存，后续直接返回
        self._singleton_instances: Dict[Type, Any] = {}
        # 缓存作用域实例，在同一个请求内共享
        self._scoped_instances: Dict[Type, Any] = {}

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None
    ) -> 'DIContainer':
        """
        注册单例服务

        单例服务在整个应用生命周期内只有一份实例，适用于：
        - 配置服务（ConfigService）
        - 日志服务（LoggerService）
        - 数据库连接池等资源密集型服务

        Returns:
            self，支持链式调用
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        self._services[service_type] = descriptor
        return self

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'DIContainer':
        """
        注册瞬态服务

        瞬态服务每次被请求时都会创建新实例，适用于：
        - 轻量级、无状态的服务
        - 需要隔离每次请求状态的服务

        Returns:
            self，支持链式调用
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=None,
            lifetime=ServiceLifetime.TRANSIENT
        )
        self._services[service_type] = descriptor
        return self

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'DIContainer':
        """
        注册作用域服务

        作用域服务在同一个 Flask 请求内共享同一实例，请求结束后自动清除，适用于：
        - 需要在整个请求生命周期内保持状态的服务
        - 数据库会话（Session）等需要事务一致性的场景

        Returns:
            self，支持链式调用
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=None,
            lifetime=ServiceLifetime.SCOPED
        )
        self._services[service_type] = descriptor
        return self

    def resolve(self, service_type: Type[T]) -> T:
        """
        解析服务实例

        根据服务类型查找对应的描述符，按照生命周期策略创建或返回缓存的实例。
        如果实例需要构造函数注入，会自动解析其依赖的其他服务。

        Args:
            service_type: 要解析的服务类型（接口或抽象类）

        Returns:
            服务实例

        Raises:
            ValueError: 如果服务未注册
        """
        if service_type not in self._services:
            raise ValueError(f"服务 {service_type} 未注册")

        descriptor = self._services[service_type]

        # 单例模式：检查缓存，如果没有则创建并缓存
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singleton_instances:
                return self._singleton_instances[service_type]

            instance = self._create_instance(descriptor)
            self._singleton_instances[service_type] = instance
            return instance

        # 作用域模式：检查作用域缓存，如果没有则创建并缓存
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]

            instance = self._create_instance(descriptor)
            self._scoped_instances[service_type] = instance
            return instance

        # 瞬态模式：每次都创建新实例
        else:
            return self._create_instance(descriptor)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """
        根据服务描述符创建实例

        创建优先级：
        1. 如果有预置实例，直接返回
        2. 如果有工厂函数，调用工厂函数
        3. 如果有实现类型，通过构造函数注入创建

        Args:
            descriptor: 服务描述符

        Returns:
            创建的服务实例
        """
        # 优先级 1：使用预置实例
        if descriptor.instance is not None:
            return descriptor.instance

        # 优先级 2：使用工厂函数创建
        if descriptor.factory is not None:
            return descriptor.factory()

        # 优先级 3：通过构造函数注入创建
        if descriptor.implementation_type is not None:
            return self._create_with_injection(descriptor.implementation_type)

        raise ValueError(f"无法创建服务 {descriptor.service_type} 的实例")

    def _create_with_injection(self, implementation_type: Type) -> Any:
        """
        通过构造函数注入创建实例

        自动分析构造函数的参数类型，并在容器中查找对应的服务进行注入。
        如果参数有默认值且未注册，则使用默认值。

        Args:
            implementation_type: 实现类的类型

        Returns:
            创建并注入依赖后的实例
        """
        sig = inspect.signature(implementation_type.__init__)

        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 如果参数有类型注解，尝试从容器中解析
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation
                if param_type in self._services:
                    kwargs[param_name] = self.resolve(param_type)
            # 如果参数有默认值且未在容器中注册，使用默认值
            elif param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default

        return implementation_type(**kwargs)

    def clear_scope(self):
        """
        清除所有作用域实例

        通常在每次 HTTP 请求结束时调用，以确保下一个请求获取新的实例。
        """
        self._scoped_instances.clear()

    def is_registered(self, service_type: Type) -> bool:
        """检查指定类型的服务是否已注册"""
        return service_type in self._services


# ============================================================
# 全局容器实例及便捷函数
# ============================================================

# 全局唯一的容器实例（模块级变量）
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """
    获取全局的依赖注入容器实例

    使用单例模式确保整个应用共享同一个容器。
    首次调用时会自动创建容器并注册默认服务。
    """
    global _container
    if _container is None:
        _container = DIContainer()
        _register_default_services(_container)
    return _container


def _register_default_services(container: DIContainer) -> None:
    """
    注册框架默认的服务

    注意：DatabaseService 等依赖于完整应用配置的服务在
    setup_services() 中注册，因为那时 app.config 才可用。
    """
    from core.db_config import DatabaseConfig
    container.register_singleton(DatabaseConfig)


def configure_services(configurator: Callable[[DIContainer], None]) -> None:
    """
    通过配置函数注册服务

    Args:
        configurator: 接收 DIContainer 并进行服务注册的回调函数
    """
    container = get_container()
    configurator(container)


def inject(service_type: Type[T]) -> T:
    """
    便捷函数：从全局容器中解析服务

    这是最常用的依赖获取方式，等价于：
        container = get_container()
        return container.resolve(service_type)

    Args:
        service_type: 要获取的服务类型

    Returns:
        服务实例
    """
    container = get_container()
    return container.resolve(service_type)


class Injectable(ABC):
    """
    可注入服务的抽象基类

    所有可以通过依赖注入容器管理的服务类都应继承此类。
    这提供了统一的类型标识，但不强制任何抽象方法。
    """
    pass