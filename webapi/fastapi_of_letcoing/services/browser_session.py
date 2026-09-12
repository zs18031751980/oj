"""浏览器刷新凭证仅放入 HttpOnly Cookie；自定义头和精确 Origin 校验防 CSRF。"""
from flask import after_this_request, current_app, request
from werkzeug.exceptions import Forbidden

COOKIE_NAME = 'letcoding_refresh'


def require_browser_request():
    if request.headers.get('X-CSRF-Protection') != '1':
        raise Forbidden('缺少浏览器请求保护头')
    origin = request.headers.get('Origin')
    allowed = current_app.config.get('ALLOWED_ORIGINS', [])
    if origin and origin != request.host_url.rstrip('/') and origin not in allowed:
        raise Forbidden('不允许的请求来源')


def browser_tokens(tokens):
    data = dict(tokens)
    refresh = data.pop('refresh_token')
    remember = (request.get_json(silent=True) or {}).get('remember', True) is True

    @after_this_request
    def set_cookie(response):
        response.set_cookie(COOKIE_NAME, refresh, httponly=True,
            secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
            samesite=current_app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
            path='/auth', max_age=604800 if remember else None)
        response.headers['Cache-Control'] = 'no-store'
        return response
    return data


def clear_refresh_cookie():
    @after_this_request
    def clear(response):
        response.delete_cookie(COOKIE_NAME, path='/auth', httponly=True,
            secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
            samesite=current_app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'))
        return response
