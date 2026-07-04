"""
认证 API 控制器模块

提供所有与用户认证相关的 API 接口，包括：
- OAuth/OIDC 第三方登录（GitHub 等）
- 本地用户名/密码登录
- 通过外部提供商进行密码登录
- OAuth 回调处理
- JWT 令牌刷新
- 用户登出（令牌撤销）
- 令牌验证
- 支持的认证提供商列表查询
"""

import asyncio          # 异步 I/O 支持，用于调用异步服务方法
import json             # JSON 数据处理
from typing import Optional
from urllib.parse import urlparse, urlunparse, urlencode  # URL 解析与构建

import jwt             # PyJWT 库，用于解码未经验证的 JWT 令牌
import requests        # HTTP 请求库，用于调用外部认证服务
from flask import redirect, request, session    # Flask 核心模块
from flask_restx import Namespace, Resource, fields  # Flask-RESTX：API 命名空间、资源、模型字段
from werkzeug.security import check_password_hash   # Werkzeug 安全工具，用于密码哈希验证

from core.di_container import inject  # 依赖注入辅助函数
from interfaces.service_interfaces import IConfigService, IJWTService, ILoggerService, IOIDCService, IUserService
from models.auth_models import TokenResponse, UserInfo
from utils.role_utils import normalize_role, pick_highest_role


# ============================================================
# 1. API 命名空间与请求/响应模型定义
# ============================================================

# 创建认证相关的 API 命名空间（路由分组为 /auth）
api = Namespace('auth', description='用户认证相关接口')

# ---------- 请求模型 ----------

# OAuth 登录请求模型：指定登录提供商和回调地址
login_request_model = api.model('LoginRequest', {
    'provider': fields.String(required=True, description='OAuth 提供商名称（如 github）'),
    'redirect_uri': fields.String(description='OAuth 回调地址（可选）'),
})

# 用户名/密码登录请求模型
password_login_request_model = api.model('PasswordLoginRequest', {
    'identifier': fields.String(required=True, description='用户名或邮箱'),
    'password': fields.String(required=True, description='密码'),
    'remember': fields.Boolean(description='是否保持上游会话持续有效'),
})

# 令牌刷新请求模型
token_request_model = api.model('TokenRequest', {
    'refresh_token': fields.String(required=True, description='刷新令牌（Refresh Token）'),
})

# ---------- 响应模型 ----------

# 登录响应模型
login_response_model = api.model('LoginResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'authorization_url': fields.String(description='OAuth 授权地址'),
    'error': fields.String(description='错误信息'),
})

# 令牌响应模型（包含访问令牌和刷新令牌）
token_response_model = api.model('TokenResponse', {
    'access_token': fields.String(description='访问令牌（Access Token）'),
    'refresh_token': fields.String(description='刷新令牌（Refresh Token）'),
    'expires_in': fields.Integer(description='令牌有效期（秒）'),
    'token_type': fields.String(description='令牌类型（如 Bearer）'),
    'user_info': fields.Raw(description='用户信息'),
})

# 认证结果模型
auth_result_model = api.model('AuthResult', {
    'success': fields.Boolean(description='操作是否成功'),
    'user_info': fields.Raw(description='用户信息'),
    'tokens': fields.Nested(token_response_model, description='令牌数据'),
    'error': fields.String(description='错误信息'),
})

# 提供商列表响应模型
providers_response_model = api.model('ProvidersResponse', {
    'providers': fields.List(fields.String(), description='支持的认证提供商列表'),
})


# ============================================================
# 2. 辅助函数（工具方法）
# ============================================================

