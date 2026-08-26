<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getContest, listContestProblems, joinContest, type ContestData, type ContestProblemData } from '../services/api';
import { formatDateTime as formatCSTDateTime } from '../utils/time';

const route = useRoute();
const router = useRouter();
const contestId = Number(route.params.id);

const contest = ref<ContestData | null>(null);
const problems = ref<ContestProblemData[]>([]);
const isLoading = ref(true);
const error = ref('');

const difficultyClass = (d: string) =>
  d === '简单' ? 'ui-diff ui-diff-easy'
  : d === '中等' ? 'ui-diff ui-diff-mid'
  : 'ui-diff ui-diff-hard';

const formatTime = (dateStr?: string | null) => {
  if (!dateStr) return '待定';
  const d = formatCSTDateTime(dateStr, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  return d || '待定';
};

const loadData = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    const [c, p] = await Promise.all([
      getContest(contestId),
      listContestProblems(contestId),
    ]);
    contest.value = c;
    problems.value = p;
    try { await joinContest(contestId); } catch {}
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败';
  } finally {
    isLoading.value = false;
  }
};

const openProblem = (problemId: number) => {
  router.push(`/contests/${contestId}/problems/${problemId}`);
};

onMounted(loadData);
</script>

<template>
  <div class="min-h-[calc(100vh-var(--header-h,4rem))] bg-[#F6F8FC] dark:bg-[#0F172A]">
    <div class="app-container py-6">
      <button class="ui-btn ui-btn-secondary ui-btn-sm mb-4" @click="router.push('/contests')">
        ← 返回比赛列表
      </button>

      <div v-if="isLoading" class="space-y-4">
        <div class="ui-skeleton h-24 w-full rounded-xl"></div>
        <div v-for="i in 3" :key="i" class="ui-skeleton h-16 w-full rounded-xl"></div>
      </div>

      <div v-else-if="error" class="ui-empty">
        <span class="mb-2 text-5xl">❌</span>
        <p class="font-bold">{{ error }}</p>
        <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="loadData">重试</button>
      </div>

      <template v-else-if="contest">
        <!-- 比赛信息卡片 -->
        <div class="ui-card mb-6 p-6">
          <div class="flex items-start justify-between">
            <div>
              <div class="flex items-center gap-3">
                <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">{{ contest.title }}</h1>
                <span class="ui-badge" :class="contest.status === 'ongoing' ? 'ui-badge-green' : contest.status === 'upcoming' ? 'ui-badge-blue' : 'ui-badge-slate'">
                  {{ contest.status === 'ongoing' ? '进行中' : contest.status === 'upcoming' ? '即将开始' : '已结束' }}
                </span>
              </div>
              <p v-if="contest.description" class="mt-2 text-sm text-[#64748B] dark:text-[#94A3B8]">{{ contest.description }}</p>
            </div>
          </div>
          <div class="mt-4 flex items-center gap-6 text-sm text-[#64748B] dark:text-[#94A3B8]">
            <span>🏆 {{ contest.contest_type }}</span>
            <span>🕐 {{ formatTime(contest.start_time) }} ~ {{ formatTime(contest.end_time) }}</span>
            <span>👥 {{ contest.participants_count }} 人参与</span>
            <span>📝 {{ problems.length }} 道题目</span>
          </div>
        </div>

        <!-- 题目列表（类似题库） -->
        <div class="ui-card overflow-hidden !p-0">
          <div class="hidden grid-cols-[3rem_minmax(0,1fr)_6rem_6rem_6rem] items-center gap-4 border-b border-[#E2E8F0] px-4 text-xs font-bold text-[#64748B] dark:border-[#1E293B]" style="height:48px">
            <span class="text-center">编号</span>
            <span>题目</span>
            <span class="text-center">难度</span>
            <span class="text-center">时间限制</span>
            <span class="text-center">内存限制</span>
          </div>

          <div v-if="problems.length === 0" class="ui-empty m-4">
            <span class="mb-2 text-5xl">📝</span>
            <p class="font-bold">暂无题目</p>
          </div>

          <div v-else class="divide-y divide-[#F1F5F9] dark:divide-[#1E293B]">
            <button
              v-for="p in problems"
              :key="p.id"
              class="grid w-full grid-cols-[3rem_minmax(0,1fr)] items-center gap-4 px-4 py-3 text-left transition hover:bg-[#EFF6FF] dark:hover:bg-[#172554] sm:grid-cols-[3rem_minmax(0,1fr)_6rem_6rem_6rem]"
              @click="openProblem(p.id)"
            >
              <span class="text-center text-sm font-black text-[#2563EB] dark:text-[#60A5FA]">{{ p.problem_index }}</span>
              <span class="min-w-0 truncate font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ p.title }}</span>
              <span class="hidden justify-center sm:flex">
                <span :class="difficultyClass(p.difficulty)">{{ p.difficulty }}</span>
              </span>
              <span class="hidden text-center text-sm text-[#64748B] dark:text-[#94A3B8] sm:block">{{ p.time_limit }}ms</span>
              <span class="hidden text-center text-sm text-[#64748B] dark:text-[#94A3B8] sm:block">{{ p.memory_limit }}MB</span>
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
