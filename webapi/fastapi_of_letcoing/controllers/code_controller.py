"""
代码执行 API 控制器模块

提供代码运行相关的 API 接口，支持：
- 登录用户的代码执行（需要身份验证）
- 游客（未登录用户）的代码执行（频率限制更严格）

代码执行通过 Glot.io 服务完成，支持多种编程语言。
"""

import asyncio  # 异步 I/O 支持

from flask import g, request   # g: 请求全局上下文, request: HTTP 请求对象
from flask_restx import Namespace, Resource, fields  # Flask-RESTX 组件

from core.di_container import inject  # 依赖注入
from interfaces.service_interfaces import ICodeExecutionService  # 代码执行服务接口
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware  # 认证与频率限制中间件
from models.glot_models import CodeExecutionRequest  # 代码执行请求模型


# ============================================================
# 1. API 命名空间与请求/响应模型定义
# ============================================================

# 创建代码执行相关的 API 命名空间（路由分组为 /code）
api = Namespace('code', description='代码运行相关接口')

# ---------- 请求模型 ----------

# 代码执行请求模型
code_execution_model = api.model('CodeExecution', {
    'code': fields.String(required=True, description='要运行的源代码'),
    'language': fields.String(default='javascript', description='编程语言（如 python, javascript, java 等）'),
    'stdin': fields.String(description='程序的标准输入'),
})

# ---------- 响应模型 ----------

# 代码执行成功响应模型
response_model = api.model('CodeExecutionResponse', {
    'stdout': fields.String(description='程序的标准输出'),
    'stderr': fields.String(description='程序的错误输出'),
    'message': fields.String(description='执行结果消息'),
})

# 错误响应模型
error_model = api.model('ErrorResponse', {
    'error': fields.String(description='错误信息'),
})


# ============================================================
# 2. 辅助函数
# ============================================================

def _parse_execution_request():
    """
    解析并验证代码执行请求中的参数

    从 HTTP 请求体中提取 code、language 和 stdin 参数，
    验证代码不为空后构建 CodeExecutionRequest 对象。

    Returns:
        (CodeExecutionRequest, None) 或 (None, (error_response, status_code))
    """
    model = request.get_json(silent=True) or {}
    code = str(model.get('code', ''))
    language = str(model.get('language', 'javascript') or 'javascript')
    stdin = model.get('stdin', '')

    if not code.strip():
        return None, ({'error': '代码不能为空'}, 400)

    return CodeExecutionRequest(
        code=code,
        language=language,
        stdin=stdin if stdin else None,
    ), None


def _execute_code(execution_request: CodeExecutionRequest):
    """
    执行代码并返回结果

    通过依赖注入获取代码执行服务，异步执行代码，
    并根据执行结果返回成功响应或错误信息。

    Args:
        execution_request: 代码执行请求对象

    Returns:
        (response_data, None) 或 (None, (error_response, status_code))
    """
    code_service = inject(ICodeExecutionService)
    result = asyncio.run(code_service.execute_code(execution_request))

    if not result.success:
        return None, ({'error': result.stderr}, 400)

    return {
        'message': '执行成功',
        'stdout': result.stdout,
        'stderr': result.stderr,
    }, None


# ============================================================
# 3. API 端点
# ============================================================

@api.route('/run')
class CodeExecutionController(Resource):
    """
    登录用户代码执行接口

    要求用户携带有效的 Bearer 令牌进行身份验证，
    执行频率限制为每小时 100 次。
    """

    @api.expect(code_execution_model)
    @api.doc('execute_code')
    @api.response(200, 'Success', response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized')
    @AuthMiddleware.require_auth           # 需要有效的访问令牌
    @RateLimitMiddleware.rate_limit(max_requests=100, window_seconds=3600)  # 每小时100次限制
    def post(self):
        """执行登录用户的代码运行请求"""
        current_user = getattr(g, 'current_user', None)

        execution_request, error_response = _parse_execution_request()
        if error_response:
            return error_response

        response_data, execution_error = _execute_code(execution_request)
        if execution_error:
            return execution_error

        # 如果用户已登录，在响应中附加用户信息
        if current_user:
            response_data['user'] = {
                'id': current_user.get('id'),
                'username': current_user.get('username'),
            }

        return response_data, 200


@api.route('/run/public')
class PublicCodeExecutionController(Resource):
    """
    游客代码执行接口

    无需身份验证即可执行代码，但频率限制更严格（每小时 20 次），
    以防止滥用。
    """

    @api.expect(code_execution_model)
    @api.doc('execute_code_public')
    @api.response(200, 'Success', response_model)
    @api.response(400, 'Bad Request', error_model)
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=3600)  # 每小时20次限制
    def post(self):
        """执行游客（未登录用户）的代码运行请求"""
        execution_request, error_response = _parse_execution_request()
        if error_response:
            return error_response

        response_data, execution_error = _execute_code(execution_request)
        if execution_error:
            return execution_error

        return response_data, 200
