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
const retryNext = ref('/');
const loginFailed = ref(false);

const sanitizeNext = (value: unknown) => {
  const next = Array.isArray(value) ? String(value[0] ?? '/') : String(value || '/');
  return next.startsWith('/') ? next : '/';
};

const retryLogin = () => {
  authStore.startOAuthLogin('iOSClub', retryNext.value, true);
};

onMounted(async () => {
  retryNext.value = sanitizeNext(route.query.next);
  try {
    authStore.completeOAuthCallback(route.query);
    message.success('登录成功');
    await router.replace(retryNext.value);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '登录失败，请稍后重试';
    statusText.value = errorMessage.includes('timeout') || errorMessage.includes('超时')
      ? '登录请求超时，请稍后重试。'
      : errorMessage;
    loginFailed.value = true;
    message.error(errorMessage);
  }
});
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <div class="flex max-w-lg flex-col items-center gap-4 rounded-[2rem] border border-slate-200 bg-white px-6 py-6 text-center shadow-lg shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20">
      <Icon
        :icon="loginFailed ? 'material-symbols:error-outline-rounded' : 'material-symbols:progress-activity'"
        class="h-8 w-8"
        :class="loginFailed ? 'text-rose-500' : 'animate-spin text-cyan-500'"
      />
      <span class="text-sm font-bold">{{ statusText }}</span>
      <div v-if="loginFailed" class="flex flex-wrap justify-center gap-3">
        <NButton type="primary" @click="retryLogin">重新登录</NButton>
        <NButton tertiary @click="router.push('/')">返回首页</NButton>
      </div>
    </div>
  </div>
</template>
