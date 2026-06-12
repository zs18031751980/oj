<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { Icon } from '@iconify/vue';
import { NButton } from 'naive-ui';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const authStore = useAuthStore();

const safeNext = computed(() => {
  const nextValue = Array.isArray(route.query.next)
    ? String(route.query.next[0] || '/')
    : String(route.query.next || '/');
  return nextValue.startsWith('/') ? nextValue : '/';
});

const startClubLogin = () => {
  authStore.startOAuthLogin('iOSClub', safeNext.value, true);
};

const handleLogout = async () => {
  await authStore.logout();
};
</script>

<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),_transparent_30%),linear-gradient(180deg,_#ecfeff_0%,_#f8fafc_100%)] px-4 py-12 text-slate-950 dark:bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.12),_transparent_26%),linear-gradient(180deg,_#020617_0%,_#020617_100%)] dark:text-slate-50 sm:px-6 lg:px-8">
    <div class="mx-auto flex w-full max-w-5xl flex-col overflow-hidden rounded-[2rem] border border-white/80 bg-white/80 shadow-2xl shadow-slate-200/70 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80 dark:shadow-black/30 lg:grid lg:grid-cols-[0.95fr_1.05fr]">
      <div class="relative overflow-hidden bg-slate-950 px-8 py-10 text-white dark:bg-slate-900 lg:px-10 lg:py-12">
        <div class="absolute -left-10 top-12 h-32 w-32 rounded-full bg-cyan-400/20 blur-3xl"></div>
        <div class="absolute bottom-0 right-0 h-40 w-40 rounded-full bg-amber-300/10 blur-3xl"></div>

        <div class="relative">
          <div class="inline-flex items-center gap-3 rounded-full bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-[0.22em] text-cyan-200">
            <img src="/assets/logo.png" alt="Let Coding" class="h-6 w-6" />
            Let Coding Access
          </div>

          <h1 class="mt-8 text-4xl font-black tracking-tight">登录之后，你就能把练习和身份体系接起来。</h1>
          <p class="mt-5 text-base leading-8 text-slate-300">
            这里使用社团统一认证登录。登录完成后会自动回到你刚才访问的页面，不需要手动再跳一次。
          </p>

          <div class="mt-10 space-y-4">
            <div class="info-card">
              <Icon icon="material-symbols:verified-user" class="h-5 w-5 text-cyan-300" />
              <span>统一 OAuth 登录，减少重复注册。</span>
            </div>
            <div class="info-card">
              <Icon icon="material-symbols:history" class="h-5 w-5 text-cyan-300" />
              <span>登录后可保持会话，方便后续扩展保存与个性化功能。</span>
            </div>
            <div class="info-card">
              <Icon icon="material-symbols:route" class="h-5 w-5 text-cyan-300" />
              <span>回调成功后自动返回原页面，流程更顺畅。</span>
            </div>
          </div>
        </div>
      </div>

      <div class="px-8 py-10 lg:px-10 lg:py-12">
        <div class="max-w-md">
          <p class="text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Secure Sign In</p>
          <h2 class="mt-3 text-3xl font-black tracking-tight">登录 Let Coding</h2>
          <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
            点击下面的按钮后，会跳转到社团官网的统一认证页面。认证完成后会自动返回当前站点。
          </p>

          <div v-if="authStore.isAuthenticated" class="mt-8 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-5 text-sm leading-7 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100">
            当前已登录：<span class="font-black">{{ authStore.displayName }}</span>。如果需要切换账号，可以先退出再重新登录。
            <div class="mt-4">
              <NButton tertiary type="error" @click="handleLogout">退出当前账号</NButton>
            </div>
          </div>

          <div class="mt-8 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5 text-sm leading-7 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
            登录将沿用你当前访问路径作为返回地址：
            <code class="mt-2 block rounded-xl bg-white px-3 py-2 text-sm font-bold text-slate-800 dark:bg-slate-950 dark:text-slate-100">{{ safeNext }}</code>
          </div>

          <NButton
            block
            :bordered="false"
            class="mt-8 h-14 rounded-full bg-slate-950 text-base font-black text-white hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300"
            @click="startClubLogin"
          >
            <template #icon>
              <Icon icon="material-symbols:login" class="h-5 w-5" />
            </template>
            使用社团统一认证登录
          </NButton>

          <p class="mt-6 text-sm text-slate-500 dark:text-slate-400">
            登录完成后会自动返回你原本访问的页面。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.info-card {
  @apply flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-sm leading-7 text-slate-200;
}
</style>
