import { expect, test } from '@playwright/test';

test('并发刷新共用一次轮换并更新会话', async ({ page }) => {
  let requests = 0;
  let enabled = false;
  await page.route('**/auth/refresh', async route => {
    if (!enabled) return route.fulfill({ status: 400, json: { error: 'no session' } });
    requests += 1;
    await new Promise(resolve => setTimeout(resolve, 80));
    await route.fulfill({ json: {
      access_token: 'new-access', refresh_token: 'new-refresh', expires_in: 900, token_type: 'Bearer',
    } });
  });
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  enabled = true;
  const results = await page.evaluate(async () => {
    localStorage.setItem('refresh_token', 'old-refresh');
    const path = '/src/services/api.ts';
    const api = await import(/* @vite-ignore */ path);
    const values = await Promise.all([api.refreshSessionTokens(), api.refreshSessionTokens(), api.refreshSessionTokens()]);
    return values.map(value => value.access_token);
  });
  expect(requests).toBe(1);
  expect(results).toEqual(['new-access', 'new-access', 'new-access']);
});

test('OAuth 回调兑换代码且不在 URL 中传递令牌', async ({ page }) => {
  await page.route('**/auth/exchange', async route => {
    expect(route.request().postDataJSON()).toEqual({ code: 'one-time-code', remember: true });
    await route.fulfill({ json: {
      access_token: 'new-access', refresh_token: 'new-refresh', expires_in: 900, token_type: 'Bearer',
      user_info: { id: '1', username: 'alice', email: '', role: 'member', is_active: true },
    } });
  });
  await page.route('**/auth/verify', route => route.fulfill({ json: {
    valid: true, user_info: { id: '1', username: 'alice', email: '', role: 'member', is_active: true },
  } }));
  await page.goto('/auth/callback?code=one-time-code&next=/');
  await expect.poll(() => page.evaluate(() => localStorage.getItem('access_token'))).toBe('new-access');
  expect(page.url()).not.toContain('new-access');
  expect(page.url()).not.toContain('new-refresh');
  expect(await page.evaluate(() => localStorage.getItem('refresh_token'))).toBeNull();
});

test('复制 sessionStorage 的两个标签页共用 Cookie 且刷新不重叠', async ({ context, page }) => {
  let enabled = false;
  let active = 0;
  let maxActive = 0;
  let count = 0;
  await context.route('**/auth/refresh', async route => {
    if (!enabled) return route.fulfill({ status: 400, json: { error: 'no session' } });
    expect(route.request().postDataJSON()).not.toHaveProperty('refresh_token');
    expect(route.request().headers()['x-csrf-protection']).toBe('1');
    active++; maxActive = Math.max(maxActive, active); count++;
    await new Promise(resolve => setTimeout(resolve, 80));
    active--;
    await route.fulfill({ json: { access_token: `access-${count}`, expires_in: 900, token_type: 'Bearer' } });
  });
  await page.goto('/login'); await page.waitForLoadState('networkidle');
  const second = await context.newPage();
  await second.goto('/login'); await second.waitForLoadState('networkidle');
  for (const tab of [page, second]) {
    await tab.evaluate(() => {
      localStorage.setItem('auth_storage_mode', 'session');
      sessionStorage.setItem('refresh_token', 'copied-stale-token');
    });
  }
  enabled = true;
  const refresh = (tab: typeof page) => tab.evaluate(async () => {
    const path = '/src/services/api.ts';
    const api = await import(/* @vite-ignore */ path);
    await api.refreshSessionTokens();
    return { access: sessionStorage.getItem('access_token'), refresh: sessionStorage.getItem('refresh_token') };
  });
  const results = await Promise.all([refresh(page), refresh(second)]);
  expect(maxActive).toBe(1); expect(count).toBe(2);
  expect(results.every(result => result.access && result.refresh === null)).toBe(true);
});

test('网络丢失时沿用请求编号恢复刷新', async ({ page }) => {
  await page.route('**/auth/refresh', route => route.fulfill({ status: 400, json: { error: 'no session' } }));
  await page.goto('/login'); await page.waitForLoadState('networkidle');
  const ids: string[] = [];
  await page.route('**/auth/refresh', async route => {
    ids.push(route.request().headers()['idempotency-key']!);
    if (ids.length === 1) return route.abort('failed');
    await route.fulfill({ json: { access_token: 'recovered', expires_in: 900, token_type: 'Bearer' } });
  });
  const access = await page.evaluate(async () => {
    const path = '/src/services/api.ts'; const api = await import(/* @vite-ignore */ path);
    await api.refreshSessionTokens().catch(() => null);
    return (await api.refreshSessionTokens()).access_token;
  });
  expect(access).toBe('recovered'); expect(ids[0]).toBe(ids[1]);
});
