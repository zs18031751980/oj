<template>
  <div
    class="min-h-screen bg-[#F6F8FC] text-[#1E293B] transition-colors duration-300 dark:bg-[#0F172A] dark:text-[#E5E7EB]"
    :style="{ '--header-h': '4rem' }"
  >
    <header
      class="fixed inset-x-0 top-0 z-50 h-[var(--header-h,4rem)] border-b border-[#E2E8F0] bg-[#F6F8FC]/90 backdrop-blur-xl transition-colors dark:border-[#1E293B] dark:bg-[#0F172A]/90"
    >
      <div
        class="mx-auto flex h-full max-w-[1440px] items-center gap-4 px-4 sm:px-6 lg:px-8"
      >
        <a href="https://www.xauat.site/" target="_blank" rel="noopener" class="flex shrink-0 items-center gap-2.5">
          <img
            src="/assets/logo.png"
            alt="Let Coding Logo"
            class="h-9 w-9 rounded-xl object-cover shadow-sm"
          />
          <span class="text-lg font-black tracking-tight">Let Coding</span>
        </a>

        <nav
          class="hidden shrink items-center gap-1 md:flex"
        >
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-link"
            :class="{ 'nav-link-active': isActive(item.to) }"
            @click="closeMenu"
          >
            <Icon :icon="item.icon" class="h-5 w-5 shrink-0" />
            <span>{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="flex flex-1 items-center justify-end gap-2">
          <div class="relative hidden xl:flex">
            <Icon icon="material-symbols:search-rounded" class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
            <input
              v-model="globalSearchQuery"
              type="text"
              placeholder="搜索题目…"
              class="h-10 w-48 rounded-lg border border-[#E2E8F0] bg-white pl-9 pr-3 text-sm text-[#1E293B] outline-none transition focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/30 dark:border-[#1E293B] dark:bg-[#0F172A] dark:text-[#E5E7EB] dark:placeholder-[#64748B]"
              @keydown.enter="goSearch"
            />
          </div>
          <button
            class="ui-icon-btn xl:hidden"
            aria-label="搜索"
            @click="router.push('/problems')"
          >
            <Icon icon="material-symbols:search-rounded" class="h-5 w-5" />
          </button>
          <button
            class="ui-icon-btn"
            :aria-label="isDark ? '切换到浅色模式' : '切换到深色模式'"
            @click="mainToggleTheme"
          >
            <Icon
              v-if="!isDark"
              icon="material-symbols:light-mode"
              class="h-5 w-5 text-[#F59E0B]"
            />
            <Icon
              v-else
              icon="material-symbols:dark-mode"
              class="h-5 w-5 text-[#60A5FA]"
            />
          </button>

          <button
            v-if="!authStore.isAuthenticated"
            class="ui-btn ui-btn-primary ui-btn-sm"
            @click="startClubLogin"
          >
            登录
          </button>
          <div v-else class="relative">
            <button
              class="ui-btn ui-btn-secondary ui-btn-sm"
              :aria-expanded="userMenuVisible"
              aria-label="个人中心"
              @click.stop="userMenuVisible = !userMenuVisible"
            >
              <Icon icon="material-symbols:person-rounded" class="h-4 w-4" />
              <span class="max-w-[8rem] truncate">{{ authStore.displayName }}</span>
              <Icon
                :icon="
                  userMenuVisible
                    ? 'material-symbols:keyboard-arrow-up'
                    : 'material-symbols:keyboard-arrow-down'
                "
                class="h-4 w-4"
              />
            </button>

            <transition name="dropdown-fade">
              <div v-if="userMenuVisible" class="user-dropdown">
                <button
                  class="user-dropdown-item"
                  @click="goUserPage('/profile')"
                >
                  <Icon icon="material-symbols:person-rounded" class="h-4 w-4" />
                  <span>个人中心</span>
                </button>
                <div class="user-dropdown-divider"></div>
                <button
                  class="user-dropdown-item"
                  @click="goUserPage('/submissions')"
                >
                  <Icon icon="material-symbols:history-rounded" class="h-4 w-4" />
                  <span>题目提交记录</span>
                </button>
                <button
                  class="user-dropdown-item"
                  @click="goUserPage('/favorites')"
                >
                  <Icon icon="material-symbols:star-rounded" class="h-4 w-4" />
                  <span>收藏题目</span>
                </button>
                <div class="user-dropdown-divider"></div>
                <button
                  class="user-dropdown-item user-dropdown-logout"
                  @click="handleLogout"
                >
                  <Icon icon="material-symbols:logout" class="h-4 w-4" />
                  <span>退出登录</span>
                </button>
              </div>
            </transition>
          </div>

          <button
            class="ui-icon-btn md:hidden"
            aria-label="打开导航菜单"
            :aria-expanded="menuVisible"
            @click.stop="menuVisible = !menuVisible"
          >
            <Icon
              :icon="
                menuVisible
                  ? 'material-symbols:close-rounded'
                  : 'material-symbols:menu-rounded'
              "
              class="h-6 w-6"
            />
          </button>
        </div>
      </div>
    </header>

    <transition name="drawer-backdrop">
      <div
        v-if="menuVisible"
        class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden"
        aria-label="关闭导航菜单"
        @click="closeMenu"
      ></div>
    </transition>
    <transition name="drawer-slide">
      <aside
        v-if="menuVisible"
        class="mobile-drawer md:hidden"
        aria-label="导航菜单"
      >
        <div class="drawer-heading">
          <div class="flex items-center gap-3">
            <img
              src="/assets/logo.png"
              alt="Let Coding Logo"
              class="h-10 w-10 rounded-xl object-cover"
            />
            <div>
              <div class="font-black">Let Coding</div>
              <div class="text-[10px] uppercase text-[#94A3B8]">Online Judge</div>
            </div>
          </div>
          <button class="ui-icon-btn" aria-label="关闭导航菜单" @click="closeMenu">
            <Icon icon="material-symbols:close-rounded" />
          </button>
        </div>
        <nav class="drawer-nav">
          <button
            v-for="item in navItems"
            :key="`${item.to}-menu`"
            type="button"
            class="drawer-link"
            :class="{ 'drawer-link-active': isActive(item.to) }"
            @click="navigateFromMenu(item.to)"
          >
            <Icon :icon="item.icon" class="h-5 w-5 shrink-0" />
            <span>{{ item.label }}</span>
          </button>
        </nav>
      </aside>
    </transition>

    <main class="pt-16">
      <router-view v-slot="{ Component, route }">
        <transition name="page-shift" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Icon } from "@iconify/vue";
