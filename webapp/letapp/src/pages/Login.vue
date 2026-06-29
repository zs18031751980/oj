<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { NAlert, NButton, NCheckbox, NInput, useMessage } from 'naive-ui';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const router = useRouter();
const message = useMessage();
const authStore = useAuthStore();

const identifier = ref('');
const password = ref('');
const remember = ref(true);
const isSubmitting = ref(false);
const loginError = ref('');

const safeNext = computed(() => {
  const nextValue = Array.isArray(route.query.next)
    ? String(route.query.next[0] || '/')
    : String(route.query.next || '/');
  return nextValue.startsWith('/') ? nextValue : '/';
});

const startClubLogin = () => {
  authStore.startOAuthLogin('iOSClub', safeNext.value, remember.value);
};

const handlePasswordLogin = async () => {
  const trimmedIdentifier = identifier.value.trim();

  if (!trimmedIdentifier) {
    loginError.value = '请输入学号或账号';
    return;
  }

  if (!password.value) {
    loginError.value = '请输入密码';
    return;
  }

  isSubmitting.value = true;
  loginError.value = '';

  try {
    await authStore.loginWithProviderPassword('iOSClub', trimmedIdentifier, password.value, remember.value);
    message.success('登录成功');
    await router.replace(safeNext.value);
  } catch (error) {
    loginError.value = error instanceof Error ? error.message : '登录失败，请稍后重试';
  } finally {
    isSubmitting.value = false;
  }
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

          <h1 class="mt-8 text-4xl font-black tracking-tight">登录后继续你的代码练习</h1>
          <p class="mt-5 text-base leading-8 text-slate-300">
            这里使用 iOSClub 账号完成身份验证。登录成功后会自动回到你刚才访问的页面。
          </p>

          <div class="mt-10 space-y-4">
            <div class="info-card">
              <Icon icon="material-symbols:verified-user" class="h-5 w-5 text-cyan-300" />
              <span>统一账号验证，减少重复注册和重复登录。</span>
            </div>
            <div class="info-card">
              <Icon icon="material-symbols:lock-open-right" class="h-5 w-5 text-cyan-300" />
              <span>登录成功后签发本站会话，可继续访问学习资源和练习页面。</span>
            </div>
            <div class="info-card">
              <Icon icon="material-symbols:route" class="h-5 w-5 text-cyan-300" />
              <span>完成后会自动返回你刚才访问的页面。</span>
            </div>
          </div>
        </div>
      </div>

      <div class="px-8 py-10 lg:px-10 lg:py-12">
        <div class="max-w-md">
          <p class="text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Secure Sign In</p>
          <h2 class="mt-3 text-3xl font-black tracking-tight">登录 Let Coding</h2>
          <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
            输入你的 iOSClub 账号和密码。
          </p>

          <div v-if="authStore.isAuthenticated" class="mt-8 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-5 text-sm leading-7 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100">
            当前已登录：<span class="font-black">{{ authStore.displayName }}</span>。如果需要切换账号，可以先退出再重新登录。
            <div class="mt-4">
              <NButton tertiary type="error" @click="handleLogout">退出当前账号</NButton>
            </div>
          </div>

          <form class="mt-8 space-y-5" @submit.prevent="handlePasswordLogin">
            <NAlert v-if="loginError" type="error" :bordered="false">
              {{ loginError }}
            </NAlert>

            <NInput
              v-model:value="identifier"
              size="large"
              placeholder="学号或账号"
              :input-props="{ autocomplete: 'username' }"
            >
              <template #prefix>
                <Icon icon="material-symbols:person-rounded" class="text-slate-400" />
              </template>
            </NInput>

            <NInput
              v-model:value="password"
              type="password"
              size="large"
              placeholder="密码"
              show-password-on="click"
              :input-props="{ autocomplete: 'current-password' }"
              @keyup.enter="handlePasswordLogin"
            >
              <template #prefix>
                <Icon icon="material-symbols:lock-rounded" class="text-slate-400" />
              </template>
            </NInput>

            <div class="flex items-center justify-between gap-4 text-sm">
              <NCheckbox v-model:checked="remember">记住登录状态</NCheckbox>
              <span class="truncate text-slate-500 dark:text-slate-400">返回：{{ safeNext }}</span>
            </div>

            <NButton
              block
              attr-type="submit"
              :loading="isSubmitting"
              :bordered="false"
              class="h-14 rounded-full bg-cyan-500 text-base font-black text-white hover:bg-cyan-400 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300"
            >
              <template #icon>
                <Icon icon="material-symbols:login" class="h-5 w-5" />
              </template>
              登录
            </NButton>
          </form>

          <NButton
            block
            tertiary
            class="mt-4 h-12 rounded-full"
            @click="startClubLogin"
          >
            <template #icon>
              <Icon icon="material-symbols:open-in-new" class="h-5 w-5" />
            </template>
            使用 OAuth 页面登录
          </NButton>
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
