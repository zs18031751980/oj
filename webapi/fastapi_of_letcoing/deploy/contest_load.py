"""专用预演比赛的 HTTPS 负载门禁；会产生正式提交，禁止指向正在举办的比赛。

账号文件为 [{"identifier": "...", "password": "..."}]，应为预先报名的独立验收队伍。
脚本不输出凭证，账号在各线程独立登录并在结束时登出。
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from time import monotonic, sleep
from urllib.parse import urlsplit
from uuid import uuid4

import requests


def percentile(values, fraction):
    return sorted(values)[min(len(values)-1, max(0, int(len(values)*fraction)-1))] if values else None


def run_account(account, args, code):
    session = requests.Session()
    session.headers.update({'Origin': args.frontend_origin, 'X-CSRF-Protection': '1'})
    measurements = []
    base = args.base_url.rstrip('/')
    def call(method, path, **kwargs):
        response = session.request(method, base+path, timeout=(3, 20), allow_redirects=False, **kwargs)
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f'{path}: HTTP {response.status_code}')
        return response
    try:
        token = call('POST', '/auth/login/password', json={**account, 'remember': False}).json()['tokens']['access_token']
        session.headers['Authorization'] = 'Bearer '+token
        path = f'/contests/{args.contest_id}/problems/{args.problem_id}/submit'
        for _ in range(args.submissions):
            payload = {'code': code, 'language': args.language}
            headers = {'Idempotency-Key': uuid4().hex}
            started = monotonic()
            accepted = call('POST', path, json=payload, headers=headers).json()
            accepted_ms = (monotonic()-started)*1000
            replay = call('POST', path, json=payload, headers=headers).json()
            if replay['submission_id'] != accepted['submission_id']:
                raise RuntimeError('幂等验收失败')
            result_path = f'/contests/{args.contest_id}/problems/{args.problem_id}/submission/{accepted["submission_id"]}'
            while monotonic()-started < args.judge_timeout:
                result = call('GET', result_path).json()
                if result['status'] not in {'Pending','Queued','Claimed','Compiling','Compiled','Running','Checking'}:
                    if result['status'] != args.expected:
                        raise RuntimeError(f'判定不符: {result["status"]}')
                    measurements.append({'accept_ms': accepted_ms, 'end_to_end_seconds': monotonic()-started})
                    break
                sleep(1)
            else:
                raise RuntimeError('判题超时')
            sleep(args.interval)
    finally:
        try:
            session.post(base+'/auth/logout', json={}, timeout=10, allow_redirects=False)
        finally:
            session.close()
    return measurements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--frontend-origin', required=True)
    parser.add_argument('--accounts-file', type=Path, required=True)
    parser.add_argument('--contest-id', type=int, required=True)
    parser.add_argument('--problem-id', type=int, required=True)
    parser.add_argument('--code-file', type=Path, required=True)
    parser.add_argument('--language', default='python')
    parser.add_argument('--expected', default='AC')
    parser.add_argument('--workers', type=int, default=20)
    parser.add_argument('--submissions', type=int, default=3)
    parser.add_argument('--interval', type=float, default=12)
    parser.add_argument('--judge-timeout', type=int, default=120)
    parser.add_argument('--accept-p95-ms', type=float, default=300)
    parser.add_argument('--output', type=Path, default=Path('contest-load-result.json'))
    args = parser.parse_args()
    for value in (args.base_url, args.frontend_origin):
        url = urlsplit(value)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            parser.error('验收地址必须为 HTTPS 且不包含凭证或查询参数')
    if not 1 <= args.workers <= 256 or not 1 <= args.submissions <= 100 or args.interval < 0:
        parser.error('无效负载参数')
    accounts = json.loads(args.accounts_file.read_text())
    code = args.code_file.read_text()
    results, failures = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(run_account, account, args, code) for account in accounts]
        for job in jobs:
            try:
                results.extend(job.result())
            except Exception as exc:
                failures.append(type(exc).__name__)  # 避免 HTTP 错误对象携带账号/请求详情
    p95 = percentile([row['accept_ms'] for row in results], .95)
    report = {'successful_submissions': len(results), 'failed_accounts': len(failures),
        'accept_p95_ms': p95, 'end_to_end_p95_seconds': percentile([row['end_to_end_seconds'] for row in results], .95),
        'passed': bool(results) and not failures and p95 <= args.accept_p95_ms}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
