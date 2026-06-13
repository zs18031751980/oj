"""Authentication API controllers."""

import asyncio
import json
from urllib.parse import urlparse, urlunparse, urlencode

from flask import redirect, request, session
from flask_restx import Namespace, Resource, fields
from werkzeug.security import check_password_hash

from core.di_container import inject
from interfaces.service_interfaces import IConfigService, IJWTService, IOIDCService, IUserService
from models.auth_models import TokenResponse, UserInfo


api = Namespace('auth', description='Authentication operations')

login_request_model = api.model('LoginRequest', {
    'provider': fields.String(required=True, description='OAuth provider'),
    'redirect_uri': fields.String(description='OAuth callback URL'),
})

login_response_model = api.model('LoginResponse', {
    'success': fields.Boolean(description='Whether the operation succeeded'),
    'authorization_url': fields.String(description='Authorization URL'),
    'error': fields.String(description='Error message'),
})

password_login_request_model = api.model('PasswordLoginRequest', {
    'identifier': fields.String(required=True, description='Username or email'),
    'password': fields.String(required=True, description='Password'),
})

token_request_model = api.model('TokenRequest', {
    'refresh_token': fields.String(required=True, description='Refresh token'),
})

token_response_model = api.model('TokenResponse', {
    'access_token': fields.String(description='Access token'),
    'refresh_token': fields.String(description='Refresh token'),
    'expires_in': fields.Integer(description='Token lifetime in seconds'),
    'token_type': fields.String(description='Token type'),
    'user_info': fields.Raw(description='User profile'),
})

auth_result_model = api.model('AuthResult', {
    'success': fields.Boolean(description='Whether the operation succeeded'),
    'user_info': fields.Raw(description='User profile'),
    'tokens': fields.Nested(token_response_model, description='Token payload'),
    'error': fields.String(description='Error message'),
})

providers_response_model = api.model('ProvidersResponse', {
    'providers': fields.List(fields.String(), description='Supported providers'),
})


def _frontend_callback_url(tokens: TokenResponse, user_info: UserInfo, next_path: str = '/') -> str:
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
    username = user_info_data.get('username', '') or ''
    email = user_info_data.get('email', '') or ''
    return UserInfo(
        id=str(user_info_data.get('id') or ''),
        username=username,
        email=email,
        name=user_info_data.get('name') or username or email,
        avatar_url=user_info_data.get('avatar_url', '') or '',
        provider=user_info_data.get('provider', provider),
    )


def _provider_config(provider: str) -> dict:
    config_service = inject(IConfigService)
    raw_configs = config_service.get_config('OIDC_PROVIDERS', {})
    normalized_provider = provider.casefold()

    if isinstance(raw_configs, dict):
        for provider_name, config in raw_configs.items():
            if str(provider_name).casefold() == normalized_provider and isinstance(config, dict):
                return config
        return {}

    if isinstance(raw_configs, list):
        for config in raw_configs:
            if isinstance(config, dict) and str(config.get('name', '')).casefold() == normalized_provider:
                return config

    return {}


def _provider_redirect_uri(provider: str) -> str:
    config_service = inject(IConfigService)
    provider_config = _provider_config(provider)
    configured_uri = (
        config_service.get_config(f'{provider.upper()}_REDIRECT_URI')
        or provider_config.get('redirect_uri')
        or provider_config.get('callback_url')
    )
    if configured_uri:
        return str(configured_uri)

    request_base_url = request.url_root.rstrip('/')
    if request_base_url:
        return f'{request_base_url}/auth/callback/{provider}'

    public_backend_url = config_service.get_config('PUBLIC_BACKEND_URL')
    if public_backend_url:
        parsed_url = urlparse(str(public_backend_url))
        backend_origin = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
        return f"{backend_origin.rstrip('/')}/auth/callback/{provider}"

    return f'/auth/callback/{provider}'


@api.route('/login')
class AuthLoginController(Resource):
    @api.expect(login_request_model)
    @api.doc('login')
    @api.response(200, 'Success', login_response_model)
    @api.response(400, 'Bad Request')
    def post(self):
        """Return an authorization URL for API clients."""
        oidc_service = inject(IOIDCService)
        data = request.get_json(silent=True) or {}
        provider = data.get('provider', '')
        redirect_uri = data.get('redirect_uri')

        if not provider:
            return {'success': False, 'error': '请输入登录方式'}, 400

        if not oidc_service.validate_provider(provider):
            return {'success': False, 'error': f'不支持的登录方式：{provider}'}, 400

        authorization_url = oidc_service.get_authorization_url(provider, redirect_uri)
        if not authorization_url:
            return {'success': False, 'error': '创建授权地址失败'}, 500

        return {'success': True, 'authorization_url': authorization_url}, 200


@api.route('/login/<provider>')
class AuthBrowserLoginController(Resource):
    @api.doc('browser_login')
    @api.response(302, 'Redirect to OAuth provider')
    @api.response(400, 'Bad Request')
    def get(self, provider: str):
        """Start browser-based OAuth login."""
        oidc_service = inject(IOIDCService)

        if not oidc_service.validate_provider(provider):
            return {'success': False, 'error': f'不支持的登录方式：{provider}'}, 400

        resolved_provider = oidc_service.resolve_provider_name(provider) or provider
        session['oauth_next'] = request.args.get('next', '/')
        redirect_uri = _provider_redirect_uri(resolved_provider)
        response = oidc_service.get_authorization_redirect(resolved_provider, redirect_uri)
        if not response:
            return {'success': False, 'error': '启动 OAuth 登录失败'}, 500

        return response


