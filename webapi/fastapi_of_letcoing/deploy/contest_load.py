"""专用预演比赛的 HTTPS 负载门禁；会产生正式提交，禁止指向正在举办的比赛。

账号文件为 [{"identifier": "...", "password": "..."}]，应为预先报名的独立验收队伍。
脚本不输出凭证，账号在各线程独立登录并在结束时登出。
"""
import argparse
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
import math
import json
from pathlib import Path
from time import monotonic, sleep
from urllib.parse import urlsplit
from uuid import uuid4

import requests


def percentile(values, fraction):
    return sorted(values)[min(len(values)-1, max(0, math.ceil(len(values)*fraction)-1))] if values else None


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


def schedule_arrivals(operation: Callable[[int, float], dict], count: int,
                      rate: float, workers: int) -> list[dict]:
    """固定到达时刻；压测机饱和明确计失败，不使用无界任务队列。"""
    slots = BoundedSemaphore(workers)
    rows, jobs = [], []
    started = monotonic()
    def execute(index: int, scheduled: float, lag: float) -> dict:
        try:
            try:
                row = operation(index, scheduled)
            except Exception as exc:
                row = {'error': type(exc).__name__}
            return {**row, 'schedule_lag_ms': lag}
        finally:
            slots.release()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for index in range(count):
            scheduled = started + index/rate
            sleep(max(0, scheduled-monotonic()))
            lag = max(0, (monotonic()-scheduled)*1000)
            if not slots.acquire(blocking=False):
                rows.append({'error': 'generator_capacity', 'schedule_lag_ms': lag})
                continue
            jobs.append(pool.submit(execute, index, scheduled, lag))
        rows.extend(job.result() for job in jobs)
    return rows


def run_open_loop(accounts: list[dict], args: argparse.Namespace, code: str) -> list[dict]:
    base = args.base_url.rstrip('/')
    sessions, tokens = [], []
    try:
        # 登录不计入提交压力；Session 不跨线程共享。
        for account in accounts:
            session = requests.Session()
            sessions.append(session)
            session.headers.update({'Origin': args.frontend_origin, 'X-CSRF-Protection': '1'})
            response = session.post(base+'/auth/login/password', json={**account, 'remember': False},
                timeout=(3, 20), allow_redirects=False)
            if response.status_code != 200:
                raise RuntimeError('load account login failed')
            token = response.json()['tokens']['access_token']
            session.headers['Authorization'] = 'Bearer '+token
            tokens.append(token)
        def submit(index: int, scheduled: float) -> dict:
            row = {}
            with requests.Session() as session:
                session.headers.update({'Origin': args.frontend_origin, 'X-CSRF-Protection': '1',
                    'Authorization': 'Bearer '+tokens[index % len(tokens)]})
                path = f'/contests/{args.contest_id}/problems/{args.problem_id}/submit'
                started = monotonic()
                try:
                    response = session.post(base+path, json={'code': code, 'language': args.language},
                        headers={'Idempotency-Key': uuid4().hex}, timeout=(3,20), allow_redirects=False)
                    row.update(accept_ms=(monotonic()-started)*1000, http_status=response.status_code)
                    if response.status_code != 202:
                        return {**row, 'error': 'http_rejected'}
                    submission_id = response.json()['submission_id']
                    result_path = f'/contests/{args.contest_id}/problems/{args.problem_id}/submission/{submission_id}'
                    while monotonic()-started < args.judge_timeout:
                        response = session.get(base+result_path, timeout=(3,20), allow_redirects=False)
                        if response.status_code != 200:
                            return {**row, 'error': 'poll_http_error'}
                        status = response.json()['status']
                        if status not in {'Pending','Queued','Claimed','Compiling','Compiled','Running','Checking'}:
                            row.update(verdict=status, end_to_end_seconds=monotonic()-scheduled)
                            if status != args.expected:
                                row['error'] = 'unexpected_verdict'
                            return row
                        sleep(1)
                    return {**row, 'error': 'judge_timeout'}
                except Exception as exc:
                    return {**row, 'error': type(exc).__name__}
        return schedule_arrivals(submit, len(accounts)*args.submissions, args.arrival_rate, args.workers)
    finally:
        for session in sessions:
            try:
                session.post(base+'/auth/logout', json={}, timeout=10, allow_redirects=False)
            except requests.RequestException:
                pass
            finally:
                session.close()


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
    parser.add_argument('--mode', choices=['closed', 'open'], default='closed')
    parser.add_argument('--arrival-rate', type=float, default=1, help='open 模式每秒提交数，不包含轮询')
    parser.add_argument('--max-schedule-lag-ms', type=float, default=100)
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
    if not math.isfinite(args.arrival_rate) or args.arrival_rate <= 0 or args.judge_timeout <= 0 or not math.isfinite(args.max_schedule_lag_ms) or args.max_schedule_lag_ms < 0:
        parser.error('到达率、超时和调度延迟必须有效')
    accounts = json.loads(args.accounts_file.read_text())
    if not isinstance(accounts, list) or not accounts or any(not isinstance(a, dict) or not a.get('identifier') or not a.get('password') for a in accounts):
        parser.error('账号文件必须为非空的 identifier/password 列表')
    code = args.code_file.read_text()
    results, failures = [], []
    if args.mode == 'open':
        try:
            results = run_open_loop(accounts, args, code)
        except Exception as exc:
            failures.append(type(exc).__name__)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            jobs = [pool.submit(run_account, account, args, code) for account in accounts]
            for job in jobs:
                try:
                    results.extend(job.result())
                except Exception as exc:
                    failures.append(type(exc).__name__)
    accepted = [row['accept_ms'] for row in results if 'accept_ms' in row]
    p95 = percentile(accepted, .95)
    errors, statuses = {}, {}
    for row in results:
        if row.get('error'):
            errors[row['error']] = errors.get(row['error'], 0)+1
        if 'http_status' in row:
            key = str(row['http_status'])
            statuses[key] = statuses.get(key, 0)+1
    lag = max((row.get('schedule_lag_ms', 0) for row in results), default=0)
    report = {'mode': args.mode, 'arrival_rate': args.arrival_rate if args.mode == 'open' else None,
        'scheduled_submissions': len(accounts)*args.submissions,
        'successful_submissions': sum(not row.get('error') for row in results), 'failed_accounts': len(failures),
        'errors': errors, 'http_statuses': statuses, 'max_schedule_lag_ms': lag,
        'accept_p95_ms': p95, 'end_to_end_p95_seconds': percentile([row['end_to_end_seconds'] for row in results if 'end_to_end_seconds' in row], .95),
        'passed': bool(results) and not failures and not errors and p95 is not None
            and p95 <= args.accept_p95_ms and lag <= args.max_schedule_lag_ms}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
