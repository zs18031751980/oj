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
import re           # 用于正则匹配 .env 文件中的 OIDC_PROVIDERS 配置
from pathlib import Path  # 用于跨平台路径操作

from dotenv import find_dotenv, load_dotenv  # 用于加载 .env 环境变量文件
from flask import Flask, request              # Flask 核心框架
from flask_restx import Api                   # Flask-RESTX 扩展，用于构建 RESTful API 和 Swagger 文档
import gzip
import io
from werkzeug.middleware.proxy_fix import ProxyFix  # 用于解决反向代理下的请求头问题

from models.db_models import create_tables, migrate_add_role_column

# 导入 API 命名空间
from controllers.auth_controller import api as auth_api
from controllers.code_controller import api as code_api
from controllers.submission_controller import api as submission_api
# 导入依赖注入容器和服务配置
from core.di_container import get_container
from core.service_config import setup_services
from interfaces.service_interfaces import IOIDCService


# ============================================================
# 1. 环境变量加载
# ============================================================

# 当前文件的绝对路径（main.py 的完整路径）
CURRENT_FILE_PATH = Path(__file__).resolve()

# 后端 .env 文件路径：与 main.py 同级的 .env 文件
BACKEND_DOTENV_PATH = CURRENT_FILE_PATH.with_name('.env')

# 在本地开发环境下，仓库根目录在 main.py 的上两级目录
# 不同部署平台的挂载路径深度可能不同，所以这里做兼容判断
ROOT_DOTENV_PATH = (
    CURRENT_FILE_PATH.parents[2] / '.env'   # 本地开发：项目根目录下的 .env
    if len(CURRENT_FILE_PATH.parents) > 2
    else BACKEND_DOTENV_PATH                # 部署环境：回退到后端层的 .env
)

# 依次加载各个层级的 .env 文件，优先级：后加载的覆盖先加载的
if BACKEND_DOTENV_PATH.exists():
    load_dotenv(BACKEND_DOTENV_PATH, override=False)

if ROOT_DOTENV_PATH.exists():
    load_dotenv(ROOT_DOTENV_PATH, override=False)

# 加载 .env.local（本地开发覆盖，不会被 Git 追踪）
BACKEND_DOTENV_LOCAL_PATH = CURRENT_FILE_PATH.with_name('.env.local')
if BACKEND_DOTENV_LOCAL_PATH.exists():
    load_dotenv(BACKEND_DOTENV_LOCAL_PATH, override=True)

# 最后加载系统环境变量（部署时优先级最高）
load_dotenv()


# ============================================================
# 2. OIDC 提供商配置加载函数
# ============================================================

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

    # 如果环境变量中没有，则从 .env 文件中搜索
    dotenv_candidates = [
        BACKEND_DOTENV_PATH,                                   # 后端层的 .env
        Path(find_dotenv(usecwd=True)) if find_dotenv(usecwd=True) else None,  # 通过 python-dotenv 查找
        ROOT_DOTENV_PATH,                                      # 项目根目录的 .env
    ]

    for dotenv_path in dotenv_candidates:
        if not dotenv_path or not dotenv_path.exists():
            continue

        try:
            dotenv_content = dotenv_path.read_text(encoding='utf-8')
        except OSError:
            continue

        # 使用正则表达式匹配 OIDC_PROVIDERS= 后面的字典或列表内容
        match = re.search(r'^OIDC_PROVIDERS\s*=\s*(\{[\s\S]*?\}|\[[\s\S]*?\])', dotenv_content, re.MULTILINE)
        if not match:
            continue

        raw_block = match.group(1).strip()
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(raw_block)
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

# ============================================================
# 3. Flask 应用初始化与配置
# ============================================================

# 创建 Flask 应用实例
app = Flask(__name__)

# 配置 ProxyFix 中间件，用于处理反向代理（如 Nginx）传递的请求头信息
# x_for=1: 信任 X-Forwarded-For 的第一个 IP
# x_proto=1: 信任 X-Forwarded-Proto（HTTP/HTTPS）
# x_host=1: 信任 X-Forwarded-Host
# x_port=1: 信任 X-Forwarded-Port
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# ---------- API 认证配置 ----------
# API 调用令牌，用于 Glot.io 代码执行服务的身份验证
app.config['API_TOKEN'] = os.environ.get('API_TOKEN', '')

