import json
import random
import string
import subprocess
import tempfile
import os
from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import (
    Contest, ContestParticipant, ContestProblem, ContestTestcase, User
)
from core.di_container import inject
from interfaces.service_interfaces import IJWTService

api = Namespace('admin/contests', description='比赛管理接口（管理员）')

contest_problem_model = api.model('ContestProblem', {
    'id': fields.Integer(description='题目ID'),
    'contest_id': fields.Integer(description='比赛ID'),
    'problem_index': fields.String(description='题目编号'),
    'title': fields.String(description='题目标题'),
    'description': fields.String(description='题目描述(Markdown)'),
    'input_desc': fields.String(description='输入格式'),
    'output_desc': fields.String(description='输出格式'),
    'correct_answer': fields.String(description='正确答案'),
    'time_limit': fields.Integer(description='时间限制(ms)'),
    'memory_limit': fields.Integer(description='内存限制(MB)'),
    'difficulty': fields.String(description='难度'),
    'language': fields.String(description='参考代码语言'),
    'samples': fields.String(description='样例输入输出(JSON)'),
    'testcase_count': fields.Integer(description='测试用例数'),
})

contest_problem_input = api.model('ContestProblemInput', {
    'problem_index': fields.String(required=True, description='题目编号(A/B/C...)'),
    'title': fields.String(required=True, description='题目标题'),
    'description': fields.String(required=True, description='题目描述(Markdown)'),
    'input_desc': fields.String(description='输入格式'),
    'output_desc': fields.String(description='输出格式'),
    'correct_answer': fields.String(required=True, description='正确答案(参考代码)'),
    'time_limit': fields.Integer(default=1000, description='时间限制(ms)'),
    'memory_limit': fields.Integer(default=256, description='内存限制(MB)'),
    'difficulty': fields.String(default='中等', description='难度'),
    'language': fields.String(default='cpp', description='参考代码语言'),
    'samples': fields.String(description='样例输入输出(JSON)'),
})


