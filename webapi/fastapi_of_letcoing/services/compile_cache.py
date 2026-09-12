"""Worker 私有的编译缓存。缓存不挂入执行沙箱，命中后复制到独立工作目录。"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def _hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _restore(entry, workdir, key):
    if entry.is_symlink():
        return None
    metadata = json.loads((entry / 'manifest.json').read_text())
    if not isinstance(metadata, dict) or metadata.get('key') != key:
        return None
    files, command = metadata.get('files'), metadata.get('command')
    if not isinstance(files, dict) or not 1 <= len(files) <= 256:
        return None
    if not isinstance(command, list) or not command or any(
            not isinstance(part, str) or not part or '\0' in part for part in command):
        return None
    for relative, digest in metadata['files'].items():
        path = entry / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(entry.resolve()):
            return None
        if _hash(path) != digest:
            return None
    for relative in metadata['files']:
        destination = Path(workdir) / relative
        if not destination.resolve().is_relative_to(Path(workdir).resolve()):
            return None
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry / relative, destination)
    return [part.replace('{work}', workdir) for part in metadata['command']]


def _store(root, entry, program, key):
    staging = Path(tempfile.mkdtemp(prefix='.build-', dir=root))
    try:
        files = {}
        size = 0
        for source in Path(program.workdir).rglob('*'):
            if source.is_symlink():
                return
            if not source.is_file():
                continue
            size += source.stat().st_size
            if size > 64 * 1024 * 1024 or len(files) >= 256:
                return
            relative = source.relative_to(program.workdir).as_posix()
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            files[relative] = _hash(target)
        metadata = {'key': key, 'files': files, 'command': [part.replace(program.workdir, '{work}') for part in program.command]}
        (staging / 'manifest.json').write_text(json.dumps(metadata))
        if entry.exists():
            shutil.rmtree(entry)
        staging.rename(entry)
        # 缓存是可丢弃派生数据；设置磁盘预算，始终保留当前已验证条目。
        limit = max(64, min(int(os.environ.get('JUDGE_CACHE_MAX_MB', 512)), 4096)) * 1024 * 1024
        entries = [path for path in root.iterdir() if path.is_dir() and not path.is_symlink() and len(path.name) == 64]
        sizes = {path: sum(file.stat().st_size for file in path.rglob('*') if file.is_file()) for path in entries}
        total = sum(sizes.values())
        for path in sorted(entries, key=lambda item: item.stat().st_mtime):
            if total <= limit:
                break
            if path != entry:
                shutil.rmtree(path, ignore_errors=True)
                total -= sizes[path]
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def prepare_cached(code, language, compile_timeout=20.):
    from controllers.contest_problem_controller import _prepare_program, PreparedProgram
    location = os.environ.get('JUDGE_COMPILE_CACHE')
    if not location or language not in {'cpp', 'java', 'go'}:
        return _prepare_program(code, language, compile_timeout)
    policy = Path(__file__).parent.parent / 'controllers' / 'contest_problem_controller.py'
    image = os.environ.get('JUDGE_SANDBOX_IMAGE', 'local-development')
    key = hashlib.sha256(json.dumps([code, language, image, _hash(policy), compile_timeout]).encode()).hexdigest()
    root = Path(location).resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise RuntimeError('编译缓存目录必须归 Worker 所有且权限为 0700')
    entry = root / key
    # 256 个固定锁桶，避免大量不同源码消耗无限 lock 文件/inode。
    with (root / (key[:2] + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        work_root = os.environ.get('JUDGE_WORK_ROOT')
        if work_root:
            Path(work_root).mkdir(parents=True, exist_ok=True)
        workdir = tempfile.mkdtemp(prefix='letcoding-cached-', dir=work_root)
        transferred = False
        try:
            try:
                command = _restore(entry, workdir, key)
            except (OSError, ValueError, KeyError, TypeError):
                command = None
            if command:
                program = PreparedProgram(command, workdir, language)
                program.cache_hit = True
                transferred = True
                return program, None, None
        finally:
            if not transferred:
                shutil.rmtree(workdir, ignore_errors=True)
        program, error, stderr = _prepare_program(code, language, compile_timeout)
        if program:
            program.cache_hit = False
            try:
                _store(root, entry, program, key)
            except (OSError, ValueError):
                pass  # 缓存故障不改变新编译的判定依据。
        return program, error, stderr
