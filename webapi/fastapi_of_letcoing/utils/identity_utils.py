from typing import Any, Mapping, Optional


_TRUE_VALUES = {'active', 'enabled', 'normal', 'valid', '1', 'true'}
_FALSE_VALUES = {'inactive', 'disabled', 'locked', 'suspended', 'invalid', '0', 'false'}


def extract_account_status(source: Mapping[str, Any]) -> Optional[bool]:
    for field in ('is_active', 'active', 'enabled', 'status', 'account_status'):
        if field not in source:
            continue

        value = source[field]
        if isinstance(value, bool):
            return value

        normalized = str(value).strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False

    return None
