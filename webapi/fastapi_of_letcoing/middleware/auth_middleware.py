"""
认证与频率限制中间件模块

提供三个核心功能：
1. AuthMiddleware: JWT 认证中间件（必需认证、可选认证）
2. RateLimitMiddleware: 基于 Redis 的用户频率限制
3. RoleBasedAuth: 基于角色的访问控制

这些中间件以装饰器形式应用于 Flask-RESTX 的路由方法上。
"""

from functools import wraps

from flask import g, request  # g: 请求全局上下文

from core.di_container import inject
from interfaces.service_interfaces import IJWTService, IRedisService


class AuthMiddleware:
    """
    JWT 认证中间件

    提供两种认证策略：
    - require_auth: 强制要求有效的 Bearer 令牌，否则返回 401
    - optional_auth: 如果有有效的 Bearer 令牌则附加用户信息，否则不拦截
    """

    @staticmethod
    def require_auth(f):
        """
        强制认证装饰器

        要求请求必须携带有效的 Bearer 令牌。
        验证通过后将用户信息附加到 g.current_user 中。

        Returns:
            验证失败返回 401 JSON 响应
        """

        @wraps(f)
        def decorated_function(*args, **kwargs):
            jwt_service = inject(IJWTService)
            auth_header = request.headers.get('Authorization', '')

            if not auth_header:
                return {'error': 'Missing Authorization header'}, 401

            if not auth_header.startswith('Bearer '):
                return {'error': 'Invalid Authorization format'}, 401

            token = auth_header[7:]
            user_info = jwt_service.verify_access_token(token)

            if not user_info:
                return {'error': 'Token is invalid or expired'}, 401

            # 将用户信息存储到请求全局变量中，供后续处理使用
            g.current_user = user_info
            return f(*args, **kwargs)

        return decorated_function

    @staticmethod
    def optional_auth(f):
        """
        可选认证装饰器

        如果请求携带了有效的 Bearer 令牌，则将用户信息附加到 g.current_user；
        如果没有令牌或令牌无效，请求仍然正常通过。

        适用于需要区分登录/未登录用户的接口。
        """

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
    """
    用户频率限制中间件

    基于 Redis 实现滑动窗口频率限制算法。
    对已认证的用户按用户 ID 进行计数，在指定时间窗口内超过阈值则返回 429。
    """

    @staticmethod
    def rate_limit(max_requests: int = 1000, window_seconds: int = 3600):
        """
        频率限制装饰器

        限制认证用户在指定时间窗口内的请求次数。
        仅对已认证用户进行计数（未登录用户不限制）。

        Args:
            max_requests: 时间窗口内允许的最大请求次数
            window_seconds: 时间窗口长度（秒），默认 1 小时

        Returns:
            超过限制时返回 429 Too Many Requests
        """

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_info = getattr(g, 'current_user', None)

                if user_info:
                    try:
                        redis_service = inject(IRedisService)
                        user_id = user_info.get('id')
                        key = f'rate_limit:{user_id}'

                        if not redis_service.rate_limit_check(key, max_requests, window_seconds):
                            return {
                                'error': '请求过于频繁，请稍后再试',
                                'limit': max_requests,
                                'window': window_seconds,
                            }, 429
                    except Exception:
                        pass

                return f(*args, **kwargs)

            return decorated_function

        return decorator


class RoleBasedAuth:
    """
    基于角色的访问控制中间件

    通过用户角色进行权限校验，支持：
    - require_role: 需要特定角色
    - require_admin: 需要管理员角色（管理员拥有所有权限）
    """

    @staticmethod
    def require_role(required_role: str):
        """
        角色要求装饰器

        要求当前用户具有指定角色才能访问。
        如果是管理员角色则自动放行。

        Args:
            required_role: 所需的角色名称

        Returns:
            未认证返回 401，权限不足返回 403
        """

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_info = getattr(g, 'current_user', None)

                if not user_info:
                    return {'error': 'Authentication required'}, 401

                user_role = user_info.get('role', 'user')
                if user_role != required_role and user_role != 'admin':
                    return {'error': 'Insufficient permissions'}, 403

                return f(*args, **kwargs)

            return decorated_function

        return decorator

    @staticmethod
    def require_admin(f):
        """
        管理员权限装饰器

        快捷方式，等价于 require_role('admin')。
        只有角色为 'admin' 的用户才能访问。
        """
        return RoleBasedAuth.require_role('admin')(f)
