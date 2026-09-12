"""专用沙箱验收：必须在有 Docker / cgroup v2 的非 root Linux 主机运行。

单独运行 pytest tests/sandbox_integration.py；daemon/镜像缺失会失败，不会跳过。
"""
import os
import subprocess

import pytest

from controllers.contest_problem_controller import _prepare_program


@pytest.fixture(autouse=True)
def docker_backend(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('JUDGE_BACKEND', 'docker')
    assert os.getuid() != 0
    subprocess.run(['docker', 'info'], check=True, capture_output=True)
    image = os.environ.get('JUDGE_SANDBOX_IMAGE', 'letcoding-sandbox:local')
    digest = subprocess.run(['docker', 'image', 'inspect', '--format', '{{.Id}}', image],
        check=True, capture_output=True, text=True).stdout.strip()
    monkeypatch.setenv('JUDGE_SANDBOX_IMAGE', digest)


def run(code, language='python', memory=128, timeout=3):
    program, error, stderr = _prepare_program(code, language)
    assert program is not None, (error, stderr)
    try:
        return program.run('', timeout, memory)
    finally:
        program.close()


def test_host_files_credentials_and_network_are_not_visible(tmp_path):
    secret = tmp_path / 'host-only-secret'
    secret.write_text('synthetic secret')
    source = f'''import os
print(os.path.exists({str(secret)!r}))
print(os.path.exists('/app'))
print(os.environ.get('JWT_SECRET_KEY'))
print(sorted(os.listdir('/sys/class/net')))
'''
    stdout, error, _, _ = run(source)
    assert error is None
    assert stdout.splitlines() == ['False', 'False', 'None', "['lo']"]


def test_wall_timeout_and_output_limit():
    assert run('while True: pass', timeout=.2)[1] == 'TLE'
    assert run('while True: print("x"*65536)', timeout=3)[1] == 'OLE'


def test_memory_is_limited_for_entire_container():
    assert run('x = bytearray(512*1024*1024)', memory=64)[1] == 'MLE'


def test_user_program_cannot_control_supervisor_or_inherit_capabilities():
    source = '''import os, signal
print(os.getuid() != 0)
try:
    os.kill(1, signal.SIGTERM)
    print("unsafe signal")
except PermissionError:
    print("signal denied")
try:
    open('/proc/1/fd/1', 'w')
    print("unsafe pipe")
except PermissionError:
    print("pipe denied")
for line in open('/proc/self/status'):
    if line.startswith('CapEff:'):
        print(int(line.split()[1], 16))
'''
    stdout, error, _, _ = run(source)
    assert error is None
    assert stdout.splitlines() == ['True', 'signal denied', 'pipe denied', '0']


@pytest.mark.parametrize(('language', 'source'), [
    ('cpp', '#include <iostream>\nint main(){std::cout << 42;}'),
    ('java', 'public class Main {public static void main(String[] args){System.out.println(42);}}'),
    ('go', 'package main\nimport "fmt"\nfunc main(){fmt.Println(42)}'),
])
def test_compilation_and_execution_are_isolated(language, source):
    stdout, error, _, _ = run(source, language, memory=256, timeout=5)
    assert error is None
    assert stdout.strip() == '42'
