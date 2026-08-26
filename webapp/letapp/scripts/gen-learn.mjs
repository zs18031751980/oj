// 构建学习资料静态副本：
// - 源：learn_source（保留原始中文/特殊字符文件名，仅作内容源）
// - 产物：public/learn-dist（所有目录/文件名改为 URL 安全的 ASCII，避免 + # ? & % 及中文目录在 dev/静态服务器下的问题）
// - 显示名保留中文：文件用 H1 标题，目录用原始中文名
// - 改写 markdown 内部相对链接/图片路径到 ASCII 路径
// 前端通过 /learn-dist 读取，dev 与 production 均可正常静态托管。
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.resolve(__dirname, '..', 'learn_source');
const DST = path.resolve(__dirname, '..', 'public', 'learn-dist');

// 不拷贝到产物的目录（源码/依赖/元数据）：含 C++ 库源码 include、lib 等
const SKIP_COPY = new Set([
  '__pycache__', 'node_modules', '.git', '.obsidian',
  'ai-skills教学', 'runoob', 'w3', 'opencode-skills', 'include', 'lib',
  'c-language',
]);

if (!fs.existsSync(SRC)) {
  console.error('未找到 learn_source');
  process.exit(1);
}

// 转为 URL 安全 ASCII 名称
function asciiName(name) {
  let s = name;
  s = s
    .replace(/\+/g, 'plus')
    .replace(/#/g, 'sharp')
    .replace(/\?/g, 'q')
    .replace(/&/g, 'and')
    .replace(/%/g, 'pct')
    .replace(/\s+/g, '_');
  s = s.replace(/[^A-Za-z0-9._-]/g, '_');
  if (!s) s = '_';
  return s;
}

const srcToDst = new Map();   // 源相对路径 -> 目标相对路径（均 '/' 分隔）
const dstPairs = [];          // [源绝对, 目标绝对]

// 递归规划：srcPrefix 为源相对路径前缀，dstPrefix 为目标相对路径前缀
function plan(srcDirAbs, dstDirAbs, srcPrefix, dstPrefix) {
  let entries = [];
  try {
    entries = fs.readdirSync(srcDirAbs);
  } catch {
    return;
  }
  const allOrig = new Set(entries.map((e) => e.toLowerCase()));
  for (const entry of entries) {
    if (entry === 'tree.json') continue;
    if (SKIP_COPY.has(entry.toLowerCase())) continue;
    const srcAbs = path.join(srcDirAbs, entry);
    const self = entry.toLowerCase();
    let base = asciiName(entry);
    let uniq = base;
    let i = 2;
    const probe = new Set(allOrig);
    probe.delete(self);
    while (probe.has(uniq.toLowerCase())) {
      const ext = path.extname(base);
      const stem = ext ? base.slice(0, -ext.length) : base;
      uniq = `${stem}_${i}${ext}`;
      i++;
    }
    probe.add(uniq.toLowerCase());
    allOrig.add(uniq.toLowerCase());
    const dstAbs = path.join(dstDirAbs, uniq);
    const srcRel = srcPrefix ? `${srcPrefix}/${entry}` : entry;
    const dstRel = dstPrefix ? `${dstPrefix}/${uniq}` : uniq;
    srcToDst.set(srcRel, dstRel);
    dstPairs.push([srcAbs, dstAbs]);
    let stat;
    try {
      stat = fs.statSync(srcAbs);
    } catch {
      continue;
    }
    if (stat.isDirectory()) plan(srcAbs, dstAbs, srcRel, dstRel);
  }
}

function planRoot() {
  let entries = [];
  try {
    entries = fs.readdirSync(SRC);
  } catch {
    return;
  }
  const allOrig = new Set(entries.map((e) => e.toLowerCase()));
  for (const entry of entries) {
    if (entry === 'tree.json') continue;
    if (SKIP_COPY.has(entry.toLowerCase())) continue;
    const srcAbs = path.join(SRC, entry);
    const self = entry.toLowerCase();
    let base = asciiName(entry);
    let uniq = base;
    let i = 2;
    const probe = new Set(allOrig);
    probe.delete(self);
    while (probe.has(uniq.toLowerCase())) {
      const ext = path.extname(base);
      const stem = ext ? base.slice(0, -ext.length) : base;
      uniq = `${stem}_${i}${ext}`;
      i++;
    }
    probe.add(uniq.toLowerCase());
    allOrig.add(uniq.toLowerCase());
    const dstAbs = path.join(DST, uniq);
    srcToDst.set(entry, uniq);
    dstPairs.push([srcAbs, dstAbs]);
    let stat;
    try {
      stat = fs.statSync(srcAbs);
    } catch {
      continue;
    }
    if (stat.isDirectory()) plan(srcAbs, dstAbs, entry, uniq);
  }
}

planRoot();

// 清空并重建目标目录
function rmrf(p) {
  if (fs.existsSync(p)) fs.rmSync(p, { recursive: true, force: true });
}
rmrf(DST);
fs.mkdirSync(DST, { recursive: true });

// 复制文件（.md 改写链接；其余直接拷贝）
function normalize(p) {
  const parts = [];
  for (const seg of p.split('/')) {
    if (seg === '' || seg === '.') continue;
    if (seg === '..') parts.pop();
    else parts.push(seg);
  }
  return parts.join('/');
}
function relativize(fromDir, toAbs) {
  const from = fromDir.split('/').filter(Boolean);
  const to = toAbs.split('/').filter(Boolean);
  let i = 0;
  while (i < from.length && i < to.length && from[i] === to[i]) i++;
  const up = from.slice(i).map(() => '..');
  return [...up, ...to.slice(i)].join('/') || '.';
}
function readTitle(content, fallback) {
  const m = content.split('\n').slice(0, 20).join('\n').match(/^#\s+(.+)$/m);
  return m && m[1].trim() ? m[1].trim() : fallback;
}

// 反向映射：目标相对路径 -> 源相对路径（用于链接改写）
const dstToSrc = new Map([...srcToDst.entries()].map(([s, d]) => [d, s]));

let linkCount = 0;
for (const [srcAbs, dstAbs] of dstPairs) {
  let stat;
  try {
    stat = fs.statSync(srcAbs);
  } catch {
    continue;
  }
  if (stat.isDirectory()) {
    fs.mkdirSync(dstAbs, { recursive: true });
    continue;
  }
  if (dstAbs.toLowerCase().endsWith('.md')) {
    let content;
    try {
      content = fs.readFileSync(srcAbs, 'utf-8');
    } catch {
      continue;
    }
    const srcRelKey = dstToSrc.get(relOf(dstAbs)) || '';
    const baseSrcDir = dirRel(srcRelKey);
    const baseDstDir = dirRel(dstAbs);
    const rewrite = (target) => {
      if (/^(https?:|data:|mailto:|#)/.test(target) || target.startsWith('/')) return null;
      const t = target.trim();
      if (!t) return null;
      const [pathPart, anchor] = t.split('#');
      if (!pathPart) return null;
      const resolvedSrc = normalize(`${baseSrcDir}/${pathPart}`);
      const dstTarget = srcToDst.get(resolvedSrc);
      if (!dstTarget) return null;
      const rel = relativize(baseDstDir, dstTarget);
      linkCount++;
      return anchor ? `${rel}#${anchor}` : rel;
    };
    content = content.replace(/(\]\()([^)\s]+)(\))/g, (m, a, t, c) => {
      const r = rewrite(t);
      return r ? a + r + c : m;
    });
    content = content.replace(/(src|href)=("|')([^"']+)\2/g, (m, attr, q, t) => {
      const r = rewrite(t);
      return r ? `${attr}=${q}${r}${q}` : m;
    });
    fs.writeFileSync(dstAbs, content);
  } else {
    fs.copyFileSync(srcAbs, dstAbs);
  }
}

// 生成目录树（walk 源，输出目标路径与中文显示名）
function relOf(abs) {
  return abs.split(path.sep).join('/').replace(DST.split(path.sep).join('/') + '/', '');
}
function dirRel(abs) {
  const r = relOf(abs);
  const i = r.lastIndexOf('/');
  return i < 0 ? '' : r.slice(0, i);
}

const SKIP_DIRS = new Set([
  '__pycache__', 'node_modules', '.git', 'images', 'assets',
  '.obsidian', 'ai-skills教学', 'runoob', 'w3', 'opencode-skills',
  'c-language',
]);
function chapterOf(name) {
  const m = name.match(/^(\d+)/);
  return m ? parseInt(m[1], 10) : Number.MAX_SAFE_INTEGER;
}
function sanitizeTitle(name) {
  return (name.replace(/^\d+[-_.\s]+/, '').trim()) || name;
}
function makeId(rel) {
  return crypto.createHash('md5').update(rel || '__root__').digest('hex').slice(0, 12);
}
function buildTree(srcDirAbs, rel) {
  let entries = [];
  try {
    entries = fs.readdirSync(srcDirAbs);
  } catch {
    return null;
  }
  entries.sort((a, b) => {
    const ca = chapterOf(a);
    const cb = chapterOf(b);
    if (ca !== cb) return ca - cb;
    return a.localeCompare(b, 'zh-Hans-CN');
  });
  const children = [];
  for (const entry of entries) {
    if (entry.startsWith('.')) continue;
    const srcAbs = path.join(srcDirAbs, entry);
    const entryRel = rel ? `${rel}/${entry}` : entry;
    let stat;
    try {
      stat = fs.statSync(srcAbs);
    } catch {
      continue;
    }
    if (stat.isDirectory()) {
      if (SKIP_DIRS.has(entry.toLowerCase())) continue;
      const child = buildTree(srcAbs, entryRel);
      if (child && child.children.length) children.push(child);
    } else if (entry.toLowerCase().endsWith('.md')) {
      const dstRel = srcToDst.get(entryRel) || entryRel;
      let title = sanitizeTitle(entry.replace(/\.md$/i, ''));
      try {
        const c = fs.readFileSync(srcAbs, 'utf-8');
        title = readTitle(c, title);
      } catch { /* ignore */ }
      children.push({
        id: makeId(dstRel),
        name: title,
        type: 'file',
        path: dstRel.split(path.sep).join('/'),
        size: stat.size,
        mtime: Math.floor(stat.mtimeMs / 1000),
      });
    }
  }
  const name = rel ? sanitizeTitle(path.basename(srcDirAbs)) : '学习资料';
  return {
    id: makeId(rel || '__root__'),
    name,
    type: 'folder',
    path: rel ? (srcToDst.get(rel) || rel).split(path.sep).join('/') : '',
    children,
  };
}

const tree = buildTree(SRC, '');
fs.writeFileSync(path.join(DST, 'tree.json'), JSON.stringify(tree || { id: makeId('__root__'), name: '学习资料', type: 'folder', path: '', children: [] }, null, 2));

console.log(`完成。生成 ${dstPairs.length} 项到 public/learn-dist，改写链接 ${linkCount} 处，文件数 ${tree ? countFiles(tree) : 0}。`);
function countFiles(t) {
  return (t.children || []).reduce((s, c) => s + (c.type === 'file' ? 1 : countFiles(c)), 0);
}
