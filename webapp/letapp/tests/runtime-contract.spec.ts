import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('**/auth/refresh', route => route.fulfill({ status: 400, json: { error: 'no session' } }));
  await page.goto('/login'); await page.waitForLoadState('networkidle');
});

test('请求可超时且顺序轮询在取消后停止', async ({ page }) => {
  const result = await page.evaluate(async () => {
    const path = '/src/services/api.ts'; const api = await import(/* @vite-ignore */ path);
    const oldFetch = window.fetch;
    window.fetch = (_url, options) => new Promise((_resolve, reject) => {
      options?.signal?.addEventListener('abort', () => reject(options.signal?.reason));
    });
    let timedOut = false;
    try { await api.fetchWithTimeout('/never', {}, 20); } catch { timedOut = true; }
    finally { window.fetch = oldFetch; }
    const pollingPath = '/src/services/polling.ts'; const { startPolling } = await import(/* @vite-ignore */ pollingPath);
    let active = 0; let maxActive = 0; let calls = 0;
    const stop = startPolling(async () => {
      calls++; active++; maxActive = Math.max(maxActive, active);
      await new Promise(resolve => setTimeout(resolve, 30)); active--; return 'Pending';
    }, () => false, () => {}, 5);
    await new Promise(resolve => setTimeout(resolve, 100)); stop();
    const stoppedAt = calls; await new Promise(resolve => setTimeout(resolve, 100));
    return { timedOut, maxActive, stoppedAt, calls };
  });
  expect(result.timedOut).toBe(true); expect(result.maxActive).toBe(1);
  expect(result.calls).toBe(result.stoppedAt);
});

test('升级后的 Monaco 可以编辑并回传内容', async ({ page }) => {
  await page.evaluate(async () => {
    const vue = '/node_modules/.vite/deps/vue.js'; const component = '/src/components/MonacoEditor.vue';
    const { createApp } = await import(/* @vite-ignore */ vue);
    const { default: Editor } = await import(/* @vite-ignore */ component);
    const root = document.createElement('div'); root.id = 'editor-test'; document.body.appendChild(root);
    createApp(Editor, { modelValue: 'int main() {}', language: 'cpp', isDark: false, height: 300,
      onReady: (editor: any) => { (window as any).__testEditor = editor; },
      'onUpdate:modelValue': (value: string) => { (window as any).__edited = value; },
    }).mount(root);
  });
  await expect(page.locator('#editor-test .monaco-editor')).toBeVisible();
  await page.evaluate(() => (window as any).__testEditor.focus());
  await page.keyboard.press('ControlOrMeta+A');
  await page.keyboard.type('int main() { return 0; }');
  expect(await page.evaluate(() => (window as any).__edited)).toBe('int main() { return 0; }');
});
