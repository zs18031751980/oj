<template>
  <div class="min-h-screen bg-white dark:bg-black transition-colors duration-300">
    <n-layout>
      <n-layout-header
        class="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-black/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800"
        :class="{ 'shadow-md': isScrolled }"
      >
        <div class="mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex items-center justify-between h-16">
            <router-link to="/" class="flex items-center gap-3 group">
              <img
                src="/assets/logo.png"
                alt="Let Coding Logo"
                class="w-8 h-8 transition-transform group-hover:scale-105"
              />
              <div class="text-lg font-semibold text-gray-900 dark:text-gray-100 hidden sm:block">
                Let Coding
              </div>
            </router-link>

<<<<<<< HEAD
            <nav class="hidden md:flex items-center space-x-1">
              <router-link class="nav-link" to="/">首页</router-link>
              <router-link class="nav-link" to="/learn">学习</router-link>
              <router-link class="nav-link" to="/playground">代码编辑器</router-link>

              <button
                v-if="!authStore.isAuthenticated"
                class="ml-4 px-4 py-2 bg-blue-500 text-white text-sm font-medium rounded-full hover:bg-blue-600 transition-colors"
                @click="startClubLogin"
              >
                登录
              </button>
=======
            <!-- Desktop Menu -->
            <nav class="hidden md:flex items-center space-x-6">
              <!-- 导航链接 -->
              <router-link 
                to="/" 
                class="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                首页
              </router-link>
              <router-link 
                to="/playground" 
                class="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                在线编辑
              </router-link>
              <router-link 
                to="/learn" 
                class="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                学习资源
              </router-link>

              <!-- Login/Register or Logout Button -->
              <router-link
                to="/login"
                class="ml-4 px-4 py-2 bg-blue-500 text-white text-sm font-medium rounded-full hover:bg-blue-600 transition-colors"
              >
                登录/注册
              </router-link>
              <!--              <button-->
              <!--                  v-else-->
              <!--                  class="ml-4 px-4 py-2 bg-blue-500 text-white text-sm font-medium rounded-full hover:bg-blue-600 transition-colors"-->
              <!--                  @click="toCentre"-->
              <!--              >-->
              <!--                进入中心-->
              <!--              </button>-->

              <!-- Theme Toggle -->
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
              <button
                v-else
                class="ml-4 px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm font-medium rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                @click="handleLogout"
              >
                退出：{{ authStore.displayName }}
              </button>

              <button
                class="ml-2 w-9 h-9 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                aria-label="切换主题"
                @click="mainToggleTheme"
              >
                <Icon
                  v-if="!isDark"
                  icon="material-symbols:light-mode"
                  class="h-5 w-5 text-yellow-500"
                />
                <Icon v-else icon="material-symbols:dark-mode" class="h-5 w-5 text-blue-400" />
              </button>
            </nav>

            <button
              class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              @click="drawerVisible = !drawerVisible"
            >
              <Icon
                v-if="!drawerVisible"
                icon="material-symbols:menu"
                class="text-gray-900 dark:text-gray-100"
                width="20"
                height="20"
              />
              <Icon
                v-else
                icon="material-symbols:close"
                class="text-gray-900 dark:text-gray-100"
                width="20"
                height="20"
              />
            </button>
          </div>
        </div>
      </n-layout-header>

      <n-layout-content class="pt-16">
<<<<<<< HEAD
        <transition name="slide-down">
          <div
            v-if="drawerVisible"
            class="fixed inset-0 z-40 bg-white dark:bg-black pt-16"
          >
            <div class="px-4 py-1 space-y-0.5">
              <router-link to="/" class="mobile-link" @click="drawerVisible = false">
                首页
              </router-link>
              <router-link to="/learn" class="mobile-link" @click="drawerVisible = false">
                学习
              </router-link>
              <router-link to="/playground" class="mobile-link" @click="drawerVisible = false">
                代码编辑器
              </router-link>

              <div class="pt-1.5 border-t border-gray-200 dark:border-gray-800">
                <button
                  v-if="!authStore.isAuthenticated"
                  class="w-full px-4 py-2.5 bg-blue-500 text-white text-base font-medium rounded-lg hover:bg-blue-600 transition-colors"
                  @click="startClubLogin"
                >
                  登录
                </button>
                <button
                  v-else
                  class="w-full px-4 py-2.5 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-base font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  @click="() => { handleLogout(); drawerVisible = false }"
                >
                  退出：{{ authStore.displayName }}
                </button>
