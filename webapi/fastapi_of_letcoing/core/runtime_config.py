"""生产配置必须显式给出；开发模式不允许被部署默认值隐式启用。"""
import secrets
from urllib.parse import urlsplit
from pathlib import Path


def validate_runtime_config(config):
    production = config.get('APP_ENV', 'production') == 'production'
    for key in ('JWT_SECRET_KEY', 'SECRET_KEY'):
        value = config.get(key, '')
        if not production and not value:
            config[key] = secrets.token_urlsafe(48)
            continue
        if not isinstance(value, str) or len(value.encode()) < 32 or any(
            marker in value.lower() for marker in ('secret-key', 'replace_with', 'change_me', 'your-')
        ):
            raise ValueError(f'{key} 必须配置至少 32 字节的随机密钥')
    if production:
        if config['JWT_SECRET_KEY'] == config['SECRET_KEY']:
            raise ValueError('Flask Session 与 JWT 必须使用不同密钥')
        for key in ('FRONTEND_URL', 'PUBLIC_BACKEND_URL'):
            url = urlsplit(str(config.get(key, '')))
            if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError(f'{key} 必须是明确配置的 HTTPS 地址')
        origins = config.get('ALLOWED_ORIGINS', [])
        if not origins or any(urlsplit(origin).scheme != 'https' or not urlsplit(origin).hostname
                or urlsplit(origin).path not in ('', '/') or urlsplit(origin).query or urlsplit(origin).fragment
                for origin in origins):
            raise ValueError('ALLOWED_ORIGINS 必须为明确的 HTTPS Origin 列表')
        front = urlsplit(config['FRONTEND_URL'])
        if f'{front.scheme}://{front.netloc}' not in origins:
            raise ValueError('FRONTEND_URL 必须包含在 ALLOWED_ORIGINS 中')
        if config.get('DEBUG'):
            raise ValueError('生产环境禁止 DEBUG')
    config['MAX_CONTENT_LENGTH'] = config.get('MAX_CONTENT_LENGTH') or 2 * 1024 * 1024 + 65536
    config.setdefault('MAX_FORM_MEMORY_SIZE', 128 * 1024)
    config.setdefault('MAX_FORM_PARTS', 20)
    config['SESSION_COOKIE_HTTPONLY'] = True
    config['SESSION_COOKIE_SECURE'] = production
    config['SESSION_COOKIE_SAMESITE'] = 'None' if production else 'Lax'
    config['UPLOAD_DIR'] = str(Path(config.get('UPLOAD_DIR', 'uploads')).resolve())
