"""OAuth/OIDC claim and scope helpers."""

from typing import Any, Dict, Mapping

_IDENTITY_CLAIM_NAMES = (
    'authorities',
    'department',
    'group',
    'groups',
    'identities',
    'identity',
    'level',
    'memberOf',
    'position',
    'realm_access',
    'role',
    'roles',
    'type',
    'userRole',
    'userType',
    'user_type',
)


def ensure_role_scope(scope: Any) -> str:
    scopes = str(scope or '').split()
    if 'role' not in scopes:
        scopes.append('role')
    return ' '.join(scopes)


def normalize_provider_scope(provider: str, scope: Any) -> str:
    normalized_scope = str(scope or '').strip()
    if provider.casefold() == 'iosclub':
        return ensure_role_scope(normalized_scope or 'openid profile')
    return normalized_scope


def merge_oidc_identity_claims(
    user_info: Dict[str, Any],
    identity_claims: Mapping[str, Any],
) -> None:
    for key in (
        'preferred_username',
        'nickname',
        'name',
        'email',
        'picture',
        'avatar',
        'avatar_url',
        *_IDENTITY_CLAIM_NAMES,
    ):
        if key in identity_claims:
            user_info[key] = identity_claims[key]
