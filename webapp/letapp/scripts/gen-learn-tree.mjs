// 生成学习资料目录树 manifest (public/learn/tree.json)
// 该文件在构建时生成，前端以静态文件方式读取，避免依赖后端服务。
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', 'public', 'learn');
const OUT = path.join(ROOT, 'tree.json');

const SKIP_DIRS = new Set([
  '__pycache__', 'node_modules', '.git', 'images', 'assets',
  '.obsidian', 'ai-skills教学', 'runoob', 'w3', 'opencode-skills',
]);

function sanitizeName(name) {
  return (name.replace(/^\d+[-_.\s]+/, '').trim()) || name;
}

/** 从文件名提取章节号（用于排序），无数字则排到最后 */
function chapterOf(name) {
  const m = name.match(/^(\d+)/);
  return m ? parseInt(m[1], 10) : Number.MAX_SAFE_INTEGER;
}

/** 读取 markdown 首个 H1 标题作为中文显示名 */
function readTitle(fullPath, fallback) {
  try {
    const head = fs.readFileSync(fullPath, 'utf-8').split('\n').slice(0, 20).join('\n');
    const m = head.match(/^#\s+(.+)$/m);
    if (m && m[1].trim()) return m[1].trim();
  } catch { /* ignore */ }
  return fallback;
}

function makeId(rel) {
  return crypto.createHash('md5').update(rel || '__root__').digest('hex').slice(0, 12);
}

function scan(dir, rel) {
  if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) return null;
  const children = [];
  let entries = [];
  try {
    entries = fs.readdirSync(dir);
  } catch {
    return null;
  }
  // 按章节号数值排序，无数字者按名称排序
  entries.sort((a, b) => {
    const ca = chapterOf(a);
    const cb = chapterOf(b);
    if (ca !== cb) return ca - cb;
    return a.localeCompare(b, 'zh-Hans-CN');
  });
  for (const entry of entries) {
    if (entry.startsWith('.')) continue;
    const full = path.join(dir, entry);
    const entryRel = rel ? path.join(rel, entry) : entry;
    let stat;
    try {
      stat = fs.statSync(full);
    } catch {
      continue;
    }
    if (stat.isDirectory()) {
      if (SKIP_DIRS.has(entry.toLowerCase())) continue;
      const child = scan(full, entryRel);
      if (child && child.children.length) children.push(child);
    } else if (entry.toLowerCase().endsWith('.md')) {
      const fallback = sanitizeName(entry.replace(/\.md$/i, ''));
      const name = readTitle(full, fallback);
      children.push({
        id: makeId(entryRel),
        name,
        type: 'file',
        path: entryRel.split(path.sep).join('/'),
        size: stat.size,
        mtime: Math.floor(stat.mtimeMs / 1000),
      });
    }
  }
  const name = rel ? sanitizeName(path.basename(dir)) : '学习资料';
  return {
    id: makeId(rel || '__root__'),
    name,
    type: 'folder',
    path: rel ? rel.split(path.sep).join('/') : '',
    children,
  };
}

function main() {
  if (!fs.existsSync(ROOT)) {
    console.warn(`[gen-learn-tree] 目录不存在，跳过: ${ROOT}`);
    // 仍输出空树，避免构建失败
    fs.writeFileSync(OUT, JSON.stringify({ id: makeId('__root__'), name: '学习资料', type: 'folder', path: '', children: [] }, null, 2));
    return;
  }
  const tree = scan(ROOT, '');
  fs.writeFileSync(OUT, JSON.stringify(tree || { id: makeId('__root__'), name: '学习资料', type: 'folder', path: '', children: [] }, null, 2));
  const fileCount = (function count(t) {
    if (!t) return 0;
    return (t.children || []).reduce((s, c) => s + (c.type === 'file' ? 1 : count(c)), 0);
  })(tree);
  console.log(`[gen-learn-tree] 已生成 ${OUT}，共 ${fileCount} 个文件`);
}

main();
