<script setup lang="ts">
import { Icon } from '@iconify/vue';

const stats = [
  { title: '总用户数', value: 1250, icon: 'material-symbols:people', color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300', trend: '+15%' },
  { title: '活跃用户', value: 890, icon: 'material-symbols:person', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300', trend: '+8%' },
  { title: '代码执行次数', value: 5680, icon: 'material-symbols:code', color: 'bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300', trend: '+22%' },
  { title: '学习资源数', value: 120, icon: 'material-symbols:school', color: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300', trend: '+5%' },
];

const recentUsers = [
  { id: 1, name: 'admin', email: 'admin@example.com', role: '管理员', status: 'active', joined: '2026-06-01' },
  { id: 2, name: 'user1', email: 'user1@example.com', role: '普通用户', status: 'active', joined: '2026-06-03' },
  { id: 3, name: 'user2', email: 'user2@example.com', role: '普通用户', status: 'inactive', joined: '2026-06-05' },
  { id: 4, name: 'guest1', email: 'guest1@example.com', role: '访客', status: 'active', joined: '2026-06-08' },
];

const recentExecutions = [
  { id: 1, user: 'user1', language: 'JavaScript', status: 'success', executedAt: '2026-06-12 14:30' },
  { id: 2, user: 'user2', language: 'Python', status: 'error', executedAt: '2026-06-12 14:25' },
  { id: 3, user: 'admin', language: 'Java', status: 'success', executedAt: '2026-06-12 14:20' },
  { id: 4, user: 'guest1', language: 'C++', status: 'success', executedAt: '2026-06-12 14:15' },
];
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-black tracking-tight">仪表盘</h1>
      <p class="mt-2 text-slate-600 dark:text-slate-300">欢迎来到 Let Coding 管理后台。</p>
    </div>

    <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
      <article v-for="stat in stats" :key="stat.title" class="admin-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-bold text-slate-500 dark:text-slate-400">{{ stat.title }}</p>
            <h3 class="mt-2 text-3xl font-black">{{ stat.value }}</h3>
            <div class="mt-3 flex items-center gap-1 text-sm font-bold text-emerald-600 dark:text-emerald-300">
              <Icon icon="material-symbols:trending-up" class="h-4 w-4" />
              {{ stat.trend }}
              <span class="font-medium text-slate-400">较上周</span>
            </div>
          </div>
          <div :class="['grid h-14 w-14 place-items-center rounded-2xl', stat.color]">
            <Icon :icon="stat.icon" class="h-7 w-7" />
          </div>
        </div>
      </article>
    </div>

    <div class="grid gap-6 xl:grid-cols-2">
      <section class="admin-card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-xl font-black">最近用户</h2>
          <button class="text-sm font-bold text-cyan-600 dark:text-cyan-300">查看全部</button>
        </div>
        <div class="space-y-3">
          <div v-for="user in recentUsers" :key="user.id" class="flex items-center justify-between rounded-2xl p-3 transition hover:bg-slate-50 dark:hover:bg-slate-800">
            <div class="flex items-center gap-3">
              <div class="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300">
                <Icon icon="material-symbols:person" class="h-6 w-6" />
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-black">{{ user.name }}</span>
                  <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ user.role }}</span>
                </div>
                <p class="text-sm text-slate-500 dark:text-slate-400">{{ user.email }}</p>
              </div>
            </div>
            <span class="rounded-full px-2.5 py-1 text-xs font-black" :class="user.status === 'active' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'">
              {{ user.status === 'active' ? '活跃' : '未激活' }}
            </span>
          </div>
        </div>
      </section>

      <section class="admin-card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-xl font-black">最近代码执行</h2>
          <button class="text-sm font-bold text-cyan-600 dark:text-cyan-300">查看全部</button>
        </div>
        <div class="space-y-3">
          <div v-for="execution in recentExecutions" :key="execution.id" class="flex items-center justify-between rounded-2xl p-3 transition hover:bg-slate-50 dark:hover:bg-slate-800">
            <div class="flex items-center gap-3">
              <div class="grid h-11 w-11 place-items-center rounded-2xl bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300">
                <Icon icon="material-symbols:code" class="h-6 w-6" />
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-black">{{ execution.user }}</span>
                  <span class="rounded-full bg-violet-100 px-2 py-0.5 text-xs font-bold text-violet-700 dark:bg-violet-950 dark:text-violet-300">{{ execution.language }}</span>
                </div>
                <p class="text-sm text-slate-500 dark:text-slate-400">{{ execution.executedAt }}</p>
              </div>
            </div>
            <span class="rounded-full px-2.5 py-1 text-xs font-black" :class="execution.status === 'success' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300'">
              {{ execution.status === 'success' ? '成功' : '失败' }}
            </span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.admin-card {
  @apply rounded-[1.75rem] border border-slate-200 bg-white/85 p-6 shadow-lg shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20;
}
</style>
