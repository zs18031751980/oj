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


def _run_reference_twice(
    code: str, language: str, stdin: str, timeout: int, memory_limit: int | None
) -> tuple[str | None, bool]:
    """
    运行参考代码两次并返回 (输出, 是否自洽)。

    - 仅编译一次（cpp/java），执行两次，保证性能与一致性；
    - 若任一运行编译/运行/超时/内存出错（输出为 None），返回 (None, False)；
    - 若两次运行输出不一致（非确定性），返回 (输出, False)；
    - 否则返回 (去尾空白后的输出, True)。
    这样既保证参考代码在比赛限制内稳定通过，又能过滤掉非确定性用例。
    """
    try:
        if language == 'cpp':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                f.write(code)
                f.flush()
                src = f.name
            exe_path = src + '.exe'
            try:
                compile_result = subprocess.run(
                    ['g++', '-o', exe_path, src],
                    capture_output=True, text=True, timeout=max(timeout, 10),
                )
                if compile_result.returncode != 0:
                    return (None, False)
                r1 = _interpret(_exec_command([exe_path], stdin, timeout, memory_limit), is_compiled=True)
                if r1[0] is None:
                    return (None, False)
                r2 = _interpret(_exec_command([exe_path], stdin, timeout, memory_limit), is_compiled=True)
                if r2[0] is None:
                    return (None, False)
                return (r1[0].strip(), r1[0] == r2[0])
            finally:
                os.unlink(src)
                if os.path.exists(exe_path):
                    os.unlink(exe_path)

        elif language == 'java':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                f.write(code)
                f.flush()
                java_src = f.name
            try:
                class_dir = os.path.dirname(java_src)
                compile_result = subprocess.run(
                    ['javac', java_src],
                    capture_output=True, text=True, timeout=max(timeout, 10),
                )
                if compile_result.returncode != 0:
                    return (None, False)
                r1 = _interpret(
                    _exec_command(['java', '-cp', class_dir, 'Main'], stdin, timeout, memory_limit),
                    is_compiled=True,
                )
                if r1[0] is None:
                    return (None, False)
                r2 = _interpret(
                    _exec_command(['java', '-cp', class_dir, 'Main'], stdin, timeout, memory_limit),
                    is_compiled=True,
                )
                if r2[0] is None:
                    return (None, False)
                return (r1[0].strip(), r1[0] == r2[0])
            finally:
                try:
                    if os.path.exists(java_src):
                        os.unlink(java_src)
                    class_file = os.path.join(os.path.dirname(java_src), 'Main.class')
                    if os.path.exists(class_file):
                        os.unlink(class_file)
                except Exception:
                    pass

        else:
            r1 = _run_code(code, language, stdin, timeout, memory_limit)
            if r1[0] is None:
                return (None, False)
            r2 = _run_code(code, language, stdin, timeout, memory_limit)
            if r2[0] is None:
                return (None, False)
            return (r1[0].strip(), r1[0] == r2[0])
    except Exception:
        return (None, False)


def _generate_testcases(
    correct_answer: str,
    count: int = 100,
    time_limit_ms: int = 1000,
    memory_limit_mb: int = 256,
) -> list[dict]:
    """
    根据正确答案生成测试用例。

    关键自洽性保证：生成时使用与正式比赛判题完全相同的
    time_limit / memory_limit，并且对每个随机输入运行参考代码两次：
      - 若参考代码在该输入下编译/运行/超时/内存出错（输出为 None），丢弃该用例；
      - 若两次运行输出不一致（非确定性），丢弃该用例。
    这样生成的每个测试用例都一定能被“正确答案”在比赛限制内稳定通过，
    避免“新建题目时输入的答案，在正式比赛提交时却过不了样例”的问题。
    """
    language = _detect_language(correct_answer)
    timeout_sec = max((int(time_limit_ms) or 1000) / 1000.0, 1)
    memory_limit = int(memory_limit_mb) if memory_limit_mb else None

    testcases = []
    seed = 0
    # 多尝试一些随机种子，补齐足够的有效用例
    while len(testcases) < count and seed < count * 3:
        input_data = _generate_random_input(seed)
        output, verified = _run_reference_twice(
            correct_answer, language, input_data, timeout_sec, memory_limit
        )
        if output is not None and verified:
            testcases.append({
                'input_data': input_data,
                'expected_output': output,
                'is_sample': len(testcases) < 3,  # 前3个作为样例
                'sort_order': len(testcases),
            })
        seed += 1

    return testcases


def _generate_random_input(seed: int) -> str:
    """生成随机输入数据"""
    random.seed(seed)
    # 生成简单的随机输入：随机整数
    n = random.randint(1, 10)
    nums = [str(random.randint(-100, 100)) for _ in range(n)]
    return ' '.join(nums)


def _build_preexec(memory_mb: int | None):
    """构造 preexec_fn：限制子进程虚拟内存（用于检测 MLE）"""
    if not memory_mb or memory_mb <= 0:
        return None
    try:
        import resource

        limit = int(memory_mb) * 1024 * 1024

        def _limit():
            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
            except Exception:
                pass

        return _limit
    except Exception:
        return None