@api.route('/login/password')
class AuthPasswordLoginController(Resource):
    @api.expect(password_login_request_model)
    @api.doc('password_login')
    @api.response(200, 'Success', auth_result_model)
    @api.response(400, 'Bad Request')
    @api.response(401, 'Unauthorized')
    def post(self):
        """Authenticate a local account by username or email."""
        jwt_service = inject(IJWTService)
        user_service = inject(IUserService)
        data = request.get_json(silent=True) or {}
        identifier = str(data.get('identifier', '')).strip()
        password = str(data.get('password', ''))

        if not identifier:
            return {'success': False, 'error': '请输入用户名或邮箱'}, 400

        if not password:
            return {'success': False, 'error': '请输入密码'}, 400

        try:
            user_data = asyncio.run(user_service.get_user_with_password_hash_by_identifier(identifier))
        except Exception:
            return {'success': False, 'error': '查询用户失败，请重试'}, 500

        if not user_data:
            return {'success': False, 'error': '用户名、邮箱或密码错误'}, 401

        if not user_data.get('is_active', True):
            return {'success': False, 'error': '账号已被停用'}, 403

        password_hash = user_data.get('password_hash') or ''
        if not password_hash or not check_password_hash(password_hash, password):
            return {'success': False, 'error': '用户名、邮箱或密码错误'}, 401

        try:
            user_id = int(user_data.get('id'))
            asyncio.run(user_service.update_user_last_login(user_id))
        except Exception:
            # 登录不应因为最后登录时间更新失败而中断。
            pass

        user_info = _build_user_info('password', {
            'id': user_data.get('id'),
            'username': user_data.get('username', '') or user_data.get('email', ''),
            'email': user_data.get('email', ''),
            'name': user_data.get('username', '') or user_data.get('email', ''),
            'avatar_url': user_data.get('avatar_url', '') or '',
            'provider': 'password',
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


@api.route('/callback/<provider>')
class AuthCallbackController(Resource):
    @api.doc('auth_callback')
    @api.response(200, 'Success', auth_result_model)
    @api.response(400, 'Bad Request')
    def get(self, provider: str):
        """Handle OAuth callback and issue local JWT tokens."""
        oidc_service = inject(IOIDCService)
        jwt_service = inject(IJWTService)

        if not oidc_service.validate_provider(provider):
            return {'success': False, 'error': f'不支持的登录方式：{provider}'}, 400

        resolved_provider = oidc_service.resolve_provider_name(provider) or provider
        next_path = session.pop('oauth_next', '/')
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

        auth_result = oidc_service.authorize_callback(resolved_provider)
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

        user_info_data = auth_result['user_info']
        provider_id = str(user_info_data.get('id') or '')

        if provider_id:
            try:
                user_service = inject(IUserService)
                user_info_data = asyncio.run(
                    user_service.find_or_create_user(resolved_provider, provider_id, user_info_data)
                )
            except Exception:
                # OAuth login should still work when the optional user database is unavailable.
                pass

        user_info = _build_user_info(resolved_provider, user_info_data)
        jwt_tokens = jwt_service.generate_tokens(user_info.to_dict())
        token_response = TokenResponse(
            access_token=jwt_tokens.access_token,
            refresh_token=jwt_tokens.refresh_token,
            expires_in=jwt_tokens.expires_in,
            user_info=user_info,
        )

        if request.args.get('format') == 'json':
            return {
                'success': True,
                'user_info': user_info.to_dict(),
                'tokens': token_response.to_dict(),
            }, 200

        return redirect(_frontend_callback_url(token_response, user_info, next_path))


@api.route('/refresh')
class AuthRefreshController(Resource):
    @api.expect(token_request_model)
    @api.doc('refresh_token')
    @api.response(200, 'Success', token_response_model)
    @api.response(400, 'Bad Request')
    def post(self):
        """Refresh an access token."""
        jwt_service = inject(IJWTService)
        data = request.get_json(silent=True) or {}
        refresh_token = data.get('refresh_token', '')

        if not refresh_token:
            return {'error': 'refresh_token is required'}, 400

        new_tokens = jwt_service.refresh_access_token(refresh_token)
        if not new_tokens:
            return {'error': 'refresh_token is invalid or expired'}, 400

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
    @api.doc('logout')
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request')
    def post(self):
        """Revoke the current access token."""
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
    @api.doc('verify_token')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    def get(self):
        """Verify an access token."""
        jwt_service = inject(IJWTService)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'error': 'invalid authorization header'}, 401

        token = auth_header[7:]
        user_info = jwt_service.verify_access_token(token)
        if user_info:
            return {'valid': True, 'user_info': user_info}, 200
        return {'valid': False, 'error': 'token is invalid or expired'}, 401


@api.route('/providers')
class AuthProvidersController(Resource):
    @api.doc('list_providers')
    @api.response(200, 'Success', providers_response_model)
    def get(self):
        """List supported authentication providers."""
        oidc_service = inject(IOIDCService)
        return {'providers': oidc_service.get_supported_providers()}, 200
