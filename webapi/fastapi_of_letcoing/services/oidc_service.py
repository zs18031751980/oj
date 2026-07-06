"""
OAuth/OIDC 认证服务模块

提供第三方登录的完整实现，支持：
1. GitHub OAuth 2.0（内置支持，使用显式端点配置）
2. 标准 OIDC（OpenID Connect）提供商（通过 OIDC_PROVIDERS 配置动态注册）
3. 支持 OIDC 发现协议（自动从 .well-known/openid-configuration 获取元数据）
4. 支持跳过 ID Token 验证的自定义提供商（处理 at_hash 不匹配的情况）

认证流程：
1. 用户选择第三方登录方式
2. 后端生成授权 URL，重定向用户到第三方登录页
3. 用户授权后，第三方回调到后端的 callback 接口
4. 后端用授权码换取访问令牌和用户信息
5. 签发本地 JWT 令牌，完成登录
"""

from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from authlib.integrations.flask_client import OAuth  # Authlib OAuth 客户端
from flask import redirect, request, session
import requests

from core.di_container import Injectable
from interfaces.service_interfaces import IConfigService, ILoggerService, IOIDCService
from utils.role_utils import pick_highest_role


def _safe_client_id(client_id: Any) -> str:
    """
    安全地展示客户端 ID（隐藏中间部分）

    用于日志记录，避免暴露完整的客户端 ID。
    例如：abcd...wxyz
    """
    value = str(client_id or '')
    if len(value) <= 8:
        return value
    return f'{value[:4]}...{value[-4:]}'


