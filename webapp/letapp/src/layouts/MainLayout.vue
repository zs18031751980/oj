<template>
  <div class="min-h-screen bg-slate-50 text-slate-950 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-50">
    <n-layout has-sider class="min-h-screen bg-transparent">
      <aside
        class="fixed left-0 top-0 z-50 hidden h-screen flex-col border-r border-white/70 bg-white/88 shadow-2xl shadow-slate-200/60 backdrop-blur-2xl transition-all duration-300 dark:border-slate-800/80 dark:bg-slate-950/88 dark:shadow-black/30 md:flex"
        :class="sidebarExpanded ? 'w-72' : 'w-24'"
      >
        <div class="flex h-20 items-center justify-between px-5" :class="sidebarExpanded ? 'gap-3' : 'justify-center'">
          <router-link to="/" class="group flex min-w-0 items-center gap-3 overflow-hidden" @click="closeMenu">
            <span class="relative grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-slate-950 shadow-lg shadow-cyan-500/15 dark:bg-white">
              <img src="/assets/logo.png" alt="Let Coding Logo" class="h-8 w-8 transition-transform group-hover:scale-110" />
            </span>
            <div v-if="sidebarExpanded" class="min-w-0">
              <div class="truncate text-lg font-black tracking-tight">Let Coding</div>
              <div class="-mt-1 text-[11px] font-medium uppercase tracking-[0.24em] text-slate-400">Online Judge</div>
            </div>
          </router-link>

          <button
            v-if="sidebarExpanded"
            class="sidebar-toggle"
            aria-label="收起侧边栏"
            @click="toggleSidebar"
          >
            <Icon icon="material-symbols:left-panel-close-rounded" class="h-5 w-5" />
          </button>
        </div>

        <div class="px-4 pb-4" :class="sidebarExpanded ? '' : 'flex justify-center'">
          <button
            v-if="!sidebarExpanded"
            class="sidebar-toggle"
            aria-label="展开侧边栏"
            @click="toggleSidebar"
          >
            <Icon icon="material-symbols:right-panel-open-rounded" class="h-5 w-5" />
          </button>
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
      </aside>

      <n-layout>
        <n-layout-header
          class="fixed left-0 right-0 top-0 z-40 border-b border-white/60 bg-white/86 shadow-sm shadow-slate-200/40 backdrop-blur-2xl transition-all duration-300 dark:border-slate-800/80 dark:bg-slate-950/86 dark:shadow-black/20"
          :class="{ 'header-compact': isScrolled }"
        >
          <div
            class="h-auto min-h-20 w-full px-3 py-3 sm:px-4 lg:px-6"
            :style="headerPaddingStyle"
          >
            <div class="flex min-h-14 w-full min-w-0 items-center justify-between gap-3">
              <router-link to="/" class="flex min-w-0 items-center gap-3 md:hidden" @click="closeMenu">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-slate-950 dark:bg-white">
                  <img src="/assets/logo.png" alt="Let Coding Logo" class="h-7 w-7" />
                </span>
                <span class="truncate text-base font-black">Let Coding</span>
              </router-link>

              <div class="ml-auto flex min-w-0 items-center justify-end gap-2 sm:gap-3">
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
        </n-layout-header>

        <n-layout-content class="transition-all duration-300" :style="contentPaddingStyle">
          <div class="pt-20">
            <router-view />
          </div>
        </n-layout-content>
      </n-layout>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { NLayout, NLayoutContent, NLayoutHeader } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { storeToRefs } from 'pinia';
import { useThemeStore } from '../stores/theme';
import { useAuthStore } from '../stores/auth';

const navItems = [
  { label: '首页', to: '/', icon: 'material-symbols:home-rounded' },
  { label: '在线编辑器', to: '/playground', icon: 'material-symbols:code-rounded' },
  { label: '学习资源', to: '/learn', icon: 'material-symbols:school-rounded' },
];

const DESKTOP_EXPANDED_WIDTH = 288;
const DESKTOP_COLLAPSED_WIDTH = 96;

const router = useRouter();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const { isDark } = storeToRefs(themeStore);
const { toggleTheme } = themeStore;

const sidebarExpanded = ref(true);
const menuVisible = ref(false);
const isScrolled = ref(false);
const isDesktop = ref(false);

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

const handleScroll = () => {
  isScrolled.value = window.scrollY > 10;
};

const handleWindowClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null;
  if (!target?.closest('.icon-button') && !target?.closest('.menu-link')) {
    closeMenu();
  }
};

onMounted(() => {
  updateViewportFlags();
  window.addEventListener('scroll', handleScroll);
  window.addEventListener('click', handleWindowClick);
  window.addEventListener('resize', updateViewportFlags);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  window.removeEventListener('click', handleWindowClick);
  window.removeEventListener('resize', updateViewportFlags);
});
</script>

<style scoped>
@reference 'tailwindcss';

.header-compact {
  @apply shadow-lg shadow-slate-200/60 dark:shadow-black/30;
}

.sidebar-toggle {
  @apply grid h-10 w-10 place-items-center rounded-2xl text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white;
}

.sidebar-link {
  @apply flex h-13 items-center gap-3 rounded-2xl text-sm font-bold text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white;
}

.router-link-active.sidebar-link {
  @apply bg-slate-950 text-white shadow-lg shadow-slate-900/15 dark:bg-white dark:text-slate-950;
}

.primary-pill {
  @apply inline-flex h-11 items-center rounded-full bg-cyan-500 px-4 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/25 transition hover:-translate-y-0.5 hover:bg-cyan-300 sm:px-5;
}

.secondary-pill {
  @apply inline-flex h-11 max-w-[16rem] items-center rounded-full bg-slate-100 px-4 text-sm font-bold text-slate-800 transition hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 sm:px-5;
}

.icon-button {
  @apply grid h-11 w-11 shrink-0 place-items-center rounded-full text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800;
}

.menu-link {
  @apply flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-bold text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800;
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
