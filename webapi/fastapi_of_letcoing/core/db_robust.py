"""
数据库健壮性增强模块

目标：让数据库层在面对连接断开、认证失败、临时故障等场景时更健壮：
1. 统一异常类型（DatabaseUnavailableError），对客户端安全、不含连接细节；
2. 连接断开时自动重连并有限重试，提升对瞬时故障的容错；
3. 错误信息脱敏，避免把数据库主机/端口/账号/密码泄露到前端。
"""

import re
from contextlib import contextmanager
from typing import Callable, TypeVar

from peewee import (
    Database,
    InterfaceError,
    OperationalError,
)

T = TypeVar("T")

# 可重试的数据库异常：连接断开、超时、认证失败等瞬时/连接级故障
RETRYABLE_DB_ERRORS = (OperationalError, InterfaceError)


class DatabaseUnavailableError(Exception):
    """数据库暂时不可用。对外安全，绝不包含主机/端口/账号/密码等连接细节。"""

    def __init__(self, message: str = "数据库暂时不可用，请稍后重试") -> None:
        super().__init__(message)


def sanitize_db_error(message: str) -> str:
    """去除数据库错误信息中的敏感连接细节（主机/端口/账号/密码）。"""
    if not message:
        return message
    cleaned = message
    # postgresql://user:pass@host -> postgresql://***:***@host
    cleaned = re.sub(
        r"postgresql://[^@\s]+@",
        "postgresql://***:***@",
        cleaned,
    )
    cleaned = re.sub(
        r"password authentication failed for user \"?[^\"\s,]+?\"?",
        "数据库身份认证失败",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"connection to server at \"[^\"]+\"(, port \d+)?",
        "无法连接到数据库服务器",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"role \"[^\"]+\" does not exist",
        "数据库用户不存在",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\bFATAL:\s*[^\n]*", "数据库发生致命错误", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def is_retryable_db_error(exc: Exception) -> bool:
    """判断异常是否为可重试的数据库瞬时故障。"""
    return isinstance(exc, RETRYABLE_DB_ERRORS)


@contextmanager
def ensure_connected(database: Database):
    """
    确保数据库连接可用，遇到瞬时故障自动重连一次。

    使用方式：
        with ensure_connected(db):
            db.execute_sql("SELECT 1")
    若重连后仍不可用，抛出 DatabaseUnavailableError（已脱敏）。
    """
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            if database.is_closed() or not database.is_connection_usable():
                database.connect()
            try:
                yield
                return
            finally:
                # 使用结束后把连接归还连接池，避免连接泄漏
                database.close()
        except RETRYABLE_DB_ERRORS as exc:
            last_exc = exc
            if attempt == 0:
                continue
            break
    raise DatabaseUnavailableError() from last_exc


def run_db_operation(
    database: Database,
    operation: Callable[[], T],
    *,
    retries: int = 1,
) -> T:
    """
    在数据库连接上执行操作，遇到瞬时故障自动重连并重试。

    Args:
        database: Peewee 数据库连接实例
        operation: 无参可调用对象，返回结果（可安全重复执行）
        retries: 最大重试次数（默认 1，即总共最多尝试 2 次）

    Raises:
        DatabaseUnavailableError: 多次重试后仍不可用
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            if database.is_closed() or not database.is_connection_usable():
                database.connect()
            try:
                return operation()
            finally:
                # 操作结束后务必把连接归还连接池，避免连接泄漏导致
                # "Exceeded maximum connections"
                database.close()
        except RETRYABLE_DB_ERRORS as exc:
            last_exc = exc
            if attempt < retries:
                continue
            break
    raise DatabaseUnavailableError() from last_exc
