"""生产配置必须显式给出；开发模式不允许被部署默认值隐式启用。"""
import secrets
from urllib.parse import urlsplit
from pathlib import Path


def validate_runtime_config(config):
    production = config.get('APP_ENV', 'production') == 'production'
    errors = []
    if config.get('APP_ENV', 'production') not in {'production', 'development', 'test'}:
        errors.append('APP_ENV 必须为 production、development 或 test')
    for key in ('JWT_SECRET_KEY', 'SECRET_KEY'):
        value = config.get(key, '')
        if not production and not value:
            config[key] = secrets.token_urlsafe(48)
            continue
        if not isinstance(value, str) or len(value.encode()) < 32 or any(
            marker in value.lower() for marker in ('secret-key', 'replace_with', 'change_me', 'your-')
        ):
            public_key = 'FLASK_SECRET_KEY' if key == 'SECRET_KEY' else key
            errors.append(f'{public_key} 必须配置至少 32 字节的随机密钥')
    if production:
        if config.get('JWT_SECRET_KEY') and config.get('JWT_SECRET_KEY') == config.get('SECRET_KEY'):
            errors.append('FLASK_SECRET_KEY 与 JWT_SECRET_KEY 必须使用不同密钥')
        for key in ('FRONTEND_URL', 'PUBLIC_BACKEND_URL'):
            try:
                url = urlsplit(str(config.get(key, '')))
            except ValueError:
                url = urlsplit('')
            if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
                errors.append(f'{key} 必须是明确配置的 HTTPS 地址')
        origins = config.get('ALLOWED_ORIGINS', [])
        def valid_origin(origin):
            try:
                url = urlsplit(origin)
                return (url.scheme == 'https' and bool(url.hostname) and not url.username
                        and not url.password and url.path in ('', '/')
                        and not url.query and not url.fragment)
            except (ValueError, TypeError, AttributeError):
                return False
        if not isinstance(origins, (list, tuple)) or not origins or not all(map(valid_origin, origins)):
            errors.append('ALLOWED_ORIGINS 必须为明确的 HTTPS Origin 列表')
        else:
            try:
                front = urlsplit(str(config.get('FRONTEND_URL', '')))
                if f'{front.scheme}://{front.netloc}' not in origins:
                    errors.append('FRONTEND_URL 必须包含在 ALLOWED_ORIGINS 中')
            except ValueError:
                pass
        if config.get('DEBUG'):
            errors.append('生产环境禁止 DEBUG')
    if errors:
        raise ValueError('; '.join(errors))
    config['MAX_CONTENT_LENGTH'] = config.get('MAX_CONTENT_LENGTH') or 2 * 1024 * 1024 + 65536
    config.setdefault('MAX_FORM_MEMORY_SIZE', 128 * 1024)
    config.setdefault('MAX_FORM_PARTS', 20)
    config['SESSION_COOKIE_HTTPONLY'] = True
    config['SESSION_COOKIE_SECURE'] = production
    config['SESSION_COOKIE_SAMESITE'] = 'None' if production else 'Lax'
    config['UPLOAD_DIR'] = str(Path(config.get('UPLOAD_DIR', 'uploads')).resolve())
