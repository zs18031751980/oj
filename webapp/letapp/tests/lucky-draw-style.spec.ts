import { expect, test } from '@playwright/test';

test('抽奖页样式不会覆盖主站登录按钮', async ({ page }) => {
  await page.goto('/chou');
  await page.goto('/');

  const loginButton = page.getByRole('button', { name: '登录' });
  await expect(loginButton).toHaveCSS('background-color', 'rgb(37, 99, 235)');
  await expect(loginButton).toHaveCSS('border-radius', '6px');
  await expect(loginButton).toHaveCSS('box-shadow', 'none');
});

test('题库使用克制的组件字重与圆角', async ({ page }) => {
  await page.goto('/problems');

  await expect(page.getByRole('heading', { name: '在线题库' })).toHaveCSS('font-weight', '600');
  const sidebarAllProblems = page.getByRole('button', { name: '全部题目', exact: true }).first();
  await expect(sidebarAllProblems).toHaveCSS('font-weight', '500');
  await expect(sidebarAllProblems).toHaveCSS('border-radius', '6px');
});

test('题库以工具栏和独立筛选卡呈现主要操作', async ({ page }) => {
  await page.goto('/problems');

  await expect(page.getByTestId('problem-filter-card')).toHaveCSS('background-color', 'rgb(255, 255, 255)');
  await expect(page.getByTestId('problem-toolbar')).toBeVisible();
  await expect(page.getByRole('button', { name: '全部题目', exact: true }).last()).toHaveCSS('background-color', 'rgb(37, 99, 235)');
});
