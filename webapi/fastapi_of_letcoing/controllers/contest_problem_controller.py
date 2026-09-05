import json
import random
import re
import string
import subprocess
import tempfile
import os
import shutil
import signal
import time
from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from models.db_models import (
    Contest, ContestParticipant, ContestProblem, ContestTestcase, ContestSubmission, User
)
from core.di_container import inject
from interfaces.service_interfaces import IJWTService, IRedisService

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
    'testcases': fields.List(fields.Raw, description='测试数据列表，每项含 input/output/is_sample'),
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


# 典型的「非确定性」来源：基于时间/随机种子的播种。一旦参考代码依赖这些，
# 它在不同时间/进程下输出会变化，导致「建题时答案能过、正式比赛提交却部分 WA」。
_NONDET_PATTERNS = [
    (r'srand\s*\(\s*(time|std::time|chrono)', "srand(time(...)) 按时间播种"),
    (r'random_device', "std::random_device（通常非确定性）"),
    (r'(system_clock|steady_clock|high_resolution_clock)\s*::\s*now\s*\(\s*\)', "chrono::now() 取当前时间"),
    (r'time\s*\(\s*(NULL|0|nullptr|_)', "time(NULL) 取当前时间"),
    (r'arc4random', "arc4random（非确定性随机）"),
    (r'/dev/urandom', "读取 /dev/urandom（非确定性随机）"),
    (r'Math\.random\s*\(', "Math.random()（非确定性随机）"),
    (r'Date\.now\s*\(', "Date.now()（取当前时间）"),
    (r'performance\.now\s*\(', "performance.now()（取当前时间）"),
    (r'(time\.time|datetime\.now)\s*\(', "time/datetime.now（取当前时间）"),
    (r'os\.urandom|secrets\.', "os.urandom/secrets（非确定性随机）"),
]


def _strip_comments(code: str, language: str) -> str:
    """粗略剔除注释，避免注释里的字眼（如 `// time(NULL) 不好`）误触发非确定性判定。"""
    # 字符串字面量中的 // # /* 不处理（OJ 答案代码极少在字符串里写这些关键字），足够稳妥
    if language in ('cpp', 'java', 'js', 'javascript'):
        code = re.sub(r'/\*.*?\*/', ' ', code, flags=re.S)
        code = re.sub(r'//[^\n]*', ' ', code)
    else:  # python 等以 # 注释
        code = re.sub(r'#[^\n]*', ' ', code)
    return code


def _reference_looks_nondeterministic(code: str, language: str) -> tuple[bool, str]:
    """
    静态扫描参考代码是否含有「非确定性」特征（时间/随机播种等）。

    为什么需要静态扫描：仅靠「多次运行一致性」校验无法 100% 捕捉非确定性——
    例如 C 库 rand() 的最低位在不同秒之间常保持稳定，仅靠重跑会误判为“确定”。
    因此直接识别常见的非确定性播种写法，从源头拦截，确保只有确定性参考代码
    才能生成比赛测试用例。
    """
    code = _strip_comments(code, language)

    # srand 使用非常量种子（如 srand(t)）必然非确定；srand(42) 这类常量种子是确定的
    m = re.search(r'srand\s*\((.*?)\)', code, re.S)
    if m and not re.search(r'^\s*-?\d+\s*$', m.group(1)):
        return True, "srand 使用了非常量种子（疑似时间/随机播种）"

    # Python 的 random 默认按系统熵播种；只有显式 random.seed(常量) 才是确定的
    if language in ('python', 'py'):
        if re.search(r'random\.', code) and not re.search(r'random\.seed\s*\(\s*-?\d+', code):
            return True, "使用了 random 但未用固定种子（默认非确定性）"

    for pat, desc in _NONDET_PATTERNS:
        if re.search(pat, code):
            return True, desc
    return False, ''


