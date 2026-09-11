import { expect, test } from '@playwright/test';

test('抽奖页样式不会覆盖主站登录按钮', async ({ page }) => {
  await page.goto('/chou');
  await page.goto('/');

  const loginButton = page.getByRole('button', { name: '登录' });
  await expect(loginButton).toHaveCSS('background-color', 'rgb(37, 99, 235)');
  await expect(loginButton).toHaveCSS('border-radius', '6px');
  await expect(loginButton).toHaveCSS('box-shadow', 'none');
});