import { storeToRefs } from "pinia";
import { markRaw } from "vue";
import { useThemeStore } from "../stores/theme";
import { useAuthStore } from "../stores/auth";

const navItems = markRaw([
  { label: "首页", to: "/", icon: "material-symbols:home-rounded" },
  { label: "题库", to: "/problems", icon: "material-symbols:library-books-rounded" },
  { label: "学习", to: "/learn", icon: "material-symbols:school-rounded" },
  { label: "在线编辑器", to: "/playground", icon: "material-symbols:code-rounded" },
  { label: "比赛", to: "/contests", icon: "material-symbols:trophy-rounded" },
  { label: "排行榜", to: "/rankings", icon: "material-symbols:leaderboard-rounded" },
  { label: "讨论", to: "/discussion", icon: "material-symbols:forum" },
  { label: "公告", to: "/announcements", icon: "material-symbols:campaign" },
]);

const router = useRouter();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const { isDark } = storeToRefs(themeStore);
const { toggleTheme } = themeStore;

const menuVisible = ref(false);
const userMenuVisible = ref(false);
const globalSearchQuery = ref('');

const goSearch = () => {
  const q = globalSearchQuery.value.trim();
  if (!q) return;
  router.push({ path: '/problems', query: { q } });
  globalSearchQuery.value = '';
};

const currentPath = computed(() => router.currentRoute.value.path);
const isActive = (to: string) =>
  to === "/" ? currentPath.value === "/" : currentPath.value.startsWith(to);

const closeMenu = () => {
  menuVisible.value = false;
  document.body.style.overflow = "";
};

