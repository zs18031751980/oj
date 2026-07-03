<template>
  <div class="min-h-screen bg-slate-50 text-slate-950 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-50">
    <n-layout has-sider class="min-h-screen bg-transparent">
      <aside
        class="fixed left-0 top-0 z-50 hidden h-screen flex-col border-r border-white/40 bg-transparent backdrop-blur-2xl transition-all duration-300 dark:border-slate-700/40 md:flex rounded-r-[1.75rem] dark:bg-slate-950/85"
        :class="sidebarExpanded ? 'w-72' : 'w-24'"
      >
        <div class="flex h-20 items-center justify-between gap-3 px-5">
          <a href="https://www.xauat.site/" target="_blank" rel="noopener noreferrer" class="group flex min-w-0 items-center gap-3 overflow-hidden">
            <span class="relative grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-white shadow-lg shadow-cyan-500/15 dark:bg-slate-950">
              <img src="/assets/logo.png" alt="Let Coding Logo" class="h-8 w-8 transition-transform group-hover:scale-110" />
            </span>
            <div v-if="sidebarExpanded" class="min-w-0">
              <div class="truncate text-lg font-black tracking-tight">Let Coding</div>
              <div class="-mt-1 text-[11px] font-medium uppercase tracking-[0.24em] text-slate-400">Online Judge</div>
            </div>
          </a>
        </div>

        <nav class="flex-1 space-y-2 px-4 pb-6">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="sidebar-link"
            :class="sidebarExpanded ? 'justify-start px-4' : 'justify-center px-0'"
            @click="closeMenu"
          >
            <Icon :icon="item.icon" class="h-5 w-5 shrink-0" />
            <span v-if="sidebarExpanded" class="truncate">{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="border-t border-slate-200 p-4 dark:border-slate-800">
          <button
            class="sidebar-toggle w-full"
            :class="sidebarExpanded ? 'justify-between px-4' : 'justify-center'"
            :aria-label="sidebarExpanded ? '收起侧边栏' : '展开侧边栏'"
            @click="toggleSidebar"
          >
            <span v-if="sidebarExpanded" class="text-sm font-bold">收起</span>
            <Icon :icon="sidebarExpanded ? 'material-symbols:chevron-left' : 'material-symbols:chevron-right'" class="h-5 w-5" />
          </button>
        </div>
      </aside>

      <n-layout class="bg-transparent">
        <header
          class="fixed left-0 right-0 top-0 z-40 border-b border-white/30 transition-all duration-300 dark:border-slate-800/20"
          :class="headerCollapsed ? '-translate-y-full' : 'translate-y-0'"
          :style="headerGradient"
        >
          <div
            class="h-auto min-h-20 w-full px-3 py-3 sm:px-4 lg:px-6"
            :style="headerPaddingStyle"
          >
            <div class="flex min-h-14 w-full min-w-0 items-center justify-between gap-3">
              <a href="https://www.xauat.site/" target="_blank" rel="noopener noreferrer" class="flex min-w-0 items-center gap-3 md:hidden">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-white dark:bg-slate-950">
                  <img src="/assets/logo.png" alt="Let Coding Logo" class="h-7 w-7" />
                </span>
                <span class="truncate text-base font-black">Let Coding</span>
              </a>

              <div class="ml-auto flex min-w-0 items-center justify-end gap-2 sm:gap-3">
                <button class="icon-button shrink-0 max-md:hidden" aria-label="收起导航栏" @click="headerCollapsed = !headerCollapsed">
                  <Icon icon="material-symbols:expand-less" class="h-5 w-5" />
                </button>
                <div class="relative shrink-0">
                  <button class="icon-button" aria-label="打开导航菜单" @click.stop="menuVisible = !menuVisible">
                    <Icon :icon="menuVisible ? 'material-symbols:close-rounded' : 'material-symbols:menu-rounded'" class="h-6 w-6" />
                  </button>

                  <transition name="fade-scale">
                    <div
                      v-if="menuVisible"
                      class="absolute right-0 top-[calc(100%+0.75rem)] z-50 w-[min(18rem,calc(100vw-1.5rem))] rounded-[1.75rem] border border-slate-200 bg-white p-3 shadow-2xl shadow-slate-200/70 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/40"
                    >
                      <button
                        v-for="item in navItems"
                        :key="`${item.to}-menu`"
                        type="button"
                        class="menu-link"
                        @click="navigateFromMenu(item.to)"
                      >
                        <Icon :icon="item.icon" class="h-5 w-5" />
                        <span>{{ item.label }}</span>
                      </button>
                    </div>
                  </transition>
                </div>

                <button
                  class="icon-button shrink-0"
                  :aria-label="isDark ? '切换到浅色模式' : '切换到深色模式'"
                  @click="mainToggleTheme"
                >
                  <Icon v-if="!isDark" icon="material-symbols:light-mode" class="h-5 w-5 text-amber-500" />
                  <Icon v-else icon="material-symbols:dark-mode" class="h-5 w-5 text-cyan-300" />
                </button>

                <button v-if="!authStore.isAuthenticated" class="primary-pill shrink-0" @click="startClubLogin">
                  登录
                </button>
                <button v-else class="secondary-pill shrink-0" @click="handleLogout">
                  <span class="truncate">退出 {{ authStore.displayName }}</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        <button
          v-if="headerCollapsed"
          class="fixed left-1/2 top-0 z-50 -translate-x-1/2 rounded-b-2xl border-x border-b border-slate-200 bg-white/90 px-5 py-2 shadow-lg backdrop-blur-2xl transition hover:bg-white dark:border-slate-700 dark:bg-slate-900/90 dark:hover:bg-slate-900"
          aria-label="展开导航栏"
          @click="headerCollapsed = false"
        >
          <Icon icon="material-symbols:expand-more" class="h-5 w-5 text-slate-600 dark:text-slate-300" />
        </button>

        <div
          v-if="headerCollapsed"
          class="fixed left-0 top-0 z-30 h-6 w-full cursor-pointer"
          @click="headerCollapsed = false"
        ></div>

        <n-layout-content class="bg-transparent transition-all duration-300" :style="[contentPaddingStyle, { paddingTop: headerCollapsed ? '0px' : '5rem', '--header-h': headerCollapsed ? '0px' : '5rem' }]">
          <router-view />
        </n-layout-content>
      </n-layout>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { NLayout, NLayoutContent } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { storeToRefs } from 'pinia';
import { markRaw } from 'vue';
import { useThemeStore } from '../stores/theme';
import { useAuthStore } from '../stores/auth';

const navItems = markRaw([
  { label: '首页', to: '/', icon: 'material-symbols:home-rounded' },
  { label: '在线编辑器', to: '/playground', icon: 'material-symbols:code-rounded' },
  { label: '学习资源', to: '/learn', icon: 'material-symbols:school-rounded' },
  { label: '题库', to: '/problems', icon: 'material-symbols:library-books-rounded' },
  { label: '公告', to: '/announcements', icon: 'material-symbols:campaign-rounded' },
]);

const DESKTOP_EXPANDED_WIDTH = 288;
const DESKTOP_COLLAPSED_WIDTH = 96;

const router = useRouter();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const { isDark } = storeToRefs(themeStore);
const { toggleTheme } = themeStore;

const sidebarExpanded = ref(true);
const menuVisible = ref(false);
const isDesktop = ref(false);
const headerCollapsed = ref(false);

const desktopSidebarWidth = computed(() => (
  sidebarExpanded.value ? DESKTOP_EXPANDED_WIDTH : DESKTOP_COLLAPSED_WIDTH
));

const headerPaddingStyle = computed(() => (
  isDesktop.value
    ? {
        paddingLeft: `${desktopSidebarWidth.value + 16}px`,
        paddingRight: '16px',
      }
    : undefined
));

const headerGradient = computed(() => {
  if (isDark.value) {
    return {
      backgroundImage: 'linear-gradient(to bottom, rgba(2, 6, 23, 0.92), rgba(2, 6, 23, 0.4))',
      backdropFilter: 'blur(24px)',
      WebkitBackdropFilter: 'blur(24px)',
    };
  }
  return {
    backgroundImage: 'linear-gradient(to bottom, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0))',
    backdropFilter: 'blur(24px)',
    WebkitBackdropFilter: 'blur(24px)',
  };
});

const contentPaddingStyle = computed(() => ({
  ...(isDesktop.value ? { paddingLeft: `${desktopSidebarWidth.value}px` } : {}),
  '--app-content-left': isDesktop.value ? `${desktopSidebarWidth.value}px` : '0px',
}));

const updateViewportFlags = () => {
  isDesktop.value = window.innerWidth >= 768;
};

const toggleSidebar = () => {
  sidebarExpanded.value = !sidebarExpanded.value;
};

const closeMenu = () => {
  menuVisible.value = false;
};

const mainToggleTheme = () => {
  toggleTheme();
  closeMenu();
};

const startClubLogin = () => {
  closeMenu();
  authStore.startOAuthLogin('iOSClub', router.currentRoute.value.fullPath, true);
};

const handleLogout = async () => {
  closeMenu();
  await authStore.logout();
};

const navigateFromMenu = async (to: string) => {
  closeMenu();
  await router.push(to);
};

const handleWindowClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null;
  if (!target?.closest('.icon-button') && !target?.closest('.menu-link')) {
    closeMenu();
  }
};

