"""
日志服务实现

提供简单的日志记录功能。
"""

import logging
from typing import Optional
from interfaces.service_interfaces import ILoggerService


class LoggerService(ILoggerService):
    """日志服务实现"""
    
    def __init__(self, name: str = "letcoding", level: int = logging.INFO):
        """
        初始化日志服务
        
        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        self._logger = logging.getLogger(name)
        
        # 避免重复添加处理器
        if not self._logger.handlers:
            # 创建控制台处理器
            handler = logging.StreamHandler()
            
            # 创建格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # 添加处理器
            self._logger.addHandler(handler)
        
        self._logger.setLevel(level)
    
    def info(self, message: str) -> None:
        """记录信息日志"""
        self._logger.info(message)
    
    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """记录错误日志"""
        if exception:
            self._logger.error(f"{message}: {str(exception)}", exc_info=True)
        else:
            self._logger.error(message)
    
    def warning(self, message: str) -> None:
        """记录警告日志"""
        self._logger.warning(message)
    
    def debug(self, message: str) -> None:
        """记录调试日志"""
        self._logger.debug(message)