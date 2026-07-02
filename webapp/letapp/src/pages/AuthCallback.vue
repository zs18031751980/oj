<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { NButton, useMessage } from 'naive-ui';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const router = useRouter();
const message = useMessage();
const authStore = useAuthStore();

const statusText = ref('正在完成登录，请稍候...');
const detailText = ref('');
const retryNext = ref('/');
const loginFailed = ref(false);

const sanitizeNext = (value: unknown) => {
  const next = Array.isArray(value) ? String(value[0] ?? '/') : String(value || '/');
  return next.startsWith('/') ? next : '/';
};

const resolveNextPath = () => {
  const queryNext = sanitizeNext(route.query.next);
  if (queryNext !== '/') {
    return queryNext;
  }

  return sanitizeNext(sessionStorage.getItem('oauth_login_next'));
};

const retryLogin = () => {
  authStore.startOAuthLogin('iOSClub', retryNext.value, true);
};

onMounted(async () => {
  retryNext.value = resolveNextPath();

  try {
    authStore.completeOAuthCallback(route.query);
    message.success('登录成功');
    await router.replace(retryNext.value);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '登录失败，请稍后重试。';
    const provider = Array.isArray(route.query.provider)
      ? String(route.query.provider[0] ?? '')
      : String(route.query.provider ?? '');

    statusText.value = errorMessage;
    detailText.value = provider
      ? `登录提供方：${provider}。如果持续失败，说明问题很可能出在第三方统一认证页面或其会话服务。`
      : '如果持续失败，说明问题很可能出在第三方统一认证页面或其会话服务。';
    loginFailed.value = true;
    message.error(errorMessage);
  }
});
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <div class="flex max-w-lg flex-col items-center gap-4 rounded-[2rem] border border-slate-200 bg-white/80 px-6 py-6 text-center shadow-lg shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/80 dark:shadow-black/20">
      <Icon
        :icon="loginFailed ? 'material-symbols:error-outline-rounded' : 'material-symbols:progress-activity'"
        class="h-8 w-8"
        :class="loginFailed ? 'text-rose-500' : 'animate-spin text-cyan-500'"
      />
      <span class="text-sm font-bold">{{ statusText }}</span>
      <p v-if="detailText" class="max-w-md text-xs leading-6 text-slate-500 dark:text-slate-400">
        {{ detailText }}
      </p>
      <div v-if="loginFailed" class="flex flex-wrap justify-center gap-3">
        <NButton type="primary" @click="retryLogin">重新登录</NButton>
        <NButton tertiary @click="router.push('/')">返回首页</NButton>
      </div>
    </div>
  </div>
</template>