def _sleep_to_next_second():
    """睡到下一个整秒之后一点点，保证后续运行落在与当前不同的墙钟秒内。

    用于捕捉「按秒播种」的非确定性（srand(time(NULL))、chrono::system_clock 取秒等）：
    紧挨着跑两次往往落在同一秒 → 种子相同 → 误判为确定；跨秒后种子不同 → 暴露差异。
    """
    now = time.time()
    time.sleep(1.0 - (now - int(now)) + 0.02)


def _run_reference_twice(
    code: str, language: str, stdin: str, timeout: int, memory_limit: int | None
) -> tuple[str | None, bool, int]:
    """
    运行参考代码三次（两次之间强制跨秒）并返回 (输出, 是否自洽, 首次运行耗时ms)。

    这是「答案代码在比赛提交时却过不了部分用例」的根因修复关键：
      - 编译型语言每次运行都是独立进程（ASLR 不同），可捕捉未初始化变量/UB/容器遍历序
        等非确定性；
      - 两次运行强制跨秒（见 `_sleep_to_next_second`），可捕捉 time(NULL)/chrono 按秒
        播种等非确定性——这是原题「新建时答案能过、正式比赛（另一时刻运行）却 WA」的主因；
      - 任意一次编译/运行/超时/内存出错（输出为 None）→ 返回 (None, False, 0)；
      - 三次原始输出不一致 → 视为非确定性，返回 (输出, False, 0)；
      - 三次完全一致 → 返回 (去尾空白后的输出, True, 首次运行耗时ms)。
    耗时 ms 用于「确保用例在时间限制内」与「卡时间限制」的规模校准。
    """
    try:
        outputs = []
        times = []
        for i in range(3):
            out, err_type, time_used_ms, _ = _run_code(
                code, language, stdin, timeout, memory_limit
            )
            if err_type is not None or out is None:
                return (None, False, 0)
            outputs.append(out)
            times.append(time_used_ms)
            if i < 2:
                _sleep_to_next_second()
        return (outputs[0].strip(), all(o == outputs[0] for o in outputs), times[0])
    except Exception:
        return (None, False, 0)



def _measure_reference_runtime(
    code: str, language: str, size: int, seed: int, timeout_sec: float, memory_limit: int | None
) -> int | None:
    """单次运行参考代码并返回耗时 ms；编译/运行/TLE/MLE/RE 时返回 None。"""
    stdin = _generate_random_input(seed, size)
    out, err_type, time_used_ms, _ = _run_code(
        code, language, stdin, timeout_sec, memory_limit
    )
    if err_type is not None or out is None:
        return None
    return time_used_ms


def _find_max_feasible_size(
    code: str, language: str, timeout_sec: float, memory_limit: int | None, target_ms: float
) -> int:
    """倍增 + 二分，求出「运行时长最接近但不超过 target_ms」的最大输入规模。

    参考代码复杂度未知（O(n)/O(n log n)/O(n²)…），因此直接用实测运行时长驱动搜索，
    对任意时间限制都能自适应地求出可用的最大规模——时间限制越大，得到的规模越大，
    从而保证「卡时限」用例对不同的 time_limit 都成立。
    """
    last_ok = 1
    size = 1
    while size <= _MAX_INPUT_ELEMENTS:
        rt = _measure_reference_runtime(code, language, size, seed=size, timeout_sec=timeout_sec, memory_limit=memory_limit)
        if rt is None:
            # 当前规模运行出错/超时：以最后一个可用规模为下界，进入二分
            break
        if rt >= target_ms:
            break
        last_ok = size
        size *= 2

    if size > _MAX_INPUT_ELEMENTS:
        # 达到规模上限仍未触及目标（如 O(1) 快速实现）：直接以上限作为最大规模
        return _MAX_INPUT_ELEMENTS

    # 二分：在 (last_ok, size] 间找运行时长 < target 的最大规模
    lo, hi = last_ok, size
    while lo < hi:
        mid = (lo + hi + 1) // 2
        rt = _measure_reference_runtime(code, language, mid, seed=mid, timeout_sec=timeout_sec, memory_limit=memory_limit)
        if rt is None or rt >= target_ms:
            hi = mid - 1
        else:
            lo = mid
    return max(lo, 1)


