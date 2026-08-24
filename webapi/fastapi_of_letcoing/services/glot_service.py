"""
代码执行服务模块（Judge0 CE 免费公共实例）

通过 Judge0 CE (ce.judge0.com) 公共 API 实现远程代码执行功能。
完全免费，无需 API Key，支持 60+ 种编程语言。
"""

import aiohttp
import asyncio
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
    """
    Judge0 CE 免费代码执行服务

    通过 ce.judge0.com 公共实例执行代码，完全免费，无需注册。
    """

    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        self._config_service = config_service
        self._logger_service = logger_service
        self._timeout = aiohttp.ClientTimeout(total=config_service.get_timeout())
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_loop_id: Optional[int] = None

    def _get_session(self) -> aiohttp.ClientSession:
        try:
            current_loop = asyncio.get_running_loop()
            current_loop_id = id(current_loop)
        except RuntimeError:
            current_loop_id = None

        if (self._session is None or self._session.closed or
                (current_loop_id is not None and self._session_loop_id != current_loop_id)):
            connector = aiohttp.TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
            )
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                connector=connector,
            )
            self._session_loop_id = current_loop_id
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def execute_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
        try:
            self._logger_service.info(f"开始执行代码，语言: {request.language}")

            result = await self._run_judge0_async(request.code, request.language, request.stdin)

            if result["ok"]:
                return CodeExecutionResponse(
                    stdout=str(result["stdout"]),
                    stderr=str(result["stderr"]),
                    success=True,
                )

            return CodeExecutionResponse(
                stdout=str(result["stdout"]),
                stderr=str(result["stderr"]),
                success=False,
            )
        except Exception as ex:
            self._logger_service.error("代码执行过程中发生异常", ex)
            return CodeExecutionResponse(
                stdout="",
                stderr=f"执行异常: {str(ex)}",
                success=False,
            )

    async def _run_judge0_async(
        self,
        code: str,
        language: str = "python",
        stdin: Optional[str] = None,
    ) -> Dict[str, str | bool]:
        """
        异步调用 Judge0 CE 公共 API 执行代码

        使用 ?wait=true 参数实现同步执行（提交后等待结果返回）。
        """
        if not code or code.strip() == "":
            return {"ok": False, "stdout": "", "stderr": "请输入代码"}

        language_lower = language.lower().strip()
        language_id = JUDGE0_LANGUAGES.get(language_lower)
        if not language_id:
            supported = ", ".join(sorted(JUDGE0_LANGUAGES.keys()))
            return {"ok": False, "stdout": "", "stderr": f"不支持的语言: {language}。支持: {supported}"}

        url = f"{JUDGE0_BASE_URL}/submissions"
        params = {
            "base64_encoded": "false",
            "wait": "true",
            "fields": "stdout,stderr,status,compile_output",
        }
        payload = {
            "source_code": code,
            "language_id": language_id,
        }
        if stdin:
            payload["stdin"] = stdin

        try:
            async with self._get_session().post(url, json=payload, params=params) as response:
                resp_text = await response.text()

                if response.status == 429:
                    return {"ok": False, "stdout": "", "stderr": "请求过于频繁，请稍后再试"}

                if not response.ok:
                    return {
                        "ok": False,
                        "stdout": "",
                        "stderr": f"请求失败: HTTP {response.status} - {resp_text[:200]}",
                    }

                resp_json = json.loads(resp_text)

                stdout = resp_json.get("stdout", "") or ""
                stderr = resp_json.get("stderr", "") or ""
                compile_output = resp_json.get("compile_output", "") or ""
                status = resp_json.get("status", {})

                if compile_output:
                    stderr = compile_output

                # status.id: 1=in queue, 2=processing, 3=accepted, 4=wrong answer,
                # 5=time limit, 6=runtime error, 7=compilation error, etc.
                is_success = status.get("id") in (3, None)
                if not is_success and not stderr:
                    stderr = f"执行状态: {status.get('description', '未知')}"

                return {
                    "ok": is_success and not stderr,
                    "stdout": stdout,
                    "stderr": stderr,
                }
        except asyncio.TimeoutError:
            return {"ok": False, "stdout": "", "stderr": "请求超时（超过30秒限制）"}
        except aiohttp.ClientError as ex:
            return {"ok": False, "stdout": "", "stderr": f"请求失败: {str(ex)}"}
        except Exception as ex:
            return {"ok": False, "stdout": "", "stderr": f"请求失败: {str(ex)}"}
