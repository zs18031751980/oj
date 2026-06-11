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
const statusText = ref('正在完成登录...');

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
    const errorMessage = error instanceof Error ? error.message : '登录失败，请重试';
    statusText.value = errorMessage;
    message.error(errorMessage);
    await router.replace({
      path: '/login',
      query: {
        next: sanitizeNext(route.query.next),
      },
    });
  }
});
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div class="flex items-center gap-3 text-base">
      <Icon icon="material-symbols:progress-activity" class="h-6 w-6 animate-spin text-blue-600" />
      <span>{{ statusText }}</span>
    </div>
  </div>
</template>
