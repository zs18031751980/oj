<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  getContest,
  listContestRankings,
  type ContestData,
  type ContestRankingsData,
  type ContestRankingData,
} from '../services/api';
import { formatDateTime as formatCSTDateTime } from '../utils/time';
import { Icon } from '@iconify/vue';

const route = useRoute();
const router = useRouter();
const contestId = Number(route.params.id);

const contest = ref<ContestData | null>(null);
const data = ref<ContestRankingsData | null>(null);
const rankings = ref<ContestRankingData[]>([]);
const isLoading = ref(true);
const error = ref('');

const formatTime = (dateStr?: string | null) => {
  if (!dateStr) return '待定';
  const d = formatCSTDateTime(dateStr, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  return d || '待定';
};

const isOI = () => data.value?.mode === 'OI';

let timer: ReturnType<typeof setInterval> | null = null;

const loadData = async () => {
  error.value = '';
  try {
    const [c, r] = await Promise.all([
      getContest(contestId).catch(() => null),
      listContestRankings(contestId),
    ]);
    contest.value = c;
    data.value = r;
    rankings.value = r.rankings || [];
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败';
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadData();
  timer = setInterval(loadData, 10000);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<template>
  <div class="min-h-[calc(100vh-var(--header-h,4rem))] bg-[#F6F8FC] dark:bg-[#0F172A]">
    <div class="app-container max-w-[1200px] py-6">
      <button class="ui-btn ui-btn-secondary ui-btn-sm mb-4" @click="router.push(`/contests/${contestId}`)">
        ← 返回比赛
      </button>

      <!-- 头部 -->
      <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 class="ui-section-title text-2xl">
            {{ contest ? contest.title : '比赛' }} · 实时排行榜
          </h1>
          <div class="ui-section-sub mt-2 flex flex-wrap items-center gap-2">
            <span class="ui-badge ui-badge-blue">
              {{ isOI() ? 'OI（按得分）' : 'ACM（解题数 + 罚时）' }}
            </span>
             <span v-if="contest" class="inline-flex items-center gap-1"><Icon icon="material-symbols:schedule" class="h-4 w-4" />{{ formatTime(contest.start_time) }} ~ {{ formatTime(contest.end_time) }}</span>
            <span class="text-[#94A3B8]">每 10 秒自动刷新</span>
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="isLoading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="ui-skeleton h-14 w-full rounded-xl"></div>
      </div>

      <!-- 错误 -->
      <div v-else-if="error" class="ui-empty">
        <Icon icon="material-symbols:error-outline-rounded" class="mb-2 h-12 w-12 text-rose-500" />
        <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">加载失败</p>
        <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="loadData">重试</button>
      </div>

      <!-- 排行榜 -->
      <div v-else-if="rankings.length" class="ui-card !p-0 overflow-x-auto">
        <table class="w-full border-collapse text-sm">
          <thead>
            <tr class="border-b border-[#E2E8F0] text-xs font-bold text-[#64748B] dark:border-[#1E293B] dark:text-[#94A3B8]">
              <th class="px-4 py-3 text-left font-bold w-16">排名</th>
              <th class="px-4 py-3 text-left font-bold">用户</th>
              <th
                v-for="pidx in (data?.problem_indexes || [])"
                :key="pidx"
                class="px-2 py-3 text-center font-bold"
              >{{ pidx }}</th>
              <th class="px-4 py-3 text-center font-bold">
                {{ isOI() ? '总分' : '解题' }}
              </th>
              <th v-if="!isOI()" class="px-4 py-3 text-center font-bold">罚时</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#F1F5F9] dark:divide-[#1E293B]">
            <tr
              v-for="row in rankings"
              :key="row.user_id"
              class="transition hover:bg-[#EFF6FF] dark:hover:bg-[#172554]"
              :class="row.rank <= 3 ? 'ring-2 ring-inset ring-amber-200 dark:ring-amber-800' : ''"
            >
              <td class="px-4 py-3">
                 <Icon v-if="row.rank <= 3" icon="material-symbols:military-tech" class="h-8 w-8 text-amber-500" />
                <span v-else class="text-lg font-black text-[#64748B] dark:text-[#94A3B8]">#{{ row.rank }}</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div class="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
                     <Icon icon="material-symbols:person-rounded" class="h-5 w-5" />
                  </div>
                  <span class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ row.username }}</span>
                </div>
              </td>
              <td
                v-for="pr in row.problems"
                :key="pr.problem_index"
                class="px-2 py-3 text-center"
              >
                <span
                  v-if="pr.solved"
                  class="ui-badge ui-badge-green"
                  :title="`状态: ${pr.status}｜通过 ${pr.passed}/${pr.total}｜提交 ${pr.submissions} 次｜距比赛开始 ${pr.solve_minutes ?? 0} 分钟`"
                >
                  {{ isOI() ? pr.score : '✓' }}
                  <span v-if="!isOI() && pr.solve_minutes != null" class="ml-1 text-[10px] font-normal opacity-80">{{ pr.solve_minutes }}m</span>
                </span>
                <span
                  v-else-if="pr.submissions > 0"
                  class="ui-badge ui-badge-red"
                  :title="`状态: ${pr.status}｜通过 ${pr.passed}/${pr.total}｜提交 ${pr.submissions} 次`"
                >
                  {{ isOI() ? (pr.score > 0 ? pr.score : '✗') : '✗' }}
                </span>
                <span v-else class="text-[#CBD5E1] dark:text-[#475569]">—</span>
              </td>
              <td class="px-4 py-3 text-center">
                <span class="text-lg font-black text-[#2563EB] dark:text-[#60A5FA]">
                  {{ isOI() ? row.score : row.solved_count }}
                </span>
              </td>
              <td v-if="!isOI()" class="px-4 py-3 text-center text-[#64748B] dark:text-[#94A3B8]">
                {{ row.penalty }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 空态 -->
      <div v-else class="ui-empty mt-6">
        <Icon icon="material-symbols:leaderboard-rounded" class="mb-2 h-12 w-12 text-slate-400" />
        <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">暂无排名数据</p>
        <p class="text-sm text-[#64748B] dark:text-[#94A3B8]">参赛并提交代码后即可上榜</p>
      </div>
    </div>
  </div>
</template>
