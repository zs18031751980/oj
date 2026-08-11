<script setup lang="ts">
import { Icon } from '@iconify/vue';
import { NButton } from 'naive-ui';
import { useRouter } from 'vue-router';


const router = useRouter();
</script>

<template>
  <main class="grid min-h-screen place-items-center bg-slate-50 px-6 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <section class="w-full max-w-xl border-l-4 border-rose-500 py-4 pl-6 sm:pl-8">
      <Icon icon="material-symbols:lock-outline-rounded" class="h-12 w-12 text-rose-500" />
      <p class="mt-5 text-sm font-bold text-rose-600 dark:text-rose-400">403</p>
      <h1 class="mt-2 text-3xl font-black sm:text-4xl">权限不足</h1>
      <p class="mt-4 text-base leading-7 text-slate-600 dark:text-slate-300">
        当前账号没有访问公告管理的权限。
      </p>
      <div class="mt-8 flex flex-wrap gap-3">
        <NButton type="primary" @click="router.push('/announcements')">
          返回公告
        </NButton>
        <NButton secondary @click="router.push('/')">
          返回首页
        </NButton>
      </div>
    </section>
  </main>
</template>
