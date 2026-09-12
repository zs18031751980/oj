"""沙箱基础设施错误不得丢失诊断、污染判定或被清理异常覆盖。"""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest


def test_unprivileged_launcher_enters_private_directory_without_exposing_environment(tmp_path):
    runtime = Path(__file__).resolve().parents[1]/'services/execution_runtime.py'
    tmp_path.chmod(0o700)
    result = subprocess.run([sys.executable, str(runtime), '--exec', str(tmp_path),
                             sys.executable, '-c', 'import os; print(os.getcwd()); print(os.getuid())'],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [str(tmp_path), str(os.getuid())]
    assert tmp_path.stat().st_mode & 0o777 == 0o700


def test_sandbox_cleanup_timeout_preserves_primary_failure(tmp_path, monkeypatch, caplog):
    from services import sandbox_service as sandbox
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'docker')
    result = {'stdout': '', 'stderr': 'permission denied password=private-secret',
              'returncode': 126, 'timed_out': False}
    def boundary(command, **kwargs):
        if command[1] == 'inspect':
            return subprocess.CompletedProcess(command, 0, 'false', '')
        raise subprocess.TimeoutExpired(command, 10)
    with patch.object(sandbox, 'run_process', return_value=result), \
         patch.object(sandbox.subprocess, 'run', side_effect=boundary):
        with pytest.raises(RuntimeError) as failure:
            sandbox.execute(['python3', 'main.py'], '', 1, 128, str(tmp_path))
    assert 'permission_denied' in str(failure.value)
    assert 'cleanup' in caplog.text
    assert 'private-secret' not in caplog.text + str(failure.value)


def test_sandbox_cleanup_failure_does_not_replace_success(tmp_path, monkeypatch):
    from services import sandbox_service as sandbox
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'docker')
    payload = {'stdout': '42', 'stderr': '', 'returncode': 0, 'timed_out': False,
               'output_exceeded': False, 'memory_exceeded': False, 'cpu_ms': 1, 'memory_bytes': 1}
    with patch.object(sandbox, 'run_process', return_value={
        'stdout': json.dumps(payload), 'stderr': '', 'returncode': 0, 'timed_out': False}), \
         patch.object(sandbox.subprocess, 'run', side_effect=subprocess.TimeoutExpired('docker', 10)):
        assert sandbox.execute(['python3', 'main.py'], '', 1, 128, str(tmp_path))['stdout'] == '42'


def test_docker_environment_keeps_only_trusted_connection_settings(monkeypatch):
    from services.sandbox_service import docker_environment
    monkeypatch.setenv('DOCKER_HOST', 'unix:///tmp/isolated.sock')
    monkeypatch.setenv('JWT_SECRET_KEY', 'private-jwt')
    monkeypatch.setenv('DATABASE_URL', 'private-db')
    values = docker_environment()
    assert values['DOCKER_HOST'] == 'unix:///tmp/isolated.sock'
    assert 'JWT_SECRET_KEY' not in values and 'DATABASE_URL' not in values


def test_orphan_reaper_removes_only_labelled_expired_containers(tmp_path, monkeypatch):
    from services.sandbox_service import reap_expired_containers
    docker = tmp_path/'docker'
    log = tmp_path/'removed'
    # 用真实子进程模拟 Docker API 边界，不访问宿主容器。
    docker.write_text('#!'+sys.executable+'\n'+f'''import sys, json
args = sys.argv[1:]
if args[0] == 'ps':
    print('a'*64); print('b'*64); print('c'*64)
elif args[0] == 'inspect':
    kind = args[-1][0]
    print(json.dumps({{'io.letcoding.sandbox': '1' if kind != 'c' else '0',
                       'io.letcoding.expires': '50' if kind != 'b' else '200'}}))
elif args[0] == 'rm':
    with open({str(log)!r}, 'a') as f: f.write(args[-1]+'\\n')
else:
    sys.exit(2)
''')
    docker.chmod(0o700)
    monkeypatch.setenv('PATH', str(tmp_path)+os.pathsep+os.environ['PATH'])
    assert reap_expired_containers(now=100) == 1
    assert log.read_text().splitlines() == ['a'*64]
