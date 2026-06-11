import aiohttp
import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import json
from interfaces.service_interfaces import ICodeExecutionService, IConfigService, ILoggerService
from models.glot_models import PostFile, PostDataModel, RunResult, CodeExecutionRequest, CodeExecutionResponse
from core.di_container import Injectable



class GlotService(ICodeExecutionService, Injectable):
    """Glot.io 代码运行服务（异步版本）"""
    
    # 语言映射字典
    LANGUAGES: Dict[str, str] = {
        "assembly": "asm", "ats": "dats", "bash": "sh", "c": "c", "clojure": "clj",
        "cobol": "cob", "coffeescript": "coffee", "cpp": "cpp", "crystal": "cr",
        "csharp": "cs", "d": "d", "elixir": "ex", "elm": "elm", "erlang": "erl",
        "fsharp": "fs", "go": "go", "groovy": "groovy", "hare": "hare", "haskell": "hs",
        "idris": "idr", "java": "java", "javascript": "js", "julia": "jl", "kotlin": "kt",
        "lua": "lua", "mercury": "m", "nim": "nim", "nix": "nix", "ocaml": "ml",
        "perl": "pl", "php": "php", "python": "py", "raku": "raku", "ruby": "rb",
        "rust": "rs", "sac": "sac", "scala": "scala", "swift": "swift", "typescript": "ts",
        "zig": "zig"
    }
    
    def __init__(self, config_service: IConfigService, logger_service: ILoggerService):
        """
        初始化服务
        
        Args:
            config_service: 配置服务
            logger_service: 日志服务
        """
        self._config_service = config_service
        self._logger_service = logger_service
        self.timeout = aiohttp.ClientTimeout(total=config_service.get_timeout())
    
    async def execute_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
        """
        执行代码（实现接口方法）
        
        Args:
            request: 代码执行请求
            
        Returns:
            代码执行响应
        """
        try:
            self._logger_service.info(f"开始执行代码，语言: {request.language}")
            
            # 获取API Token
            api_token = self._config_service.get_api_token()
            if not api_token:
                return CodeExecutionResponse(
                    stdout="",
                    stderr="API Token未配置",
                    success=False
                )
            
            # 调用原有方法
            result = await self._run_glot_async(api_token, request.code, request.language, request.stdin)
            
            # 检查结果
            if (result.startswith("请求出错:") or 
                result.startswith("运行出错:") or 
                result in ["请输入代码", "不支持的语言", "请求超时"]):
                return CodeExecutionResponse(
                    stdout="",
                    stderr=result,
                    success=False
                )
            
            return CodeExecutionResponse(
                stdout=result,
                stderr="",
                success=True
            )
            
        except Exception as ex:
            self._logger_service.error("代码执行过程中发生异常", ex)
            return CodeExecutionResponse(
                stdout="",
                stderr=f"执行异常: {str(ex)}",
                success=False
            )
    
    async def _run_glot_async(self, api_token: str, code: str, 
                            language: str = "javascript", 
                            stdin: Optional[str] = None) -> str:
        """
        使用 glot.io 运行在线代码（异步）
        
        Args:
            api_token: API Token
            code: 要运行的代码
            language: 语言（如 "javascript"，默认为 "javascript"）
            stdin: 标准输入（可选）
            
        Returns:
            结果字符串
        """
        # 验证代码
        if not code or code.strip() == "":
            return "请输入代码"
        
        # 设置默认语言
        if not language or language.strip() == "":
            language = "javascript"
        
        # 查找对应后缀（不区分大小写）
        language_lower = language.lower()
        extension = self.LANGUAGES.get(language_lower)
        
        if not extension:
            return "不支持的语言"
        
        # 构建 URL
        url = f"https://glot.io/api/run/{language_lower}/latest"
        
        # 构建 POST 数据
        post_file = PostFile(
            name=f"main.{extension}",
            content=code
        )
        
        data = PostDataModel(
            files=[post_file],
            stdin=stdin
        )
        
        # 设置请求头
        headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # 发送异步 POST 请求
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=data.to_dict(), headers=headers) as response:
                    resp_text = await response.text()
                    
                    # 检查响应状态
                    if not response.ok:
                        return f"请求出错: HTTP {response.status}"
                    
                    # 解析响应
                    resp_json = json.loads(resp_text)
                    
                    result = RunResult(
                        stdout=resp_json.get("stdout", ""),
                        stderr=resp_json.get("stderr", "")
                    )
                    
                    # 兼容接口结构
                    if result.stderr:
                        return f"运行出错: {self._escape(result.stderr)}\n{self._escape(result.stderr)}"
                    else:
                        return self._escape(result.stdout + result.stderr)
                    
        except asyncio.TimeoutError:
            return "请求超时"
        except aiohttp.ClientError as ex:
            return f"请求出错: {str(ex)}"
        except Exception as ex:
            return f"请求出错: {str(ex)}"
    
    @staticmethod
    def _escape(text: str) -> str:
        """
        转义输出，防注入（简单实现）
        
        Args:
            text: 要转义的文本
            
        Returns:
            转义后的文本
        """
        if not text:
            return ""
        
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))