def _build_size_plan(max_size: int, count: int) -> list[int]:
    """构造 count 个用例的规模计划：
      - 前 3 个为小规模样例；
      - 中部约 3/4 为中等规模（分布偏向更小，保证绝大多数用例轻量稳定）；
      - 末段约 1/4 为「卡时间限制」的大规模（用于卡掉暴力解法）。
    规模均不超过 max_size，即参考代码运行时长不超过时间限制。
    """
    plan = [1, 2, 3]
    if count <= 3:
        return plan[:count]
    mid = int((count - 3) * 0.75)
    for i in range(mid):
        f = i / max(mid - 1, 1)
        plan.append(max(1, int(max_size * (0.05 + 0.45 * (f ** 0.7)))))
    tight = count - len(plan)
    for i in range(tight):
        f = i / max(tight - 1, 1)
        plan.append(max(1, int(max_size * (0.7 + 0.25 * f))))
    return plan


def _generate_testcases(
    correct_answer: str,
    count: int = 100,
    time_limit_ms: int = 1000,
    memory_limit_mb: int = 256,
) -> list[dict]:
    """
    根据正确答案生成测试用例。

    关键自洽性保证：生成时使用与正式比赛判题完全相同的
    time_limit / memory_limit，并且对每个随机输入运行参考代码多次：
      - 若参考代码在该输入下编译/运行/超时/内存出错（输出为 None），丢弃该用例；
      - 若多次运行输出不一致（非确定性），丢弃该用例；
      - 若首次运行耗时超过时间限制（保留 2% 余量），丢弃该用例。
    这样生成的每个测试用例都一定能在时间限制内被参考代码稳定通过。

    时间限制自适应：先用「倍增 + 二分」实测求出参考代码在时间限制内能处理的最大
    输入规模（对任意复杂度/任意 time_limit 均自适应），再按规模计划生成用例——
    其中末段约 1/4 为贴近时间限制的大规模用例，用于在正式比赛中卡掉暴力解法。
    """
    language = _detect_language(correct_answer)
    limit_ms = max(int(time_limit_ms or 1000), 50)
    timeout_sec = limit_ms / 1000.0
    memory_limit = int(memory_limit_mb) if memory_limit_mb else None

    # 找「卡时限」规模：运行时长 ≈ 85% × 时间限制，留足判题机波动的余量
    target_ms = 0.85 * limit_ms
    max_size = _find_max_feasible_size(
        correct_answer, language, timeout_sec, memory_limit, target_ms=target_ms,
    )
    plan = _build_size_plan(max_size, count)

    testcases = []
    for idx, size in enumerate(plan):
        # 每个规模最多尝试多个随机种子，直到拿到一个自洽且不超时的用例
        for attempt in range(20):
            input_data = _generate_random_input(1000 + idx * 1000 + attempt, size)
            output, verified, time_ms = _run_reference_twice(
                correct_answer, language, input_data, timeout_sec, memory_limit
            )
            if output is not None and verified and 0 < time_ms <= limit_ms * 0.98:
                testcases.append({
                    'input_data': input_data,
                    'expected_output': output,
                    'is_sample': len(testcases) < 3,  # 前3个作为样例
                    'sort_order': len(testcases),
                })
                break

    return testcases


# 单个测试用例的元素个数上限（约 300KB 输入），避免用例体积失控
_MAX_INPUT_ELEMENTS = 50000


def _generate_random_input(seed: int, size: int = 1) -> str:
    """生成随机输入数据；size 控制元素个数（规模），用于把参考代码运行时长推向时间限制。"""
    random.seed(seed)
    n = max(1, size)
    # 值域随规模适度放大，让大规模用例的数值分布也更有区分度
    bound = max(1, min(size, 1000))
    nums = [str(random.randint(-bound, bound)) for _ in range(n)]
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


