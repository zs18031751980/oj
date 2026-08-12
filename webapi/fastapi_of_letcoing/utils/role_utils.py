"""
角色标准化工具模块

提供统一的角色名称标准化和多角色优先级选取逻辑。
所有涉及角色解析的模块（auth_controller、oidc_service、user_service）共享此实现。
"""

from collections.abc import Mapping
from typing import Any, Iterator, List

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

_ROLE_FIELD_NAMES = {
    'authorities',
    'department',
    'group',
    'groups',
    'identities',
    'identity',
    'level',
    'memberof',
    'position',
    'realmaccess',
    'role',
    'roles',
    'userrole',
    'usertype',
}

_IDENTITY_CONTAINER_FIELD_NAMES = {
    'account',
    'claims',
    'principal',
    'user',
    'userinfo',
}


def _normalize_field_name(field_name: Any) -> str:
    return ''.join(character for character in str(field_name).casefold() if character.isalnum())


def _is_role_field(field_name: Any) -> bool:
    normalized = _normalize_field_name(field_name)
    return (
        normalized in _ROLE_FIELD_NAMES
        or normalized.endswith('claimsrole')
        or normalized.endswith('claimsroles')
    )


def _iter_role_values(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
        return

    if isinstance(value, Mapping):
        for field_name, nested_value in value.items():
            if _is_role_field(field_name) or _normalize_field_name(field_name) == 'name':
                yield from _iter_role_values(nested_value)
        return

    if isinstance(value, (list, tuple, set)):
        for nested_value in value:
            yield from _iter_role_values(nested_value)


def collect_role_values(source: Mapping[str, Any]) -> List[str]:
    roles: List[str] = []

    def visit(value: Any, *, allow_ambiguous_fields: bool = False) -> None:
        if isinstance(value, Mapping):
            for field_name, nested_value in value.items():
                normalized_field = _normalize_field_name(field_name)
                if _is_role_field(field_name) or (
                    allow_ambiguous_fields and normalized_field == 'type'
                ):
                    roles.extend(_iter_role_values(nested_value))
                if normalized_field in _IDENTITY_CONTAINER_FIELD_NAMES:
                    if isinstance(nested_value, Mapping):
                        visit(nested_value, allow_ambiguous_fields=True)
                    elif isinstance(nested_value, (list, tuple, set)):
                        for item in nested_value:
                            if isinstance(item, Mapping):
                                visit(item, allow_ambiguous_fields=True)

    visit(source)
    return roles


def extract_highest_role(source: Mapping[str, Any], logger: Any = None) -> str:
    return pick_highest_role(collect_role_values(source), logger)


def normalize_role(raw_role: Any, logger: Any = None) -> str:
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


def pick_highest_role(raw_roles: List[Any], logger: Any = None) -> str:
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
