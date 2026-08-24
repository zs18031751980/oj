<script setup lang="ts">
import { computed, markRaw, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const sidebarExpanded = ref(true);

const navMenu = markRaw([
  { title: '仪表盘', icon: 'material-symbols:dashboard', route: '/admin/dashboard' },
  { title: '用户管理', icon: 'material-symbols:group', route: '/admin/users' },
  { title: '公告管理', icon: 'material-symbols:campaign-rounded', route: '/admin/announcements' },
  { title: '比赛管理', icon: 'material-symbols:emoji-events-rounded', route: '/admin/contests' },
]);

const activePath = computed(() => route.path);

const toggleSidebar = () => {
  sidebarExpanded.value = !sidebarExpanded.value;
};

const navigateTo = (targetRoute: string) => {
  router.push(targetRoute);
};

const goHome = () => {
  router.push('/');
};

const logout = async () => {
  await authStore.logout();
  router.push('/');
};
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <header class="sticky top-0 z-50 border-b border-slate-200/30 bg-transparent backdrop-blur-2xl dark:border-slate-800/20">
      <div class="flex h-16 items-center justify-between px-4">
        <div class="flex items-center gap-3">
          <button class="admin-icon-button" aria-label="返回首页" title="返回首页" @click="goHome">
            <Icon icon="material-symbols:home-rounded" class="h-6 w-6" />
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
        class="app-sidebar fixed bottom-0 top-16 z-40 flex flex-col overflow-y-auto border-r border-slate-200 bg-slate-100/95 backdrop-blur-xl transition-all duration-300 dark:border-slate-700/50 dark:bg-slate-950/95"
        :class="sidebarExpanded ? 'w-64' : 'w-20'"
      >
        <nav class="flex-1 p-4">
          <button
            v-for="item in navMenu"
            :key="item.route"
            class="mb-2 flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left font-bold transition"
            :class="[
              sidebarExpanded ? 'justify-start' : 'justify-center',
              activePath === item.route
                ? 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200'
                : 'text-slate-600 hover:bg-white/70 dark:text-slate-300 dark:hover:bg-slate-800',
            ]"
            @click="navigateTo(item.route)"
          >
            <Icon :icon="item.icon" class="h-6 w-6 shrink-0" />
            <span v-if="sidebarExpanded">{{ item.title }}</span>
          </button>
        </nav>

        <div class="border-t border-slate-200 p-4 dark:border-slate-800">
          <button
            class="sidebar-toggle w-full"
            :class="sidebarExpanded ? 'justify-between px-4' : 'justify-center'"
            :aria-label="sidebarExpanded ? '收起侧边栏' : '展开侧边栏'"
            @click="toggleSidebar"
          >
            <span v-if="sidebarExpanded" class="text-sm font-bold">收起</span>
            <Icon
              :icon="sidebarExpanded ? 'material-symbols:chevron-left' : 'material-symbols:chevron-right'"
              class="h-5 w-5"
            />
          </button>
        </div>
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

.app-sidebar {
  border-radius: 0 1.5rem 1.5rem 0;
  box-shadow: 8px 0 28px rgba(15, 23, 42, 0.06);
}

.dark .app-sidebar {
  box-shadow: 8px 0 30px rgba(0, 0, 0, 0.18);
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  min-height: 2.75rem;
  border-radius: 0.875rem;
  color: #475569;
  transition: all 0.15s ease;
}

.sidebar-toggle:hover {
  background-color: #e2e8f0;
  color: #475569;
}

.dark .sidebar-toggle {
  color: #cbd5e1;
}

.dark .sidebar-toggle:hover {
  background-color: #1e293b;
  color: #ffffff;
}
</style>
