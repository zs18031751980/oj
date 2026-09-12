"""请求边界校验；明确类型与字节上限，禁止静默转换非法输入。"""
from flask import request
from werkzeug.exceptions import BadRequest

MAX_CODE_BYTES = 128 * 1024
MAX_STDIN_BYTES = 1024 * 1024


def json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest('请求体必须是 JSON 对象')
    return data


def execution_fields(data, default_language='cpp', languages=None):
    code = data.get('code')
    language = data.get('language', default_language)
    stdin = data.get('stdin', '')
    if not isinstance(code, str) or not code.strip():
        raise ValueError('代码必须为非空字符串')
    if len(code.encode()) > MAX_CODE_BYTES:
        raise ValueError('代码不能超过 128 KiB')
    if not isinstance(language, str):
        raise ValueError('语言必须为字符串')
    language = language.lower().strip()
    if languages is not None and language not in languages:
        raise ValueError('不支持的编程语言')
    if stdin is None:
        stdin = ''
    if not isinstance(stdin, str) or len(stdin.encode()) > MAX_STDIN_BYTES:
        raise ValueError('输入必须为不超过 1 MiB 的字符串')
    return code, language, stdin
