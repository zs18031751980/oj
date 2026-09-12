"""低基数 HTTP 指标；队列与 Worker 信息由隔离的内部端点导出。"""
import os
import secrets

from flask import Response, g, request
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest


def register_metrics(app):
    registry = CollectorRegistry()
    requests = Counter('letcoding_http_requests_total', 'HTTP requests', ['method', 'route', 'status'], registry=registry)
    latency = Histogram('letcoding_http_duration_seconds', 'HTTP latency', ['route'], registry=registry,
                        buckets=(.01, .05, .1, .25, .5, 1, 2, 5, 15, 30))

    lock_wait = Histogram('letcoding_contest_lock_wait_seconds', 'Contest row lock acquisition duration',
        registry=registry, buckets=(.001, .005, .01, .05, .1, .5, 1, 2, 5, 15))

    transaction_time = Histogram('letcoding_contest_transaction_seconds', 'Contest transaction duration',
        registry=registry, buckets=(.001, .005, .01, .05, .1, .5, 1, 2, 5, 15))

    @app.after_request
    def count(response):
        import time
        route = str(request.url_rule or 'unmatched')
        requests.labels(request.method, route, str(response.status_code)).inc()
        latency.labels(route).observe(time.monotonic() - getattr(g, 'request_started', time.monotonic()))
        if hasattr(g, 'contest_lock_wait'):
            lock_wait.observe(g.contest_lock_wait)
        if hasattr(g, 'contest_transaction_seconds'):
            transaction_time.observe(g.contest_transaction_seconds)
        return response

    @app.get('/metrics')
    def metrics():
        token = app.config.get('METRICS_TOKEN') or os.environ.get('METRICS_TOKEN', '')
        if not token or not secrets.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + token):
            return {'error': 'Unauthorized'}, 401
        if os.environ.get('PROMETHEUS_MULTIPROC_DIR'):
            from prometheus_client import multiprocess
            combined = CollectorRegistry()
            multiprocess.MultiProcessCollector(combined)
            body = generate_latest(combined)
        else:
            body = generate_latest(registry)
        from core.di_container import inject
        from interfaces.service_interfaces import IRedisService
        cache = inject(IRedisService)
        try:
            if not cache.is_connected():
                raise ConnectionError('Redis unavailable')
            for queue in ('judge_queue', 'contest_judge_queue', 'practice_judge_queue', 'rejudge_queue', 'testcase_gen_queue'):
                for state, suffix in (('pending', ''), ('processing', ':processing'), ('dead', ':dead')):
                    value = cache._client.llen(queue + suffix)
                    body += f'letcoding_queue_length{{queue="{queue}",state="{state}"}} {value}\n'.encode()
                value = cache._client.zcard(queue + ':retry')
                body += f'letcoding_queue_length{{queue="{queue}",state="retry"}} {value}\n'.encode()
            from services.contest_metrics import POOLS, judge_histogram_text
            body += judge_histogram_text(cache)
            workers = [cache.get(key) or {} for key in cache._client.scan_iter('judge:worker:*', count=100)]
            from services.health import worker_is_fresh, worker_accepts
            workers = [w for w in workers if worker_is_fresh(w)]
            alive = len(workers)
            for pool in POOLS:
                available = [w for w in workers if w.get('alive') and w.get('pool', 'all') == pool]
                body += f'letcoding_worker_slots{{pool="{pool}",state="alive"}} {len(available)}\n'.encode()
                body += f'letcoding_worker_slots{{pool="{pool}",state="idle"}} {sum(not w.get("active_job") and worker_accepts(w, pool) for w in available)}\n'.encode()
                body += f'letcoding_worker_slots{{pool="{pool}",state="accepting"}} {sum(worker_accepts(w, pool) for w in available)}\n'.encode()
                body += f'letcoding_worker_slots{{pool="{pool}",state="draining"}} {sum(bool(w.get("draining")) for w in available)}\n'.encode()
                body += f'letcoding_projection_consecutive_failures{{pool="{pool}"}} {max((w.get("projection_consecutive_failures", 0) for w in available), default=0)}\n'.encode()
            audit = [w for w in workers if w.get('alive') and w.get('audit_enabled')]
            body += f'letcoding_audit_exporters {len(audit)}\n'.encode()
            body += f'letcoding_audit_last_success_unix {max((w.get("audit_last_success_unix", 0) for w in audit), default=0)}\n'.encode()
            body += f'letcoding_audit_consecutive_failures {max((w.get("audit_consecutive_failures", 0) for w in audit), default=0)}\n'.encode()
            body += f'letcoding_workers_alive {alive}\nletcoding_dependency_up{{dependency="redis"}} 1\n'.encode()
        except Exception:
            body += b'letcoding_dependency_up{dependency="redis"} 0\n'
        try:
            from datetime import datetime
            from models.db_models import SubmissionOutbox, ContestJudgeOutbox, ReferenceValidationJob
            from peewee import fn
            for model, queue in ((SubmissionOutbox, 'judge_queue'), (ContestJudgeOutbox, 'contest_judge_queue'),
                                 (ReferenceValidationJob, 'testcase_gen_queue')):
                count, oldest = model.select(fn.COUNT(model.id), fn.MIN(model.created_at)).where(model.state == 'PENDING').tuples().get()
                age = max(0, (datetime.now() - oldest).total_seconds()) if oldest else 0
                body += f'letcoding_outbox_pending{{queue="{queue}"}} {count}\nletcoding_outbox_oldest_seconds{{queue="{queue}"}} {age}\n'.encode()
            from services.contest_metrics import competition_health
            health = competition_health()
            for name in ('waiting', 'oldest_wait_seconds', 'projection_version_lag', 'projection_stale_seconds', 'unresolved_system_errors'):
                body += f'letcoding_contest_{name} {health[name]}\n'.encode()
            for stage, values in health['stages'].items():
                body += f'letcoding_contest_stage_samples{{stage="{stage}"}} {values["samples"]}\n'.encode()
                if values['p95_seconds'] is not None:
                    body += f'letcoding_contest_stage_p95_seconds{{stage="{stage}"}} {values["p95_seconds"]}\n'.encode()
            body += b'letcoding_dependency_up{dependency="postgres"} 1\n'
        except Exception:
            body += b'letcoding_dependency_up{dependency="postgres"} 0\n'
        body += backup_metrics_text()
        return Response(body, content_type='text/plain; version=0.0.4; charset=utf-8')


def backup_metrics_text() -> bytes:
    """可选挂载 manifest；没有状态不能被解释成备份年龄为零。"""
    import json
    import time
    import math
    from pathlib import Path
    path = os.environ.get('BACKUP_MANIFEST_FILE')
    if not path:
        return b'letcoding_backup_monitor_enabled 0\n'
    body = b'letcoding_backup_monitor_enabled 1\n'
    try:
        with Path(path).open() as stream:
            value = json.loads(stream.read(4*1024*1024))
        if not isinstance(value, dict):
            raise ValueError('backup manifest must be an object')
        timestamp = value['snapshot_at_unix'] if 'snapshot_at_unix' in value else value['created_at_unix']
        if type(timestamp) not in (int, float):
            raise ValueError('backup timestamp must be numeric')
        created = float(timestamp)
        if not math.isfinite(created) or created <= 0 or created > time.time()+60:
            raise ValueError('invalid backup timestamp')
        return body + f'letcoding_backup_status_up 1\nletcoding_backup_age_seconds {max(0, time.time()-created)}\n'.encode()
    except (OSError, ValueError, TypeError, KeyError):
        return body + b'letcoding_backup_status_up 0\n'