def _exec_command(cmd: list, stdin: str, timeout: float, memory_mb: int | None, cwd: str | None = None):
    """
    执行命令并返回 (stdout, stderr, returncode, timed_out, mem_exceeded)。
    通过 preexec_fn 限制内存，可区分 TLE 与 MLE。
    """
    preexec = _build_preexec(memory_mb)
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec,
            start_new_session=True,
            cwd=cwd,
            # 运行用户代码时不传递数据库、JWT 等服务进程环境变量。
            env={'PATH': os.environ.get('PATH', ''), 'LANG': 'C.UTF-8'},
        )
        try:
            stdout, stderr = process.communicate(input=stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            # 终止整个进程组，防止提交代码 fork 后子进程继续占用主机资源。
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            return (None, None, None, True, False)
        result = type('ExecutionResult', (), {
            'stdout': stdout, 'stderr': stderr, 'returncode': process.returncode,
        })()
        if memory_mb and result.returncode != 0 and result.stderr and 'MemoryError' in result.stderr:
            # RLIMIT_AS 触发 Python 内存错误：标记为内存超限
            return (result.stdout, result.stderr, result.returncode, False, True)
        return (result.stdout, result.stderr, result.returncode, False, False)
    except (MemoryError, OSError) as exc:
        # setrlimit 生效时可能抛出 MemoryError / OSError(12, 'Cannot allocate memory')
        if isinstance(exc, MemoryError) or (isinstance(exc, OSError) and exc.errno == 12):
            return (None, None, None, False, True)
        return (None, None, None, False, False)
    except Exception:
        return (None, None, None, False, False)


class PreparedProgram:
    """一次编译、多次执行的受限程序。

    比赛判题会对同一提交运行多组数据；将编译移出测试点循环可显著降低
    C++/Java/Go 的队列耗时，也保证 Java 的 ``public class Main`` 使用正确文件名。
    这不是安全沙箱：生产环境必须在容器执行器中运行本对象。
    """

    def __init__(self, command: list[str], workdir: str, language: str):
        self.command = command
        self.workdir = workdir
        self.language = language

    def run(self, stdin: str, timeout: float, memory_limit: int | None):
        started = time.perf_counter()
        command, os_memory_limit = self.command, memory_limit
        if self.language == 'java' and memory_limit:
            # JVM 会预留远大于 Java 堆的虚拟地址空间，RLIMIT_AS 会导致其在
            # 业务代码执行前启动失败。改为限制堆，并保留进程级时间/PID 控制。
            heap_mb = max(int(memory_limit) - 64, 16)
            command = ['java', '-Xms16m', f'-Xmx{heap_mb}m', *self.command[1:]]
            os_memory_limit = None
        result = _exec_command(command, stdin, timeout, os_memory_limit, cwd=self.workdir)
        elapsed = int((time.perf_counter() - started) * 1000)
        stdout, error_type, stderr = _interpret(result, is_compiled=True)
        return stdout, error_type, elapsed, stderr

    def close(self):
        shutil.rmtree(self.workdir, ignore_errors=True)


def _prepare_program(code: str, language: str, compile_timeout: float = 20.0):
    """准备一次可重复执行的程序，返回 ``(program, error_type, stderr)``。"""
    normalized = {'js': 'javascript', 'node': 'javascript', 'py': 'python'}.get(
        (language or '').lower(), (language or '').lower()
    )
    if normalized not in {'python', 'cpp', 'java', 'go', 'javascript'}:
        return None, 'CE', f'不支持的比赛语言: {language}'

    workdir = tempfile.mkdtemp(prefix='letcoding-judge-')
    try:
        if normalized == 'python':
            source = os.path.join(workdir, 'main.py')
            with open(source, 'w', encoding='utf-8') as f:
                f.write(code)
            return PreparedProgram(['python3', source], workdir, normalized), None, None
        if normalized == 'javascript':
            source = os.path.join(workdir, 'main.js')
            with open(source, 'w', encoding='utf-8') as f:
                f.write(code)
            return PreparedProgram(['node', source], workdir, normalized), None, None
        if normalized == 'cpp':
            source, executable = os.path.join(workdir, 'main.cpp'), os.path.join(workdir, 'main')
            with open(source, 'w', encoding='utf-8') as f:
                f.write(code)
            result = subprocess.run(
                ['g++', '-O2', '-pipe', '-std=c++17', source, '-o', executable],
                capture_output=True, text=True, timeout=compile_timeout,
            )
            if result.returncode:
                shutil.rmtree(workdir, ignore_errors=True)
                return None, 'CE', result.stderr
            return PreparedProgram([executable], workdir, normalized), None, None
        if normalized == 'java':
            source = os.path.join(workdir, 'Main.java')
            with open(source, 'w', encoding='utf-8') as f:
                f.write(code)
            result = subprocess.run(
                ['javac', '-d', workdir, source], capture_output=True, text=True,
                timeout=compile_timeout,
            )
            if result.returncode:
                shutil.rmtree(workdir, ignore_errors=True)
                return None, 'CE', result.stderr
            return PreparedProgram(['java', '-cp', workdir, 'Main'], workdir, normalized), None, None
        source, executable = os.path.join(workdir, 'main.go'), os.path.join(workdir, 'main')
        with open(source, 'w', encoding='utf-8') as f:
            f.write(code)
        result = subprocess.run(
            ['go', 'build', '-o', executable, source], capture_output=True, text=True,
            timeout=compile_timeout,
        )
        if result.returncode:
            shutil.rmtree(workdir, ignore_errors=True)
            return None, 'CE', result.stderr
        return PreparedProgram([executable], workdir, normalized), None, None
    except subprocess.TimeoutExpired:
        shutil.rmtree(workdir, ignore_errors=True)
        return None, 'CE', '编译超时'
    except Exception as exc:
        shutil.rmtree(workdir, ignore_errors=True)
        return None, 'CE', str(exc)


def _interpret(result, is_compiled: bool):
    """
    将执行结果转换为 (stdout, error_type, stderr)。
    error_type ∈ {None, 'RE', 'TLE', 'MLE'}。
    编译阶段错误由调用方单独判定为 'CE'。
    """
    stdout, stderr, returncode, timed_out, mem_exceeded = result
    if timed_out:
        return (None, 'TLE', stderr)
    if mem_exceeded:
        return (None, 'MLE', stderr)
    if returncode != 0:
        # 已编译语言此处仅可能是运行时错误；脚本语言运行失败也归为 RE
        return (None, 'RE', stderr)
    return (stdout, None, stderr)


def normalize_judge_output(value: str | None) -> str:
    """采用标准 OJ 空白规则比较输出。

    保留每行的内容与换行结构，只忽略 Windows/Unix 换行差异、行尾空白及文件末尾
    的空白行。这样不会把 ``1 2`` 与 ``12`` 等不同答案误判相同。
    """
    text = (value or '').replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip(' \t') for line in text.split('\n')]
    while lines and lines[-1] == '':
        lines.pop()
    return '\n'.join(lines)


