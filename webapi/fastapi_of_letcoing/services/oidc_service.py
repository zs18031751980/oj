"""OAuth/OIDC authentication service."""

from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from authlib.integrations.flask_client import OAuth

from core.di_container import Injectable
from interfaces.service_interfaces import IConfigService, ILoggerService, IOIDCService


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
                self._logger_service.info(f'OIDC provider registered: {provider_name}')
            except Exception as ex:
                self._logger_service.error(f'Failed to register OIDC provider: {provider_name}', ex)

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

            return client.authorize_redirect(redirect_uri)
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

            kwargs = {'redirect_uri': redirect_uri} if redirect_uri else {}
            uri, _state = client.create_authorization_url(**kwargs)
            return uri
        except Exception as ex:
            self._logger_service.error(f'Failed to create authorization URL: {provider}', ex)
            return None

    def authorize_callback(self, provider: str) -> Optional[Dict[str, Any]]:
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

            token = client.authorize_access_token()
            user_info = self._get_user_info(resolved_provider, client, token)
            if not user_info:
                return None

            return {
                'provider': resolved_provider,
                'token': token,
                'user_info': user_info,
            }
        except Exception as ex:
            self._logger_service.error(f'Failed to handle OAuth callback: {provider}', ex)
            return None

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

            if hasattr(client, 'userinfo'):
                user_data = client.userinfo(token=token)
            else:
                resp = client.get('userinfo', token=token)
                resp.raise_for_status()
                user_data = resp.json()

            if hasattr(user_data, 'to_dict'):
                user_data = user_data.to_dict()
            elif isinstance(user_data, Mapping):
                user_data = dict(user_data)
            elif hasattr(user_data, 'json'):
                user_data = user_data.json()
            else:
                self._logger_service.error(f'Unsupported userinfo response type: {type(user_data).__name__}')
                return None

            username = (
                user_data.get('preferred_username')
                or user_data.get('nickname')
                or user_data.get('username')
                or user_data.get('email')
                or ''
            )
            name = user_data.get('name') or user_data.get('nickname') or username
            return {
                'id': str(user_data.get('sub') or user_data.get('id') or ''),
                'username': username,
                'name': name or user_data.get('email') or '',
                'email': user_data.get('email') or '',
                'avatar_url': (
                    user_data.get('picture')
                    or user_data.get('avatar')
                    or user_data.get('avatar_url')
                    or ''
                ),
                'provider': provider,
            }
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
