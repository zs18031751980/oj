<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useMessage } from 'naive-ui';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const router = useRouter();
const message = useMessage();
const authStore = useAuthStore();
const statusText = ref('正在完成登录，请稍候...');

const sanitizeNext = (value: unknown) => {
  const next = Array.isArray(value) ? String(value[0] ?? '/') : String(value || '/');
  return next.startsWith('/') ? next : '/';
};

onMounted(async () => {
  try {
    authStore.completeOAuthCallback(route.query);
    message.success('登录成功');
    await router.replace(sanitizeNext(route.query.next));
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '登录失败，请稍后重试';
    statusText.value = errorMessage;
    message.error(errorMessage);
    authStore.startOAuthLogin('iOSClub', sanitizeNext(route.query.next), true);
  }
});
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <div class="flex items-center gap-4 rounded-full border border-slate-200 bg-white px-6 py-4 shadow-lg shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20">
      <Icon icon="material-symbols:progress-activity" class="h-6 w-6 animate-spin text-cyan-500" />
      <span class="text-sm font-bold">{{ statusText }}</span>
    </div>
  </div>
</template>