onMounted(() => {
  updateViewportFlags();
  window.addEventListener('click', handleWindowClick);
  window.addEventListener('resize', updateViewportFlags);
});

onUnmounted(() => {
  window.removeEventListener('click', handleWindowClick);
  window.removeEventListener('resize', updateViewportFlags);
});
</script>

<style scoped>
@reference 'tailwindcss';

.sidebar-toggle {
  @apply flex items-center rounded-2xl text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white;
}

.sidebar-link {
  @apply flex h-13 items-center gap-3 rounded-2xl border border-slate-200 bg-white text-sm font-bold text-slate-950 shadow-sm shadow-slate-200/60 transition hover:bg-slate-100 hover:text-slate-950 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:shadow-black/20 dark:hover:bg-slate-800 dark:hover:text-white;
}

.router-link-exact-active.sidebar-link {
  @apply border-cyan-300 bg-white shadow-md shadow-cyan-100 dark:border-cyan-500/50 dark:bg-slate-950 dark:shadow-cyan-950/20;
}

.primary-pill {
  display: inline-flex;
  height: 2.75rem;
  align-items: center;
  border-radius: 9999px;
  background-color: #06b6d4;
  padding-left: 1rem;
  padding-right: 1rem;
  font-size: 0.875rem;
  font-weight: 900;
  color: #082f49;
  box-shadow: 0 10px 15px -3px rgba(6, 182, 212, 0.25);
  transition: all 0.15s ease;
}
.primary-pill:hover {
  background-color: #e2e8f0;
  translate: 0 -0.125rem;
}
@media (min-width: 640px) {
  .primary-pill {
    padding-left: 1.25rem;
    padding-right: 1.25rem;
  }
}

