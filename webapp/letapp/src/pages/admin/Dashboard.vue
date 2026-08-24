<script setup lang="ts">
import { computed, markRaw, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import {
  getAdminStats,
  type AdminStats,
} from '../../services/api';

const router = useRouter();

const stats = ref<AdminStats | null>(null);
const loading = ref(true);
const loadError = ref('');

const statCards = computed(() => {
  const data = stats.value;
  return [
    {
      title: '总用户数',
      value: data?.total_users ?? 0,
      icon: 'material-symbols:group',
      color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300',
    },
    {
      title: '活跃用户',
      value: data?.active_users ?? 0,
      icon: 'material-symbols:person',
      color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
    },
    {
      title: '累计代码提交',
      value: data?.total_submissions ?? 0,
      icon: 'material-symbols:code',
      color: 'bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300',
    },
    {
      title: '公告数',
      value: data?.total_announcements ?? 0,
      icon: 'material-symbols:campaign-rounded',
      color: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
    },
  ];
});

const roleDisplayNames = markRaw({
  manager: '管理员',
  staff: '干事',
  member: '成员',
} as const);

const roleDisplayName = (role: string) =>
  roleDisplayNames[role as keyof typeof roleDisplayNames] ?? (role || '未知');

const formatDate = (dateString: string | null) => {
  if (!dateString) return '—';
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const loadStats = async () => {
  loading.value = true;
  loadError.value = '';
  try {
    stats.value = await getAdminStats();
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '加载统计数据失败';
  } finally {
    loading.value = false;
  }
};

const goUsers = () => router.push('/admin/users');
const goAnnouncements = () => router.push('/admin/announcements');

onMounted(loadStats);
</script>

<template>
  <div class="space-y-6">
    <div v-once>
      <h1 class="text-3xl font-black tracking-tight">仪表盘</h1>
      <p class="mt-2 text-slate-600 dark:text-slate-300">欢迎来到 Let Coding 管理后台。</p>
    </div>

    <div v-if="loadError" class="admin-card flex flex-col items-center gap-3 py-10 text-center">
      <Icon icon="material-symbols:cloud-off-rounded" class="h-12 w-12 text-rose-400" />
      <p class="font-bold text-slate-700 dark:text-slate-200">统计数据加载失败</p>
      <p class="text-sm text-slate-500 dark:text-slate-400">{{ loadError }}</p>
      <button
        class="mt-1 rounded-full bg-cyan-400 px-5 py-2.5 text-sm font-black text-slate-950 transition hover:bg-cyan-300"
        @click="loadStats"
      >
        重新加载
      </button>
    </div>

    <div v-else-if="loading" class="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="i in 4" :key="i" class="admin-card animate-pulse">
        <div class="flex items-center justify-between">
          <div class="space-y-3">
            <div class="h-4 w-20 rounded bg-slate-200 dark:bg-slate-800"></div>
            <div class="h-8 w-16 rounded bg-slate-200 dark:bg-slate-800"></div>
            <div class="h-3 w-24 rounded bg-slate-100 dark:bg-slate-900"></div>
          </div>
          <div class="h-14 w-14 rounded-2xl bg-slate-100 dark:bg-slate-800"></div>
        </div>
      </div>
    </div>

    <template v-else>
      <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <article v-for="stat in statCards" :key="stat.title" class="admin-card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-bold text-slate-500 dark:text-slate-400">{{ stat.title }}</p>
              <h3 class="mt-2 text-3xl font-black">{{ stat.value }}</h3>
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
            <h2 class="text-xl font-black">最近注册用户</h2>
            <button class="text-sm font-bold text-cyan-600 dark:text-cyan-300" @click="goUsers">查看全部</button>
          </div>
          <div v-if="stats?.recent_users?.length" class="space-y-3">
            <div
              v-for="user in stats.recent_users"
              :key="user.id"
              class="flex items-center justify-between rounded-2xl p-3 transition hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              <div class="flex items-center gap-3">
                <div class="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300">
                  <Icon icon="material-symbols:person" class="h-6 w-6" />
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-black">{{ user.username || `用户#${user.id}` }}</span>
                    <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ roleDisplayName(user.role) }}</span>
                  </div>
                  <p class="text-sm text-slate-500 dark:text-slate-400">{{ user.email || '未绑定邮箱' }}</p>
                </div>
              </div>
              <div class="text-right">
                <span
                  class="rounded-full px-2.5 py-1 text-xs font-black"
                  :class="user.is_active
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'"
                >
                  {{ user.is_active ? '活跃' : '未激活' }}
                </span>
                <p class="mt-1 text-xs text-slate-400">{{ formatDate(user.created_at) }}</p>
              </div>
            </div>
          </div>
          <div v-else class="flex flex-col items-center justify-center py-12 text-center">
            <Icon icon="material-symbols:person-off-rounded" class="mb-3 h-12 w-12 text-slate-300 dark:text-slate-600" />
            <p class="text-sm font-bold text-slate-500 dark:text-slate-400">暂无注册用户</p>
          </div>
        </section>

        <section class="admin-card">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-xl font-black">最近公告</h2>
            <button class="text-sm font-bold text-cyan-600 dark:text-cyan-300" @click="goAnnouncements">查看全部</button>
          </div>
          <div v-if="stats?.recent_announcements?.length" class="space-y-3">
            <div
              v-for="announcement in stats.recent_announcements"
              :key="announcement.id"
              class="flex items-center justify-between rounded-2xl p-3 transition hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              <div class="flex items-center gap-3">
                <div class="grid h-11 w-11 place-items-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                  <Icon icon="material-symbols:campaign-rounded" class="h-6 w-6" />
                </div>
                <div class="min-w-0">
                  <p class="truncate font-black">{{ announcement.title }}</p>
                  <p class="text-sm text-slate-500 dark:text-slate-400">{{ formatDate(announcement.created_at) }}</p>
                </div>
              </div>
              <span
                class="rounded-full px-2.5 py-1 text-xs font-black"
                :class="announcement.is_published
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'"
              >
                {{ announcement.is_published ? '已发布' : '草稿' }}
              </span>
            </div>
          </div>
          <div v-else class="flex flex-col items-center justify-center py-12 text-center">
            <Icon icon="material-symbols:campaign-rounded" class="mb-3 h-12 w-12 text-slate-300 dark:text-slate-600" />
            <p class="text-sm font-bold text-slate-500 dark:text-slate-400">暂无公告</p>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.admin-card {
  @apply rounded-[1.75rem] border border-slate-200 bg-white/85 p-6 shadow-lg shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20;
}
</style>
