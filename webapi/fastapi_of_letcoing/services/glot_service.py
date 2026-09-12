"""
代码执行服务模块（Judge0 CE 免费公共实例）

通过 Judge0 CE (ce.judge0.com) 公共 API 实现远程代码执行功能。
完全免费，无需 API Key，支持 60+ 种编程语言。
"""

import aiohttp
import asyncio
import base64
import json
from typing import Dict, Optional

from core.di_container import Injectable
from interfaces.service_interfaces import ICodeExecutionService, IConfigService, ILoggerService
from models.glot_models import RunResult, CodeExecutionRequest, CodeExecutionResponse


# Judge0 语言 ID 映射（常用语言）
JUDGE0_LANGUAGES: Dict[str, int] = {
    "bash": 46,
    "c": 50,
    "c++": 54,
    "cpp": 54,
    "csharp": 51,
    "go": 60,
    "java": 62,
    "javascript": 63,
    "kotlin": 78,
    "perl": 85,
    "php": 68,
    "python": 71,
    "python3": 71,
    "r": 80,
    "ruby": 72,
    "rust": 73,
    "scala": 81,
    "swift": 82,
    "typescript": 74,
    "typescript-node": 75,
}

# Judge0 CE 公共实例地址（无需 API Key）
JUDGE0_BASE_URL = "https://ce.judge0.com"


class GlotService(ICodeExecutionService, Injectable):
    """Judge0 客户端；连接池由独立的长期事件循环独占。"""
    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        import threading
        self._config_service = config_service
        self._logger_service = logger_service
        self._base_url = config_service.get_config('JUDGE0_BASE_URL', JUDGE0_BASE_URL).rstrip('/')
        self._timeout = aiohttp.ClientTimeout(total=config_service.get_timeout(), connect=5, sock_read=25)
        self._session = None
        self._loop = None
        self._thread = None
        self._lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(10)
        self._failures = 0
        self._open_until = 0.0
        import atexit
        atexit.register(self.close_sync)

    def _owner_loop(self):
        import threading
        with self._lock:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
                self._thread.start()
        return self._loop

    async def _get_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=self._timeout,
                connector=aiohttp.TCPConnector(limit=10, ttl_dns_cache=300))
        return self._session

    async def close(self):
        await asyncio.to_thread(self.close_sync)

    def close_sync(self):
        with self._lock:
            if self._loop is None:
                return
            if self._session is not None:
                asyncio.run_coroutine_threadsafe(self._session.close(), self._loop).result(timeout=5)
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)
            self._loop.close()
            self._loop = self._session = self._thread = None

    async def execute_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
        if not self._slots.acquire(blocking=False):
            return CodeExecutionResponse('', '执行服务繁忙', False, http_status=429, verdict='SystemError')
        future = asyncio.run_coroutine_threadsafe(self._execute(request), self._owner_loop())
        try:
            return await asyncio.wrap_future(future)
        finally:
            self._slots.release()

    async def _execute(self, request):
        import time
        if time.monotonic() < self._open_until:
            return CodeExecutionResponse('', '执行服务暂时不可用', False, http_status=503, verdict='SystemError')
        language_id = JUDGE0_LANGUAGES.get(request.language.lower().strip())
        if not language_id:
            return CodeExecutionResponse('', '不支持的语言', False, http_status=400, verdict='CE')
        payload = {'source_code': base64.b64encode(request.code.encode()).decode(),
                   'language_id': language_id, 'cpu_time_limit': 2, 'wall_time_limit': 5,
                   'memory_limit': 262144, 'max_file_size': 1024,
                   'enable_network': False}
        if request.stdin:
            payload['stdin'] = base64.b64encode(request.stdin.encode()).decode()
        try:
            session = await self._get_session()
            async with session.post(f'{self._base_url}/submissions', json=payload,
                params={'base64_encoded': 'true', 'wait': 'true',
                        'fields': 'stdout,stderr,status,compile_output,time,memory'},
                allow_redirects=False) as response:
                if response.status != 200 and response.status != 201:
                    self._record_failure()
                    code = 429 if response.status == 429 else 502
                    return CodeExecutionResponse('', '上游限流' if code == 429 else '执行服务异常',
                                                 False, http_status=code, verdict='SystemError')
                chunks, size = [], 0
                async for chunk in response.content.iter_chunked(65536):
                    size += len(chunk)
                    if size > 2 * 1024 * 1024:
                        return CodeExecutionResponse('', '执行输出超限', False, http_status=422, verdict='OLE')
                    chunks.append(chunk)
                data = json.loads(b''.join(chunks))
                self._failures = 0
                def decode(value):
                    return base64.b64decode(value or '', validate=True).decode('utf-8', errors='replace')
                status = data.get('status', {}).get('id')
                verdict = {3: 'AC', 4: 'WA', 5: 'TLE', 6: 'CE', 7: 'RE', 8: 'RE',
                           9: 'RE', 10: 'RE', 11: 'RE', 12: 'SystemError', 13: 'SystemError'}.get(status, 'SystemError')
                return CodeExecutionResponse(decode(data.get('stdout')),
                    decode(data.get('compile_output') or data.get('stderr')), status == 3,
                    http_status=200 if status == 3 else 503 if verdict == 'SystemError' else 422,
                    verdict=verdict, time_used=int(float(data.get('time') or 0) * 1000),
                    memory_used=int(data.get('memory') or 0))
        except asyncio.TimeoutError:
            self._record_failure()
            return CodeExecutionResponse('', '执行服务超时', False, http_status=504, verdict='SystemError')
        except (aiohttp.ClientError, ValueError, TypeError):
            self._record_failure()
            return CodeExecutionResponse('', '执行服务响应异常', False, http_status=502, verdict='SystemError')

    def _record_failure(self):
        import time
        self._failures += 1
        if self._failures >= 5:
            self._open_until = time.monotonic() + 10