# ---------- JWT（JSON Web Token）配置 ----------
# JWT 签名密钥，用于签发和验证令牌
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')
# 访问令牌（Access Token）过期时间，单位：秒，默认 1 小时
app.config['JWT_ACCESS_TOKEN_EXPIRE'] = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE', '3600'))
# 刷新令牌（Refresh Token）过期时间，单位：秒，默认 7 天
app.config['JWT_REFRESH_TOKEN_EXPIRE'] = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRE', '604800'))
# JWT 签名算法，默认使用 HMAC-SHA256
app.config['JWT_ALGORITHM'] = os.environ.get('JWT_ALGORITHM', 'HS256')
# Flask 的全局密钥，用于 session 加密等；如果没有单独配置，则复用 JWT 密钥
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY') or app.config['JWT_SECRET_KEY']

# ---------- 前端 URL 配置 ----------
# 前端应用的访问地址，用于 OAuth 登录成功后的重定向
app.config['FRONTEND_URL'] = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
# 后端服务的公网地址，用于构建 OAuth 回调 URL
app.config['PUBLIC_BACKEND_URL'] = os.environ.get('PUBLIC_BACKEND_URL', '')

# ---------- CORS 跨域配置 ----------
# 允许跨域访问的前端域名列表（逗号分隔），默认允许本地开发服务器
app.config['ALLOWED_ORIGINS'] = [
    origin.strip()
    for origin in os.environ.get(
        'ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173',
    ).split(',')
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
app.config['DB_HOST'] = os.environ.get('DB_HOST', 'localhost')
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


# ============================================================
# 5. 全局错误处理器与请求钩子
# ============================================================

@app.after_request
def add_cors_headers(response):
    """在每个 HTTP 响应后添加 CORS（跨域资源共享）相关的响应头

    仅当请求来源（Origin）在允许的域名列表中时，才会添加 CORS 头。
    这样可以确保只有受信任的前端应用才能调用 API。
    """
    origin = request.headers.get('Origin')
    allowed_origins = app.config.get('ALLOWED_ORIGINS', [])
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Vary'] = 'Origin, Accept-Encoding'
        response.headers['Access-Control-Allow-Credentials'] = 'true'   # 允许携带 Cookie
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'

    accept_encoding = request.headers.get('Accept-Encoding', '')
    content_type = response.headers.get('Content-Type', '')
    if ('gzip' in accept_encoding
            and response.status_code == 200
            and response.content_length is not None
            and response.content_length > 500
            and 'application/json' in content_type
            and 'Content-Encoding' not in response.headers):
        gzip_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode='wb', compresslevel=6) as gzip_file:
            gzip_file.write(response.get_data())
        compressed_data = gzip_buffer.getvalue()
        response.set_data(compressed_data)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = str(len(compressed_data))

    return response


# ============================================================
# 6. 服务初始化与 API 注册
# ============================================================

# 初始化并注册所有依赖注入服务（配置服务、日志服务、JWT 服务等）
setup_services(app.config)

# 创建数据库表（如不存在），失败时只打印警告，避免阻塞启动
try:
    create_tables()
except Exception as e:
    app.logger.warning(f"Database table creation failed (app will still start): {e}")

# 执行数据库迁移（如已有 users 表缺少 role 列则自动添加）
try:
    migrate_add_role_column()
except Exception as e:
    app.logger.warning(f"Database migration failed (app will still start): {e}")

# 获取依赖注入容器
container = get_container()

# 初始化 OIDC/OAuth 认证服务（注册 GitHub、自定义 OIDC 提供商等）
oidc_service = container.resolve(IOIDCService)
oidc_service.initialize_oauth(app)

# 启动后台判题 Worker（在 try-except 中防止启动失败导致整个服务崩溃）
from services.judge_service import start_judge_worker
try:
    start_judge_worker()
except Exception as e:
    app.logger.error(f"Failed to start judge worker: {e}")

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
    """捕获所有未处理的异常，返回 JSON 格式的错误信息"""
    app.logger.error(f"Unhandled exception: {traceback.format_exc()}")
    return {"error": f"服务器内部错误: {str(e)}", "detail": traceback.format_exc() if app.debug else ""}, 500

# 注册 API 命名空间
api.add_namespace(code_api, path='/code')
api.add_namespace(auth_api, path='/auth')
api.add_namespace(submission_api, path='/submissions')


# ============================================================
# 7. 应用启动入口
# ============================================================

if __name__ == '__main__':
    # 默认端口设为 6173（与 "LetCoding" 谐音）
    port = int(os.environ.get('PORT', '6173'))
    # 根据环境变量 FLASK_DEBUG 控制是否开启调试模式
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes', 'on')
    # 启动 Flask 开发服务器（生产环境应使用 Gunicorn 等 WSGI 服务器）
    app.run(debug=debug, host='0.0.0.0', port=port)
