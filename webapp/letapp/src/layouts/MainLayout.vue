<template>
  <div class="min-h-screen bg-slate-50 text-slate-950 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-50">
    <n-layout>
      <n-layout-header
        class="fixed left-0 right-0 top-0 z-50 border-b border-white/60 bg-white/80 shadow-sm shadow-slate-200/40 backdrop-blur-2xl transition-all dark:border-slate-800/80 dark:bg-slate-950/78 dark:shadow-black/20"
        :class="{ 'header-compact': isScrolled }"
      >
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="flex h-16 items-center justify-between">
            <router-link to="/" class="group flex items-center gap-3" @click="drawerVisible = false">
              <span class="relative grid h-10 w-10 place-items-center rounded-2xl bg-slate-950 shadow-lg shadow-cyan-500/15 dark:bg-white">
                <img src="/assets/logo.png" alt="Let Coding Logo" class="h-7 w-7 transition-transform group-hover:scale-110" />
              </span>
              <div class="hidden sm:block">
                <div class="text-base font-black tracking-tight">Let Coding</div>
                <div class="-mt-1 text-[11px] font-medium uppercase tracking-[0.24em] text-slate-400">Online Judge</div>
              </div>
            </router-link>

            <nav class="hidden items-center gap-2 md:flex">
              <router-link v-for="item in navItems" :key="item.to" class="nav-link" :to="item.to">
                {{ item.label }}
              </router-link>

              <button v-if="!authStore.isAuthenticated" class="primary-pill ml-3" @click="startClubLogin">
                登录
              </button>
              <button v-else class="secondary-pill ml-3" @click="handleLogout">
                退出：{{ authStore.displayName }}
              </button>

              <button class="icon-button" :aria-label="isDark ? '切换到浅色模式' : '切换到深色模式'" @click="mainToggleTheme">
                <Icon v-if="!isDark" icon="material-symbols:light-mode" class="h-5 w-5 text-amber-500" />
                <Icon v-else icon="material-symbols:dark-mode" class="h-5 w-5 text-cyan-300" />
              </button>
            </nav>

            <button class="icon-button md:hidden" aria-label="打开导航菜单" @click="drawerVisible = !drawerVisible">
              <Icon :icon="drawerVisible ? 'material-symbols:close' : 'material-symbols:menu'" class="h-6 w-6" />
            </button>
          </div>
        </div>
      </n-layout-header>

      <n-layout-content class="pt-16">
        <transition name="slide-down">
          <div v-if="drawerVisible" class="fixed inset-0 z-40 bg-slate-50/98 pt-20 backdrop-blur-xl dark:bg-slate-950/98 md:hidden">
            <div class="mx-4 rounded-[2rem] border border-white/70 bg-white p-3 shadow-2xl shadow-slate-200/80 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/40">
              <router-link v-for="item in navItems" :key="item.to" :to="item.to" class="mobile-link" @click="drawerVisible = false">
                <Icon :icon="item.icon" class="h-5 w-5" />
                {{ item.label }}
              </router-link>

              <div class="mt-3 border-t border-slate-200 pt-3 dark:border-slate-800">
                <button v-if="!authStore.isAuthenticated" class="primary-pill w-full justify-center" @click="startClubLogin">
                  登录 Let Coding
                </button>
                <button v-else class="secondary-pill w-full justify-center" @click="() => { handleLogout(); drawerVisible = false }">
                  退出：{{ authStore.displayName }}
                </button>
                <button class="mobile-link mt-2 w-full" @click="mainToggleTheme">
                  <Icon :icon="isDark ? 'material-symbols:dark-mode' : 'material-symbols:light-mode'" class="h-5 w-5" />
                  {{ isDark ? '深色模式' : '浅色模式' }}
                </button>
              </div>
            </div>
          </div>
        </transition>

        <router-view />
      </n-layout-content>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { NLayout, NLayoutContent, NLayoutHeader } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { storeToRefs } from 'pinia';
import { useThemeStore } from '../stores/theme';
import { useAuthStore } from '../stores/auth';

const navItems = [
  { label: '首页', to: '/', icon: 'material-symbols:home' },
  { label: '在线编辑器', to: '/playground', icon: 'material-symbols:code' },
  { label: '学习资源', to: '/learn', icon: 'material-symbols:school' },
];

const router = useRouter();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const { isDark } = storeToRefs(themeStore);
const { toggleTheme } = themeStore;

const drawerVisible = ref(false);
const isScrolled = ref(false);

const mainToggleTheme = () => {
  toggleTheme();
};

const startClubLogin = () => {
  drawerVisible.value = false;
  authStore.startOAuthLogin('iOSClub', router.currentRoute.value.fullPath, true);
};

const handleLogout = async () => {
  await authStore.logout();
};

const handleScroll = () => {
  isScrolled.value = window.scrollY > 10;
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<style scoped>
@reference 'tailwindcss';

.header-compact {
  @apply shadow-lg shadow-slate-200/60 dark:shadow-black/30;
}

.nav-link {
  @apply rounded-full px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white;
}

.router-link-active.nav-link {
  @apply bg-slate-950 text-white shadow-lg shadow-slate-900/15 dark:bg-white dark:text-slate-950;
}

.primary-pill {
  @apply inline-flex items-center rounded-full bg-cyan-500 px-5 py-2.5 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/25 transition hover:-translate-y-0.5 hover:bg-cyan-300;
}

.secondary-pill {
  @apply inline-flex items-center rounded-full bg-slate-100 px-5 py-2.5 text-sm font-bold text-slate-800 transition hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700;
}

.icon-button {
  @apply grid h-10 w-10 place-items-center rounded-full text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800;
}

.mobile-link {
  @apply flex items-center gap-3 rounded-2xl px-4 py-3 text-base font-bold text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.22s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
