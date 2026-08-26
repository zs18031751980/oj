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
from flask import send_file, make_response, jsonify
from flask_restx import Namespace, Resource

from services.learn_scanner_service import scan_learn_resources, read_markdown_file

api = Namespace('learn-resources', description='学习资料目录与内容')

# ============================================================
# 配置：学习资料根目录
# ============================================================

def _resolve_learn_root() -> str:
    """解析学习资料根目录，按优先级尝试：
    1. 环境变量 LEARN_RESOURCES_ROOT
    2. 本地 Obsidian 仓库路径（开发机）
    3. 前端 public/learn 目录（仓库内，生产回退）
    """
    import os
    # 1. 环境变量优先
    env_path = os.environ.get('LEARN_RESOURCES_ROOT')
    if env_path and os.path.isdir(env_path):
        return os.path.normpath(env_path)

    # 2. 本地 Obsidian 仓库（开发机）
    local_obsidian = '/home/z/桌面/资料/obsidian-github/dev'
    if os.path.isdir(local_obsidian):
        return os.path.normpath(local_obsidian)

    # 3. 仓库内 public/learn 回退
    fallback = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..', '..', '..',
        'webapp', 'letapp', 'public', 'learn'
    ))
    if os.path.isdir(fallback):
        return fallback

    # 4. 环境变量（即使不存在也返回，便于报错提示）
    if env_path:
        return os.path.normpath(env_path)

    return fallback


_LEARN_ROOT = _resolve_learn_root()

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
    @api.response(200, 'Success')
    @api.response(500, 'Scan Failed')
    def get(self):
        """获取学习资料目录树"""
        if not os.path.isdir(_LEARN_ROOT):
            resp = jsonify({'error': f'学习资料目录不存在: {_LEARN_ROOT}'})
            resp.status_code = 500
            return resp
        tree = _get_tree()
        if not tree:
            resp = jsonify({'error': f'目录扫描失败: {_LEARN_ROOT}'})
            resp.status_code = 500
            return resp
        return {'data': tree, 'root': _LEARN_ROOT}


@api.route('/file/<path:file_path>')
class LearnFile(Resource):
    @api.response(200, 'Success')
    @api.response(404, 'Not Found')
    def get(self, file_path: str):
        """获取 Markdown 文件内容"""
        result = read_markdown_file(_LEARN_ROOT, file_path)
        if not result:
            resp = jsonify({'error': '文件不存在'})
            resp.status_code = 404
            return resp
        return {'data': result}


@api.route('/asset/<path:file_path>')
class LearnAsset(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request')
    @api.response(404, 'Not Found')
    def get(self, file_path: str):
        """获取静态资源（图片等）"""
        # 安全检查：不允许跳出根目录
        normalized = os.path.normpath(file_path)
        if normalized.startswith('..') or os.path.isabs(normalized):
            resp = jsonify({'error': '非法路径'})
            resp.status_code = 400
            return resp

        full_path = os.path.join(_LEARN_ROOT, normalized)
        if not os.path.isfile(full_path):
            resp = jsonify({'error': '资源不存在'})
            resp.status_code = 404
            return resp

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
    @api.response(200, 'Success')
    def post(self):
        """重新扫描目录树（管理员用）"""
        with _lock:
            _tree_cache['data'] = scan_learn_resources(_LEARN_ROOT)
            _tree_cache['ts'] = time.time()
        return {'success': True, 'message': '目录已重新扫描'}
