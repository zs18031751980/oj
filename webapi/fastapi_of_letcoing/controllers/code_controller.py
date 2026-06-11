from flask import request, g
from flask_restx import Resource, Namespace, fields
from interfaces.service_interfaces import ICodeExecutionService
from core.di_container import inject
from models.glot_models import CodeExecutionRequest
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware

# 创建命名空间
api = Namespace('code', description='代码执行相关操作')

# 定义数据模型
code_execution_model = api.model('CodeExecution', {
    'code': fields.String(required=True, description='要执行的代码'),
    'language': fields.String(default='javascript', description='编程语言'),
    'stdin': fields.String(description='标准输入'),
})

# 定义响应模型
response_model = api.model('CodeExecutionResponse', {
    'stdout': fields.String(description='标准输出'),
    'stderr': fields.String(description='标准错误'),
    'message': fields.String(description='执行结果信息'),
})

# 定义错误响应模型
error_model = api.model('ErrorResponse', {
    'error': fields.String(description='错误信息'),
})

@api.route('/run')
class CodeExecutionController(Resource):
    @api.expect(code_execution_model)
    @api.doc('execute_code')
    @api.response(200, 'Success', response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized')
    @AuthMiddleware.require_auth
    @RateLimitMiddleware.rate_limit(max_requests=100, window_seconds=3600)
    def post(self):
        """执行代码（需要认证）"""
        # 注入服务
        code_service = inject(ICodeExecutionService)
        
        # 获取当前用户信息
        current_user = getattr(g, 'current_user', None)
        
        # 获取请求数据
        model = request.get_json()
        if not model:
            return {'error': '请求体不能为空'}, 400
        
        code = model.get('code', '')
        language = model.get('language', 'javascript')
        stdin = model.get('stdin', '')
        
        # 验证代码
        if not code or code.strip() == "":
            return {'error': '代码不能为空'}, 400
        
        # 构建请求对象
        execution_request = CodeExecutionRequest(
            code=code,
            language=language,
            stdin=stdin if stdin else None
        )
        
        # 调用服务
        import asyncio
        result = asyncio.run(code_service.execute_code(execution_request))
        
        # 处理结果并格式化响应
        if not result.success:
            return {'error': result.stderr}, 400
        
        response_data = {
            'message': '代码执行成功', 
            'stdout': result.stdout
        }
        
        # 添加用户信息到响应中（可选）
        if current_user:
            response_data['user'] = {
                'id': current_user.get('id'),
                'username': current_user.get('username')
            }
        
        return response_data, 200


@api.route('/run/public')
class PublicCodeExecutionController(Resource):
    @api.expect(code_execution_model)
    @api.doc('execute_code_public')
    @api.response(200, 'Success', response_model)
    @api.response(400, 'Bad Request', error_model)
    @RateLimitMiddleware.rate_limit(max_requests=20, window_seconds=3600)
    def post(self):
        """执行代码（公共接口，无需认证，限制较严）"""
        # 注入服务
        code_service = inject(ICodeExecutionService)
        
        # 获取请求数据
        model = request.get_json()
        if not model:
            return {'error': '请求体不能为空'}, 400
        
        code = model.get('code', '')
        language = model.get('language', 'javascript')
        stdin = model.get('stdin', '')
        
        # 验证代码
        if not code or code.strip() == "":
            return {'error': '代码不能为空'}, 400
        
        # 构建请求对象
        execution_request = CodeExecutionRequest(
            code=code,
            language=language,
            stdin=stdin if stdin else None
        )
        
        # 调用服务
        import asyncio
        result = asyncio.run(code_service.execute_code(execution_request))
        
        # 处理结果并格式化响应
        if not result.success:
            return {'error': result.stderr}, 400
        
        return {'message': '代码执行成功', 'stdout': result.stdout}, 200