.secondary-pill {
  display: inline-flex;
  height: 2.75rem;
  max-width: 16rem;
  align-items: center;
  border-radius: 9999px;
  background-color: #f1f5f9;
  padding-left: 1rem;
  padding-right: 1rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #1e293b;
  transition: all 0.15s ease;
}
.secondary-pill:hover {
  background-color: #cbd5e1;
}
.dark .secondary-pill {
  background-color: #1e293b;
  color: #f1f5f9;
}
.dark .secondary-pill:hover {
  background-color: #06b6d4;
  color: #082f49;
}
@media (min-width: 640px) {
  .secondary-pill {
    padding-left: 1.25rem;
    padding-right: 1.25rem;
  }
}

.icon-button {
  display: grid;
  height: 2.75rem;
  width: 2.75rem;
  flex-shrink: 0;
  place-items: center;
  border-radius: 9999px;
  color: #334155;
  transition: all 0.15s ease;
}
.icon-button:hover {
  background-color: #e2e8f0;
}
.dark .icon-button {
  color: #e2e8f0;
}
.dark .icon-button:hover {
  background-color: #06b6d4;
  color: #082f49;
}

.menu-link {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.75rem;
  border-radius: 1rem;
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 700;
  color: #334155;
  transition: all 0.15s ease;
}
.menu-link:hover {
  background-color: #e2e8f0;
}
.dark .menu-link {
  color: #e2e8f0;
}
.dark .menu-link:hover {
  background-color: #06b6d4;
  color: #082f49;
}

.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.18s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>

<style>
html:not(.dark) .sidebar-link {
  background-color: #f8fafc !important;
  border-color: #cbd5e1 !important;
  color: #0f172a !important;
  box-shadow: 0 8px 20px rgba(148, 163, 184, 0.18) !important;
}

html:not(.dark) .sidebar-link:hover {
  background-color: #eef6ff !important;
  border-color: #7dd3fc !important;
  color: #0f172a !important;
}

html:not(.dark) .sidebar-link * {
  color: #0f172a !important;
}

html:not(.dark) .router-link-exact-active.sidebar-link {
  background-color: #e0f2fe !important;
  border-color: #38bdf8 !important;
  color: #0f172a !important;
  box-shadow: 0 12px 24px rgba(14, 165, 233, 0.18) !important;
}

html:not(.dark) .router-link-exact-active.sidebar-link * {
  color: #0f172a !important;
}

html.dark .sidebar-link {
  background-color: #020617 !important;
  border-color: #1e293b !important;
  color: #f8fafc !important;
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.28) !important;
}

html.dark .sidebar-link:hover {
  background-color: #0f172a !important;
  border-color: #334155 !important;
  color: #ffffff !important;
}

html.dark .sidebar-link * {
  color: #f8fafc !important;
}

html.dark .router-link-exact-active.sidebar-link {
  background-color: #082f49 !important;
  border-color: #22d3ee !important;
  color: #ecfeff !important;
  box-shadow: 0 12px 24px rgba(8, 145, 178, 0.24) !important;
}

html.dark .router-link-exact-active.sidebar-link * {
  color: #ecfeff !important;
}

html:not(.dark) .menu-link,
html:not(.dark) .menu-link * {
  color: #0f172a !important;
}

html.dark .menu-link,
html.dark .menu-link * {
  color: #f8fafc !important;
}

.sidebar-link .iconify,
.menu-link .iconify,
.icon-button .iconify {
  display: inline-block !important;
  width: 1.25rem !important;
  height: 1.25rem !important;
  flex-shrink: 0 !important;
}
</style>
