import ast
import json
import os
import re
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from flask import Flask, request
from flask_restx import Api
from werkzeug.middleware.proxy_fix import ProxyFix

from controllers.auth_controller import api as auth_api
from controllers.code_controller import api as code_api
from core.di_container import get_container
from core.service_config import setup_services
from interfaces.service_interfaces import IOIDCService


CURRENT_FILE_PATH = Path(__file__).resolve()
BACKEND_DOTENV_PATH = CURRENT_FILE_PATH.with_name('.env')

# In local development the repo root is two levels above this file.
# In Zeabur the service may be mounted much shallower, so guard the lookup.
ROOT_DOTENV_PATH = (
    CURRENT_FILE_PATH.parents[2] / '.env'
    if len(CURRENT_FILE_PATH.parents) > 2
    else BACKEND_DOTENV_PATH
)

if BACKEND_DOTENV_PATH.exists():
    load_dotenv(BACKEND_DOTENV_PATH, override=False)

if ROOT_DOTENV_PATH.exists():
    load_dotenv(ROOT_DOTENV_PATH, override=False)

load_dotenv()


def _load_oidc_providers_config():
    raw_value = os.environ.get('OIDC_PROVIDERS')
    if raw_value:
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(raw_value)
                if isinstance(parsed, (dict, list)):
                    return parsed
            except Exception:
                pass

    dotenv_candidates = [
        BACKEND_DOTENV_PATH,
        Path(find_dotenv(usecwd=True)) if find_dotenv(usecwd=True) else None,
        ROOT_DOTENV_PATH,
    ]

    for dotenv_path in dotenv_candidates:
        if not dotenv_path or not dotenv_path.exists():
            continue

        try:
            dotenv_content = dotenv_path.read_text(encoding='utf-8')
        except OSError:
            continue

        match = re.search(r'^OIDC_PROVIDERS\s*=\s*(\{[\s\S]*?\}|\[[\s\S]*?\])', dotenv_content, re.MULTILINE)
        if not match:
            continue

        raw_block = match.group(1).strip()
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(raw_block)
                if isinstance(parsed, (dict, list)):
                    return parsed
            except Exception:
                pass

    return {}

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

app.config['API_TOKEN'] = os.environ.get('API_TOKEN', '')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')
app.config['JWT_ACCESS_TOKEN_EXPIRE'] = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE', '3600'))
app.config['JWT_REFRESH_TOKEN_EXPIRE'] = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRE', '604800'))
app.config['JWT_ALGORITHM'] = os.environ.get('JWT_ALGORITHM', 'HS256')
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY') or app.config['JWT_SECRET_KEY']
app.config['FRONTEND_URL'] = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
app.config['PUBLIC_BACKEND_URL'] = os.environ.get('PUBLIC_BACKEND_URL', '')
app.config['ALLOWED_ORIGINS'] = [
    origin.strip()
    for origin in os.environ.get(
        'ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173',
    ).split(',')
    if origin.strip()
]

app.config['REDIS_HOST'] = os.environ.get('REDIS_HOST', 'localhost')
app.config['REDIS_PORT'] = int(os.environ.get('REDIS_PORT', '6379'))
app.config['REDIS_DB'] = int(os.environ.get('REDIS_DB', '0'))
app.config['REDIS_PASSWORD'] = os.environ.get('REDIS_PASSWORD')
app.config['REDIS_TIMEOUT'] = int(os.environ.get('REDIS_TIMEOUT', '5'))

app.config['DB_HOST'] = os.environ.get('DB_HOST', 'localhost')
app.config['DB_PORT'] = int(os.environ.get('DB_PORT', '5432'))
app.config['DB_NAME'] = os.environ.get('DB_NAME', 'letcoding')
app.config['DB_USER'] = os.environ.get('DB_USER', 'postgres')
app.config['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', '')
app.config['DB_MAX_CONNECTIONS'] = int(os.environ.get('DB_MAX_CONNECTIONS', '20'))
app.config['DB_STALE_TIMEOUT'] = int(os.environ.get('DB_STALE_TIMEOUT', '300'))

app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID')
app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET')
app.config['GITHUB_REDIRECT_URI'] = os.environ.get('GITHUB_REDIRECT_URI')
app.config['IOSCLUB_REDIRECT_URI'] = os.environ.get('IOSCLUB_REDIRECT_URI')

app.config['OIDC_PROVIDERS'] = _load_oidc_providers_config()


@app.get('/')
def index():
    return {
        'service': 'LetCoding API',
        'status': 'ok',
        'docs': '/swagger/',
        'health': '/healthz',
    }


@app.get('/healthz')
def healthcheck():
    return {'status': 'ok'}


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    allowed_origins = app.config.get('ALLOWED_ORIGINS', [])
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


setup_services(app.config)

container = get_container()
oidc_service = container.resolve(IOIDCService)
oidc_service.initialize_oauth(app)

api = Api(
    app,
    version='1.0',
    title='LetCoding API',
    description='Code execution and authentication API service.',
    doc='/swagger/',
)

api.add_namespace(code_api, path='/code')
api.add_namespace(auth_api, path='/auth')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '6173'))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes', 'on')
    app.run(debug=debug, host='0.0.0.0', port=port)
