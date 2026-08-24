<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { listContests, joinContest, type ContestData } from '../services/api';

const router = useRouter();
const activeTab = ref<'ongoing' | 'upcoming' | 'past'>('ongoing');
const contests = ref<ContestData[]>([]);
const isLoading = ref(false);
const error = ref('');

const filteredContests = computed(() =>
  contests.value.filter(c => c.status === activeTab.value)
);

const statusLabel = (status: string) => {
  if (status === 'ongoing') return '进行中';
  if (status === 'upcoming') return '即将开始';
  return '已结束';
};

const statusBadgeClass = (status: string) => {
  if (status === 'ongoing') return 'ui-badge-green';
  if (status === 'upcoming') return 'ui-badge-blue';
  return 'ui-badge-slate';
};

const formatTimeRange = (start?: string | null, end?: string | null) => {
  if (!start && !end) return '时间待定';
  const s = start ? new Date(start) : null;
  const e = end ? new Date(end) : null;
  const fmt = (d: Date) => d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  if (s && e) return `${fmt(s)} ~ ${fmt(e)}`;
  if (s) return `${fmt(s)} 开始`;
  return `截止 ${fmt(e!)}`;
};

const enterContest = async (c: ContestData) => {
  if (c.status === 'ongoing') {
    try {
      await joinContest(c.id);
    } catch {}
    router.push(`/contests/${c.id}`);
  } else if (c.status === 'upcoming') {
    router.push(`/contests/${c.id}`);
  }
};

const loadData = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    contests.value = await listContests();
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败';
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadData);
</script>

<template>
  <div class="min-h-[calc(100vh-var(--header-h,4rem))] bg-[#F6F8FC] dark:bg-[#0F172A]">
    <div class="app-container py-6">
      <div class="mb-6">
        <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">比赛</h1>
        <p class="ui-section-sub mt-1">参与编程竞赛，挑战自我</p>
      </div>

      <div class="mb-4 flex gap-2">
        <button v-for="tab in (['ongoing','upcoming','past'] as const)" :key="tab"
          class="ui-btn ui-btn-sm"
          :class="activeTab === tab ? 'ui-btn-primary' : 'ui-btn-ghost'"
          @click="activeTab = tab"
        >
          {{ tab === 'ongoing' ? '进行中' : tab === 'upcoming' ? '即将开始' : '历史比赛' }}
        </button>
      </div>

      <div v-if="isLoading" class="space-y-4">
        <div v-for="i in 3" :key="i" class="ui-skeleton h-32 w-full rounded-xl"></div>
      </div>

      <div v-else-if="error" class="ui-empty">
        <span class="mb-2 text-5xl">❌</span>
        <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">加载失败</p>
        <p class="text-sm text-[#64748B] dark:text-[#94A3B8]">{{ error }}</p>
        <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="loadData">重试</button>
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="c in filteredContests" :key="c.id" class="ui-card p-5">
          <div class="mb-3 flex items-center gap-2">
            <span class="ui-badge" :class="statusBadgeClass(c.status)">
              {{ statusLabel(c.status) }}
            </span>
            <span class="text-xs text-[#94A3B8]">{{ c.contest_type }}</span>
          </div>
          <h3 class="mb-2 font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ c.title }}</h3>
          <p class="mb-1 text-sm text-[#64748B] dark:text-[#94A3B8]">
            {{ formatTimeRange(c.start_time, c.end_time) }}
          </p>
          <p class="mb-3 text-xs text-[#94A3B8]">{{ c.participants_count }} 人参与</p>
          <button
            class="w-full ui-btn"
            :class="c.status === 'ongoing' ? 'ui-btn-primary' : c.status === 'upcoming' ? 'ui-btn-secondary' : 'ui-btn-ghost'"
            @click="enterContest(c)"
          >
            {{ c.status === 'ongoing' ? '🚀 进入比赛' : c.status === 'upcoming' ? '查看比赛' : '查看结果' }}
          </button>
        </div>
      </div>

      <div v-if="!isLoading && !error && filteredContests.length === 0" class="ui-empty mt-6">
        <span class="mb-2 text-5xl">🏆</span>
        <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">暂无比赛</p>
      </div>
    </div>
  </div>
</template>
