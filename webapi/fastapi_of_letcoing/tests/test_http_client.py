import asyncio
import base64
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from models.glot_models import CodeExecutionRequest
from services.config_service import ConfigService
from services.glot_service import GlotService


def test_client_reuses_owner_loop_across_request_loops():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            payload = json.dumps({'stdout': base64.b64encode(b'42').decode(),
                                  'stderr': '', 'status': {'id': 3}, 'time': '0.01'}).encode()
            self.send_response(200)
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    service = GlotService(ConfigService({'JUDGE0_BASE_URL': f'http://127.0.0.1:{server.server_port}'}), logging.getLogger('test'))
    # 首先要求支持配置的隔离上游，避免测试误访问公共代码执行服务。
    try:
        assert getattr(service, '_base_url', None) == f'http://127.0.0.1:{server.server_port}'
        first = asyncio.run(service.execute_code(CodeExecutionRequest('print(42)', 'python')))
        session = service._session
        second = asyncio.run(service.execute_code(CodeExecutionRequest('print(42)', 'python')))
        assert first.stdout == second.stdout == '42'
        assert service._session is session
        asyncio.run(service.close())
        assert session.closed
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
