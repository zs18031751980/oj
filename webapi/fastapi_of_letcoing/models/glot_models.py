from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


@dataclass
class PostFile:
    """文件数据模型"""
    name: str = ""
    content: str = ""
    
    def to_dict(self):
        return {
            "name": self.name,
            "content": self.content
        }


@dataclass
class PostDataModel:
    """POST 请求数据模型"""
    files: List[PostFile] = field(default_factory=list)
    stdin: Optional[str] = None
    
    def __post_init__(self):
        pass
    
    def to_dict(self):
        return {
            "files": [f.to_dict() for f in self.files],
            "stdin": self.stdin
        }


@dataclass
class RunResult:
    """运行结果模型"""
    stdout: str = ""
    stderr: str = ""
    
    def to_dict(self):
        return {
            "stdout": self.stdout,
            "stderr": self.stderr
        }


@dataclass
class CodeExecutionRequest:
    """代码执行请求模型"""
    code: str
    language: str = "javascript"
    stdin: Optional[str] = None


@dataclass
class CodeExecutionResponse:
    """代码执行响应模型"""
    stdout: str
    stderr: str = ""
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "success": self.success
        }