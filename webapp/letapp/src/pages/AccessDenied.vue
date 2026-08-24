<script setup lang="ts">
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<template>
  <main class="grid min-h-screen place-items-center bg-[#F6F8FC] px-6 text-[#1E293B] dark:bg-[#0F172A] dark:text-[#E5E7EB]">
    <section class="w-full max-w-[480px] text-center">
      <span class="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-rose-50 text-rose-500 dark:bg-rose-950/40 dark:text-rose-400">
        <Icon icon="material-symbols:lock-outline-rounded" class="h-8 w-8" />
      </span>
      <h1 class="mt-6 text-2xl font-black">权限不足</h1>
      <p class="mt-2 text-sm text-[#64748B] dark:text-[#94A3B8]">当前账号没有访问该页面的权限，请联系管理员或返回首页。</p>
      <div class="mt-8 flex items-center justify-center gap-3">
        <button class="ui-btn ui-btn-primary" @click="router.push('/')">返回首页</button>
        <button class="ui-btn ui-btn-secondary" @click="router.back()">返回上一页</button>
      </div>
    </section>
  </main>
</template>
