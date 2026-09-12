"""
LetCoding API 主入口模块

该模块是 Flask 应用的入口点，负责：
- 加载环境变量配置（.env 文件）
- 初始化 Flask 应用实例并注册配置
- 初始化依赖注入容器和服务
- 注册 API 路由命名空间
- 配置 CORS 跨域支持和反向代理支持
"""

import ast          # 用于安全解析 Python 字面量表达式（解析 OIDC 配置）
import json         # 用于解析 JSON 格式的配置（OIDC 提供商配置）
import os           # 用于读取环境变量
import time         # 用于时区设置
import re           # 用于正则匹配 .env 文件中的 OIDC_PROVIDERS 配置
from pathlib import Path  # 用于跨平台路径操作

# 统一后端时间基准为 UTC+8（Asia/Shanghai）：模型默认 created_at/updated_at 使用
# datetime.now()，若线上主机时区非 UTC+8 会导致与数据库 now() 不一致。固定进程时区，
# 强制将进程时区固定为 Asia/Shanghai（UTC+8）。
# 注意：必须使用赋值而非 setdefault——Zeabur 等平台默认注入 TZ=UTC，
# 若用 setdefault 则无法覆盖，会导致 datetime.now() 返回 UTC，而数据库会话(session)
# 时区为 Asia/Shanghai，二者不一致将产生 8 小时偏差（created_at/submitted_at/
# 比赛开始结束时间/排行榜罚时等全部错位）。
# 配合数据库连接会话的 timezone=Asia/Shanghai，保证全链路时间统一为 UTC+8。
os.environ['TZ'] = 'Asia/Shanghai'
try:
    time.tzset()
except Exception:
    pass

from dotenv import find_dotenv, load_dotenv  # 用于加载 .env 环境变量文件
from flask import Flask, request              # Flask 核心框架
from flask_restx import Api                   # Flask-RESTX 扩展，用于构建 RESTful API 和 Swagger 文档
import gzip
import io
from werkzeug.middleware.proxy_fix import ProxyFix  # 用于解决反向代理下的请求头问题

from models.db_models import create_tables, migrate_add_role_column, run_schema_migrations, seed_problem_catalog
from core.db_robust import DatabaseUnavailableError, sanitize_db_error

# 导入 API 命名空间
from controllers.auth_controller import api as auth_api
from controllers.code_controller import api as code_api
from controllers.submission_controller import api as submission_api
from controllers.user_code_controller import api as user_code_api
from controllers.announcement_controller import api as announcement_api
from controllers.problem_controller import api as problem_api
from controllers.admin_controller import api as admin_api
from controllers.favorite_controller import api as favorite_api
from controllers.contest_controller import api as contest_api
from controllers.contest_operations_controller import api as contest_operations_api
from controllers.discussion_controller import api as discussion_api
from controllers.rankings_controller import api as rankings_api
from controllers.contest_rankings_controller import api as contest_rankings_api
from controllers.contest_problem_controller import api as contest_problem_api
from controllers.learn_favorite_controller import api as learn_favorite_api
from controllers.learn_history_controller import api as learn_history_api
from controllers.learn_resources_controller import api as learn_resources_api
from controllers.user_controller import api as user_api
# 导入依赖注入容器和服务配置
from core.di_container import get_container
from core.service_config import setup_services
from interfaces.service_interfaces import IOIDCService



def _load_oidc_providers_config():
    """
    加载 OIDC（OpenID Connect）第三方登录提供商的配置信息。

    加载优先级：
    1. 先尝试从环境变量 OIDC_PROVIDERS 中读取（支持 JSON 或 Python 字面量格式）
    2. 如果环境变量中不存在，则从 .env 文件中通过正则表达式匹配提取
    3. 如果仍然找不到，返回空字典

    Returns:
        dict 或 list: OIDC 提供商的配置信息，格式如 {"provider_name": {...}}
    """
    # 优先从系统环境变量中读取
    raw_value = os.environ.get('OIDC_PROVIDERS')
    if raw_value:
        # 尝试用 JSON 解析，如果失败则尝试用 Python 字面量解析
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(raw_value)
                if isinstance(parsed, (dict, list)):
                    return _merge_oidc_providers_with_env(parsed)
            except Exception:
                pass

    return _merge_oidc_providers_with_env({})


def _normalize_provider_env_prefix(provider_name: str) -> str:
    """将 provider 名称转换为环境变量前缀，如 iOSClub -> IOSCLUB"""
    return re.sub(r'[^A-Za-z0-9]+', '_', str(provider_name or '').strip()).upper()


