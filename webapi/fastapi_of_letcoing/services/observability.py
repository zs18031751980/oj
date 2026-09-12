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

    @app.after_request
    def count(response):
        import time
        route = str(request.url_rule or 'unmatched')
        requests.labels(request.method, route, str(response.status_code)).inc()
        latency.labels(route).observe(time.monotonic() - getattr(g, 'request_started', time.monotonic()))
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
            alive = sum(bool((cache.get(key) or {}).get('alive')) for key in cache._client.scan_iter('judge:worker:*', count=100))
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
            for name in ('waiting', 'oldest_wait_seconds', 'projection_version_lag', 'unresolved_system_errors'):
                body += f'letcoding_contest_{name} {health[name]}\n'.encode()
            for stage, values in health['stages'].items():
                body += f'letcoding_contest_stage_samples{{stage="{stage}"}} {values["samples"]}\n'.encode()
                if values['p95_seconds'] is not None:
                    body += f'letcoding_contest_stage_p95_seconds{{stage="{stage}"}} {values["p95_seconds"]}\n'.encode()
            body += b'letcoding_dependency_up{dependency="postgres"} 1\n'
        except Exception:
            body += b'letcoding_dependency_up{dependency="postgres"} 0\n'
        return Response(body, content_type='text/plain; version=0.0.4; charset=utf-8')