def _require_manager():
    """验证管理员权限"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, ('请先登录', 401)
    jwt_service = inject(IJWTService)
    user_info = jwt_service.verify_access_token(auth_header[7:])
    if not user_info:
        return None, ('令牌无效', 401)
    try:
        user = User.get_by_id(int(user_info.get('id', 0)))
        if user.role not in ('manager', 'staff'):
            return None, ('权限不足', 403)
        return user, None
    except Exception:
        return None, ('用户不存在', 401)


def _detect_language(code: str) -> str:
    """检测代码语言"""
    code_stripped = code.strip()
    if code_stripped.startswith('#include') or 'int main()' in code_stripped:
        return 'cpp'
    if code_stripped.startswith('import ') or code_stripped.startswith('def '):
        return 'python'
    if code_stripped.startswith('public class') or code_stripped.startswith('class '):
        return 'java'
    return 'python'


def _generate_testcases(correct_answer: str, count: int = 100) -> list[dict]:
    """
    根据正确答案生成测试用例。
    策略：生成随机输入，运行正确代码获取输出，保存为测试用例。
    """
    language = _detect_language(correct_answer)
    testcases = []

    for i in range(count):
        # 生成随机输入（简单策略：随机数字/字符串）
        input_data = _generate_random_input(i)

        # 运行正确代码获取输出
        output = _run_code(correct_answer, language, input_data)
        if output is not None:
            testcases.append({
                'input_data': input_data,
                'expected_output': output.strip(),
                'is_sample': i < 3,  # 前3个作为样例
                'sort_order': i,
            })

    return testcases


def _generate_random_input(seed: int) -> str:
    """生成随机输入数据"""
    random.seed(seed)
    # 生成简单的随机输入：随机整数
    n = random.randint(1, 10)
    nums = [str(random.randint(-100, 100)) for _ in range(n)]
    return ' '.join(nums)


def _run_code(code: str, language: str, stdin: str, timeout: int = 5) -> str | None:
    """运行代码并返回输出"""
    try:
        if language == 'python':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                result = subprocess.run(
                    ['python3', f.name],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                os.unlink(f.name)
                if result.returncode == 0:
                    return result.stdout
        elif language == 'cpp':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                f.write(code)
                f.flush()
                exe_path = f.name + '.exe'
                compile_result = subprocess.run(
                    ['g++', '-o', exe_path, f.name],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                os.unlink(f.name)
                if compile_result.returncode != 0:
                    return None
                result = subprocess.run(
                    [exe_path],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                os.unlink(exe_path)
                if result.returncode == 0:
                    return result.stdout
        elif language == 'java':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                f.write(code)
                f.flush()
                java_src = f.name
            try:
                class_dir = os.path.dirname(java_src)
                compile_result = subprocess.run(
                    ['javac', java_src],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if compile_result.returncode != 0:
                    return None
                result = subprocess.run(
                    ['java', '-cp', class_dir, 'Main'],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if result.returncode == 0:
                    return result.stdout
            except (subprocess.TimeoutExpired, Exception):
                return None
            finally:
                try:
                    if os.path.exists(java_src):
                        os.unlink(java_src)
                    class_file = os.path.join(os.path.dirname(java_src), 'Main.class')
                    if os.path.exists(class_file):
                        os.unlink(class_file)
                except Exception:
                    pass
        elif language == 'go':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(code)
                f.flush()
                go_src = f.name
            try:
                result = subprocess.run(
                    ['go', 'run', go_src],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=max(timeout, 15),
                )
                if result.returncode == 0:
                    return result.stdout
            except (subprocess.TimeoutExpired, Exception):
                return None
            finally:
                try:
                    if os.path.exists(go_src):
                        os.unlink(go_src)
                except Exception:
                    pass
        elif language in ('javascript', 'js', 'node'):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                f.flush()
                js_src = f.name
            try:
                result = subprocess.run(
                    ['node', js_src],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if result.returncode == 0:
                    return result.stdout
            except (subprocess.TimeoutExpired, Exception):
                return None
            finally:
                try:
                    if os.path.exists(js_src):
                        os.unlink(js_src)
                except Exception:
                    pass
    except (subprocess.TimeoutExpired, Exception):
        pass
    return None


def _problem_to_dict(p: ContestProblem) -> dict:
    """转换比赛题目为字典"""
    data = p.to_dict()
    data['testcase_count'] = ContestTestcase.select().where(
        ContestTestcase.contest_problem == p
    ).count()
    # 样例输入输出反序列化为列表
    raw_samples = data.get('samples') or '[]'
    try:
        data['samples'] = json.loads(raw_samples) if isinstance(raw_samples, str) else raw_samples
    except Exception:
        data['samples'] = []
    return data


@api.route('/')
class ContestProblemListController(Resource):
    @api.doc('list_contest_problems')
    @api.param('contest_id', '比赛ID')
    def get(self):
        """获取比赛题目列表"""
        contest_id = request.args.get('contest_id', type=int)
        if not contest_id:
            return {'error': '缺少 contest_id'}, 400
        problems = ContestProblem.select().where(
            ContestProblem.contest_id == contest_id
        ).order_by(ContestProblem.sort_order)
        return [_problem_to_dict(p) for p in problems], 200

    @api.expect(contest_problem_input)
    @api.param('contest_id', '比赛ID')
    def post(self):
        """创建比赛题目（自动生成测试用例）"""
        user, err = _require_manager()
        if err:
            return err

        contest_id = request.args.get('contest_id', type=int)
        if not contest_id:
            return {'error': '缺少 contest_id'}, 400

        try:
            contest = Contest.get_by_id(contest_id)
        except Contest.DoesNotExist:
            return {'error': '比赛不存在'}, 404

        data = request.get_json(silent=True) or {}
        required = ['problem_index', 'title', 'description', 'correct_answer']
        for field in required:
            if not data.get(field, '').strip():
                return {'error': f'{field} 不能为空'}, 400

        # 创建题目
        problem = ContestProblem.create(
            contest=contest,
            problem_index=data['problem_index'].strip(),
            title=data['title'].strip(),
            description=data['description'],
            input_desc=data.get('input_desc', ''),
            output_desc=data.get('output_desc', ''),
            correct_answer=data['correct_answer'],
            time_limit=data.get('time_limit', 1000),
            memory_limit=data.get('memory_limit', 256),
            difficulty=data.get('difficulty', '中等'),
            language=data.get('language', 'cpp'),
            samples=data.get('samples', '[]'),
            sort_order=data.get('sort_order', 0),
        )

        # 自动生成100组测试用例
        testcases = _generate_testcases(data['correct_answer'], 100)
        for tc in testcases:
            ContestTestcase.create(
                contest_problem=problem,
                input_data=tc['input_data'],
                expected_output=tc['expected_output'],
                is_sample=tc['is_sample'],
                sort_order=tc['sort_order'],
            )

        result = _problem_to_dict(problem)
        result['generated_testcases'] = len(testcases)
        return result, 201


@api.route('/<int:problem_id>')
class ContestProblemDetailController(Resource):
    def get(self, problem_id):
        """获取比赛题目详情"""
        try:
            p = ContestProblem.get_by_id(problem_id)
            data = _problem_to_dict(p)
            # 获取测试用例
            testcases = ContestTestcase.select().where(
                ContestTestcase.contest_problem == p
            ).order_by(ContestTestcase.sort_order)
            data['testcases'] = [tc.to_dict() for tc in testcases]
            return data, 200
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

    @api.expect(contest_problem_input)
    def put(self, problem_id):
        """更新比赛题目"""
        user, err = _require_manager()
        if err:
            return err

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

        data = request.get_json(silent=True) or {}
        if 'problem_index' in data:
            problem.problem_index = data['problem_index'].strip() or problem.problem_index
        if 'title' in data:
            problem.title = data['title'].strip() or problem.title
        if 'description' in data:
            problem.description = data['description']
        if 'input_desc' in data:
            problem.input_desc = data['input_desc']
        if 'output_desc' in data:
            problem.output_desc = data['output_desc']
        if 'correct_answer' in data:
            problem.correct_answer = data['correct_answer']
        if 'time_limit' in data:
            problem.time_limit = data['time_limit']
        if 'memory_limit' in data:
            problem.memory_limit = data['memory_limit']
        if 'difficulty' in data:
            problem.difficulty = data['difficulty']
        if 'language' in data:
            problem.language = data.get('language', 'cpp')
        if 'samples' in data:
            problem.samples = data.get('samples', '[]')
        if 'sort_order' in data:
            problem.sort_order = data['sort_order']
        problem.save()
        return _problem_to_dict(problem), 200

    def delete(self, problem_id):
        """删除比赛题目"""
        user, err = _require_manager()
        if err:
            return err

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

        try:
            # 先删除该题目的测试用例，避免外键约束冲突
            ContestTestcase.delete().where(
                ContestTestcase.contest_problem == problem
            ).execute()
            problem.delete_instance()
            return {'success': True}, 200
        except Exception as exc:
            return {'error': f'删除失败: {exc}'}, 500


@api.route('/<int:problem_id>/regenerate-testcases')
class RegenerateTestcasesController(Resource):
    def post(self, problem_id):
        """重新生成测试用例"""
        user, err = _require_manager()
        if err:
            return err

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

        # 删除旧测试用例
        ContestTestcase.delete().where(
            ContestTestcase.contest_problem == problem
        ).execute()

        # 生成新测试用例
        testcases = _generate_testcases(problem.correct_answer, 100)
        for tc in testcases:
            ContestTestcase.create(
                contest_problem=problem,
                input_data=tc['input_data'],
                expected_output=tc['expected_output'],
                is_sample=tc['is_sample'],
                sort_order=tc['sort_order'],
            )

        return {'success': True, 'count': len(testcases)}, 200
