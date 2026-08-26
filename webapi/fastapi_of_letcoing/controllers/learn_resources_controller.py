"""
学习资料 API 控制器

提供以下端点：
- GET /learn-resources/tree         — 返回目录树 JSON
- GET /learn-resources/file/<path>  — 返回 Markdown 文件内容
- GET /learn-resources/asset/<path> — 返回静态资源（图片等）
"""

import os
import time
import threading
import mimetypes
from flask import send_file, make_response
from flask_restx import Namespace, Resource

from services.learn_scanner_service import scan_learn_resources, read_markdown_file

api = Namespace('learn-resources', description='学习资料目录与内容')

# ============================================================
# 配置
# ============================================================

# 本地学习资料根目录（绝对路径）
_LEARN_ROOT = '/home/z/桌面/资料/obsidian-github/dev'

# 缓存：目录树 + 扫描时间戳
_tree_cache = {'data': None, 'ts': 0}
_CACHE_TTL = 60  # 缓存 60 秒
_lock = threading.Lock()


def _get_tree():
    """带缓存的目录树获取"""
    now = time.time()
    if _tree_cache['data'] and now - _tree_cache['ts'] < _CACHE_TTL:
        return _tree_cache['data']
    with _lock:
        if _tree_cache['data'] and now - _tree_cache['ts'] < _CACHE_TTL:
            return _tree_cache['data']
        _tree_cache['data'] = scan_learn_resources(_LEARN_ROOT)
        _tree_cache['ts'] = time.time()
    return _tree_cache['data']


# ============================================================
# API 端点
# ============================================================

@api.route('/tree')
class LearnTree(Resource):
    def get(self):
        """获取学习资料目录树"""
        tree = _get_tree()
        if not tree:
            api.abort(500, '目录扫描失败')
        return {'data': tree, 'root': _LEARN_ROOT}


@api.route('/file/<path:file_path>')
class LearnFile(Resource):
    def get(self, file_path: str):
        """获取 Markdown 文件内容"""
        result = read_markdown_file(_LEARN_ROOT, file_path)
        if not result:
            api.abort(404, '文件不存在')
        return {'data': result}


@api.route('/asset/<path:file_path>')
class LearnAsset(Resource):
    def get(self, file_path: str):
        """获取静态资源（图片等）"""
        # 安全检查：不允许跳出根目录
        normalized = os.path.normpath(file_path)
        if normalized.startswith('..') or os.path.isabs(normalized):
            api.abort(400, '非法路径')

        full_path = os.path.join(_LEARN_ROOT, normalized)
        if not os.path.isfile(full_path):
            api.abort(404, '资源不存在')

        # 获取 MIME 类型
        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        response = make_response(send_file(full_path))
        response.headers['Content-Type'] = mime_type
        response.headers['Cache-Control'] = 'public, max-age=86400'
        return response


@api.route('/rescan')
class LearnRescan(Resource):
    def post(self):
        """重新扫描目录树（管理员用）"""
        with _lock:
            _tree_cache['data'] = scan_learn_resources(_LEARN_ROOT)
            _tree_cache['ts'] = time.time()
        return {'success': True, 'message': '目录已重新扫描'}
