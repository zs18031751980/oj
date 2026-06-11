<<<<<<< HEAD
import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from './layouts/MainLayout.vue';

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
        meta: { title: '学习资源 - Let Coding' },
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
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
=======
import {createRouter, createWebHistory} from 'vue-router';
//import {useAuthorizationStore} from "./stores/Authorization";
import MainLayout from "./layouts/MainLayout.vue";
import AdminLayout from "./layouts/AdminLayout.vue";

const routes = [
    {
        path: "",
        name: "main",
        component: MainLayout,
        children: [
            {
                path: '',
                name: 'Home',
                meta: {title: "首页 - Let Coding"},
                component: () => import('./pages/Home.vue'),
            },
            {
                path: '/playground',
                name: 'Playground',
                meta: {title: "在线代码编辑器 - Let Coding"},
                component: () => import('./pages/Playground.vue'),
            },
            {
                path: '/learn',
                name: 'Learn',
                meta: {title: "学习资源 - Let Coding"},
                component: () => import('./pages/Learn.vue'),
            },
        ]
    },
    {
        path: "/login",
        name: "login",
        meta: {title: "登录 - Let Coding"},
        component: () => import('./pages/Login.vue'),
    },
    {
        path: "/admin",
        name: "admin",
        component: AdminLayout,
        meta: {
            title: "管理后台 - Let Coding",
            //requiresAuth: true
        },
        children: [
            {
                path: '',
                redirect: '/admin/dashboard'
            },
            {
                path: 'dashboard',
                name: 'AdminDashboard',
                meta: {title: "仪表盘 - Let Coding 管理后台"},
                component: () => import('./pages/admin/Dashboard.vue'),
            },
            {
                path: 'users',
                name: 'AdminUsers',
                meta: {title: "用户管理 - Let Coding 管理后台"},
                component: () => import('./pages/admin/Users.vue'),
            },
        ]
    },
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
<<<<<<< HEAD
  document.title = (to.meta.title as string) || 'Let Coding';
  next();
=======
    //const authorizationStore = useAuthorizationStore();

    // Set page title
    document.title = (to.meta.title as string) || "Let Coding";

    // Check if route requires authentication
    // if (to.meta.requiresAuth && !authorizationStore.isAuthenticated) {
    //     next('/login');
    // } else {
    //     next();
    // }

    next();
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
});

export default router;