def _provider_config_from_env(provider_name: str):
    """
    从独立环境变量中构建单个 OIDC provider 配置。

    支持的变量：
    - <PROVIDER>_ISSUER
    - <PROVIDER>_CLIENT_ID
    - <PROVIDER>_CLIENT_SECRET
    - <PROVIDER>_REDIRECT_URI
    - <PROVIDER>_CALLBACK_URL
    - <PROVIDER>_SCOPE
    """
    env_prefix = _normalize_provider_env_prefix(provider_name)
    issuer = os.environ.get(f'{env_prefix}_ISSUER', '').strip()
    client_id = os.environ.get(f'{env_prefix}_CLIENT_ID', '').strip()
    client_secret = os.environ.get(f'{env_prefix}_CLIENT_SECRET', '').strip()
    redirect_uri = os.environ.get(f'{env_prefix}_REDIRECT_URI', '').strip()
    callback_url = os.environ.get(f'{env_prefix}_CALLBACK_URL', '').strip()
    scope = os.environ.get(f'{env_prefix}_SCOPE', '').strip()

    if not any((issuer, client_id, client_secret, redirect_uri, callback_url, scope)):
        return None

    provider_config = {'name': provider_name}
    if issuer:
        provider_config['issuer'] = issuer
    if client_id:
        provider_config['client_id'] = client_id
    if client_secret:
        provider_config['client_secret'] = client_secret
    if redirect_uri:
        provider_config['redirect_uri'] = redirect_uri
    if callback_url:
        provider_config['callback_url'] = callback_url
    if scope:
        provider_config['client_kwargs'] = {'scope': scope}

    return provider_config


def _merge_oidc_providers_with_env(base_config):
    """
    将 OIDC_PROVIDERS 与独立环境变量合并。

    这样域名、issuer、redirect_uri 等可以通过环境变量覆盖，
    后续换域名时无需修改代码或 JSON 配置块。
    """
    merged_configs = {}

    if isinstance(base_config, dict):
        for provider_name, config in base_config.items():
            if isinstance(config, dict):
                normalized_config = dict(config)
                normalized_config.setdefault('name', provider_name)
                merged_configs[str(provider_name)] = normalized_config
    elif isinstance(base_config, list):
        for config in base_config:
            if not isinstance(config, dict):
                continue
            provider_name = str(config.get('name') or '').strip()
            if not provider_name:
                continue
            merged_configs[provider_name] = dict(config)

    declared_provider_names = [
        name.strip()
        for name in os.environ.get('OIDC_PROVIDER_NAMES', '').split(',')
        if name.strip()
    ]

    for provider_name in declared_provider_names:
        merged_configs.setdefault(provider_name, {'name': provider_name})

    for provider_name in list(merged_configs.keys()):
        env_config = _provider_config_from_env(provider_name)
        if env_config:
            merged_configs[provider_name].update(env_config)

    return list(merged_configs.values())


