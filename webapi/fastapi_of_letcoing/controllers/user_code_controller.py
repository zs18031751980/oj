"""
用户代码存储 API 控制器

提供用户代码的上传（保存）和查询接口。
每个用户只能保存最近 5 道题目的代码。
"""

from datetime import datetime

from flask import g, request
from flask_restx import Namespace, Resource, fields

from middleware.auth_middleware import AuthMiddleware
from models.db_models import UserCode, get_database

MAX_PROBLEMS_PER_USER = 5

api = Namespace('user', description='用户相关接口')

save_code_model = api.model('SaveCodeRequest', {
    'problem_id': fields.Integer(required=True, description='题目ID'),
    'language': fields.String(required=True, description='编程语言'),
    'code': fields.String(required=True, description='用户代码'),
})

code_response_model = api.model('CodeResponse', {
    'problem_id': fields.Integer(description='题目ID'),
    'language': fields.String(description='编程语言'),
    'code': fields.String(description='用户代码'),
    'updated_at': fields.String(description='更新时间'),
})


def _get_user_id():
    return int(g.current_user['user_id'])


@api.route('/code')
class UserCodeListController(Resource):
    @api.expect(save_code_model)
    @api.doc('save_user_code')
    @AuthMiddleware.require_auth
    def put(self):
        """保存用户代码（upsert，每题最多保留一份）"""
        model = request.get_json(silent=True) or {}
        problem_id = model.get('problem_id')
        language = str(model.get('language', 'cpp'))
        code = str(model.get('code', ''))

        if not problem_id:
            return {'error': '题目ID不能为空'}, 400

        user_id = _get_user_id()
        db = get_database()

        try:
            db.connect(reuse_if_open=True)

            existing = UserCode.select().where(
                (UserCode.user == user_id) &
                (UserCode.problem_id == problem_id) &
                (UserCode.language == language)
            ).first()

            if existing:
                existing.code = code
                existing.save()
            else:
                distinct_problems = UserCode.select(
                    UserCode.problem_id
                ).where(
                    UserCode.user == user_id
                ).group_by(UserCode.problem_id).count()

                if distinct_problems >= MAX_PROBLEMS_PER_USER:
                    oldest = UserCode.select().where(
                        UserCode.user == user_id
                    ).order_by(UserCode.updated_at.asc()).first()
                    if oldest:
                        oldest.delete_instance()

                UserCode.create(
                    user=user_id,
                    problem_id=problem_id,
                    language=language,
                    code=code,
                )
        except Exception as e:
            return {'error': f'保存失败: {str(e)}'}, 500
        finally:
            if not db.is_closed():
                db.close()

        return {'message': '保存成功'}, 200

    @api.doc('list_user_codes')
    @AuthMiddleware.require_auth
    def get(self):
        """获取当前用户所有已保存的代码"""
        user_id = _get_user_id()
        db = get_database()

        try:
            db.connect(reuse_if_open=True)
            records = UserCode.select().where(
                UserCode.user == user_id
            ).order_by(UserCode.updated_at.desc()).limit(MAX_PROBLEMS_PER_USER)

            result = []
            for r in records:
                result.append({
                    'problem_id': r.problem_id,
                    'language': r.language,
                    'code': r.code,
                    'updated_at': r.updated_at.isoformat() if r.updated_at else None,
                })
            return {'data': result}, 200
        except Exception as e:
            return {'error': f'查询失败: {str(e)}'}, 500
        finally:
            if not db.is_closed():
                db.close()


@api.route('/code/<int:problem_id>')
@api.param('problem_id', '题目ID')
class UserCodeController(Resource):
    @api.doc('get_user_code_by_problem_language')
    @AuthMiddleware.require_auth
    def get(self, problem_id):
        """获取指定题目的用户代码"""
        language = request.args.get('language', 'cpp')
        user_id = _get_user_id()
        db = get_database()

        try:
            db.connect(reuse_if_open=True)
            record = UserCode.select().where(
                (UserCode.user == user_id) &
                (UserCode.problem_id == problem_id) &
                (UserCode.language == language)
            ).first()

            if record:
                return {
                    'problem_id': record.problem_id,
                    'language': record.language,
                    'code': record.code,
                    'updated_at': record.updated_at.isoformat() if record.updated_at else None,
                }, 200
            return {'code': None}, 200
        except Exception as e:
            return {'error': f'查询失败: {str(e)}'}, 500
        finally:
            if not db.is_closed():
                db.close()
