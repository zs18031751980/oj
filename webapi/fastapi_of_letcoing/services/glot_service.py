"""
Glot.io 代码执行服务模块

通过 Glot.io 公共 API 实现远程代码执行功能。
支持 40+ 种编程语言的代码运行，包括：
JavaScript, Python, Java, C++, Go, Rust, TypeScript 等。

Glot.io 是一个开源的代码运行平台，提供沙箱化的代码执行环境。
使用方式：通过 HTTP API 提交代码文件，获取执行结果。
"""

import aiohttp        # 异步 HTTP 客户端库
import asyncio        # 异步 I/O 支持
import json           # JSON 数据处理
from typing import Dict, Optional

from core.di_container import Injectable
from interfaces.service_interfaces import ICodeExecutionService, IConfigService, ILoggerService
from models.glot_models import PostFile, PostDataModel, RunResult, CodeExecutionRequest, CodeExecutionResponse


class GlotService(ICodeExecutionService, Injectable):
    """
    Glot.io 远程代码执行服务

    通过 Glot.io 的公共 API 执行代码，支持多种编程语言。
    使用 API Token 进行身份认证，通过 aiohttp 异步 HTTP 客户端发送请求。
    """

    # 编程语言名称到文件扩展名的映射字典
    # 键：语言名称（小写），值：文件扩展名
    # Glot.io API 要求使用文件扩展名来标识代码类型
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
        """
        初始化 Glot.io 服务

        Args:
            config_service: 配置服务，用于获取 API Token 和超时时间
            logger_service: 日志服务，用于记录执行日志
        """
        self._config_service = config_service
        self._logger_service = logger_service
        self._timeout = aiohttp.ClientTimeout(total=config_service.get_timeout())
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_loop_id: Optional[int] = None

    def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建复用的 aiohttp 会话，避免每次请求重建 TCP 连接"""
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
        """关闭 aiohttp 会话，释放连接资源"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def execute_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
        """
        执行代码（对外公开的接口方法）

        流程：
        1. 记录执行日志
        2. 检查 API Token 是否已配置
        3. 调用 Glot.io API 执行代码
        4. 返回标准化的执行结果

        Args:
            request: 代码执行请求（包含源代码、语言和标准输入）

        Returns:
            代码执行响应（包含标准输出、错误输出和执行状态）
        """
        try:
            self._logger_service.info(f"开始执行代码，语言: {request.language}")

            # 检查 API Token 是否已配置
            api_token = self._config_service.get_api_token()
            if not api_token:
                return CodeExecutionResponse(
                    stdout="",
                    stderr="API Token 未配置",
                    success=False,
                )

            # 异步调用 Glot.io API
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
        """
        异步调用 Glot.io API 执行代码（内部实现）

        构建符合 Glot.io API 格式的请求，发送 HTTP POST 请求，
        解析返回的 JSON 响应并提取标准输出和错误输出。

        Args:
            api_token: Glot.io API Token
            code: 要执行的源代码
            language: 编程语言名称
            stdin: 程序的标准输入

        Returns:
            包含 ok（是否成功）、stdout（标准输出）、stderr（错误输出）的字典
        """
        # 验证请求参数
        if not code or code.strip() == "":
            return {"ok": False, "stdout": "", "stderr": "请输入代码"}
        if not language or language.strip() == "":
            language = "javascript"

        # 将语言名称映射为文件扩展名
        language_lower = language.lower()
        extension = self.LANGUAGES.get(language_lower)
        if not extension:
            return {"ok": False, "stdout": "", "stderr": "不支持的语言"}

        # 构建 Glot.io API 请求
        url = f"https://glot.io/api/run/{language_lower}/latest"
        post_file = PostFile(name=f"main.{extension}", content=code)
        data = PostDataModel(files=[post_file], stdin=stdin)
        headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json",
        }

        try:
            async with self._get_session().post(url, json=data.to_dict(), headers=headers) as response:
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

                # Glot.io 约定：stderr 为空表示执行成功
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
