"""
JWT 认证中间件

提供 JWT 令牌验证功能，用于保护 API 端点
"""

from functools import wraps
from flask import request, jsonify, g
from services.jwt_service import JWTService
from core.di_container import inject


class AuthMiddleware:
    """认证中间件类"""
    
    @staticmethod
    def require_auth(f):
        """
        装饰器：要求有效的JWT令牌
        
        Args:
            f: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 注入JWT服务
            jwt_service = inject(JWTService)
            
            # 从请求头获取令牌
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header:
                return jsonify({'error': '缺少Authorization头'}), 401
            
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': '无效的Authorization格式'}), 401
            
            token = auth_header[7:]  # 移除 'Bearer ' 前缀
            
            # 验证令牌
            user_info = jwt_service.verify_access_token(token)
            
            if not user_info:
                return jsonify({'error': '令牌无效或已过期'}), 401
            
            # 将用户信息存储到g对象中
            g.current_user = user_info
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    @staticmethod
    def optional_auth(f):
        """
        装饰器：可选的JWT令牌验证
        
        如果令牌有效，会将用户信息存储到g对象中
        如果令牌无效或缺失，仍继续执行函数
        
        Args:
            f: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 注入JWT服务
            jwt_service = inject(JWTService)
            
            # 从请求头获取令牌
            auth_header = request.headers.get('Authorization', '')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]  # 移除 'Bearer ' 前缀
                
                # 验证令牌
                user_info = jwt_service.verify_access_token(token)
                
                # 如果令牌有效，存储用户信息
                if user_info:
                    g.current_user = user_info
            
            return f(*args, **kwargs)
        
        return decorated_function


class RateLimitMiddleware:
    """基于用户的速率限制中间件"""
    
    @staticmethod
    def rate_limit(max_requests: int = 1000, window_seconds: int = 3600):
        """
        装饰器：基于用户的速率限制
        
        Args:
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
            
        Returns:
            装饰器函数
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 检查是否有用户信息
                user_info = getattr(g, 'current_user', None)
                
                if user_info:
                    # 注入JWT服务获取Redis客户端
                    jwt_service = inject(JWTService)
                    redis_client = jwt_service._redis_client
                    
                    if redis_client:
                        user_id = user_info.get('id')
                        key = f"rate_limit:{user_id}"
                        
                        try:
                            # 获取当前计数
                            current_count = redis_client.get(key)
                            
                            if current_count is None:
                                # 首次请求，设置计数
                                redis_client.setex(key, window_seconds, 1)
                            else:
                                current_count = int(current_count)
                                
                                if current_count >= max_requests:
                                    # 超过限制
                                    return jsonify({
                                        'error': '请求过于频繁，请稍后再试',
                                        'limit': max_requests,
                                        'window': window_seconds
                                    }), 429
                                
                                # 增加计数
                                redis_client.incr(key)
                        except Exception:
                            # Redis错误时不限制请求
                            pass
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator


class RoleBasedAuth:
    """基于角色的访问控制"""
    
    @staticmethod
    def require_role(required_role: str):
        """
        装饰器：要求特定角色
        
        Args:
            required_role: 必需的角色
            
        Returns:
            装饰器函数
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 检查用户认证
                user_info = getattr(g, 'current_user', None)
                
                if not user_info:
                    return jsonify({'error': '需要认证'}), 401
                
                # 检查角色（这里简化处理，可以根据实际情况扩展）
                user_role = user_info.get('role', 'user')
                
                if user_role != required_role and user_role != 'admin':
                    return jsonify({'error': '权限不足'}), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator
    
    @staticmethod
    def require_admin(f):
        """
        装饰器：要求管理员权限
        
        Args:
            f: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        return RoleBasedAuth.require_role('admin')(f)