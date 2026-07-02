<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useProblemStats } from '../composables/useProblemStats';

interface Problem {
  id: number;
  title: string;
  difficulty: '简单' | '中等' | '困难';
  tags: string[];
}

const router = useRouter();
const searchQuery = ref('');
const difficultyFilter = ref<string>('');
const { getStats } = useProblemStats();

const problems = ref<Problem[]>([
  { id: 1001, title: '两数之和', difficulty: '简单', tags: ['数组', '哈希表'] },
  { id: 1002, title: '反转字符串', difficulty: '简单', tags: ['字符串', '双指针'] },
  { id: 1003, title: '斐波那契数列', difficulty: '简单', tags: ['递归', '动态规划'] },
]);

const filteredProblems = computed(() => {
  let list = problems.value;
  if (difficultyFilter.value) {
    list = list.filter(p => p.difficulty === difficultyFilter.value);
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    list = list.filter(p =>
      p.title.toLowerCase().includes(q) ||
      p.tags.some(t => t.toLowerCase().includes(q)) ||
      String(p.id).includes(q)
    );
  }
  return list;
});

const openProblem = (id: number) => {
  router.push(`/problems/${id}`);
};

const difficultyColor = (d: string) => {
  if (d === '简单') return 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30';
  if (d === '中等') return 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30';
  return 'text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/30';
};
</script>

<template>
  <div class="flex min-h-[calc(100vh-5rem)] flex-col bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <div class="border-b border-slate-200/80 bg-white/80 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-950/80">
      <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="max-w-3xl">
            <p class="text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Problem Bank</p>
            <h1 class="mt-3 text-4xl font-black tracking-tight sm:text-5xl">在线题库</h1>
          </div>
          <div class="flex items-center gap-3">
            <span class="rounded-full bg-cyan-100 px-3 py-1.5 text-xs font-bold text-cyan-700 dark:bg-cyan-900/60 dark:text-cyan-300">
              {{ filteredProblems.length }} 道题目
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div class="relative flex-1 max-w-md">
          <Icon icon="material-symbols:search" class="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索题目、标签或编号"
            class="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-12 pr-4 text-sm font-medium text-slate-800 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-cyan-500"
          />
        </div>
        <div class="flex gap-2">
          <button
            v-for="d in ['', '简单', '中等', '困难']"
            :key="d"
            class="rounded-xl border px-4 py-2 text-sm font-bold transition"
            :class="difficultyFilter === d
              ? 'border-cyan-400 bg-cyan-50 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300'
              : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400'"
            @click="difficultyFilter = d"
          >
            {{ d || '全部' }}
          </button>
        </div>
      </div>

      <div class="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white/85 shadow-lg shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20">
        <div v-if="filteredProblems.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
          <Icon icon="material-symbols:search-off" width="48" height="48" class="mb-4 text-slate-300 dark:text-slate-600" />
          <p class="text-lg font-bold text-slate-500 dark:text-slate-400">没有找到匹配的题目</p>
        </div>
        <div v-else class="divide-y divide-slate-100 dark:divide-slate-800">
          <div
            v-for="problem in filteredProblems"
            :key="problem.id"
            class="flex cursor-pointer items-center gap-4 px-6 py-4 transition hover:bg-slate-50 dark:hover:bg-slate-800/50"
            @click="openProblem(problem.id)"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-3">
                <span class="w-12 shrink-0 text-sm font-mono text-slate-400 dark:text-slate-500">{{ problem.id }}</span>
                <span class="text-base font-bold text-slate-900 dark:text-white truncate">{{ problem.title }}</span>
                <span class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold" :class="difficultyColor(problem.difficulty)">{{ problem.difficulty }}</span>
              </div>
              <div class="mt-1 flex flex-wrap gap-2">
                <span
                  v-for="tag in problem.tags"
                  :key="tag"
                  class="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                >{{ tag }}</span>
              </div>
            </div>
            <div class="hidden shrink-0 sm:block">
              <span
                class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold"
                :class="getStats(problem.id).accepted > 0
                  ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30'
                  : 'text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800'"
              >
                <Icon
                  :icon="getStats(problem.id).accepted > 0 ? 'material-symbols:check-circle' : 'material-symbols:radio-button-unchecked'"
                  class="h-3.5 w-3.5"
                />
                {{ getStats(problem.id).accepted > 0 ? '已通过' : '未通过' }}
              </span>
            </div>
            <Icon icon="material-symbols:chevron-right" class="shrink-0 h-5 w-5 text-slate-300 dark:text-slate-600" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