def _exec_command(cmd: list, stdin: str, timeout: int, memory_mb: int | None):
    """
    执行命令并返回 (stdout, stderr, returncode, timed_out, mem_exceeded)。
    通过 preexec_fn 限制内存，可区分 TLE 与 MLE。
    """
    preexec = _build_preexec(memory_mb)
    try:
        result = subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            preexec_fn=preexec,
        )
        if memory_mb and result.returncode != 0 and result.stderr and 'MemoryError' in result.stderr:
            # RLIMIT_AS 触发 Python 内存错误：标记为内存超限
            return (result.stdout, result.stderr, result.returncode, False, True)
        return (result.stdout, result.stderr, result.returncode, False, False)
    except subprocess.TimeoutExpired:
        return (None, None, None, True, False)
    except (MemoryError, OSError) as exc:
        # setrlimit 生效时可能抛出 MemoryError / OSError(12, 'Cannot allocate memory')
        if isinstance(exc, MemoryError) or (isinstance(exc, OSError) and exc.errno == 12):
            return (None, None, None, False, True)
        return (None, None, None, False, False)
    except Exception:
        return (None, None, None, False, False)


def _interpret(result, is_compiled: bool):
    """
    将执行结果转换为 (stdout, error_type)。
    error_type ∈ {None, 'RE', 'TLE', 'MLE'}。
    编译阶段错误由调用方单独判定为 'CE'。
    """
    stdout, stderr, returncode, timed_out, mem_exceeded = result
    if timed_out:
        return (None, 'TLE')
    if mem_exceeded:
        return (None, 'MLE')
    if returncode != 0:
        # 已编译语言此处仅可能是运行时错误；脚本语言运行失败也归为 RE
        return (None, 'RE')
    return (stdout, None)


def _run_code(code: str, language: str, stdin: str, timeout: int = 5, memory_limit: int | None = None) -> tuple[str | None, str | None]:
    """
    运行代码并返回 (stdout, error_type)。
    error_type ∈ {None, 'CE', 'TLE', 'RE', 'MLE'}：
      - None: 正常运行且有输出
      - 'CE': 编译错误（cpp/java/go）
      - 'TLE': 超时
      - 'RE': 运行时错误（非零退出码）
      - 'MLE': 内存超出限制
    """
    try:
        if language == 'python':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                src = f.name
            try:
                result = _exec_command(['python3', src], stdin, timeout, memory_limit)
            finally:
                os.unlink(src)
            return _interpret(result, is_compiled=False)

        elif language == 'cpp':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                f.write(code)
                f.flush()
                src = f.name
            exe_path = f.name + '.exe'
            try:
                compile_result = subprocess.run(
                    ['g++', '-o', exe_path, src],
                    capture_output=True,
                    text=True,
                    timeout=max(timeout, 10),
                )
                if compile_result.returncode != 0:
                    return (None, 'CE')
                result = _exec_command([exe_path], stdin, timeout, memory_limit)
            finally:
                os.unlink(src)
                if os.path.exists(exe_path):
                    os.unlink(exe_path)
            return _interpret(result, is_compiled=True)

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
                    timeout=max(timeout, 10),
                )
                if compile_result.returncode != 0:
                    return (None, 'CE')
                result = _exec_command(
                    ['java', '-cp', class_dir, 'Main'], stdin, timeout, memory_limit
                )
            finally:
                try:
                    if os.path.exists(java_src):
                        os.unlink(java_src)
                    class_file = os.path.join(os.path.dirname(java_src), 'Main.class')
                    if os.path.exists(class_file):
                        os.unlink(class_file)
                except Exception:
                    pass
            return _interpret(result, is_compiled=True)

        elif language == 'go':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(code)
                f.flush()
                go_src = f.name
            try:
                result = _exec_command(
                    ['go', 'run', go_src], stdin, max(timeout, 15), memory_limit
                )
            finally:
                try:
                    if os.path.exists(go_src):
                        os.unlink(go_src)
                except Exception:
                    pass
            # go run 同时完成编译与运行，非零退出码统一视为编译错误之外归为 RE
            stdout, stderr, returncode, timed_out, mem_exceeded = result
            if timed_out:
                return (None, 'TLE')
            if mem_exceeded:
                return (None, 'MLE')
            if returncode != 0:
                # go 无独立编译阶段，编译失败也归为 CE 以便前端区分
                return (None, 'CE')
            return (stdout, None)

        elif language in ('javascript', 'js', 'node'):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                f.flush()
                js_src = f.name
            try:
                result = _exec_command(['node', js_src], stdin, timeout, memory_limit)
            finally:
                try:
                    if os.path.exists(js_src):
                        os.unlink(js_src)
                except Exception:
                    pass
            return _interpret(result, is_compiled=False)

    except (subprocess.TimeoutExpired, Exception):
        pass
    return (None, 'RE')


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

        # 自动生成测试用例：使用与正式比赛判题一致的时限/内存限制
        testcases = _generate_testcases(
            data['correct_answer'], 100,
            data.get('time_limit', 1000), data.get('memory_limit', 256),
        )
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

        # 生成新测试用例：使用与正式比赛判题一致的时限/内存限制
        testcases = _generate_testcases(
            problem.correct_answer, 100,
            problem.time_limit or 1000, problem.memory_limit or 256,
        )
        for tc in testcases:
            ContestTestcase.create(
                contest_problem=problem,
                input_data=tc['input_data'],
                expected_output=tc['expected_output'],
                is_sample=tc['is_sample'],
                sort_order=tc['sort_order'],
            )

        return {'success': True, 'count': len(testcases)}, 200
