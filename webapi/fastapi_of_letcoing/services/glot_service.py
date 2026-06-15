import aiohttp
import asyncio
import json
from typing import Dict, Optional

from core.di_container import Injectable
from interfaces.service_interfaces import ICodeExecutionService, IConfigService, ILoggerService
from models.glot_models import PostFile, PostDataModel, RunResult, CodeExecutionRequest, CodeExecutionResponse


class GlotService(ICodeExecutionService, Injectable):
    """Glot.io 代码运行服务。"""

    LANGUAGES: Dict[str, str] = {
        "assembly": "asm", "ats": "dats", "bash": "sh", "c": "c", "clojure": "clj",
        "cobol": "cob", "coffeescript": "coffee", "cpp": "cpp", "crystal": "cr",
        "csharp": "cs", "d": "d", "elixir": "ex", "elm": "elm", "erlang": "erl",
        "fsharp": "fs", "go": "go", "groovy": "groovy", "hare": "hare", "haskell": "hs",
        "idris": "idr", "java": "java", "javascript": "js", "julia": "jl", "kotlin": "kt",
        "lua": "lua", "mercury": "m", "nim": "nim", "nix": "nix", "ocaml": "ml",
        "perl": "pl", "php": "php", "python": "py", "raku": "raku", "ruby": "rb",
        "rust": "rs", "sac": "sac", "scala": "scala", "swift": "swift", "typescript": "ts",
        "zig": "zig",
    }

    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        self._config_service = config_service
        self._logger_service = logger_service
        self.timeout = aiohttp.ClientTimeout(total=config_service.get_timeout())

    async def execute_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
        try:
            self._logger_service.info(f"开始执行代码，语言: {request.language}")

            api_token = self._config_service.get_api_token()
            if not api_token:
                return CodeExecutionResponse(
                    stdout="",
                    stderr="API Token 未配置",
                    success=False,
                )

            result = await self._run_glot_async(api_token, request.code, request.language, request.stdin)

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

    async def _run_glot_async(
        self,
        api_token: str,
        code: str,
        language: str = "javascript",
        stdin: Optional[str] = None,
    ) -> Dict[str, str | bool]:
        if not code or code.strip() == "":
            return {"ok": False, "stdout": "", "stderr": "请输入代码"}

        if not language or language.strip() == "":
            language = "javascript"

        language_lower = language.lower()
        extension = self.LANGUAGES.get(language_lower)
        if not extension:
            return {"ok": False, "stdout": "", "stderr": "不支持的语言"}

        url = f"https://glot.io/api/run/{language_lower}/latest"
        post_file = PostFile(name=f"main.{extension}", content=code)
        data = PostDataModel(files=[post_file], stdin=stdin)
        headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=data.to_dict(), headers=headers) as response:
                    resp_text = await response.text()

                    if not response.ok:
                        return {
                            "ok": False,
                            "stdout": "",
                            "stderr": f"请求失败: HTTP {response.status}",
                        }

                    resp_json = json.loads(resp_text)
                    result = RunResult(
                        stdout=resp_json.get("stdout", ""),
                        stderr=resp_json.get("stderr", ""),
                    )

                    return {
                        "ok": result.stderr == "",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
        except asyncio.TimeoutError:
            return {"ok": False, "stdout": "", "stderr": "请求超时"}
        except aiohttp.ClientError as ex:
            return {"ok": False, "stdout": "", "stderr": f"请求失败: {str(ex)}"}
        except Exception as ex:
            return {"ok": False, "stdout": "", "stderr": f"请求失败: {str(ex)}"}