=======
        <!-- Mobile Drawer Menu -->
            <transition name="slide-down">
              <div
                  v-if="drawerVisible"
                  class="fixed inset-0 z-40 bg-white dark:bg-black pt-16"
              >
                <div class="px-4 py-1 space-y-0.5">
                  <router-link
                      to="/"
                      class="block px-4 py-2.5 text-base font-medium text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                      @click="drawerVisible = false"
                  >
                    首页
                  </router-link>
                  <router-link
                      to="/playground"
                      class="block px-4 py-2.5 text-base font-medium text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                      @click="drawerVisible = false"
                  >
                    在线编辑
                  </router-link>
                  <router-link
                      to="/learn"
                      class="block px-4 py-2.5 text-base font-medium text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                      @click="drawerVisible = false"
                  >
                    学习资源
                  </router-link>

                  <div class="pt-1.5 border-t border-gray-200 dark:border-gray-800">
                    <router-link
                        to="/login"
                        class="block w-full px-4 py-2.5 bg-blue-500 text-white text-base font-medium rounded-lg hover:bg-blue-600 transition-colors"
                        @click="drawerVisible = false"
                    >
                      登录/注册
                    </router-link>
                <!--                <button-->
                <!--                    v-else-->
                <!--                    class="w-full px-4 py-2.5 bg-blue-500 text-white text-base font-medium rounded-lg hover:bg-blue-600 transition-colors"-->
                <!--                    @click="logout"-->
                <!--                >-->
                <!--                  退出登录-->
                <!--                </button>-->
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018

                <button
                  class="mt-1.5 w-full px-4 py-2.5 flex items-center justify-center gap-2 text-base font-medium text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  @click="mainToggleTheme"
                >
                  <Icon
                    v-if="!isDark"
                    icon="material-symbols:light-mode"
                    class="h-5 w-5 text-yellow-500"
                  />
                  <Icon v-else icon="material-symbols:dark-mode" class="h-5 w-5 text-blue-400" />
                  {{ isDark ? '浅色模式' : '深色模式' }}
                </button>
              </div>
            </div>
          </div>
        </transition>

        <div class="flex-1">
          <router-view />
        </div>
      </n-layout-content>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
<<<<<<< HEAD
import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { NLayout, NLayoutContent, NLayoutHeader } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { storeToRefs } from 'pinia';
import { useThemeStore } from '../stores/theme';
import { useAuthStore } from '../stores/auth';
=======
import { ref, onMounted, onUnmounted } from 'vue'
// import { useRouter } from 'vue-router' // 未使用，注释掉
// import { useAuthorizationStore } from '../stores/Authorization'
import {NLayout, NLayoutHeader, NLayoutContent} from 'naive-ui'
import {Icon} from '@iconify/vue'
import {useThemeStore} from '../stores/theme'
import {storeToRefs} from 'pinia'
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018

const themeStore = useThemeStore();
const authStore = useAuthStore();
const { isDark } = storeToRefs(themeStore);
const { toggleTheme } = themeStore;

const router = useRouter();
const drawerVisible = ref(false);
const isScrolled = ref(false);

const mainToggleTheme = () => {
  toggleTheme();
};

<<<<<<< HEAD
const startClubLogin = () => {
  drawerVisible.value = false;
  authStore.startOAuthLogin('iOSClub', router.currentRoute.value.fullPath, true);
};
=======
// const router = useRouter() // 未使用，注释掉
const drawerVisible = ref(false)
const isScrolled = ref(false)
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018

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

.nav-link {
  @apply px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors;
}

.mobile-link {
  @apply block px-4 py-2.5 text-base font-medium text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
