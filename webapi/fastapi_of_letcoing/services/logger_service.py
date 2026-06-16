"""
日志服务实现模块

基于 Python 标准库 logging 模块的日志服务实现。
提供统一格式的日志输出，支持四个日志级别：DEBUG、INFO、WARNING、ERROR。

日志格式：时间戳 - 名称 - 级别 - 消息
示例：2024-01-01 12:00:00,000 - letcoding - INFO - 服务启动成功
"""

import logging
from typing import Optional
from interfaces.service_interfaces import ILoggerService


class LoggerService(ILoggerService):
    """
    日志服务实现类

    封装 Python 标准库的 logging 模块，提供简洁的日志接口。
    默认输出到控制台（stdout），日志级别为 INFO。
    错误日志支持记录异常堆栈信息，便于调试和故障排查。
    """

    def __init__(self, name: str = "letcoding", level: int = logging.INFO):
        """
        初始化日志服务

        Args:
            name: 日志记录器的名称（用于区分不同模块的日志）
            level: 日志级别，默认为 INFO（只记录 INFO 及以上级别的日志）
        """
        self._logger = logging.getLogger(name)

        # 避免重复添加处理器（防止多次初始化时重复输出）
        if not self._logger.handlers:
            # 创建控制台处理器（输出到标准输出流）
            handler = logging.StreamHandler()

            # 设置日志格式：时间 - 名称 - 级别 - 消息
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

        self._logger.setLevel(level)

    def info(self, message: str) -> None:
        """记录信息级别的日志，用于正常的业务操作记录"""
        self._logger.info(message)

    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        记录错误级别的日志

        如果提供了异常对象，会自动记录完整的调用堆栈信息。

        Args:
            message: 错误描述消息
            exception: 关联的异常对象（可选），用于记录堆栈跟踪
        """
        if exception:
            self._logger.error(f"{message}: {str(exception)}", exc_info=True)
        else:
            self._logger.error(message)

    def warning(self, message: str) -> None:
        """记录警告级别的日志，用于需要注意但不影响运行的异常情况"""
        self._logger.warning(message)

    def debug(self, message: str) -> None:
        """记录调试级别的日志，用于开发和排查问题时的详细信息"""
        self._logger.debug(message)