def _frontend_callback_url(tokens: TokenResponse, user_info: UserInfo, next_path: str = '/') -> str:
    """
    构建 OAuth 登录成功后重定向到前端的回调 URL

    将 JWT 令牌和用户信息作为 URL 查询参数传递给前端，
    前端通过 /auth/callback 路由接收这些参数并完成登录流程。

    Args:
        tokens: JWT 令牌响应（包含 access_token 和 refresh_token）
        user_info: 用户信息
        next_path: 登录成功后的目标跳转路径

    Returns:
        完整的前端回调 URL
    """
    config_service = inject(IConfigService)
    frontend_url = config_service.get_config('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
    safe_next = next_path if next_path.startswith('/') else '/'
    query = urlencode({
        'access_token': tokens.access_token,
        'refresh_token': tokens.refresh_token,
        'expires_in': tokens.expires_in,
        'token_type': tokens.token_type,
        'user_info': json.dumps(user_info.to_dict(), ensure_ascii=False),
        'provider': user_info.provider,
        'next': safe_next,
    })
    return f'{frontend_url}/auth/callback?{query}'


def _frontend_error_callback_url(
    error: str,
    next_path: str = '/',
    provider: str = '',
    error_description: str = '',
) -> str:
    """
    构建 OAuth 登录失败时重定向到前端的错误回调 URL

    将错误信息作为查询参数传递给前端，前端可以读取并显示友好的错误提示。

    Args:
        error: 错误代码或简要描述
        next_path: 原始请求的目标路径
        provider: 认证提供商名称（可选）
        error_description: 详细的错误描述（可选）

    Returns:
        包含错误信息的前端回调 URL
    """
    config_service = inject(IConfigService)
    frontend_url = config_service.get_config('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
    safe_next = next_path if next_path.startswith('/') else '/'
    query = {
        'error': error,
        'next': safe_next,
    }
    if provider:
        query['provider'] = provider
    if error_description:
        query['error_description'] = error_description
    return f'{frontend_url}/auth/callback?{urlencode(query)}'


def _build_user_info(provider: str, user_info_data: dict) -> UserInfo:
    """
    从原始用户数据字典构建 UserInfo 对象

    将来自不同 OAuth 提供商的用户数据统一转换为标准格式。

    Args:
        provider: 认证提供商名称
        user_info_data: 用户原始数据字典

    Returns:
        标准化后的 UserInfo 对象
    """
    username = user_info_data.get('username', '') or ''
    email = user_info_data.get('email', '') or ''
    role = normalize_role(user_info_data.get('role', 'member'))
    return UserInfo(
        id=str(user_info_data.get('id') or ''),
        username=username,
        email=email,
        name=user_info_data.get('name') or username or email,
        avatar_url=user_info_data.get('avatar_url', '') or '',
        provider=user_info_data.get('provider', provider),
        role=role,
        theme_preference=user_info_data.get('theme_preference', 'system'),
    )


def _provider_config(provider: str) -> dict:
    """
    获取指定认证提供商的配置信息

    支持从字典或列表格式的 OIDC_PROVIDERS 配置中查找，且大小写不敏感。

    Args:
        provider: 提供商名称

    Returns:
        提供商配置字典，如果未找到则返回空字典
    """
    config_service = inject(IConfigService)
    raw_configs = config_service.get_config('OIDC_PROVIDERS', {})
    normalized_provider = provider.casefold()

    # 处理字典格式的配置：{"provider_name": {...}}
    if isinstance(raw_configs, dict):
        for provider_name, config in raw_configs.items():
            if str(provider_name).casefold() == normalized_provider and isinstance(config, dict):
                return config
        return {}

    # 处理列表格式的配置：[{"name": "provider_name", ...}]
    if isinstance(raw_configs, list):
        for config in raw_configs:
            if isinstance(config, dict) and str(config.get('name', '')).casefold() == normalized_provider:
                return config

    return {}


def _provider_issuer(provider_config: dict) -> str:
    """从提供商配置中获取颁发者（Issuer）地址"""
    issuer = provider_config.get('issuer') or provider_config.get('api_base_url') or ''
    return str(issuer).rstrip('/')


def _provider_client_id(provider_config: dict) -> str:
    """从提供商配置中获取客户端 ID"""
    return str(provider_config.get('client_id') or '')


def _provider_scope(provider_config: dict) -> str:
    """从提供商配置中获取 OAuth 授权范围（Scope）"""
    client_kwargs = provider_config.get('client_kwargs')
    if isinstance(client_kwargs, dict):
        return str(client_kwargs.get('scope') or '')
    return ''


def _decode_unverified_jwt(token: str) -> dict:
    """
    解码但不对 JWT 令牌进行签名验证

    用于从外部提供商返回的令牌中提取声明信息（如 sub、email 等），
    这些令牌是由外部提供商签发的，我们只关心其中的用户信息。

    Args:
        token: JWT 字符串

    Returns:
        解码后的声明字典，解码失败返回空字典
    """
    try:
        payload = jwt.decode(token, options={'verify_signature': False, 'verify_exp': False})
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _user_info_from_provider_token(provider: str, identifier: str, token: str) -> dict:
    """
    从外部提供商签发的 JWT 令牌中提取用户信息

    这些令牌由第三方认证服务签发（如 IOSClub），其中包含了用户的身份信息。
    函数从令牌的声明中提取各种用户字段（sub、username、email 等）。

    Args:
        provider: 提供商名称
        identifier: 用户标识（如用户名）
        token: 提供商签发的 JWT 令牌

    Returns:
        包含用户信息的字典
    """
    claims = _decode_unverified_jwt(token)
    subject = (
        claims.get('sub')
        or claims.get('id')
        or claims.get('user_id')
        or claims.get('uid')
        or claims.get('userId')
        or identifier
    )
    username = (
        claims.get('preferred_username')
        or claims.get('nickname')
        or claims.get('username')
        or claims.get('name')
        or claims.get('userId')
        or identifier
    )
    email = claims.get('email') or ''
    name = claims.get('name') or claims.get('nickname') or username or email or str(subject)

    # 从 JWT claims 中收集所有角色，选取权限最高的
    all_roles = []
    raw_role = claims.get('role')
    if raw_role:
        if isinstance(raw_role, list):
            all_roles.extend(raw_role)
        elif isinstance(raw_role, str) and raw_role:
            all_roles.append(raw_role)
    for field in ('roles', 'groups', 'group', 'user_type', 'authorities', 'memberOf'):
        val = claims.get(field)
        if val:
            if isinstance(val, list):
                all_roles.extend(val)
            elif isinstance(val, str):
                all_roles.append(val)
    role = pick_highest_role(all_roles) if all_roles else 'member'
    return {
        'id': str(subject),
        'username': str(username or ''),
        'email': str(email or ''),
        'name': str(name or ''),
        'avatar_url': (
            claims.get('picture')
            or claims.get('avatar')
            or claims.get('avatar_url')
            or ''
        ),
        'provider': provider,
        'role': role,
    }


def _issue_tokens_for_provider_user(provider: str, user_info_data: dict):
    """
    为通过外部提供商登录的用户签发 JWT 令牌

    此函数完成以下步骤：
    1. 尝试在本地数据库中查找或创建用户记录（可选）
    2. 构建标准化的用户信息
    3. 生成 JWT 访问令牌和刷新令牌

    Args:
        provider: 提供商名称
        user_info_data: 来自提供商的用户数据字典

    Returns:
        (user_info, token_response) 元组
    """
    jwt_service = inject(IJWTService)
    provider_id = str(user_info_data.get('id') or '')

    # 如果存在提供商用户 ID，尝试在本地数据库同步用户信息
    if provider_id:
        try:
            user_service = inject(IUserService)
            user_info_data = asyncio.run(
                user_service.find_or_create_user(provider, provider_id, user_info_data)
            )
        except Exception as e:
            logger_service = inject(ILoggerService)
            import traceback as _tb
            logger_service.error(f'用户同步失败 (provider={provider}, id={provider_id}): {e}\n{_tb.format_exc()}')

    user_info = _build_user_info(provider, user_info_data)
    jwt_tokens = jwt_service.generate_tokens(user_info.to_dict())
    token_response = TokenResponse(
        access_token=jwt_tokens.access_token,
        refresh_token=jwt_tokens.refresh_token,
        expires_in=jwt_tokens.expires_in,
        token_type=jwt_tokens.token_type,
        user_info=user_info,
    )
    return user_info, token_response


def _provider_redirect_uri_result(provider: str, callback_provider: Optional[str] = None):
    """
    解析 OAuth 回调重定向地址，按优先级返回地址和来源

    优先级：
    1. 环境变量中 `${PROVIDER}_REDIRECT_URI` 的配置
    2. PUBLIC_BACKEND_URL + "/auth/callback/{provider}"
    3. request.url_root（当前请求的基础 URL）
    4. OIDC_PROVIDERS 配置中的 redirect_uri 字段
    5. OIDC_PROVIDERS 配置中的 callback_url 字段
    6. 相对路径回调（兜底方案）

    Args:
        provider: 提供商名称
        callback_provider: 回调路径中使用的提供商名称（可选）

    Returns:
        (redirect_uri, source) 元组，source 标识了该 URL 的来源
    """
    config_service = inject(IConfigService)
    provider_config = _provider_config(provider)
    callback_provider = callback_provider or provider

    # 优先级 1：环境变量中的显式配置
    env_key = f'{provider.upper()}_REDIRECT_URI'
    env_uri = config_service.get_config(env_key)
    if env_uri:
        return str(env_uri), env_key

    # 优先级 2：基于 PUBLIC_BACKEND_URL 构建
    public_backend_url = config_service.get_config('PUBLIC_BACKEND_URL')
    if public_backend_url:
        parsed_url = urlparse(str(public_backend_url))
        backend_origin = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
        return f"{backend_origin.rstrip('/')}/auth/callback/{callback_provider}", 'PUBLIC_BACKEND_URL'

    # 优先级 3：基于当前请求的根 URL
    request_base_url = request.url_root.rstrip('/')
    if request_base_url:
        return f'{request_base_url}/auth/callback/{callback_provider}', 'request.url_root'

    # 优先级 4：OIDC_PROVIDERS 配置中的 redirect_uri
    if provider_config.get('redirect_uri'):
        return str(provider_config['redirect_uri']), 'OIDC_PROVIDERS.redirect_uri'

    # 优先级 5：OIDC_PROVIDERS 配置中的 callback_url
    if provider_config.get('callback_url'):
        return str(provider_config['callback_url']), 'OIDC_PROVIDERS.callback_url'

    # 优先级 6：相对路径兜底
    return f'/auth/callback/{callback_provider}', 'relative_fallback'


def _provider_redirect_uri(provider: str, callback_provider: Optional[str] = None) -> str:
    """获取 OAuth 回调重定向地址（仅返回地址部分）"""
    redirect_uri, _source = _provider_redirect_uri_result(provider, callback_provider)
    return redirect_uri


# ============================================================
# 3. API 端点（路由控制器）
# ============================================================

@api.route('/login')
class AuthLoginController(Resource):
    """
    API 客户端 OAuth 登录接口

    接受提供商名称，返回该提供商的 OAuth 授权 URL，
    供 API 客户端（非浏览器环境）使用。
    """

    @api.expect(login_request_model)
    @api.doc('login')
    @api.response(200, 'Success', login_response_model)
    @api.response(400, 'Bad Request')
    def post(self):
        """为 API 客户端生成 OAuth 授权 URL"""
        oidc_service = inject(IOIDCService)
        data = request.get_json(silent=True) or {}
        provider = data.get('provider', '')
        redirect_uri = data.get('redirect_uri')

        if not provider:
            return {'success': False, 'error': '请输入登录方式'}, 400

        if not oidc_service.validate_provider(provider):
            return {'success': False, 'error': f'不支持的登录方式：{provider}'}, 400

        resolved_provider = oidc_service.resolve_provider_name(provider) or provider
        redirect_uri = redirect_uri or _provider_redirect_uri(resolved_provider, provider)
        authorization_url = oidc_service.get_authorization_url(resolved_provider, redirect_uri)
        if not authorization_url:
            return {'success': False, 'error': '创建授权地址失败'}, 500

        return {'success': True, 'authorization_url': authorization_url}, 200


@api.route('/login/<provider>')
class AuthBrowserLoginController(Resource):
    """
    浏览器 OAuth 登录接口

    通过 GET 请求重定向到指定 OAuth 提供商的登录页面，
    适用于浏览器环境中的用户主动登录。
    """

    @api.doc('browser_login')
    @api.response(302, 'Redirect to OAuth provider')
    @api.response(400, 'Bad Request')
    def get(self, provider: str):
        """启动基于浏览器的 OAuth 登录流程（重定向到第三方登录页）"""
        oidc_service = inject(IOIDCService)
        logger_service = inject(ILoggerService)

        if not oidc_service.validate_provider(provider):
            return {'success': False, 'error': f'不支持的登录方式：{provider}'}, 400

        resolved_provider = oidc_service.resolve_provider_name(provider) or provider
        # 保存登录成功后的跳转路径到 session 中
        session['oauth_next'] = request.args.get('next', '/')
        redirect_uri, redirect_uri_source = _provider_redirect_uri_result(resolved_provider, provider)
        session['oauth_redirect_uri'] = redirect_uri
        logger_service.info(
            'Starting OAuth login: '
            f'requested_provider={provider}, '
            f'provider={resolved_provider}, '
            f'redirect_uri={redirect_uri}, '
            f'redirect_uri_source={redirect_uri_source}, '
            f'request_host={request.host}, '
            f'url_root={request.url_root}'
        )
        response = oidc_service.get_authorization_redirect(resolved_provider, redirect_uri)
        if not response:
            return {'success': False, 'error': '启动 OAuth 登录失败'}, 500

        return response


@api.route('/login/password')
class AuthPasswordLoginController(Resource):
    """
    本地用户名/密码登录接口

    通过本地数据库中的用户名或邮箱和密码进行身份验证，
    验证通过后签发 JWT 令牌。
    """

    @api.expect(password_login_request_model)
    @api.doc('password_login')
    @api.response(200, 'Success', auth_result_model)
    @api.response(400, 'Bad Request')
    @api.response(401, 'Unauthorized')
    def post(self):
        """通过用户名或邮箱进行本地账号密码登录"""
        jwt_service = inject(IJWTService)
        user_service = inject(IUserService)
        data = request.get_json(silent=True) or {}
        identifier = str(data.get('identifier', '')).strip()
        password = str(data.get('password', ''))

        # 验证请求参数
        if not identifier:
            return {'success': False, 'error': '请输入用户名或邮箱'}, 400
        if not password:
            return {'success': False, 'error': '请输入密码'}, 400

        # 根据用户名或邮箱查询用户（包含密码哈希）
        try:
            user_data = asyncio.run(user_service.get_user_with_password_hash_by_identifier(identifier))
        except Exception:
            return {'success': False, 'error': '查询用户失败，请重试'}, 500

        if not user_data:
            return {'success': False, 'error': '用户名、邮箱或密码错误'}, 401

        # 检查账号是否被停用
        if not user_data.get('is_active', True):
            return {'success': False, 'error': '账号已被停用'}, 403

        # 验证密码哈希
        password_hash = user_data.get('password_hash') or ''
        if not password_hash or not check_password_hash(password_hash, password):
            return {'success': False, 'error': '用户名、邮箱或密码错误'}, 401

        # 更新最后登录时间（非关键操作，失败不影响登录）
        try:
            user_id = int(user_data.get('id'))
            asyncio.run(user_service.update_user_last_login(user_id))
        except Exception:
            pass

        # 构建用户信息并签发 JWT 令牌
        user_info = _build_user_info('password', {
            'id': user_data.get('id'),
            'username': user_data.get('username', '') or user_data.get('email', ''),
            'email': user_data.get('email', ''),
            'name': user_data.get('username', '') or user_data.get('email', ''),
            'avatar_url': user_data.get('avatar_url', '') or '',
            'provider': 'password',
            'role': user_data.get('role', 'member'),
            'theme_preference': user_data.get('theme_preference', 'system'),
        })
        jwt_tokens = jwt_service.generate_tokens(user_info.to_dict())
        token_response = TokenResponse(
            access_token=jwt_tokens.access_token,
            refresh_token=jwt_tokens.refresh_token,
            expires_in=jwt_tokens.expires_in,
            token_type=jwt_tokens.token_type,
            user_info=user_info,
        )

        return {
            'success': True,
            'user_info': user_info.to_dict(),
            'tokens': token_response.to_dict(),
        }, 200


@api.route('/login/<provider>/password')
class AuthProviderPasswordLoginController(Resource):
    """
    外部提供商密码登录接口

    通过已配置的 OIDC 提供商进行密码登录（不经过 OAuth 浏览器跳转）。
    适用于支持 Resource Owner Password Credentials (ROPC) 流程的认证服务。
    """

    @api.expect(password_login_request_model)
    @api.doc('provider_password_login')
    @api.response(200, 'Success', auth_result_model)
    @api.response(400, 'Bad Request')
    @api.response(401, 'Unauthorized')
    def post(self, provider: str):
        """通过已配置的 OIDC 提供商进行密码登录（绕过 OAuth 浏览器跳转）"""
        oidc_service = inject(IOIDCService)
        logger_service = inject(ILoggerService)
        config_service = inject(IConfigService)
        data = request.get_json(silent=True) or {}
        identifier = str(data.get('identifier', '')).strip()
        password = str(data.get('password', ''))
        remember = bool(data.get('remember', True))

        # 验证请求参数
        if not identifier:
            return {'success': False, 'error': 'identifier is required'}, 400
        if not password:
            return {'success': False, 'error': 'password is required'}, 400

        # 验证提供商是否支持
        if not oidc_service.validate_provider(provider):
            return {'success': False, 'error': f'unsupported provider: {provider}'}, 400

        # 解析提供商配置（颁发者、客户端 ID、授权范围）
        resolved_provider = oidc_service.resolve_provider_name(provider) or provider
        provider_config = _provider_config(resolved_provider)
        issuer = _provider_issuer(provider_config)
        client_id = _provider_client_id(provider_config)
        scope = _provider_scope(provider_config)

        if not issuer or not client_id:
            return {'success': False, 'error': 'provider login is not configured'}, 500

        # 调用外部提供商的登录 API
        login_url = f'{issuer}/Auth/login'
        request_params = {'clientId': client_id}
        if scope:
            request_params['scope'] = scope

        try:
            response = requests.post(
                login_url,
                params=request_params,
                json={
                    'userId': identifier,
                    'password': password,
                    'rememberMe': remember,
                },
                timeout=max(int(config_service.get_timeout()), 5),
            )
            response_data = response.json()
        except Exception as ex:
            logger_service.error(f'Provider password login request failed: {resolved_provider}', ex)
            return {'success': False, 'error': 'provider login request failed'}, 502

        # 检查上游响应是否成功
        if (
            not response.ok
            or not isinstance(response_data, dict)
            or response_data.get('errorCode') not in (None, 0)
            or not response_data.get('data')
        ):
            upstream_message = (
                response_data.get('message')
                if isinstance(response_data, dict)
                else ''
            )
            return {
                'success': False,
                'error': upstream_message or 'provider username or password is invalid',
            }, 401

        # 从提供商返回的 JWT 令牌中提取用户信息，然后签发本地 JWT 令牌
        provider_token = str(response_data.get('data') or '')
        user_info_data = _user_info_from_provider_token(resolved_provider, identifier, provider_token)
        user_info, token_response = _issue_tokens_for_provider_user(resolved_provider, user_info_data)

        return {
            'success': True,
            'user_info': user_info.to_dict(),
            'tokens': token_response.to_dict(),
        }, 200


@api.route('/callback/<provider>')
class AuthCallbackController(Resource):
    """
    OAuth 回调处理接口

    接收 OAuth 提供商在用户授权后回调的授权码（code），
    通过授权码换取令牌，获取用户信息，签发本地 JWT 令牌，
    最后重定向回前端或返回 JSON 格式的认证结果。
    """

    @api.doc('auth_callback')
    @api.response(200, 'Success', auth_result_model)
    @api.response(400, 'Bad Request')
    def get(self, provider: str):
        """处理 OAuth 回调并签发本地 JWT 令牌"""
        oidc_service = inject(IOIDCService)
        jwt_service = inject(IJWTService)

        if not oidc_service.validate_provider(provider):
            return {'success': False, 'error': f'不支持的登录方式：{provider}'}, 400

        resolved_provider = oidc_service.resolve_provider_name(provider) or provider
        # 从 session 中取出登录前保存的跳转路径和回调地址
        next_path = session.pop('oauth_next', '/')
        redirect_uri = session.pop('oauth_redirect_uri', None) or _provider_redirect_uri(resolved_provider, provider)

        # 处理 OAuth 提供商返回的错误（用户拒绝授权等情况）
        error = request.args.get('error')
        if error:
            error_description = request.args.get('error_description', '')
            if request.args.get('format') == 'json':
                return {
                    'success': False,
                    'error': error,
                    'error_description': error_description,
                }, 400
            return redirect(
                _frontend_error_callback_url(
                    error,
                    next_path,
                    resolved_provider,
                    error_description,
                )
            )

        # 检查是否缺少授权码
        if not request.args.get('code'):
            if request.args.get('format') == 'json':
                return {'success': False, 'error': '缺少授权码'}, 400
            return redirect(
                _frontend_error_callback_url(
                    '缺少授权码',
                    next_path,
                    resolved_provider,
                )
            )

        # 通过授权码向提供商换取访问令牌和用户信息
        auth_result = oidc_service.authorize_callback(resolved_provider, redirect_uri)
        if not auth_result or not auth_result.get('user_info'):
            if request.args.get('format') == 'json':
                return {'success': False, 'error': 'OAuth 登录失败，请重试'}, 500
            return redirect(
                _frontend_error_callback_url(
                    'OAuth 登录失败，请重试',
                    next_path,
                    resolved_provider,
                )
            )

        # 尝试在本地数据库同步用户信息
        user_info_data = auth_result['user_info']
        provider_id = str(user_info_data.get('id') or '')
        if provider_id:
            try:
                user_service = inject(IUserService)
                user_info_data = asyncio.run(
                    user_service.find_or_create_user(resolved_provider, provider_id, user_info_data)
                )
            except Exception as e:
                logger_service = inject(ILoggerService)
                import traceback as _tb
                logger_service.error(f'用户同步失败 (provider={resolved_provider}, id={provider_id}): {e}\n{_tb.format_exc()}')

        # 签发本地 JWT 令牌
        user_info = _build_user_info(resolved_provider, user_info_data)
        jwt_tokens = jwt_service.generate_tokens(user_info.to_dict())
        token_response = TokenResponse(
            access_token=jwt_tokens.access_token,
            refresh_token=jwt_tokens.refresh_token,
            expires_in=jwt_tokens.expires_in,
            user_info=user_info,
        )

        # 根据 format 参数决定返回 JSON 还是重定向到前端
        if request.args.get('format') == 'json':
            return {
                'success': True,
                'user_info': user_info.to_dict(),
                'tokens': token_response.to_dict(),
            }, 200

        return redirect(_frontend_callback_url(token_response, user_info, next_path))


@api.route('/refresh')
class AuthRefreshController(Resource):
    """
    令牌刷新接口

    使用刷新令牌（Refresh Token）获取新的访问令牌（Access Token）。
    当访问令牌过期时，客户端可以使用此接口获取新的令牌对。
    """

    @api.expect(token_request_model)
    @api.doc('refresh_token')
    @api.response(200, 'Success', token_response_model)
    @api.response(400, 'Bad Request')
    def post(self):
        """使用刷新令牌获取新的访问令牌"""
        jwt_service = inject(IJWTService)
        data = request.get_json(silent=True) or {}
        refresh_token = data.get('refresh_token', '')

        if not refresh_token:
            return {'error': 'refresh_token is required'}, 400

        new_tokens = jwt_service.refresh_access_token(refresh_token)
        if not new_tokens:
            return {'error': 'refresh_token is invalid or expired'}, 400

        # 从新的访问令牌中解析用户信息
        user_info = jwt_service.verify_access_token(new_tokens.access_token)
        user_obj = UserInfo(**user_info) if user_info else None
        token_response = TokenResponse(
            access_token=new_tokens.access_token,
            refresh_token=new_tokens.refresh_token,
            expires_in=new_tokens.expires_in,
            user_info=user_obj,
        )
        return token_response.to_dict(), 200


@api.route('/logout')
class AuthLogoutController(Resource):
    """
    用户登出接口

    将当前的访问令牌加入黑名单，使其立即失效。
    前端应清除本地存储的令牌。
    """

    @api.doc('logout')
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request')
    def post(self):
        """撤销当前访问令牌（登出）"""
        jwt_service = inject(IJWTService)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'error': 'invalid authorization header'}, 400

        token = auth_header[7:]
        if jwt_service.revoke_token(token):
            return {'message': 'logout successful'}, 200
        return {'error': 'failed to revoke token'}, 400


@api.route('/verify')
class AuthVerifyController(Resource):
    """
    令牌验证接口

    验证当前请求携带的 Bearer 令牌是否有效，
    返回用户信息和令牌有效性状态。
    """

    @api.doc('verify_token')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    def get(self):
        """验证访问令牌的有效性"""
        jwt_service = inject(IJWTService)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'error': 'invalid authorization header'}, 401

        token = auth_header[7:]
        user_info = jwt_service.verify_access_token(token)
        if user_info:
            return {'valid': True, 'user_info': user_info}, 200
        return {'valid': False, 'error': 'token is invalid or expired'}, 401