class OIDCService(Injectable, IOIDCService):
    """
    OAuth/OIDC 认证服务实现类

    GitHub 使用 OAuth 2.0 协议（非标准 OIDC），因此使用显式的
    authorize/token/API 端点进行注册。额外的 OIDC 提供商通过
    OIDC_PROVIDERS 配置项动态注册，支持标准 OIDC 发现协议。
    """

    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        """
        初始化 OIDC 认证服务

        Args:
            config_service: 配置服务（读取 OAuth 客户端配置）
            logger_service: 日志服务
        """
        self._config_service = config_service
        self._logger_service = logger_service
        self._oauth: Optional[OAuth] = None
        self._metadata_timeout = max(int(self._config_service.get_timeout()), 5)
        self._metadata_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._normalized_configs_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._http_session: Optional[requests.Session] = None

    def _get_http_session(self) -> requests.Session:
        """获取或创建复用的 requests Session，复用 TCP 连接"""
        if self._http_session is None:
            self._http_session = requests.Session()
            self._http_session.headers.update({'Accept': 'application/json'})
        return self._http_session

    def resolve_provider_name(self, provider: str) -> Optional[str]:
        """
        将提供商名称解析为配置中的规范名称（大小写不敏感匹配）

        例如：用户传入 "GitHub"、"GITHUB" 或 "github"，都会解析为 "github"。

        Args:
            provider: 用户传入的提供商名称

        Returns:
            配置中的规范名称，未找到返回 None
        """
        if not provider:
            return None

        normalized_provider = provider.casefold()
        for provider_name in self.get_supported_providers():
            if provider_name.casefold() == normalized_provider:
                return provider_name
        return None

    # ============================================================
    # OAuth 初始化与提供商注册
    # ============================================================

    def initialize_oauth(self, app) -> None:
        """
        初始化 OAuth 服务，注册所有已配置的认证提供商

        1. 创建 Authlib OAuth 实例
        2. 注册内置的 GitHub OAuth 提供商（如果已配置）
        3. 注册所有自定义 OIDC 提供商（如果已配置）
        """
        self._oauth = OAuth(app)

        # ----- GitHub OAuth 注册 -----
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
            self._logger_service.info('GitHub OAuth 已注册')
        else:
            self._logger_service.warning('GitHub OAuth 未配置')

        # ----- 自定义 OIDC 提供商注册 -----
        self._register_custom_providers()

    def _normalize_provider_config(self, provider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化自定义 OIDC 提供商的配置

        补充缺失的配置项：
        - 如果没有 server_metadata_url 但有 issuer，自动拼接 OIDC 发现地址
        - 如果未设置 scope，默认使用 'openid profile role'
        - 如果未设置 token_endpoint_auth_method，默认使用 'client_secret_post'

        Args:
            provider_name: 提供商名称
            config: 原始配置字典

        Returns:
            补充了默认值后的标准化配置字典
        """
        normalized_config = dict(config or {})
        normalized_config.setdefault('name', provider_name)

        # 自动构建 OIDC 发现端点 URL
        if not normalized_config.get('server_metadata_url'):
            issuer = normalized_config.get('issuer')
            if issuer:
                normalized_config['server_metadata_url'] = f"{str(issuer).rstrip('/')}/.well-known/openid-configuration"

        # 确保 client_kwargs 存在
        client_kwargs = normalized_config.get('client_kwargs')
        if not isinstance(client_kwargs, dict):
            client_kwargs = {}

        # 设置默认 scope
        if not client_kwargs.get('scope'):
            client_kwargs['scope'] = 'openid profile role'

        # 设置默认令牌端点认证方式
        if not client_kwargs.get('token_endpoint_auth_method'):
            client_kwargs['token_endpoint_auth_method'] = 'client_secret_post'

        normalized_config['client_kwargs'] = client_kwargs
        return normalized_config

    def _normalize_oidc_provider_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        将 OIDC_PROVIDERS 配置标准化为字典格式（结果缓存，避免重复处理）

        支持两种输入格式：
        - 字典格式：{"provider_name": {...}}
        - 列表格式：[{"name": "provider_name", ...}]

        Returns:
            标准化后的字典格式配置
        """
        if self._normalized_configs_cache is not None:
            return self._normalized_configs_cache

        raw_configs = self._config_service.get_config('OIDC_PROVIDERS', {})
        if isinstance(raw_configs, dict):
            self._normalized_configs_cache = raw_configs
            return raw_configs

        if isinstance(raw_configs, list):
            normalized: Dict[str, Dict[str, Any]] = {}
            for item in raw_configs:
                if isinstance(item, dict) and item.get('name'):
                    normalized[item['name']] = item
            self._normalized_configs_cache = normalized
            return normalized

        self._normalized_configs_cache = {}
        return {}

    def _register_custom_providers(self) -> None:
        """注册所有自定义 OIDC 提供商（从 OIDC_PROVIDERS 配置读取）"""
        if not self._oauth:
            return

        for provider_name, config in self._normalize_oidc_provider_configs().items():
            normalized_config = self._normalize_provider_config(provider_name, config)
            server_metadata_url = normalized_config.get('server_metadata_url')
            access_token_url = normalized_config.get('access_token_url')
            authorize_url = normalized_config.get('authorize_url')
            token_endpoint = normalized_config.get('access_token_url') or normalized_config.get('token_url')
            userinfo_endpoint = normalized_config.get('userinfo_endpoint')

            # 跳过配置不完整的提供商
            if not server_metadata_url and not (access_token_url and authorize_url):
                self._logger_service.warning(
                    f'OIDC provider skipped because metadata or endpoints are missing: {provider_name}'
                )
                continue

            # 尝试预取 OIDC 元数据
            resolved_metadata = self._fetch_server_metadata(server_metadata_url) if server_metadata_url else None
            if resolved_metadata:
                authorize_url = authorize_url or resolved_metadata.get('authorization_endpoint')
                token_endpoint = token_endpoint or resolved_metadata.get('token_endpoint')
                userinfo_endpoint = userinfo_endpoint or resolved_metadata.get('userinfo_endpoint')
                normalized_config['server_metadata'] = resolved_metadata

            try:
                effective_server_metadata_url = server_metadata_url if not resolved_metadata else 'prefetched'
                effective_access_token_url = token_endpoint or access_token_url
                effective_authorize_url = authorize_url
                effective_userinfo_endpoint = userinfo_endpoint

                # 向 Authlib 注册 OAuth 客户端
                self._oauth.register(
                    provider_name,
                    client_id=normalized_config['client_id'],
                    client_secret=normalized_config['client_secret'],
                    server_metadata=normalized_config.get('server_metadata'),
                    server_metadata_url=server_metadata_url if not resolved_metadata else None,
                    access_token_url=token_endpoint or access_token_url,
                    authorize_url=authorize_url,
                    api_base_url=normalized_config.get('api_base_url'),
                    userinfo_endpoint=userinfo_endpoint,
                    client_kwargs=normalized_config.get('client_kwargs', {}),
                )
                self._logger_service.info(
                    'OIDC provider registered: '
                    f'provider={provider_name}, '
                    f'client_id={_safe_client_id(normalized_config.get("client_id"))}, '
                    f'server_metadata_source={effective_server_metadata_url}, '
                    f'authorize_url={effective_authorize_url}, '
                    f'access_token_url={effective_access_token_url}, '
                    f'userinfo_endpoint={effective_userinfo_endpoint}, '
                    f'scope={normalized_config.get("client_kwargs", {}).get("scope")}'
                )
            except Exception as ex:
                self._logger_service.error(f'Failed to register OIDC provider: {provider_name}', ex)

    def _fetch_server_metadata(self, server_metadata_url: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        预取 OIDC 提供商的服务元数据（结果缓存，避免重复请求）

        从 OIDC 发现端点（.well-known/openid-configuration）获取提供商的服务信息，
        包括授权端点、令牌端点、用户信息端点等。

        Args:
            server_metadata_url: OIDC 发现端点 URL

        Returns:
            元数据字典，获取失败返回 None
        """
        if not server_metadata_url:
            return None

        if server_metadata_url in self._metadata_cache:
            return self._metadata_cache[server_metadata_url]

        try:
            response = self._get_http_session().get(server_metadata_url, timeout=self._metadata_timeout)
            response.raise_for_status()
            metadata = response.json()
            if not isinstance(metadata, dict):
                self._logger_service.warning(
                    f'OIDC metadata is not a JSON object: {server_metadata_url}'
                )
                self._metadata_cache[server_metadata_url] = None
                return None

            self._logger_service.info(
                'OIDC metadata prefetched: '
                f'url={server_metadata_url}, '
                f'keys={",".join(sorted(metadata.keys()))}'
            )
            self._metadata_cache[server_metadata_url] = metadata
            return metadata
        except Exception as ex:
            self._logger_service.warning(
                f'Failed to prefetch OIDC metadata, will fall back to runtime fetch: {server_metadata_url} ({str(ex)})'
            )
            self._metadata_cache[server_metadata_url] = None
            return None

    # ============================================================
    # OAuth 授权流程（生成授权 URL 与重定向）
    # ============================================================

    def _authorization_kwargs(self, provider: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        构建 OAuth 授权请求的额外参数

        Args:
            provider: 提供商名称
            redirect_uri: 自定义回调地址（可选）

        Returns:
            包含 redirect_uri 和 scope 等参数的字典
        """
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
        """从 Authlib 返回的授权结果中提取授权 URL"""
        if isinstance(authorization_result, Mapping):
            url_value = authorization_result.get('url')
            if url_value:
                return str(url_value)

        if isinstance(authorization_result, tuple):
            return str(authorization_result[0]) if authorization_result else ''

        return str(authorization_result or '')

    def _extract_authorization_state(self, authorization_result: Any) -> str:
        """从 Authlib 返回的授权结果中提取 CSRF 保护用的 state 参数"""
        if isinstance(authorization_result, Mapping):
            return str(authorization_result.get('state') or '')

        if isinstance(authorization_result, tuple) and len(authorization_result) > 1:
            return str(authorization_result[1] or '')

        return ''

    def _authorization_data(self, authorization_result: Any) -> Dict[str, Any]:
        """将 Authlib 返回的授权结果统一转换为字典格式"""
        if isinstance(authorization_result, Mapping):
            return dict(authorization_result)

        if isinstance(authorization_result, tuple):
            data = {'url': authorization_result[0]} if authorization_result else {}
            if len(authorization_result) > 1:
                data['state'] = authorization_result[1]
            return data

        return {'url': str(authorization_result or '')}

    def _should_skip_id_token_validation(self, provider: str) -> bool:
        """
        判断是否应跳过 ID Token 验证

        某些自托管的 OIDC 提供商签发的 id_token 中，at_hash 声明
        与实际 access_token 不匹配。Authlib 的 authorize_access_token()
        方法会事先验证 at_hash，导致回调失败。对于自定义提供商，
        我们可以安全地跳过 ID Token 验证，直接使用 access_token
        从 userinfo 端点获取用户信息。

        Args:
            provider: 提供商名称

        Returns:
            是否跳过 ID Token 验证
        """
        if provider == 'github':
            return False

        provider_config = self._normalize_oidc_provider_configs().get(provider, {})
        if not isinstance(provider_config, dict):
            return True

        if 'skip_id_token_validation' in provider_config:
            return bool(provider_config.get('skip_id_token_validation'))

        if 'validate_id_token' in provider_config:
            return not bool(provider_config.get('validate_id_token'))

        return True

    def _authorize_access_token_without_id_token_validation(self, client, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        跳过 ID Token 验证的 OAuth 回调令牌交换

        此方法模拟 Authlib 的 FlaskOAuth2App.authorize_access_token()
        的状态处理逻辑，但在 parse_id_token() 之前停止，
        避免 at_hash 验证失败导致整个回调流程中断。
        """
        if request.method == 'GET':
            params = {
                'code': request.args['code'],
                'state': request.args.get('state'),
            }
        else:
            params = {
                'code': request.form['code'],
                'state': request.form.get('state'),
            }

        state_data = client.framework.get_state_data(session, params.get('state'))
        client.framework.clear_state_data(session, params.get('state'))
        if state_data:
            params = client._format_state_params(state_data, params)
        if redirect_uri and 'redirect_uri' not in params:
            params['redirect_uri'] = redirect_uri
        token = client.fetch_access_token(**params)
        client.token = token
        return token

    # ============================================================
    # 外部接口方法（供控制器调用）
    # ============================================================

    def get_authorization_redirect(self, provider: str, redirect_uri: str):
        """
        创建浏览器重定向响应，将用户引导至第三方登录页面

        此方法供浏览器登录流程使用（AuthBrowserLoginController），
        直接返回 Flask 的重定向响应对象。

        Args:
            provider: 提供商名称
            redirect_uri: 登录成功后的回调地址

        Returns:
            Flask redirect 响应对象，失败返回 None
        """
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
            authorization_result = client.create_authorization_url(**authorization_kwargs)
            authorization_url = self._extract_authorization_url(authorization_result)
            authorization_state = self._extract_authorization_state(authorization_result)
            authorization_data = self._authorization_data(authorization_result)
            client.save_authorize_data(
                redirect_uri=redirect_uri,
                **authorization_data,
            )
            self._logger_service.info(
                'Authorization URL created: '
                f'provider={resolved_provider}, '
                f'state_length={len(authorization_state)}, '
                f'url={authorization_url}'
            )
            return redirect(authorization_url)
        except Exception as ex:
            self._logger_service.error(f'Failed to create OAuth redirect: {provider}', ex)
            return None

    def get_authorization_url(self, provider: str, redirect_uri: Optional[str] = None) -> Optional[str]:
        """
        获取 OAuth 授权 URL（供 API 客户端使用）

        此方法供 API 客户端登录流程使用（AuthLoginController），
        返回授权 URL 字符串，客户端自行决定如何跳转。

        Args:
            provider: 提供商名称
            redirect_uri: 自定义回调地址（可选）

        Returns:
            OAuth 授权 URL 字符串，失败返回 None
        """
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
        """
        处理 OAuth 授权回调

        接收第三方提供商回调的授权码（code），
        完成以下步骤：
        1. 用授权码向提供商换取访问令牌
        2. 使用访问令牌获取用户信息
        3. 返回标准化的认证结果

        Args:
            provider: 提供商名称
            redirect_uri: 回调地址（通常不需要传递，Authlib 会使用之前保存的地址）

        Returns:
            包含 provider、token 和 user_info 的字典，失败返回 None
        """
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

            if self._should_skip_id_token_validation(resolved_provider):
                self._logger_service.warning(
                    'Skipping OIDC id_token validation and using userinfo endpoint: '
                    f'provider={resolved_provider}'
                )
                token = self._authorize_access_token_without_id_token_validation(client, redirect_uri)
            else:
                token = client.authorize_access_token()

            self._logger_service.info(
                'OAuth token received: '
                f'provider={resolved_provider}, '
                f'token_keys={",".join(sorted(token.keys())) if isinstance(token, dict) else type(token).__name__}'
            )

            # 获取用户信息
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

    # ============================================================
    # 用户信息获取（处理不同提供商的数据格式）
    # ============================================================

    def _normalize_user_data(self, user_data: Any) -> Optional[Dict[str, Any]]:
        """
        将不同格式的用户数据统一转换为字典

        支持：to_dict() 方法、Mapping 类型、json() 方法

        Args:
            user_data: 来自不同来源的用户数据

        Returns:
            标准化的字典格式，转换失败返回 None
        """
        if hasattr(user_data, 'to_dict'):
            return user_data.to_dict()

        if isinstance(user_data, Mapping):
            return dict(user_data)

        if hasattr(user_data, 'json'):
            return user_data.json()

        return None

    def _build_oidc_user_info(self, provider: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从 OIDC 用户信息中提取标准化的用户数据

        OIDC 标准字段映射：
        - sub -> id（用户唯一标识）
        - preferred_username -> username
        - email -> email
        - picture -> avatar_url

        Args:
            provider: 提供商名称
            user_data: 来自提供商的标准 OIDC 用户信息

        Returns:
            标准化后的用户信息字典，缺少唯一标识时返回 None
        """
        subject = user_data.get('sub') or user_data.get('id') or user_data.get('user_id') or user_data.get('uid')
        if not subject:
            self._logger_service.error(
                'OIDC user info does not include a stable subject: '
                f'provider={provider}, keys={",".join(sorted(user_data.keys()))}'
            )
            return None

        username = (
            user_data.get('name')
            or user_data.get('preferred_username')
            or user_data.get('nickname')
            or user_data.get('username')
            or user_data.get('email')
            or str(subject)
        )
        name = user_data.get('name') or user_data.get('nickname') or username

        # 从多个字段收集所有角色，选取权限最高的
        all_roles = []
        raw_role = user_data.get('role')
        if raw_role:
            if isinstance(raw_role, list):
                all_roles.extend(raw_role)
            elif isinstance(raw_role, str):
                all_roles.append(raw_role)
        for field in ('roles', 'groups', 'group', 'user_type', 'authorities', 'memberOf',
                      'position', 'department', 'identity', 'type'):
            val = user_data.get(field)
            if val:
                if isinstance(val, list):
                    all_roles.extend(val)
                elif isinstance(val, str):
                    all_roles.append(val)
        realm_access = user_data.get('realm_access')
        if isinstance(realm_access, dict):
            roles = realm_access.get('roles', [])
            if isinstance(roles, list):
                tech_roles = {'offline_access', 'uma_authorization'}
                all_roles.extend(r for r in roles if str(r).lower() not in tech_roles)

        # 兜底：遍历所有 user_data 值，找到标准角色关键词
        known_roles = ('member', 'staff', 'manager', 'admin', 'minister', 'president', 'founder',
                       '部长', '部员', '社员', '社长', '副社长', '副部长', '干事', '管理员', '普通用户')
        if not all_roles:
            for key, val in user_data.items():
                s = str(val).strip()
                if not s:
                    continue
                for r in known_roles:
                    if r.lower() in s.lower():
                        all_roles.append(r)
                        break
        role = pick_highest_role(all_roles, self._logger_service) if all_roles else 'member'
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
            'role': role,
        }

    def _get_user_info(self, provider: str, client, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从 OAuth 提供商获取用户信息

        根据提供商类型采用不同的获取方式：
        - GitHub：调用 GitHub API（/user 和 /user/emails）
        - 标准 OIDC：优先从 ID Token 中获取，然后尝试 userinfo 端点

        Args:
            provider: 提供商名称
            client: Authlib OAuth 客户端实例
            token: OAuth 访问令牌

        Returns:
            标准化的用户信息字典，获取失败返回 None
        """
        try:
            # ----- GitHub 特殊处理 -----
            if provider == 'github':
                user_resp = client.get('user', token=token)
                user_resp.raise_for_status()
                user_data = user_resp.json()

                # GitHub 可能不在 /user 接口返回 email，需要额外调用 /user/emails
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
            'email': user_data.get('email') or None,
                    'avatar_url': user_data.get('avatar_url') or '',
                    'provider': provider,
                }

            # ----- 标准 OIDC 提供商处理 -----
            # 优先从 token 中提取 id_token claims（跳过签名验证以兼容各种提供商）
            id_token_claims = None
            if isinstance(token, dict) and token.get('id_token'):
                try:
                    import jwt as _jwt
                    id_token_claims = _jwt.decode(
                        token['id_token'],
                        options={'verify_signature': False, 'verify_exp': False},
                    )
                    if not isinstance(id_token_claims, dict):
                        id_token_claims = None
                    else:
                        self._logger_service.info(
                            f'ID Token claims extracted for {provider}: '
                            f'keys={",".join(sorted(id_token_claims.keys()))}'
                        )
                except Exception as ex:
                    self._logger_service.warning(f'Failed to decode id_token for {provider}: {str(ex)}')

            # 尝试从 ID Token 的 userinfo 字段获取
            token_user_data = self._normalize_user_data(token.get('userinfo')) if isinstance(token, dict) else None
            if token_user_data:
                if id_token_claims:
                    token_user_data.update(id_token_claims)
                self._logger_service.info(
                    'Using OIDC user info from token payload: '
                    f'provider={provider}, keys={",".join(sorted(token_user_data.keys()))}'
                )
                return self._build_oidc_user_info(provider, token_user_data)

            # 尝试调用 userinfo 端点
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

            # 用 id_token claims 覆盖 userinfo 数据（id_token 是签名的，更权威）
            if id_token_claims:
                print(f"[ROLE_DEBUG] id_token claims keys: {sorted(id_token_claims.keys())}")
                print(f"[ROLE_DEBUG] role fields: role={id_token_claims.get('role')}, roles={id_token_claims.get('roles')}, groups={id_token_claims.get('groups')}")
                for key in ('preferred_username', 'nickname', 'name', 'email', 'picture',
                           'avatar', 'avatar_url', 'role', 'roles', 'groups', 'group',
                           'user_type', 'authorities', 'memberOf', 'realm_access'):
                    if key in id_token_claims:
                        normalized_user_data[key] = id_token_claims[key]

            self._logger_service.info(
                'OIDC user info received: '
                f'provider={provider}, keys={",".join(sorted(normalized_user_data.keys()))}'
            )
            return self._build_oidc_user_info(provider, normalized_user_data)
        except Exception as ex:
            self._logger_service.error(f'Failed to fetch user info: {provider}', ex)
            return None

    # ============================================================
    # 提供商查询与验证
    # ============================================================

    def get_supported_providers(self) -> List[str]:
        """
        获取所有已配置的认证提供商名称列表

        返回顺序：GitHub > 自定义 OIDC 提供商（去重）

        Returns:
            提供商名称列表
        """
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
        """检查指定的提供商是否已配置且受支持"""
        return self.resolve_provider_name(provider) is not None
