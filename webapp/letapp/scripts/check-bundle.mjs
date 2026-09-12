import assert from 'node:assert/strict';
import { readFileSync, statSync } from 'node:fs';
const manifest = JSON.parse(readFileSync('dist/.vite/manifest.json', 'utf8'));
function staticFiles(key, seen = new Set()) {
  if (seen.has(key)) return seen;
  seen.add(key);
  for (const dep of manifest[key]?.imports || []) staticFiles(dep, seen);
  return seen;
}
for (const name of ['index.html', 'MarkdownComponent', 'MonacoEditor']) {
  const key = Object.keys(manifest).find(key => key.includes(name) && (name === 'index.html' || manifest[key].file.endsWith('.js')));
  assert(key, `missing bundle: ${name}`);
  const keys = [...staticFiles(key)];
  assert(!keys.some(dep => /mermaid/i.test(manifest[dep]?.file || '')), `Mermaid eagerly imported by ${key}`);
  const bytes = keys.reduce((sum, dep) => sum + statSync('dist/' + manifest[dep].file).size, 0);
  console.log(`${key}: ${Math.round(bytes / 1024)} KiB static JS, Mermaid lazy`);
}