def create_app(overrides=None):
    if os.environ.get('APP_ENV') == 'development':
        load_dotenv(Path(__file__).with_name('.env'), override=False)
    app = Flask(__name__)

    # 配置 ProxyFix 中间件，用于处理反向代理（如 Nginx）传递的请求头信息
    # x_for=1: 信任 X-Forwarded-For 的第一个 IP
    # x_proto=1: 信任 X-Forwarded-Proto（HTTP/HTTPS）
    # x_host=1: 信任 X-Forwarded-Host
    # x_port=1: 信任 X-Forwarded-Port
    proxy_hops = int(os.environ.get('TRUSTED_PROXY_HOPS', '0'))
    if proxy_hops:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxy_hops, x_proto=proxy_hops)

    # ---------- API 认证配置 ----------
    # API 调用令牌，用于 Glot.io 代码执行服务的身份验证
    app.config['API_TOKEN'] = os.environ.get('API_TOKEN', '')

    # ---------- JWT（JSON Web Token）配置 ----------
    # JWT 签名密钥，用于签发和验证令牌
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', '')
    # 访问令牌（Access Token）过期时间，单位：秒，默认 1 小时
    app.config['JWT_ACCESS_TOKEN_EXPIRE'] = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE', '900'))
    # 刷新令牌（Refresh Token）过期时间，单位：秒，默认 7 天
    app.config['JWT_REFRESH_TOKEN_EXPIRE'] = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRE', '604800'))
    # JWT 签名算法，默认使用 HMAC-SHA256
    app.config['JWT_ALGORITHM'] = os.environ.get('JWT_ALGORITHM', 'HS256')
    # Flask 的全局密钥，用于 session 加密等；如果没有单独配置，则复用 JWT 密钥
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', '')

    # ---------- 前端 URL 配置 ----------
    # 前端应用的访问地址，用于 OAuth 登录成功后的重定向
    app.config['FRONTEND_URL'] = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    # 后端服务的公网地址，用于构建 OAuth 回调 URL
    app.config['PUBLIC_BACKEND_URL'] = os.environ.get('PUBLIC_BACKEND_URL', '')

    # ---------- CORS 跨域配置 ----------
    # 允许跨域访问的前端域名列表（逗号分隔），默认允许本地开发服务器
    # 服务器部署时需设置 ALLOWED_ORIGINS 环境变量（如 http://your-domain:5173）
    _default_origins = 'http://localhost:5173,http://127.0.0.1:5173'
    app.config['ALLOWED_ORIGINS'] = [
        origin.strip()
        for origin in os.environ.get('ALLOWED_ORIGINS', _default_origins).split(',')
        if origin.strip()
    ]

    # ---------- Redis 缓存配置 ----------
    # Redis 服务器地址
    app.config['REDIS_HOST'] = os.environ.get('REDIS_HOST', 'localhost')
    # Redis 服务端口
    app.config['REDIS_PORT'] = int(os.environ.get('REDIS_PORT', '6379'))
    # Redis 数据库编号（0-15）
    app.config['REDIS_DB'] = int(os.environ.get('REDIS_DB', '0'))
    # Redis 连接密码（可选）
    app.config['REDIS_PASSWORD'] = os.environ.get('REDIS_PASSWORD')
    # Redis 连接超时时间，单位：秒
    app.config['REDIS_TIMEOUT'] = int(os.environ.get('REDIS_TIMEOUT', '5'))

    # ---------- PostgreSQL 数据库配置 ----------
    # 数据库主机地址
    app.config['DB_HOST'] = os.environ.get('DB_HOST')
    # 数据库端口
    app.config['DB_PORT'] = int(os.environ.get('DB_PORT', '5432'))
    # 数据库名称
    app.config['DB_NAME'] = os.environ.get('DB_NAME', 'letcoding')
    # 数据库用户名
    app.config['DB_USER'] = os.environ.get('DB_USER', 'postgres')
    # 数据库密码
    app.config['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', '')
    # 数据库连接池的最大连接数
    app.config['DB_MAX_CONNECTIONS'] = int(os.environ.get('DB_MAX_CONNECTIONS', '20'))
    # 连接池中空闲连接的超时时间，单位：秒
    app.config['DB_STALE_TIMEOUT'] = int(os.environ.get('DB_STALE_TIMEOUT', '300'))

    # ---------- GitHub OAuth 配置 ----------
    # GitHub OAuth 应用客户端 ID
    app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID')
    # GitHub OAuth 应用客户端密钥
    app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET')
    # GitHub OAuth 回调地址
    app.config['GITHUB_REDIRECT_URI'] = os.environ.get('GITHUB_REDIRECT_URI')
    # IOSClub OAuth 回调地址
    app.config['IOSCLUB_REDIRECT_URI'] = os.environ.get('IOSCLUB_REDIRECT_URI')

    # ---------- 自定义 OIDC 提供商配置 ----------
    # 从环境变量或 .env 文件中加载所有 OIDC 提供商的配置
    app.config['OIDC_PROVIDERS'] = _load_oidc_providers_config()
    app.config['APP_ENV'] = os.environ.get('APP_ENV', 'production')
    app.config['UPLOAD_DIR'] = os.environ.get('UPLOAD_DIR', str(Path(__file__).parent / 'uploads'))
    if overrides:
        app.config.update(overrides)
    if app.testing:
        app.config['APP_ENV'] = 'test'
    from core.runtime_config import validate_runtime_config
    validate_runtime_config(app.config)
    from middleware.request_middleware import register_request_hooks
    register_request_hooks(app)
    from services.observability import register_metrics
    register_metrics(app)



    # ============================================================
    # 4. API 路由与端点
    # ============================================================

    @app.get('/')
    def index():
        """根路径端点，返回 API 的基本信息和服务状态"""
        return {
            'service': 'LetCoding API',
            'status': 'ok',
            'docs': '/swagger/',     # Swagger API 文档地址
            'health': '/healthz',    # 健康检查端点地址
        }


    @app.get('/healthz')
    def healthcheck():
        """健康检查端点，用于监控和负载均衡器的心跳检测"""
        response = {'status': 'ok'}
        return response


    @app.get('/healthz/db')
    @app.get('/readyz')
    def readiness():
        from models.db_models import get_database
        from interfaces.service_interfaces import IRedisService
        try:
            get_database().execute_sql('SELECT 1')
            redis_service = get_container().resolve(IRedisService)
            if not redis_service.is_connected() or not redis_service._client.ping():
                raise RuntimeError('redis unavailable')
            return {'status': 'ok'}, 200
        except Exception:
            return {'status': 'unavailable'}, 503


    @app.get('/healthz/judge')
    def judge_healthcheck():
        """判题 Worker 和比赛队列健康状态，不返回代码或用户数据。"""
        from interfaces.service_interfaces import IRedisService
        try:
            cache = get_container().resolve(IRedisService)
            if not cache.is_connected():
                raise RuntimeError('redis unavailable')
            alive = any((cache.get(key) or {}).get('alive') for key in cache._client.scan_iter('judge:worker:*', count=100))
            return {'status': 'ok' if alive else 'unavailable'}, 200 if alive else 503
        except Exception:
            return {'status': 'unavailable'}, 503



    # ============================================================
    # 5. 全局错误处理器与请求钩子
    # ============================================================

    @app.after_request
    def add_cors_headers(response):
        """在每个 HTTP 响应后添加 CORS（跨域资源共享）相关的响应头

        仅当请求来源（Origin）在允许的域名列表中时，才会添加 CORS 头。
        同时自动允许同源请求（Origin 为空或与 Host 相同）。
        """
        origin = request.headers.get('Origin')
        if origin in app.config.get('ALLOWED_ORIGINS', []):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.vary.add('Origin')
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Idempotency-Key, X-CSRF-Protection'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return response


    # ============================================================
    # 6. 服务初始化与 API 注册
    # ============================================================

    # 初始化并注册所有依赖注入服务（配置服务、日志服务、JWT 服务等）
    from core.di_container import DIContainer
    import core.di_container as di
    di._container = DIContainer()
    setup_services(app.config)
    from interfaces.service_interfaces import ILoggerService
    application_logger = get_container().resolve(ILoggerService)._logger
    app.logger.handlers = application_logger.handlers
    app.logger.setLevel(application_logger.level)
    app.logger.propagate = False

    # 初始化数据库连接并绑定到 Peewee 模型
    # 使用 DatabaseProxy 模式，确保在 DI 容器就绪后才创建实际连接
    from models.db_models import init_database
    if not app.testing:
        init_database()

    # 每个请求结束后把线程本地数据库连接归还连接池，避免多线程下连接泄漏
    # 导致 "Exceeded maximum connections"
    from models.db_models import get_database


    @app.teardown_appcontext
    def _close_db_pool(exc=None):
        from models import db_models
        db = db_models._actual_db
        if db is not None and not db.is_closed():
            db.close()


    # 获取依赖注入容器
    container = get_container()

    # 初始化 OIDC/OAuth 认证服务（注册 GitHub、自定义 OIDC 提供商等）
    if not app.testing:
        oidc_service = container.resolve(IOIDCService)
        oidc_service.initialize_oauth(app)

    # 创建 Flask-RESTX API 实例，自动生成 Swagger 文档
    api = Api(
        app,
        version='1.0',
        title='LetCoding API',
        description='Code execution and authentication API service.',
        doc='/swagger/',           # Swagger UI 的访问路径
    )

    import traceback

    @api.errorhandler(Exception)
    def handle_uncaught_error(e):
        """捕获所有未处理的异常，返回 JSON 格式的错误信息（对数据库错误脱敏）"""
        from flask import g
        from werkzeug.exceptions import HTTPException
        from peewee import OperationalError, InterfaceError
        if isinstance(e, HTTPException):
            return {'error': e.description, 'request_id': getattr(g, 'request_id', '')}, e.code
        app.logger.error('Unhandled exception type=%s request_id=%s', type(e).__name__, getattr(g, 'request_id', ''), exc_info=True)
        status = 503 if isinstance(e, (DatabaseUnavailableError, OperationalError, InterfaceError)) else 500
        return {'error': '服务暂时不可用' if status == 503 else '服务器内部错误',
                'request_id': getattr(g, 'request_id', '')}, status


    # 注册 API 命名空间
    api.add_namespace(code_api, path='/code')
    api.add_namespace(auth_api, path='/auth')
    api.add_namespace(submission_api, path='/submissions')
    api.add_namespace(user_code_api, path='/user')
    api.add_namespace(announcement_api, path='/announcement')
    api.add_namespace(problem_api, path='/problems')
    api.add_namespace(admin_api, path='/admin')
    api.add_namespace(favorite_api, path='/favorites')
    api.add_namespace(contest_api, path='/contests')
    api.add_namespace(contest_operations_api, path='/contests')
    api.add_namespace(discussion_api, path='/discussions')
    api.add_namespace(rankings_api, path='/rankings')
    api.add_namespace(contest_rankings_api, path='/contests')
    api.add_namespace(contest_problem_api, path='/admin/contests')
    api.add_namespace(learn_favorite_api, path='/learn-favorites')
    api.add_namespace(learn_history_api, path='/learn-history')
    api.add_namespace(learn_resources_api, path='/learn-resources')
    api.add_namespace(user_api, path='/users')


    # ============================================================
    # 7. 静态文件服务（头像等上传文件）
    # ============================================================

    from flask import send_from_directory

    _UPLOADS_DIR = app.config['UPLOAD_DIR']


    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        """提供上传文件的访问（头像等）"""
        return send_from_directory(_UPLOADS_DIR, filename)



    return app
