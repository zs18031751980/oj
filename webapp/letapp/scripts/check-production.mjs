import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';

const origin = 'http://127.0.0.1:4174';
const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', '4174', '--strictPort'], { stdio: 'pipe' });
let browser;
try {
  for (let i = 0; i < 100; i++) {
    if (server.exitCode !== null) throw new Error('production preview failed to start');
    try { if ((await fetch(origin)).ok) break; } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  browser = await chromium.launch(process.env.CI ? {} : { executablePath: '/usr/bin/google-chrome' });
  const page = await browser.newPage();
  const row = { id: 1, title: 'Security fixture', content: '安全正文\n\n```cpp\nint main() {}\n```', author_id: 1, author_name: 'test', category: '问答', tags: '', reply_count: 0, like_count: 0, view_count: 0, is_pinned: false, is_liked: false, replies: [] };
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/auth/refresh')) return route.fulfill({ status: 400, json: { error: 'no session' } });
    if (path.endsWith('/auth/providers')) return route.fulfill({ json: { providers: [] } });
    if (path.endsWith('/discussions/1')) return route.fulfill({ json: row });
    return route.fulfill({ json: [row] });
  });
  const requests = [];
  page.on('request', request => requests.push(request.url()));
  await page.goto(origin + '/discussion');
  await page.getByText('Security fixture', { exact: true }).click();
  await page.locator('.markdown-content .code-copy-btn').waitFor();
  assert(!requests.some(url => /mermaid/i.test(url)), 'plain Markdown loaded Mermaid');
  const policy = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');
  assert(policy.includes("script-src 'self'") && !policy.includes("script-src 'self' 'unsafe-inline'"));
  await page.evaluate(() => {
    const image = document.createElement('img'); image.setAttribute('onerror', 'window.__cspFailed = true');
    image.src = '/missing-security-image'; document.body.appendChild(image);
  });
  await page.waitForTimeout(100);
  assert.equal(await page.evaluate(() => window.__cspFailed), undefined);
  await page.goto(origin + '/playground');
  await page.locator('.monaco-editor').waitFor();
  assert(!requests.some(url => /mermaid/i.test(url)), 'editor loaded Mermaid');
  row.content = '```mermaid\ngraph TD\n  A-->B\n```';
  await page.goto(origin + '/discussion');
  await page.getByText('Security fixture', { exact: true }).click();
  await page.locator('.mermaid svg').waitFor({ timeout: 20000 });
  assert(requests.some(url => /mermaid/i.test(url)), 'diagram did not load Mermaid');
  console.log('Production browser gate passed: CSP, Markdown, Monaco, lazy Mermaid and diagram rendering');
} finally {
  await browser?.close();
  server.kill('SIGTERM');
}
