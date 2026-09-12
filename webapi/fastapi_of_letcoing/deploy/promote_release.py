"""由验收成功的 CI 调用：仅把精确提交快进到 production 分支。"""
import argparse
import re
import subprocess


def promote(sha, cwd=None):
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('invalid commit SHA')
    result = subprocess.run(['git', 'ls-remote', '--exit-code', 'origin', 'refs/heads/main'],
                            cwd=cwd, check=True, capture_output=True, text=True, timeout=30)
    if result.stdout.split()[0] != sha:
        raise RuntimeError('main advanced; stale acceptance must not promote production')
    # Git 的快进检查同时拒绝并发发布倒退；不使用 force，不修改 main。
    subprocess.run(['git', 'push', 'origin', f'{sha}:refs/heads/production'],
                   cwd=cwd, check=True, timeout=60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sha', required=True)
    promote(parser.parse_args().sha)
