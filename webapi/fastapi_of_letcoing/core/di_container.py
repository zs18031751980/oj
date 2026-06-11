"""
依赖注入容器模块

提供简单的依赖注入功能，支持服务注册、解析和生命周期管理。
"""

import inspect
from typing import Any, Dict, Type, TypeVar, Callable, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum

T = TypeVar('T')


class ServiceLifetime(Enum):
    """服务生命周期枚举"""
    SINGLETON = "singleton"  # 单例模式
    TRANSIENT = "transient"  # 每次请求都创建新实例
    SCOPED = "scoped"       # 作用域内单例（Flask请求级别）


class ServiceDescriptor:
    """服务描述符"""
    
    def __init__(
        self,
        service_type: Type,
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ):
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        
        # 验证参数
        if sum(bool(x) for x in [implementation_type, factory, instance]) != 1:
            raise ValueError("必须且只能提供 implementation_type, factory, 或 instance 中的一个")


class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
    
    def register_singleton(
        self, 
        service_type: Type[T], 
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None
    ) -> 'DIContainer':
        """注册单例服务"""
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
        """注册瞬态服务"""
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
        """注册作用域服务"""
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
        """解析服务"""
        if service_type not in self._services:
            raise ValueError(f"服务 {service_type} 未注册")
        
        descriptor = self._services[service_type]
        
        # 处理单例
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singleton_instances:
                return self._singleton_instances[service_type]
            
            instance = self._create_instance(descriptor)
            self._singleton_instances[service_type] = instance
            return instance
        
        # 处理作用域
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]
            
            instance = self._create_instance(descriptor)
            self._scoped_instances[service_type] = instance
            return instance
        
        # 处理瞬态
        else:
            return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例"""
        # 如果有预定义实例
        if descriptor.instance is not None:
            return descriptor.instance
        
        # 如果有工厂方法
        if descriptor.factory is not None:
            return descriptor.factory()
        
        # 如果有实现类型
        if descriptor.implementation_type is not None:
            return self._create_with_injection(descriptor.implementation_type)
        
        raise ValueError(f"无法创建服务 {descriptor.service_type} 的实例")
    
    def _create_with_injection(self, implementation_type: Type) -> Any:
        """通过构造函数注入创建实例"""
        # 获取构造函数参数
        sig = inspect.signature(implementation_type.__init__)
        
        # 准备参数
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # 尝试解析参数类型
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation
                if param_type in self._services:
                    kwargs[param_name] = self.resolve(param_type)
            # 如果有默认值，使用默认值
            elif param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
        
        return implementation_type(**kwargs)
    
    def clear_scope(self):
        """清除作用域实例（通常在请求结束时调用）"""
        self._scoped_instances.clear()
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services


# 全局容器实例
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = DIContainer()
        _register_default_services(_container)
    return _container


def _register_default_services(container: DIContainer) -> None:
    """注册默认服务"""
    # 注册数据库配置
    from core.db_config import DatabaseConfig
    container.register_singleton(DatabaseConfig)
    
    # 注意：DatabaseService 在 setup_services 中注册，因为它依赖于 IConfigService


def configure_services(configurator: Callable[[DIContainer], None]) -> None:
    """配置服务"""
    container = get_container()
    configurator(container)


def inject(service_type: Type[T]) -> T:
    """依赖注入装饰器辅助函数"""
    container = get_container()
    return container.resolve(service_type)


class Injectable(ABC):
    """可注入服务的抽象基类"""
    pass