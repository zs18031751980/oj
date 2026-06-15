import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from './layouts/MainLayout.vue';
import AdminLayout from './layouts/AdminLayout.vue';
import { useAuthStore } from './stores/auth';
import { OAUTH_LOGIN_URL } from './services/api';

const routes = [
  {
    path: '',
    name: 'main',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Home',
        meta: { title: '首页 - Let Coding' },
        component: () => import('./pages/Home.vue'),
      },
      {
        path: '/playground',
        name: 'Playground',
        meta: { title: '在线代码编辑器 - Let Coding' },
        component: () => import('./pages/Playground.vue'),
      },
      {
        path: '/learn',
        name: 'Learn',
        meta: { title: '学习资源 - Let Coding', requiresAuth: true },
        component: () => import('./pages/Learn.vue'),
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    meta: { title: '登录 - Let Coding' },
    component: () => import('./pages/Login.vue'),
  },
  {
    path: '/auth/callback',
    name: 'authCallback',
    meta: { title: '登录中 - Let Coding' },
    component: () => import('./pages/AuthCallback.vue'),
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminLayout,
    meta: { title: '管理后台 - Let Coding' },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard',
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        meta: { title: '仪表盘 - Let Coding 管理后台' },
        component: () => import('./pages/admin/Dashboard.vue'),
      },
      {
        path: 'users',
        name: 'AdminUsers',
        meta: { title: '用户管理 - Let Coding 管理后台' },
        component: () => import('./pages/admin/Users.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  document.title = (to.meta.title as string) || 'Let Coding';

  if (to.meta.requiresAuth) {
    const authStore = useAuthStore();
    if (!authStore.isAuthenticated) {
      window.location.href = OAUTH_LOGIN_URL;
      next(false);
      return;
    }
  }

  next();
});

export default router;
