<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const sidebarExpanded = ref(true);

const navMenu = [
  { title: '仪表盘', icon: 'material-symbols:dashboard', route: '/admin/dashboard' },
  { title: '用户管理', icon: 'material-symbols:people', route: '/admin/users' },
  { title: '返回首页', icon: 'material-symbols:home', route: '/' },
];

const activePath = computed(() => route.path);

const toggleSidebar = () => {
  sidebarExpanded.value = !sidebarExpanded.value;
};

const navigateTo = (targetRoute: string) => {
  router.push(targetRoute);
};

const logout = async () => {
  await authStore.logout();
  router.push('/');
};
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <header class="sticky top-0 z-50 border-b border-slate-200 bg-white/85 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/85">
      <div class="flex h-16 items-center justify-between px-4">
        <div class="flex items-center gap-3">
          <button class="admin-icon-button" aria-label="切换侧边栏" @click="toggleSidebar">
            <Icon :icon="sidebarExpanded ? 'material-symbols:menu-open' : 'material-symbols:menu'" class="h-6 w-6" />
          </button>
          <h1 class="text-xl font-black">Let Coding 管理后台</h1>
        </div>

        <div class="flex items-center gap-3">
          <span class="hidden text-sm font-bold text-slate-500 dark:text-slate-400 md:inline">
            {{ authStore.displayName }}
          </span>
          <button class="admin-icon-button" aria-label="退出登录" @click="logout">
            <Icon icon="material-symbols:logout" class="h-6 w-6 text-rose-500" />
          </button>
        </div>
      </div>
    </header>

    <div class="flex">
      <aside
        class="fixed bottom-0 top-16 z-40 overflow-y-auto border-r border-slate-200 bg-white shadow-lg shadow-slate-200/50 transition-all duration-300 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20"
        :class="sidebarExpanded ? 'w-64' : 'w-20'"
      >
        <nav class="p-4">
          <button
            v-for="item in navMenu"
            :key="item.route"
            class="mb-2 flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left font-bold transition"
            :class="activePath === item.route ? 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'"
            @click="navigateTo(item.route)"
          >
            <Icon :icon="item.icon" class="h-6 w-6 shrink-0" />
            <span v-if="sidebarExpanded">{{ item.title }}</span>
          </button>
        </nav>
      </aside>

      <main class="flex-1 p-6 transition-all duration-300" :class="sidebarExpanded ? 'ml-64' : 'ml-20'">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.admin-icon-button {
  @apply grid h-10 w-10 place-items-center rounded-2xl text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800;
}
</style>
