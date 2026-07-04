"""
角色标准化工具模块

提供统一的角色名称标准化和多角色优先级选取逻辑。
所有涉及角色解析的模块（auth_controller、oidc_service、user_service）共享此实现。
"""

from typing import List, Optional, Union

ROLE_PRIORITY = {
    'manager': 3,
    'staff': 2,
    'member': 1,
}

_ROLE_MAP = {
    'member': 'member',
    'staff': 'staff',
    'manager': 'manager',
    'admin': 'manager',
    'department': 'staff',
    'minister': 'manager',
    'president': 'manager',
    'founder': 'manager',
    'user': 'member',
    '部长': 'manager',
    '部员': 'staff',
    '社员': 'member',
    '社长': 'manager',
    '副社长': 'manager',
    '副部长': 'manager',
    '干事': 'staff',
    '部门主管': 'manager',
    'role_admin': 'manager',
    'role_manager': 'manager',
    'role_staff': 'staff',
    'role_member': 'member',
    'role_user': 'member',
    'administrator': 'manager',
    'superuser': 'manager',
    '普通用户': 'member',
    '管理员': 'manager',
}


def normalize_role(raw_role, logger=None) -> str:
    """
    将原始角色值标准化为内部格式（member/staff/manager）

    支持单个字符串或列表（取第一个元素后标准化）。
    """
    if raw_role is None:
        return 'member'

    if isinstance(raw_role, list):
        raw_role = raw_role[0] if raw_role else ''

    cleaned = str(raw_role or '').strip().lower()
    result = _ROLE_MAP.get(cleaned, 'member')

    if cleaned and cleaned not in _ROLE_MAP:
        msg = f'Unrecognized role value "{raw_role}" normalized to "{result}"'
        if logger:
            logger.warning(msg)
        else:
            print(msg)

    return result


def pick_highest_role(raw_roles: List[str], logger=None) -> str:
    """
    从多个角色值中选出权限最高的角色

    优先级（由高到低）：manager > staff > member

    对每个原始角色进行标准化，然后按优先级选取最高者。
    如果列表为空或所有角色都无法识别，返回 'member'。

    Args:
        raw_roles: 原始角色值列表（如 ['部长', '部员', '社员']）
        logger: 可选的日志记录器

    Returns:
        最高权限的标准化角色名
    """
    best_role = 'member'
    best_priority = 1

    for role in raw_roles:
        if not role:
            continue
        if isinstance(role, (list, tuple)):
            for sub in role:
                if sub:
                    normalized = normalize_role(sub, logger)
                    priority = ROLE_PRIORITY.get(normalized, 0)
                    if priority > best_priority:
                        best_priority = priority
                        best_role = normalized
        else:
            normalized = normalize_role(role, logger)
            priority = ROLE_PRIORITY.get(normalized, 0)
            if priority > best_priority:
                best_priority = priority
                best_role = normalized

    if logger and best_role == 'member' and raw_roles:
        logger.info(f'All roles normalized to member: {raw_roles}')

    return best_role