def _run_code(code: str, language: str, stdin: str, timeout: int = 5, memory_limit: int | None = None) -> tuple[str | None, str | None, int, str | None]:
    """
    运行代码并返回 (stdout, error_type, time_used_ms, stderr)。
    error_type ∈ {None, 'CE', 'TLE', 'RE', 'MLE'}：
      - None: 正常运行且有输出
      - 'CE': 编译错误（cpp/java/go）
      - 'TLE': 超时
      - 'RE': 运行时错误（非零退出码）
      - 'MLE': 内存超出限制
    time_used_ms 仅统计「运行」耗时（不含编译），单位毫秒。
    """
    # 对单次调用也复用统一的编译/运行实现，避免各语言行为漂移。
    program, prepare_error, prepare_stderr = _prepare_program(code, language)
    if program is not None:
        try:
            return program.run(stdin, timeout, memory_limit)
        finally:
            program.close()
    return None, prepare_error or 'CE', 0, prepare_stderr


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


def _normalize_testcases(raw_testcases, raw_samples) -> list[dict]:
    """校验管理员提供的测试数据；不再凭参考代码臆造题目输入格式。"""
    source = raw_testcases
    if source is None:
        source = raw_samples or []
    if isinstance(source, str):
        try:
            source = json.loads(source)
        except json.JSONDecodeError as exc:
            raise ValueError('测试数据必须是合法 JSON') from exc
    if not isinstance(source, list) or not source:
        raise ValueError('至少需要提供一组测试数据')
    if len(source) > 200:
        raise ValueError('测试数据最多 200 组')
    normalized = []
    for index, item in enumerate(source):
        if not isinstance(item, dict) or 'input' not in item or 'output' not in item:
            raise ValueError(f'第 {index + 1} 组测试数据必须包含 input 与 output')
        input_data, output_data = str(item['input']), str(item['output'])
        if len(input_data) > 65536 or len(output_data) > 65536:
            raise ValueError(f'第 {index + 1} 组测试数据过大（上限 64KB）')
        normalized.append({
            'input_data': input_data,
            'expected_output': output_data,
            'is_sample': bool(item.get('is_sample', raw_testcases is None)),
            'sort_order': index,
        })
    return normalized


