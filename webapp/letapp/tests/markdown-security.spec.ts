import { expect, test } from '@playwright/test';

test('Markdown 清除脚本、事件和危险链接，保留代码与公式', async ({ page }) => {
  await page.route('**/auth/refresh', route => route.fulfill({ status: 400, json: { error: 'no session' } }));
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.evaluate(async () => {
    const vuePath = '/node_modules/.vite/deps/vue.js';
    const componentPath = '/src/components/MarkdownComponent.vue';
    const routerPath = '/node_modules/.vite/deps/vue-router.js';
    const { createRouter, createMemoryHistory } = await import(/* @vite-ignore */ routerPath);
    const router = createRouter({ history: createMemoryHistory(), routes: [] });
    const { createApp } = await import(/* @vite-ignore */ vuePath);
    const { default: Component } = await import(/* @vite-ignore */ componentPath);
    const root = document.createElement('div');
    root.id = 'security-test'; document.body.appendChild(root);
    createApp(Component, { showNav: false, source: '<img src=x onerror="window.__xss=1"><a href="javascript:alert(1)">link</a>\n\n```cpp\nint x = 1;\n```\n\n$x^2$' }).use(router).mount(root);
  });
  await expect(page.locator('#security-test .code-copy-btn')).toBeVisible();
  expect(await page.locator('#security-test [onerror], #security-test [onclick], #security-test a[href^="javascript:"]').count()).toBe(0);
  expect(await page.evaluate(() => (window as any).__xss)).toBeUndefined();
  await expect(page.locator('#security-test .katex')).toBeVisible();
});
