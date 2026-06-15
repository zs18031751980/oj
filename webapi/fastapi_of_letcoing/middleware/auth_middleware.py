"""Authentication and rate-limit middleware."""

from functools import wraps

from flask import g, jsonify, request

from core.di_container import inject
from interfaces.service_interfaces import IJWTService, IRedisService


class AuthMiddleware:
    """JWT authentication decorators."""

    @staticmethod
    def require_auth(f):
        """Require a valid bearer access token."""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            jwt_service = inject(IJWTService)
            auth_header = request.headers.get('Authorization', '')

            if not auth_header:
                return jsonify({'error': 'Missing Authorization header'}), 401

            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Invalid Authorization format'}), 401

            token = auth_header[7:]
            user_info = jwt_service.verify_access_token(token)

            if not user_info:
                return jsonify({'error': 'Token is invalid or expired'}), 401

            g.current_user = user_info
            return f(*args, **kwargs)

        return decorated_function

    @staticmethod
    def optional_auth(f):
        """Attach current_user when a valid bearer token is present."""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            jwt_service = inject(IJWTService)
            auth_header = request.headers.get('Authorization', '')

            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]
                user_info = jwt_service.verify_access_token(token)
                if user_info:
                    g.current_user = user_info

            return f(*args, **kwargs)

        return decorated_function


class RateLimitMiddleware:
    """User-based rate limiting decorators."""

    @staticmethod
    def rate_limit(max_requests: int = 1000, window_seconds: int = 3600):
        """Limit authenticated users to max_requests per time window."""

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_info = getattr(g, 'current_user', None)

                if user_info:
                    try:
                        redis_service = inject(IRedisService)
                        user_id = user_info.get('id')
                        key = f'rate_limit:{user_id}'
                        current_count = redis_service.get(key)

                        if current_count is None:
                            redis_service.set(key, 1, window_seconds)
                        else:
                            current_count = int(current_count)
                            if current_count >= max_requests:
                                return jsonify({
                                    'error': 'Too many requests, please try again later',
                                    'limit': max_requests,
                                    'window': window_seconds,
                                }), 429

                            next_count = redis_service.increment(key)
                            if next_count is not None and redis_service.ttl(key) < 0:
                                redis_service.expire(key, window_seconds)
                    except Exception:
                        # Redis failures should not block code execution.
                        pass

                return f(*args, **kwargs)

            return decorated_function

        return decorator


class RoleBasedAuth:
    """Role-based access-control decorators."""

    @staticmethod
    def require_role(required_role: str):
        """Require a specific role, allowing admins through."""

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_info = getattr(g, 'current_user', None)

                if not user_info:
                    return jsonify({'error': 'Authentication required'}), 401

                user_role = user_info.get('role', 'user')
                if user_role != required_role and user_role != 'admin':
                    return jsonify({'error': 'Insufficient permissions'}), 403

                return f(*args, **kwargs)

            return decorated_function

        return decorator

    @staticmethod
    def require_admin(f):
        """Require an administrator role."""
        return RoleBasedAuth.require_role('admin')(f)
