"""部署门禁：对专用验收账号执行真实登录、刷新、持久化提交与判题。

SMOKE_IDENTIFIER / SMOKE_PASSWORD 仅从环境读取；禁止在命令行或日志打印令牌。
需显式指定已知会通过的赛后题目与代码文件；会新增一条该账号的练习提交。
"""
import argparse
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
from uuid import uuid4

import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--frontend-url', required=True)
    parser.add_argument('--problem-id', type=int, required=True)
    parser.add_argument('--code-file', type=Path, required=True)
    parser.add_argument('--language', default='python')
    args = parser.parse_args()
    for value in (args.base_url, args.frontend_url):
        url = urlsplit(value)
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            parser.error('部署验收仅允许 HTTPS 地址')
    base = args.base_url.rstrip('/')
    front = urlsplit(args.frontend_url)
    session = requests.Session()
    session.headers.update({'Origin': f'{front.scheme}://{front.netloc}', 'X-CSRF-Protection': '1'})
    def call(path, method='GET', **kwargs):
        response = session.request(method, base + path, timeout=(3, 20), allow_redirects=False, **kwargs)
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f'{method} {path}: HTTP {response.status_code}')
        return response
    try:
        for path in ('/healthz', '/readyz', '/problems?page=1&page_size=1', '/contests/?page=1&page_size=1',
                     '/healthz/judge?pool=practice'):
            call(path)
        response = call('/auth/login/password', 'POST', json={
            'identifier': os.environ['SMOKE_IDENTIFIER'], 'password': os.environ['SMOKE_PASSWORD'], 'remember': False})
        tokens = response.json()['tokens']
        assert 'refresh_token' not in tokens
        cookie = response.headers.get('Set-Cookie', '')
        assert 'HttpOnly' in cookie and 'Secure' in cookie
        refreshed = call('/auth/refresh', 'POST', json={'remember': False}, headers={'Idempotency-Key': uuid4().hex}).json()
        session.headers['Authorization'] = 'Bearer ' + refreshed['access_token']
        call('/auth/verify')
        body = {'contest_problem_id': args.problem_id, 'code': args.code_file.read_text(), 'language': args.language}
        headers = {'Idempotency-Key': uuid4().hex}
        first = call('/problems/library/submit', 'POST', json=body, headers=headers).json()
        replay = call('/problems/library/submit', 'POST', json=body, headers=headers).json()
        assert first['submission_id'] == replay['submission_id']
        pending = {'Pending', 'Queued', 'Claimed', 'Compiling', 'Compiled', 'Running', 'Checking'}
        for _ in range(120):
            result = call(f"/problems/library/submission/{first['submission_id']}").json()
            if result['status'] not in pending:
                assert result['status'] == 'AC', f"验收代码未通过：{result['status']}"
                assert all(not case.get(key) for case in result['testcase_results'] for key in ('input', 'expected', 'stdout'))
                print('部署验收通过：登录、Cookie 刷新、幂等提交、实际判题、隐藏用例隔离')
                break
            time.sleep(1)
        else:
            raise RuntimeError('判题在 120 秒内未完成')
    finally:
        try:
            call('/auth/logout', 'POST', json={})
        finally:
            session.close()


if __name__ == '__main__':
    main()