def _verify_reference_answer(code: str, language: str, testcases: list[dict], time_limit: int, memory_limit: int):
    """建题时验证参考答案能稳定通过管理员提供的每组测试数据。"""
    program, error_type, stderr = _prepare_program(code, language)
    if program is None:
        raise ValueError(f'参考代码编译失败：{stderr or error_type}')
    try:
        timeout = max(int(time_limit or 1000) / 1000.0, 0.05)
        for index, testcase in enumerate(testcases):
            output, run_error, _, run_stderr = program.run(
                testcase['input_data'], timeout, int(memory_limit or 256),
            )
            if run_error:
                raise ValueError(f'参考代码在第 {index + 1} 组测试数据上失败：{run_error} {run_stderr or ""}'.strip())
            if normalize_judge_output(output) != normalize_judge_output(testcase['expected_output']):
                raise ValueError(f'参考代码输出与第 {index + 1} 组测试数据的期望输出不一致')
    finally:
        program.close()


def _replace_testcases(problem: ContestProblem, testcases: list[dict]):
    ContestTestcase.delete().where(ContestTestcase.contest_problem == problem).execute()
    for testcase in testcases:
        ContestTestcase.create(contest_problem=problem, **testcase)


def _validate_limits(time_limit, memory_limit) -> tuple[int, int]:
    """统一限制题目资源配置，避免 0ms/负数等配置破坏严格判题语义。"""
    try:
        time_ms, memory_mb = int(time_limit), int(memory_limit)
    except (TypeError, ValueError) as exc:
        raise ValueError('时间限制和内存限制必须是整数') from exc
    if not 50 <= time_ms <= 60000:
        raise ValueError('时间限制必须在 50ms 到 60000ms 之间')
    if not 16 <= memory_mb <= 2048:
        raise ValueError('内存限制必须在 16MB 到 2048MB 之间')
    return time_ms, memory_mb


@api.route('/')
class ContestProblemListController(Resource):
    @api.doc('list_contest_problems')
    @api.param('contest_id', '比赛ID')
    def get(self):
        """获取比赛题目列表"""
        _, err = _require_manager()
        if err:
            return err
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
        try:
            time_limit, memory_limit = _validate_limits(
                data.get('time_limit', 1000), data.get('memory_limit', 256),
            )
        except ValueError as exc:
            return {'error': str(exc)}, 400

        try:
            testcases = _normalize_testcases(data.get('testcases'), data.get('samples'))
            _verify_reference_answer(
                data['correct_answer'], data.get('language', 'cpp'), testcases,
                time_limit, memory_limit,
            )
        except ValueError as exc:
            return {'error': str(exc)}, 400

        # 创建题目及已验证的测试数据。测试数据必须由出题人提供，避免泛化随机输入
        # 对任意题目都生成非法数据的错误设计。
        problem = ContestProblem.create(
            contest=contest,
            problem_index=data['problem_index'].strip(),
            title=data['title'].strip(),
            description=data['description'],
            input_desc=data.get('input_desc', ''),
            output_desc=data.get('output_desc', ''),
            correct_answer=data['correct_answer'],
            time_limit=time_limit,
            memory_limit=memory_limit,
            difficulty=data.get('difficulty', '中等'),
            language=data.get('language', 'cpp'),
            samples=data.get('samples', '[]'),
            sort_order=data.get('sort_order', 0),
        )
        _replace_testcases(problem, testcases)

        result = _problem_to_dict(problem)
        result['testcase_generation'] = 'done'
        return result, 201


