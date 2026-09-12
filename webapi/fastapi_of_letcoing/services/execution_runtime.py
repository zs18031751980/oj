"""独立进程监督器。仅依赖标准库，可随执行镜像独立发布。"""
import json
from pathlib import Path
import resource
import os
import selectors
import signal
import subprocess
import sys
import time


def process_group_cpu(group_id):
    """开发模式资源计量；生产使用容器进程树 cgroup CPU 计量。"""
    ticks = 0
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = path.read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == group_id:
                ticks += sum(int(fields[i]) for i in (11, 12, 13, 14))
        except (OSError, ValueError, IndexError):
            continue
    return ticks / os.sysconf('SC_CLK_TCK')


def run_process(command, stdin, timeout, cwd=None, output_limit=1024 * 1024, uid=None, gid=None,
                cpu_timeout=None, cpu_reader=None):
    started = time.monotonic()
    identity = {'user': uid, 'group': gid, 'extra_groups': []} if uid is not None else {}
    process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        **identity,
        env={'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'LANG': 'C.UTF-8',
             'HOME': '/tmp', 'GOCACHE': '/tmp/go-cache', 'GOMAXPROCS': '2',
             'GOFLAGS': '-p=2', 'PYTHONDONTWRITEBYTECODE': '1'})
    cpu_reader = cpu_reader or (lambda: process_group_cpu(process.pid))
    cpu_used = 0.0
    output = {'stdout': bytearray(), 'stderr': bytearray()}
    data = memoryview((stdin or '').encode())
    offset = 0
    timed_out = output_exceeded = False
    usage = None
    selector = selectors.DefaultSelector()
    for stream, name in ((process.stdout, 'stdout'), (process.stderr, 'stderr')):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, name)
    os.set_blocking(process.stdin.fileno(), False)
    if data:
        selector.register(process.stdin, selectors.EVENT_WRITE, 'stdin')
    else:
        process.stdin.close()
    try:
        while True:
            elapsed = time.monotonic() - started
            if cpu_timeout is not None:
                cpu_used = max(cpu_used, cpu_reader())
            if elapsed >= timeout or (cpu_timeout is not None and cpu_used >= cpu_timeout):
                timed_out = True
                break
            for key, _ in selector.select(min(.02, timeout - elapsed)):
                if key.data == 'stdin':
                    try:
                        offset += os.write(key.fd, data[offset:offset + 65536])
                    except BrokenPipeError:
                        offset = len(data)
                    if offset == len(data):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                else:
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    target = output[key.data]
                    remaining = output_limit - sum(len(v) for v in output.values())
                    target.extend(chunk[:max(remaining, 0)])
                    if len(chunk) > remaining:
                        output_exceeded = True
                        break
            if output_exceeded:
                break
            if process.returncode is None:
                pid, status, stats = os.wait4(process.pid, os.WNOHANG)
                if pid:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    usage = stats
                    # 主进程结束也清理派生进程，避免后代一直持有输出管道。
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            if process.returncode is not None and not selector.get_map():
                break
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        if process.returncode is None:
            _, status, usage = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            if not stream.closed:
                stream.close()
    return {**{key: value.decode('utf-8', errors='replace') for key, value in output.items()},
        'returncode': process.returncode, 'timed_out': timed_out,
        'output_exceeded': output_exceeded, 'memory_exceeded': False,
        'wall_ms': int((time.monotonic() - started) * 1000),
        'cpu_ms': max(int(cpu_used * 1000), int((usage.ru_utime + usage.ru_stime) * 1000) if usage else 0),
        'memory_bytes': int(usage.ru_maxrss * 1024) if usage else 0}


if __name__ == '__main__':
    request = json.load(sys.stdin)
    if type(request.get('uid')) is not int or request['uid'] <= 0 or type(request.get('gid')) is not int or request['gid'] <= 0:
        raise RuntimeError('执行用户必须为非 root 身份')
    def cgroup_seconds():
        with open('/sys/fs/cgroup/cpu.stat') as stream:
            return next(int(line.split()[1]) / 1e6 for line in stream if line.startswith('usage_usec '))
    baseline_cpu = cgroup_seconds()
    own_usage = resource.getrusage(resource.RUSAGE_SELF)
    baseline_own = own_usage.ru_utime + own_usage.ru_stime
    def child_cpu():
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return max(0., cgroup_seconds() - baseline_cpu - usage.ru_utime - usage.ru_stime + baseline_own)
    result = run_process(request['command'], request.get('stdin', ''), request['timeout'],
                         cwd='/work', output_limit=request['output_limit'], uid=request['uid'], gid=request['gid'],
                         cpu_timeout=request.get('cpu_timeout'), cpu_reader=child_cpu)
    # 每个执行容器有独立 cgroup；统计整个进程树，包含 JVM native 内存。
    try:
        with open('/sys/fs/cgroup/memory.peak') as stream:
            result['memory_bytes'] = int(stream.read())
        with open('/sys/fs/cgroup/memory.events') as stream:
            result['memory_exceeded'] = any(line.startswith('oom_kill ') and int(line.split()[1]) > 0
                                            for line in stream)
        result['cpu_ms'] = int(child_cpu() * 1000)
    except (OSError, ValueError, StopIteration):
        # 无法提供可信 cgroup 指标时执行环境不合格，不返回伪造的零指标。
        raise SystemExit('cgroup v2 accounting unavailable')
    print(json.dumps(result))
