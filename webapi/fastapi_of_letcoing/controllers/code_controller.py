import asyncio

from flask import g, request
from flask_restx import Namespace, Resource, fields

from core.di_container import inject
from interfaces.service_interfaces import ICodeExecutionService
from middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware
from models.glot_models import CodeExecutionRequest


api = Namespace('code', description='浠ｇ爜鎵ц鐩稿叧鎿嶄綔')

code_execution_model = api.model('CodeExecution', {
    'code': fields.String(required=True, description='瑕佹墽琛岀殑浠ｇ爜'),
    'language': fields.String(default='javascript', description='缂栫▼璇█'),
    'stdin': fields.String(description='鏍囧噯杈撳叆'),
})

response_model = api.model('CodeExecutionResponse', {
    'stdout': fields.String(description='鏍囧噯杈撳嚭'),
    'stderr': fields.String(description='鏍囧噯閿欒'),
    'message': fields.String(description='鎵ц缁撴灉淇℃伅'),
})

error_model = api.model('ErrorResponse', {
    'error': fields.String(description='閿欒淇℃伅'),
})


def _parse_execution_request():
    model = request.get_json(silent=True) or {}
    code = str(model.get('code', ''))
    language = str(model.get('language', 'javascript') or 'javascript')
    stdin = model.get('stdin', '')

    if not code.strip():
        return None, ({'error': '浠ｇ爜涓嶈兘涓虹┖'}, 400)

    return CodeExecutionRequest(
        code=code,
        language=language,
        stdin=stdin if stdin else None,
    ), None


def _execute_code(execution_request: CodeExecutionRequest):
    code_service = inject(ICodeExecutionService)
    result = asyncio.run(code_service.execute_code(execution_request))

    if not result.success:
        return None, ({'error': result.stderr}, 400)

    return {
        'message': '浠ｇ爜鎵ц鎴愬姛',
        'stdout': result.stdout,
        'stderr': result.stderr,
    }, None


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
        """鎵ц浠ｇ爜锛堥渶瑕佽璇侊級"""
        current_user = getattr(g, 'current_user', None)

        execution_request, error_response = _parse_execution_request()
        if error_response:
            return error_response

        response_data, execution_error = _execute_code(execution_request)
        if execution_error:
            return execution_error

        if current_user:
            response_data['user'] = {
                'id': current_user.get('id'),
                'username': current_user.get('username'),
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
        """鎵ц浠ｇ爜锛堝叕鍏辨帴鍙ｏ紝鏃犻渶璁よ瘉锛岄檺鍒惰緝涓ワ級"""
        execution_request, error_response = _parse_execution_request()
        if error_response:
            return error_response

        response_data, execution_error = _execute_code(execution_request)
        if execution_error:
            return execution_error

        return response_data, 200
