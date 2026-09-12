"""公共请求边界、关联 ID、错误响应和基础安全头。"""
import logging
import time
from uuid import uuid4

from flask import g, request
from werkzeug.exceptions import BadRequest


def register_request_hooks(app):
    @app.before_request
    def validate_request():
        g.request_id = uuid4().hex
        g.request_started = time.monotonic()
        if request.is_json:
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                raise BadRequest('请求体必须是 JSON 对象')
            text_limits = {'code': 131072, 'correct_answer': 131072, 'stdin': 1048576,
                           'language': 50, 'identifier': 254, 'password': 1024,
                           'title': 200, 'description': 131072, 'name': 100, 'email': 254}
            for field, limit in text_limits.items():
                if field in data and (not isinstance(data[field], str) or len(data[field].encode()) > limit):
                    raise BadRequest(f'{field} 类型错误或超过长度限制')
            for field in ('time_limit', 'memory_limit', 'sort_order'):
                if field in data and type(data[field]) is not int:
                    raise BadRequest(f'{field} 必须为整数')
        # Origin 是浏览器写请求的边界；Bearer API 的非浏览器调用可无 Origin。
        origin = request.headers.get('Origin')
        if origin and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            allowed = app.config.get('ALLOWED_ORIGINS', [])
            if origin not in allowed and origin != request.host_url.rstrip('/'):
                return {'error': '不允许的请求来源'}, 403

    @app.after_request
    def response_metadata(response):
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        if request.path.startswith(('/auth/', '/submissions', '/users/me', '/admin/')) or '/submission' in request.path:
            response.headers['Cache-Control'] = 'no-store'
        elapsed = time.monotonic() - getattr(g, 'request_started', time.monotonic())
        logging.getLogger('letcoding.requests').info('request_id=%s method=%s route=%s status=%s duration_ms=%.2f',
            getattr(g, 'request_id', ''), request.method, str(request.url_rule or 'unmatched'),
            response.status_code, elapsed * 1000)
        return response
