"""
学习资料文件扫描服务

从指定本地目录递归扫描所有 .md 文件和文件夹，生成树形目录结构。
"""

import os
import re
import hashlib
from typing import Dict, List, Optional


def _sanitize_name(name: str) -> str:
    """去掉文件名中的排序前缀，如 01-xxx → xxx"""
    return re.sub(r'^\d+[-_.\s]+', '', name).strip() or name


def _make_id(relative_path: str) -> str:
    """用相对路径生成唯一 ID"""
    return hashlib.md5(relative_path.encode()).hexdigest()[:12]


def _scan_directory(
    root_dir: str,
    relative_path: str = '',
    depth: int = 0,
    max_depth: int = 20,
) -> Optional[Dict]:
    """递归扫描目录，返回树形结构"""
    if depth > max_depth:
        return None

    full_path = os.path.join(root_dir, relative_path) if relative_path else root_dir

    if not os.path.isdir(full_path):
        return None

    children: List[Dict] = []

    try:
        entries = sorted(os.listdir(full_path))
    except PermissionError:
        return None

    for entry in entries:
        entry_full = os.path.join(full_path, entry)
        entry_rel = os.path.join(relative_path, entry) if relative_path else entry

        if entry.startswith('.'):
            continue

        if os.path.isdir(entry_full):
            # 跳过无用目录
            if entry.lower() in ('__pycache__', 'node_modules', '.git', 'images', 'assets', '.obsidian', 'ai-skills教学', 'runoob', 'w3', 'opencode-skills'):
                continue
            child = _scan_directory(root_dir, entry_rel, depth + 1, max_depth)
            if child and child.get('children'):
                children.append(child)
        elif entry.lower().endswith('.md'):
            name = _sanitize_name(entry.replace('.md', ''))
            file_id = _make_id(entry_rel)
            stat = os.stat(entry_full)
            children.append({
                'id': file_id,
                'name': name,
                'type': 'file',
                'path': entry_rel,
                'size': stat.st_size,
                'mtime': int(stat.st_mtime),
            })

    if not children and not relative_path:
        return None

    name = _sanitize_name(os.path.basename(full_path)) if relative_path else '学习资料'

    return {
        'id': _make_id(relative_path or '__root__'),
        'name': name,
        'type': 'folder',
        'path': relative_path or '',
        'children': children,
    }


def scan_learn_resources(root_dir: str, max_depth: int = 20) -> Optional[Dict]:
    """
    扫描指定根目录，返回完整的树形目录结构。
    """
    return _scan_directory(root_dir, '', 0, max_depth)


def read_markdown_file(root_dir: str, relative_path: str) -> Optional[Dict]:
    """
    读取指定相对路径的 .md 文件内容。
    返回 { content, title, path, mtime } 或 None。
    """
    # 安全检查：不允许跳出根目录
    normalized = os.path.normpath(relative_path)
    if normalized.startswith('..') or os.path.isabs(normalized):
        return None

    full_path = os.path.join(root_dir, normalized)
    if not os.path.isfile(full_path) or not full_path.endswith('.md'):
        return None

    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except (PermissionError, OSError):
        return None

    # 提取标题
    title_match = re.match(r'^#\s+(.+)', content)
    title = title_match.group(1).strip() if title_match else os.path.basename(normalized).replace('.md', '')

    stat = os.stat(full_path)
    return {
        'content': content,
        'title': title,
        'path': normalized,
        'mtime': int(stat.st_mtime),
    }


def resolve_asset(root_dir: str, md_relative_path: str, asset_relative: str) -> Optional[str]:
    """
    解析 Markdown 中引用的资源（图片等）的真实路径。
    基于 Markdown 文件所在目录解析相对路径。
    """
    md_dir = os.path.dirname(md_relative_path)
    asset_path = os.path.normpath(os.path.join(md_dir, asset_relative))

    # 安全检查
    if asset_path.startswith('..') or os.path.isabs(asset_path):
        return None

    full_path = os.path.join(root_dir, asset_path)
    if os.path.isfile(full_path):
        return full_path
    return None
