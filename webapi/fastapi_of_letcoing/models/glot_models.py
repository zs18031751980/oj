"""
代码执行相关数据模型模块

定义了与远程代码执行（通过 Glot.io API）相关的所有数据结构：
- PostFile / PostDataModel: 发送到 Glot.io 的文件和数据格式
- RunResult: Glot.io 返回的运行结果
- CodeExecutionRequest: API 层的代码执行请求
- CodeExecutionResponse: API 层的代码执行响应
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


# ============================================================
# 1. Glot.io API 通信模型（与外部服务交互）
# ============================================================

@dataclass
class PostFile:
    """
    文件数据模型

    表示发送到 Glot.io 执行的一个文件。
    Glot.io API 要求以文件为单位提交代码，每个文件有文件名和内容。
    """
    name: str = ""        # 文件名（如 main.py, main.js）
    content: str = ""     # 文件内容（源代码）

    def to_dict(self):
        return {
            "name": self.name,
            "content": self.content
        }


@dataclass
class PostDataModel:
    """
    POST 请求数据模型

    封装发送到 Glot.io API 的完整请求体。
    包含要执行的文件列表和标准输入数据。
    """
    files: List[PostFile] = field(default_factory=list)  # 要执行的文件列表
    stdin: Optional[str] = None                          # 程序的标准输入

    def __post_init__(self):
        pass

    def to_dict(self):
        return {
            "files": [f.to_dict() for f in self.files],
            "stdin": self.stdin
        }


@dataclass
class RunResult:
    """
    Glot.io 运行结果模型

    从 Glot.io API 返回的原始运行结果，
    包含程序的标准输出和错误输出。
    """
    stdout: str = ""      # 程序的标准输出
    stderr: str = ""      # 程序的错误输出

    def to_dict(self):
        return {
            "stdout": self.stdout,
            "stderr": self.stderr
        }


# ============================================================
# 2. API 层请求/响应模型（与应用交互）
# ============================================================

@dataclass
class CodeExecutionRequest:
    """
    代码执行请求模型

    前端向 API 提交代码执行时的请求数据格式。
    包含要执行的源代码、编程语言和可选的标准输入。
    """
    code: str                                  # 要执行的源代码
    language: str = "javascript"               # 编程语言（默认 JavaScript）
    stdin: Optional[str] = None                # 程序的标准输入


@dataclass
class CodeExecutionResponse:
    """
    代码执行响应模型

    API 返回给前端的代码执行结果。
    包含标准输出、错误输出和执行成功/失败状态。
    """
    stdout: str                                # 程序的标准输出
    stderr: str = ""                           # 程序的错误输出
    success: bool = True                       # 执行是否成功（根据 stderr 是否为空判断）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "success": self.success
        }