const toggleMenuLock = () => {
  document.body.style.overflow = menuVisible.value ? "hidden" : "";
};

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    closeMenu();
    userMenuVisible.value = false;
  }
};

const mainToggleTheme = () => {
  toggleTheme();
  closeMenu();
};

const startClubLogin = () => {
  closeMenu();
  authStore.startOAuthLogin(
    "iOSClub",
    router.currentRoute.value.fullPath,
    true,
  );
};

const handleLogout = async () => {
  closeMenu();
  userMenuVisible.value = false;
  await authStore.logout();
};

const goUserPage = async (to: string) => {
  userMenuVisible.value = false;
  await router.push(to);
};

const navigateFromMenu = async (to: string) => {
  closeMenu();
  await router.push(to);
};

const handleWindowClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null;
  if (
    !target?.closest(".ui-icon-btn") &&
    !target?.closest(".user-dropdown") &&
    !target?.closest(".ui-btn")
  ) {
    userMenuVisible.value = false;
  }
};

onMounted(() => {
  window.addEventListener("click", handleWindowClick);
  window.addEventListener("resize", closeMenu);
  window.addEventListener("keydown", handleEscape);
});

onUnmounted(() => {
  window.removeEventListener("click", handleWindowClick);
  window.removeEventListener("resize", closeMenu);
  window.removeEventListener("keydown", handleEscape);
  document.body.style.overflow = "";
});

watch(menuVisible, toggleMenuLock);
</script>

<style scoped>
@reference 'tailwindcss';

.nav-link {
  @apply relative flex h-16 items-center gap-1.5 px-4 text-sm font-semibold text-[#475569] transition-colors dark:text-[#94A3B8];
}
.nav-link:hover {
  @apply text-[#2563EB] dark:text-[#60A5FA];
}
.nav-link-active {
  @apply text-[#2563EB] dark:text-[#60A5FA];
}
.nav-link-active::after {
  content: "";
  @apply absolute bottom-0 left-1/2 h-0.5 w-10 -translate-x-1/2 rounded-full bg-[#2563EB] dark:bg-[#60A5FA];
}

.user-dropdown {
  @apply absolute right-0 top-[calc(100%+0.5rem)] z-60 grid min-w-[13rem] gap-1 rounded-2xl border border-[#E2E8F0] bg-white/95 p-2 shadow-xl backdrop-blur-xl dark:border-[#1E293B] dark:bg-[#111827]/95;
}
.user-dropdown-item {
  @apply flex w-full items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-left text-sm font-bold text-[#334155] transition-colors dark:text-[#E5E7EB];
}
.user-dropdown-item:hover {
  @apply bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA];
}
.user-dropdown-divider {
  @apply my-1 h-px bg-[#E2E8F0] dark:bg-[#1E293B];
}
.user-dropdown-logout:hover {
  @apply bg-[#FEF2F2] text-[#DC2626] dark:bg-[#450A0A] dark:text-[#FCA5A5];
}

.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: all 0.18s ease;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

.mobile-drawer {
  @apply fixed right-0 top-0 z-50 flex h-full w-[20rem] max-w-[88vw] flex-col border-l border-[#E2E8F0] bg-white shadow-2xl dark:border-[#1E293B] dark:bg-[#111827];
}
.drawer-heading {
  @apply flex h-16 items-center justify-between border-b border-[#E2E8F0] px-4 dark:border-[#1E293B];
}
.drawer-nav {
  @apply grid gap-1 p-3;
}
.drawer-link {
  @apply flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold text-[#334155] transition-colors dark:text-[#E5E7EB];
}
.drawer-link:hover {
  @apply bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA];
}
.drawer-link-active {
  @apply bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA];
}

.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: translateX(100%);
}
.drawer-backdrop-enter-active,
.drawer-backdrop-leave-active {
  transition: opacity 0.3s ease;
}
.drawer-backdrop-enter-from,
.drawer-backdrop-leave-to {
  opacity: 0;
}

.page-shift-enter-active,
.page-shift-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}
.page-shift-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-shift-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
