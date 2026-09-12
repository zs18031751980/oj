"""只允许已验收的当前 main 提交快进生产分支，拒绝旧提交覆盖。"""
import subprocess

import pytest


def git(directory, *args):
    return subprocess.run(['git', '-C', str(directory), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def test_promotion_refuses_stale_commit_and_preserves_production(tmp_path):
    from deploy.promote_release import promote
    remote, repo = tmp_path/'remote.git', tmp_path/'checkout'
    subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    repo.mkdir()
    git(repo, 'init', '-b', 'main')
    git(repo, 'config', 'user.name', 'Acceptance Test')
    git(repo, 'config', 'user.email', 'test@example.invalid')
    git(repo, 'remote', 'add', 'origin', str(remote))
    (repo/'version').write_text('one')
    git(repo, 'add', 'version'); git(repo, 'commit', '-m', 'first')
    first = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'push', 'origin', 'main')
    promote(first, cwd=repo)
    assert git(remote, 'rev-parse', 'production') == first
    (repo/'version').write_text('two')
    git(repo, 'commit', '-am', 'second')
    second = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'push', 'origin', 'main')
    with pytest.raises(RuntimeError, match='main'):
        promote(first, cwd=repo)
    assert git(remote, 'rev-parse', 'production') == first
    promote(second, cwd=repo)
    assert git(remote, 'rev-parse', 'production') == second