@api.route('/theme')
class AuthThemeController(Resource):
    """
    主题偏好更新接口
    允许已登录用户保存他们的主题偏好（light / dark / system）到数据库
    """

    @api.doc('update_theme')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    @api.response(400, 'Bad Request')
    def patch(self):
        """更新当前用户的主题偏好"""
        jwt_service = inject(IJWTService)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'error': 'unauthorized'}, 401

        token = auth_header[7:]
        user_info = jwt_service.verify_access_token(token)
        if not user_info:
            return {'error': 'unauthorized'}, 401

        data = request.get_json(silent=True) or {}
        theme_preference = data.get('theme_preference', '')
        if theme_preference not in ('light', 'dark', 'system'):
            return {'error': 'invalid theme_preference, must be light, dark, or system'}, 400

        from models.db_models import User

        try:
            user_id = int(user_info.get('id', 0))
            user = User.get_by_id(user_id)
            user.theme_preference = theme_preference
            user.save()

            user_info['theme_preference'] = theme_preference
            jwt_service.refresh_cached_user(str(user_id), user_info)

            return {'success': True}, 200
        except Exception:
            return {'error': 'user not found'}, 404



@api.route('/providers')
class AuthProvidersController(Resource):
    """
    认证提供商列表接口

    返回当前系统支持的所有认证提供商名称列表，
    供前端展示可用的第三方登录方式。
    """

    @api.doc('list_providers')
    @api.response(200, 'Success', providers_response_model)
    def get(self):
        """获取支持的认证提供商列表"""
        oidc_service = inject(IOIDCService)
        return {'providers': oidc_service.get_supported_providers()}, 200