@api.route('/<int:problem_id>')
class ContestProblemDetailController(Resource):
    def get(self, problem_id):
        """获取比赛题目详情"""
        _, err = _require_manager()
        if err:
            return err
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
        try:
            time_limit, memory_limit = _validate_limits(problem.time_limit, problem.memory_limit)
        except ValueError as exc:
            return {'error': str(exc)}, 400
        problem.time_limit = time_limit
        problem.memory_limit = memory_limit
        replacement_testcases = None
        if 'testcases' in data or 'samples' in data:
            try:
                replacement_testcases = _normalize_testcases(data.get('testcases'), data.get('samples'))
                _verify_reference_answer(
                    data.get('correct_answer', problem.correct_answer),
                    data.get('language', problem.language), replacement_testcases,
                    time_limit, memory_limit,
                )
            except ValueError as exc:
                return {'error': str(exc)}, 400
        problem.save()
        if replacement_testcases is not None:
            _replace_testcases(problem, replacement_testcases)
        return _problem_to_dict(problem), 200

    def delete(self, problem_id):
        """删除比赛题目（同时清理其测试用例与提交记录）"""
        user, err = _require_manager()
        if err:
            return err

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

        try:
            # 显式按依赖顺序清理子表，避免外键约束冲突或级联未生效导致删除失败
            ContestTestcase.delete().where(
                ContestTestcase.contest_problem == problem
            ).execute()
            from models.db_models import ContestSubmission
            ContestSubmission.delete().where(
                ContestSubmission.contest_problem == problem
            ).execute()
            problem.delete_instance()
            return {'success': True}, 200
        except Exception as exc:
            return {'error': f'删除失败: {exc}'}, 500


@api.route('/<int:problem_id>/regenerate-testcases')
class RegenerateTestcasesController(Resource):
    def post(self, problem_id):
        """废弃自动生成：通用题目必须由管理员提供有效测试数据。"""
        user, err = _require_manager()
        if err:
            return err

        try:
            problem = ContestProblem.get_by_id(problem_id)
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

        return {'error': '自动随机生成已停用，请在编辑题目时提交经过验证的测试数据'}, 409


@api.route('/<int:problem_id>/testcase-generation')
class TestcaseGenerationStatusController(Resource):
    def get(self, problem_id):
        """轮询测试用例生成进度（建题/重生成后供前端展示）"""
        user, err = _require_manager()
        if err:
            return err

        try:
            ContestProblem.get_by_id(problem_id)
        except ContestProblem.DoesNotExist:
            return {'error': '题目不存在'}, 404

        redis_service = inject(IRedisService)
        status = redis_service.get(f"testcase_gen:{problem_id}")
        if not status:
            # 无记录：可能是任务刚入队、worker 尚未写入 generating（存在竞态窗口），
            # 也可能是生成完成且缓存已过期。以数据库实际用例数区分，避免把“尚未开始”
            # 误报为“已完成 0 组”，导致前端提前停止轮询、误显示生成了 0 组。
            try:
                from models.db_models import ContestTestcase
                count = ContestTestcase.select().where(
                    ContestTestcase.contest_problem == problem_id
                ).count()
                if count == 0:
                    status = {'status': 'pending', 'generated': 0, 'total': 0}
                else:
                    status = {'status': 'done', 'generated': count, 'total': count}
            except Exception:
                status = {'status': 'pending', 'generated': 0, 'total': 0}
        return status, 200
