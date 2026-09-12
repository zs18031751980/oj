"""只在专用 Worker 主机使用 Docker CLI；API 镜像不挂载 Docker socket。"""
import json
import logging
import time
import os
import re
from pathlib import Path
import subprocess
from uuid import uuid4

from services.execution_runtime import run_process


logger = logging.getLogger('letcoding.sandbox')


def docker_environment():
    # 仅可信 Docker CLI 使用；选手程序始终使用 execution_runtime 的隔离环境。
    keys = ('PATH', 'HOME', 'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_CONFIG',
            'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH', 'XDG_RUNTIME_DIR')
    return {key: os.environ[key] for key in keys if key in os.environ}


def diagnostic_reason(stderr):
    text = str(stderr).lower()
    for needle, reason in (
        ('permission denied', 'permission_denied'),
        ('cannot connect', 'daemon_unavailable'),
        ('failed to connect', 'daemon_unavailable'),
        ('cgroup', 'cgroup_unavailable'),
        ('no such file', 'path_unavailable'),
        ('executable file not found', 'executable_unavailable'),
    ):
        if needle in text:
            return reason
    return 'supervisor_failed'


def cleanup_container(name, timeout=10):
    try:
        result = subprocess.run(['docker', 'rm', '-f', name], capture_output=True,
                                timeout=timeout, env=docker_environment())
        if result.returncode == 0:
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass
    logger.error('sandbox cleanup_failed container=%s', name)
    return False


def reap_expired_containers(now=None):
    """只清理本应用标记且已超过硬截止时间的容器；每轮限制 5 秒/10 个候选。"""
    current = time.time() if now is None else now
    deadline = time.monotonic() + 5
    result = run_process(['docker', 'ps', '-aq', '--filter', 'label=io.letcoding.sandbox=1'],
                         '', 2, output_limit=8192, environment=docker_environment())
    if result['returncode'] != 0 or result['timed_out']:
        raise RuntimeError('sandbox reaper daemon unavailable')
    removed = 0
    for name in result['stdout'].splitlines()[-10:]:
        remaining = deadline-time.monotonic()
        if remaining <= 0 or not re.fullmatch(r'[0-9a-f]{12,64}', name):
            continue
        inspected = run_process(['docker', 'inspect', '--format', '{{json .Config.Labels}}', name],
                                '', min(remaining, 2), output_limit=4096, environment=docker_environment())
        if inspected['returncode'] != 0 or inspected['timed_out']:
            continue
        try:
            labels = json.loads(inspected['stdout'])
            expires = int(labels.get('io.letcoding.expires', '0'))
            eligible = labels.get('io.letcoding.sandbox') == '1' and 0 < expires <= current
        except (ValueError, TypeError, AttributeError):
            continue
        remaining = deadline-time.monotonic()
        if eligible and remaining > 0:
            removed += int(cleanup_container(name, min(remaining, 2)))
    return removed


def execute(command, stdin, timeout, memory_mb, cwd, output_limit=1024 * 1024, compiling=False):
    backend = os.environ.get('JUDGE_BACKEND', 'docker')
    wall_timeout = timeout if compiling else max(timeout * 3, timeout + 1)
    cpu_timeout = None if compiling else timeout
    if backend == 'local':
        if os.environ.get('APP_ENV') not in ('development', 'test') or os.environ.get('ALLOW_UNSAFE_LOCAL_JUDGE') != '1':
            raise RuntimeError('本地执行仅允许显式授权的开发/测试环境')
        return run_process(command, stdin, wall_timeout, cwd, output_limit, cpu_timeout=cpu_timeout)
    if backend != 'docker':
        raise RuntimeError('未知执行后端')
    if not cwd:
        raise RuntimeError('执行器必须指定隔离工作目录')
    workdir = str(Path(cwd).resolve())
    name = 'letcoding-job-' + uuid4().hex
    memory = max(16, min(int(memory_mb or 256), 2048))
    translated = [part.replace(workdir, '/work') for part in command]
    payload = json.dumps({'command': translated, 'stdin': stdin, 'timeout': wall_timeout, 'cpu_timeout': cpu_timeout,
                          'output_limit': output_limit, 'uid': os.getuid(), 'gid': os.getgid()})
    # 每次编译/执行一个容器，编译产物在专用目录复用；测试点只读挂载。
    image = os.environ.get('JUDGE_SANDBOX_IMAGE', 'letcoding-sandbox:local')
    if os.environ.get('APP_ENV') == 'production' and not re.fullmatch(r'(?:[^\s]+@)?sha256:[0-9a-f]{64}', image):
        raise RuntimeError('生产判题镜像必须使用不可变 sha256 digest')
    options = ['docker', 'run', '--name', name, '--network=none', '--read-only',
        '--cap-drop=ALL', '--cap-add=SETUID', '--cap-add=SETGID', '--cap-add=KILL',
        '--security-opt=no-new-privileges', '--pids-limit=128',
        f'--memory={memory}m', f'--memory-swap={memory}m', '--cpus=1',
        '--ulimit', 'nofile=128:128', '--ulimit', 'fsize=67108864:67108864',
        # 可信监督器与用户程序不同 UID；子进程降权后不能信号/ptrace/写监督器结果管道。
        '--user', '0:0',
        '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,size=256m',
        '--mount', f'type=bind,src={workdir},dst=/work' + ('' if compiling else ',readonly'),
        '--workdir', '/',
        '--label', 'io.letcoding.sandbox=1',
        '--label', f'io.letcoding.expires={int(time.time() + wall_timeout + 90)}', '--log-driver=none', '-i',
        image,
        'python3', '/opt/execution_runtime.py']
    cpuset = os.environ.get('JUDGE_CPUSET')
    if cpuset:
        if not re.fullmatch(r'[0-9]+', cpuset):
            raise RuntimeError('每个 Worker 槽位只允许绑定一个 CPU')
        options[2:2] = ['--cpuset-cpus', cpuset]
    if os.getuid() == 0:
        raise RuntimeError('判题 Worker 必须以非 root 用户运行')
    try:
        result = run_process(options, payload, wall_timeout + 15, output_limit=output_limit * 8 + 65536,
                             environment=docker_environment())
        if result['timed_out']:
            raise RuntimeError('执行容器启动或监督超时')
        if result['returncode'] != 0:
            try:
                inspect = subprocess.run(['docker', 'inspect', '--format', '{{.State.OOMKilled}}', name],
                    capture_output=True, text=True, timeout=5, env=docker_environment())
                oom = inspect.returncode == 0 and inspect.stdout.strip() == 'true'
            except (OSError, subprocess.TimeoutExpired):
                oom = False
            if oom:
                return {'stdout': '', 'stderr': '', 'returncode': -9, 'timed_out': False,
                        'output_exceeded': False, 'memory_exceeded': True, 'cpu_ms': 0,
                        'memory_bytes': memory * 1024 * 1024}
            reason = diagnostic_reason(result.get('stderr', ''))
            logger.error('sandbox failure container=%s reason=%s exit=%s', name, reason, result['returncode'])
            raise RuntimeError(f'执行器异常 reason={reason} diagnostic_id={name}')
        return json.loads(result['stdout'])
    finally:
        cleanup_container(name)
