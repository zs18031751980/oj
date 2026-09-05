"""判题状态机与结果分类。

状态迁移集中在这里，控制器、Worker 和恢复逻辑不得自行拼接状态字符串。
"""

from typing import Final


QUEUED: Final = "Pending"
CLAIMED: Final = "Claimed"
COMPILING: Final = "Compiling"
COMPILED: Final = "Compiled"
RUNNING: Final = "Running"
CHECKING: Final = "Checking"
ACCEPTED: Final = "AC"
WRONG_ANSWER: Final = "WA"
COMPILATION_ERROR: Final = "CE"
TIME_LIMIT_EXCEEDED: Final = "TLE"
MEMORY_LIMIT_EXCEEDED: Final = "MLE"
OUTPUT_LIMIT_EXCEEDED: Final = "OLE"
RUNTIME_ERROR: Final = "RE"
SEGMENTATION_FAULT: Final = "SIGSEGV"
ILLEGAL_SYSTEM_CALL: Final = "SIGSYS"
SYSTEM_ERROR: Final = "SystemError"
CANCELLED: Final = "Cancelled"
PARTIAL: Final = "Partial"

TERMINAL_STATES = frozenset({
    ACCEPTED,
    WRONG_ANSWER,
    COMPILATION_ERROR,
    TIME_LIMIT_EXCEEDED,
    MEMORY_LIMIT_EXCEEDED,
    OUTPUT_LIMIT_EXCEEDED,
    RUNTIME_ERROR,
    SEGMENTATION_FAULT,
    ILLEGAL_SYSTEM_CALL,
    SYSTEM_ERROR,
    CANCELLED,
    PARTIAL,
})

ALLOWED_TRANSITIONS = {
    QUEUED: frozenset({CLAIMED, CANCELLED, SYSTEM_ERROR}),
    CLAIMED: frozenset({COMPILING, SYSTEM_ERROR, CANCELLED}),
    COMPILING: frozenset({COMPILED, COMPILATION_ERROR, SYSTEM_ERROR, CANCELLED}),
    COMPILED: frozenset({RUNNING, SYSTEM_ERROR, CANCELLED}),
    RUNNING: frozenset({CHECKING, TIME_LIMIT_EXCEEDED, MEMORY_LIMIT_EXCEEDED,
                        OUTPUT_LIMIT_EXCEEDED, RUNTIME_ERROR, SEGMENTATION_FAULT,
                        ILLEGAL_SYSTEM_CALL, SYSTEM_ERROR, CANCELLED}),
    CHECKING: frozenset({ACCEPTED, WRONG_ANSWER, PARTIAL, SYSTEM_ERROR, CANCELLED}),
}


def can_transition(current: str, target: str) -> bool:
    """判断一次状态迁移是否合法；终态不可被任何旧 Worker 覆盖。"""
    if current in TERMINAL_STATES:
        return False
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def is_terminal(status: str | None) -> bool:
    return status in TERMINAL_STATES


def status_for_execution_error(error_type: str | None) -> str:
    return {
        "TLE": TIME_LIMIT_EXCEEDED,
        "MLE": MEMORY_LIMIT_EXCEEDED,
        "OLE": OUTPUT_LIMIT_EXCEEDED,
        "SIGSEGV": SEGMENTATION_FAULT,
        "SIGSYS": ILLEGAL_SYSTEM_CALL,
        "RE": RUNTIME_ERROR,
    }.get(error_type or "", RUNTIME_ERROR)
