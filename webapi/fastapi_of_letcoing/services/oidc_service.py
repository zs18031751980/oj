"""OAuth/OIDC authentication service."""

from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from authlib.integrations.flask_client import OAuth

from core.di_container import Injectable
from interfaces.service_interfaces import IConfigService, ILoggerService, IOIDCService


def _safe_client_id(client_id: Any) -> str:
    value = str(client_id or '')
    if len(value) <= 8:
        return value
    return f'{value[:4]}...{value[-4:]}'


class OIDCService(Injectable, IOIDCService):
    """OAuth/OIDC authentication service.

    GitHub uses OAuth2 rather than pure OIDC, so it is registered with explicit
    authorize/token/API endpoints. Extra OIDC providers can be supplied through
    the OIDC_PROVIDERS config.
    """

    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        self._config_service = config_service
        self._logger_service = logger_service
        self._oauth: Optional[OAuth] = None

    def resolve_provider_name(self, provider: str) -> Optional[str]:
        """Resolve a provider name case-insensitively."""
        if not provider:
            return None

        normalized_provider = provider.casefold()
        for provider_name in self.get_supported_providers():
            if provider_name.casefold() == normalized_provider:
                return provider_name
        return None

    def initialize_oauth(self, app) -> None:
        self._oauth = OAuth(app)

        github_client_id = self._config_service.get_config('GITHUB_CLIENT_ID')
        github_client_secret = self._config_service.get_config('GITHUB_CLIENT_SECRET')

        if github_client_id and github_client_secret:
            self._oauth.register(
                name='github',
                client_id=github_client_id,
                client_secret=github_client_secret,
                access_token_url='https://github.com/login/oauth/access_token',
                authorize_url='https://github.com/login/oauth/authorize',
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'read:user user:email'},
            )
            self._logger_service.info('GitHub OAuth registered')
        else:
            self._logger_service.warning('GitHub OAuth is not configured')

        self._register_custom_providers()

    def _normalize_provider_config(self, provider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """补齐自定义 OIDC 提供方配置。"""
        normalized_config = dict(config or {})
        normalized_config.setdefault('name', provider_name)

        if not normalized_config.get('server_metadata_url'):
            issuer = normalized_config.get('issuer')
            if issuer:
                normalized_config['server_metadata_url'] = f"{str(issuer).rstrip('/')}/.well-known/openid-configuration"

        client_kwargs = normalized_config.get('client_kwargs')
        if not isinstance(client_kwargs, dict):
            client_kwargs = {}

        if not client_kwargs.get('scope'):
            client_kwargs['scope'] = 'openid profile email'

        if not client_kwargs.get('token_endpoint_auth_method'):
            client_kwargs['token_endpoint_auth_method'] = 'client_secret_post'

        normalized_config['client_kwargs'] = client_kwargs
        return normalized_config

    def _normalize_oidc_provider_configs(self) -> Dict[str, Dict[str, Any]]:
        raw_configs = self._config_service.get_config('OIDC_PROVIDERS', {})
        if isinstance(raw_configs, dict):
            return raw_configs

        if isinstance(raw_configs, list):
            normalized: Dict[str, Dict[str, Any]] = {}
            for item in raw_configs:
                if isinstance(item, dict) and item.get('name'):
                    normalized[item['name']] = item
            return normalized

        return {}

    def _register_custom_providers(self) -> None:
        if not self._oauth:
            return

        for provider_name, config in self._normalize_oidc_provider_configs().items():
            normalized_config = self._normalize_provider_config(provider_name, config)
            server_metadata_url = normalized_config.get('server_metadata_url')
            access_token_url = normalized_config.get('access_token_url')
            authorize_url = normalized_config.get('authorize_url')

            if not server_metadata_url and not (access_token_url and authorize_url):
                self._logger_service.warning(
                    f'OIDC provider skipped because metadata or endpoints are missing: {provider_name}'
                )
                continue

            try:
                self._oauth.register(
                    provider_name,
                    client_id=normalized_config['client_id'],
                    client_secret=normalized_config['client_secret'],
                    server_metadata_url=server_metadata_url,
                    access_token_url=access_token_url,
                    authorize_url=authorize_url,
                    api_base_url=normalized_config.get('api_base_url'),
                    client_kwargs=normalized_config.get('client_kwargs', {}),
                )
                self._logger_service.info(
                    'OIDC provider registered: '
                    f'provider={provider_name}, '
                    f'client_id={_safe_client_id(normalized_config.get("client_id"))}, '
                    f'server_metadata_url={server_metadata_url}, '
                    f'authorize_url={authorize_url}, '
                    f'access_token_url={access_token_url}, '
                    f'scope={normalized_config.get("client_kwargs", {}).get("scope")}'
                )
            except Exception as ex:
                self._logger_service.error(f'Failed to register OIDC provider: {provider_name}', ex)

    def _authorization_kwargs(self, provider: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        provider_config = self._normalize_oidc_provider_configs().get(provider, {})
        normalized_config = (
            self._normalize_provider_config(provider, provider_config)
            if isinstance(provider_config, dict)
            else {}
        )
        client_kwargs = normalized_config.get('client_kwargs', {})

        kwargs: Dict[str, Any] = {}
        if redirect_uri:
            kwargs['redirect_uri'] = redirect_uri

        scope = client_kwargs.get('scope')
        if scope:
            kwargs['scope'] = scope

        return kwargs

    def _extract_authorization_url(self, authorization_result: Any) -> str:
        if isinstance(authorization_result, tuple):
            return str(authorization_result[0]) if authorization_result else ''

        if isinstance(authorization_result, Mapping):
            url_value = authorization_result.get('url')
            if url_value:
                return str(url_value)

        return str(authorization_result or '')

    def get_authorization_redirect(self, provider: str, redirect_uri: str):
        """Return a Flask redirect response that starts the OAuth login."""
        if not self._oauth:
            return None

        try:
            resolved_provider = self.resolve_provider_name(provider)
            if not resolved_provider:
                self._logger_service.error(f'OAuth provider not found: {provider}')
                return None

            client = self._oauth.create_client(resolved_provider)
            if not client:
                self._logger_service.error(f'OAuth provider not found: {resolved_provider}')
                return None

            authorization_kwargs = self._authorization_kwargs(resolved_provider, redirect_uri)
            self._logger_service.info(
                'Creating OAuth redirect: '
                f'provider={resolved_provider}, '
                f'redirect_uri={redirect_uri}, '
                f'scope={authorization_kwargs.get("scope", "")}'
            )
            response = client.authorize_redirect(**authorization_kwargs)
            authorization_url = (
                response.headers.get('Location', '')
                if hasattr(response, 'headers')
                else ''
            )
            self._logger_service.info(
                'Authorization URL created: '
                f'provider={resolved_provider}, '
                f'url={authorization_url}'
            )
            return response
        except Exception as ex:
            self._logger_service.error(f'Failed to create OAuth redirect: {provider}', ex)
            return None

    def get_authorization_url(self, provider: str, redirect_uri: Optional[str] = None) -> Optional[str]:
        """Return an authorization URL for API clients."""
        if not self._oauth:
            return None

        try:
            resolved_provider = self.resolve_provider_name(provider)
            if not resolved_provider:
                self._logger_service.error(f'OAuth provider not found: {provider}')
                return None

            client = self._oauth.create_client(resolved_provider)
            if not client:
                self._logger_service.error(f'OAuth provider not found: {resolved_provider}')
                return None

            kwargs = self._authorization_kwargs(resolved_provider, redirect_uri)
            authorization_result = client.create_authorization_url(**kwargs)
            return self._extract_authorization_url(authorization_result)
        except Exception as ex:
            self._logger_service.error(f'Failed to create authorization URL: {provider}', ex)
            return None

    def authorize_callback(self, provider: str, redirect_uri: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self._oauth:
            return None

        try:
            resolved_provider = self.resolve_provider_name(provider)
            if not resolved_provider:
                self._logger_service.error(f'OAuth provider not found: {provider}')
                return None

            client = self._oauth.create_client(resolved_provider)
            if not client:
                self._logger_service.error(f'OAuth provider not found: {resolved_provider}')
                return None

            # Authlib's Flask integration already persists the redirect URI used
            # during authorize_redirect() and reuses it while exchanging the code.
            # Passing redirect_uri again here can collide with the stored value and
            # raise "got multiple values for keyword argument 'redirect_uri'".
            token = client.authorize_access_token()
            self._logger_service.info(
                'OAuth token received: '
                f'provider={resolved_provider}, '
                f'token_keys={",".join(sorted(token.keys())) if isinstance(token, dict) else type(token).__name__}'
            )
            user_info = self._get_user_info(resolved_provider, client, token)
            if not user_info:
                self._logger_service.error(f'OAuth callback failed because user info is empty: {resolved_provider}')
                return None

            return {
                'provider': resolved_provider,
                'token': token,
                'user_info': user_info,
            }
        except Exception as ex:
            self._logger_service.error(f'Failed to handle OAuth callback: {provider}', ex)
            return None

    def _normalize_user_data(self, user_data: Any) -> Optional[Dict[str, Any]]:
        if hasattr(user_data, 'to_dict'):
            return user_data.to_dict()

        if isinstance(user_data, Mapping):
            return dict(user_data)

        if hasattr(user_data, 'json'):
            return user_data.json()

        return None

    def _build_oidc_user_info(self, provider: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        subject = user_data.get('sub') or user_data.get('id') or user_data.get('user_id') or user_data.get('uid')
        if not subject:
            self._logger_service.error(
                'OIDC user info does not include a stable subject: '
                f'provider={provider}, keys={",".join(sorted(user_data.keys()))}'
            )
            return None

        username = (
            user_data.get('preferred_username')
            or user_data.get('nickname')
            or user_data.get('username')
            or user_data.get('name')
            or user_data.get('email')
            or str(subject)
        )
        name = user_data.get('name') or user_data.get('nickname') or username
        return {
            'id': str(subject),
            'username': username,
            'name': name or user_data.get('email') or str(subject),
            'email': user_data.get('email') or '',
            'avatar_url': (
                user_data.get('picture')
                or user_data.get('avatar')
                or user_data.get('avatar_url')
                or ''
            ),
            'provider': provider,
        }

    def _get_user_info(self, provider: str, client, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if provider == 'github':
                user_resp = client.get('user', token=token)
                user_resp.raise_for_status()
                user_data = user_resp.json()

                if not user_data.get('email'):
                    email_resp = client.get('user/emails', token=token)
                    email_resp.raise_for_status()
                    emails = email_resp.json()
                    primary_email = next(
                        (
                            email['email']
                            for email in emails
                            if email.get('primary') and email.get('verified')
                        ),
                        None,
                    )
                    if primary_email:
                        user_data['email'] = primary_email

                return {
                    'id': str(user_data['id']),
                    'username': user_data.get('login', ''),
                    'name': user_data.get('name') or user_data.get('login', ''),
                    'email': user_data.get('email') or '',
                    'avatar_url': user_data.get('avatar_url') or '',
                    'provider': provider,
                }

            token_user_data = self._normalize_user_data(token.get('userinfo')) if isinstance(token, dict) else None
            if token_user_data:
                self._logger_service.info(
                    'Using OIDC user info from token payload: '
                    f'provider={provider}, keys={",".join(sorted(token_user_data.keys()))}'
                )
                return self._build_oidc_user_info(provider, token_user_data)

            user_data = None
            if hasattr(client, 'userinfo'):
                try:
                    user_data = client.userinfo(token=token)
                except Exception as ex:
                    self._logger_service.warning(f'OIDC client.userinfo failed for {provider}: {str(ex)}')

            if not user_data:
                resp = client.get('userinfo', token=token)
                resp.raise_for_status()
                user_data = resp.json()

            normalized_user_data = self._normalize_user_data(user_data)
            if not normalized_user_data:
                self._logger_service.error(f'Unsupported userinfo response type: {type(user_data).__name__}')
                return None

            self._logger_service.info(
                'OIDC user info received: '
                f'provider={provider}, keys={",".join(sorted(normalized_user_data.keys()))}'
            )
            return self._build_oidc_user_info(provider, normalized_user_data)
        except Exception as ex:
            self._logger_service.error(f'Failed to fetch user info: {provider}', ex)
            return None

    def get_supported_providers(self) -> List[str]:
        providers: List[str] = []
        seen = set()

        if (
            self._config_service.get_config('GITHUB_CLIENT_ID')
            and self._config_service.get_config('GITHUB_CLIENT_SECRET')
        ):
            providers.append('github')
            seen.add('github')

        for provider_name in self._normalize_oidc_provider_configs().keys():
            if provider_name not in seen:
                providers.append(provider_name)
                seen.add(provider_name)
        return providers

    def validate_provider(self, provider: str) -> bool:
        return self.resolve_provider_name(provider) is not None
