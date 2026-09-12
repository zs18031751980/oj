<script setup lang="ts">
import { computed, onMounted, ref, shallowRef } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useMessage } from 'naive-ui';
import { useProblemStats } from '../composables/useProblemStats';
import { useAuthStore } from '../stores/auth';
import { apiRequest, listFavorites, addFavorite, removeFavorite } from '../services/api';

const route = useRoute();

interface Problem {
  id: number;
  sourceNumber?: number;
  category: string;
  categoryLabel?: string;
  title: string;
  difficulty: '简单' | '中等' | '困难';
  tags: string[];
  interactive?: boolean;
  judgeable?: boolean;
}

interface ProblemListResponse {
  data: Problem[];
  total: number;
}

const router = useRouter();
const message = useMessage();
const searchQuery = ref('');
const difficultyFilter = ref<string>('');
const categoryFilter = ref('');
const statusFilter = ref<'' | 'solved' | 'unsolved' | 'attempted' | 'favorite'>('');
const sortMode = ref<'latest' | 'number'>('latest');
const isLoading = ref(true);
const loadError = ref('');
const { getStats } = useProblemStats();
const authStore = useAuthStore();

const problems = shallowRef<Problem[]>([]);
const favoriteIds = ref<Set<number>>(new Set());

// 统一处理空格和常见分隔符，让 "binary search"、"binary-search" 等写法都能命中。
const normalizeSearchText = (value: string) =>
  value.toLocaleLowerCase().replace(/[\s\-_./\\()[\]{}:：,，。]+/g, '');

const fuzzyMatch = (value: string, query: string) => {
  const text = normalizeSearchText(value);
  const normalizedQuery = normalizeSearchText(query);
  if (!normalizedQuery) return true;
  if (text.includes(normalizedQuery)) return true;

  let queryIndex = 0;
  for (const character of text) {
    if (character === normalizedQuery[queryIndex]) queryIndex += 1;
    if (queryIndex === normalizedQuery.length) return true;
  }
  return false;
};

const loadProblems = async () => {
  isLoading.value = true;
  loadError.value = '';
  try {
    const response = await apiRequest<ProblemListResponse>('/problems', { skipAuth: true });
    problems.value = response.data;
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '题目加载失败，请稍后重试。';
  } finally {
    isLoading.value = false;
  }
};

const loadFavorites = async () => {
  if (!authStore.isAuthenticated) {
    favoriteIds.value = new Set();
    return;
  }
  try {
    const res = await listFavorites();
    favoriteIds.value = new Set(res.data.map((item) => item.problem_id));
  } catch {
    favoriteIds.value = new Set();
  }
};

const categoryLabelMap: Record<string, string> = {
  'general': '练习',
  'c-language': 'C语言专栏',
};
const categoryDisplayName = (key: string) => categoryLabelMap[key] || key;

interface CategoryOption {
  key: string;
  label: string;
}
const categories = computed<CategoryOption[]>(() => {
  const seen = new Map<string, string>();
  for (const p of problems.value) {
    if (!p.category) continue;
    if (!seen.has(p.category)) {
      seen.set(p.category, p.categoryLabel || categoryDisplayName(p.category));
    }
  }
  return Array.from(seen, ([key, label]) => ({ key, label }))
    .filter(({ label }) => label.trim() !== '1');
});

const filteredProblems = computed(() => {
  const q = searchQuery.value.trim();
  return problems.value
    .filter((p) => {
      if (categoryFilter.value && p.category !== categoryFilter.value) return false;
      if (difficultyFilter.value && p.difficulty !== difficultyFilter.value) return false;
      const stat = getStats(p.id);
      if (statusFilter.value === 'solved' && !(authStore.isAuthenticated && stat.accepted > 0)) return false;
      if (statusFilter.value === 'unsolved' && authStore.isAuthenticated && stat.accepted > 0) return false;
      if (statusFilter.value === 'attempted' && !(authStore.isAuthenticated && stat.attempted)) return false;
      if (statusFilter.value === 'favorite' && !favoriteIds.value.has(p.id)) return false;
      if (q) {
        return (
          fuzzyMatch(p.title, q) ||
          p.tags.some((t) => fuzzyMatch(t, q)) ||
          fuzzyMatch(p.categoryLabel || p.category, q) ||
          fuzzyMatch(String(p.sourceNumber || p.id), q)
        );
      }
      return true;
    })
    .map((p) => {
      const stat = getStats(p.id);
      return {
        ...p,
        stat,
        isAccepted: authStore.isAuthenticated && stat.accepted > 0,
        isAttempted: authStore.isAuthenticated && stat.attempted,
        acceptRate: stat.submissions > 0 ? Math.round((stat.accepted / stat.submissions) * 100) : null,
      };
    })
    .sort((a, b) => {
      const aNumber = a.sourceNumber ?? a.id;
      const bNumber = b.sourceNumber ?? b.id;
      return sortMode.value === 'latest' ? bNumber - aNumber : aNumber - bNumber;
    });
});

const openProblem = (id: number) => {
  router.push(`/problems/${id}`);
};

const isFavorited = (id: number) => favoriteIds.value.has(id);

const openRandomProblem = () => {
  const candidates = filteredProblems.value;
  if (!candidates.length) {
    message.info('当前筛选条件下没有可打开的题目');
    return;
  }
  const selectedProblem = candidates[Math.floor(Math.random() * candidates.length)];
  if (selectedProblem) openProblem(selectedProblem.id);
};

const goLogin = () => {
  authStore.startOAuthLogin('iOSClub', router.currentRoute.value.fullPath, true);
};

const toggleFavorite = async (problem: Problem, event: MouseEvent) => {
  event.stopPropagation();
  if (!authStore.isAuthenticated) {
    message.warning('请先登录后再收藏题目');
    goLogin();
    return;
  }
  const favorited = favoriteIds.value.has(problem.id);
  const next = new Set(favoriteIds.value);
  try {
    const res = favorited ? await removeFavorite(problem.id) : await addFavorite(problem.id);
    if (res.favorited) next.add(problem.id);
    else next.delete(problem.id);
    favoriteIds.value = next;
    message.success(res.favorited ? '已加入收藏题目' : '已取消收藏');
  } catch (error) {
    message.error(error instanceof Error ? error.message : '操作失败，请稍后重试');
  }
};

const difficultyClass = (d: string) =>
  d === '简单'
    ? 'ui-diff ui-diff-easy'
    : d === '中等'
      ? 'ui-diff ui-diff-mid'
      : 'ui-diff ui-diff-hard';

const resetFilters = () => {
  searchQuery.value = '';
  difficultyFilter.value = '';
  categoryFilter.value = '';
  statusFilter.value = '';
};

onMounted(() => {
  const q = route.query.q;
  const tag = route.query.tag;
  if (typeof q === 'string' && q.trim()) {
    searchQuery.value = q.trim();
  } else if (typeof tag === 'string' && tag.trim()) {
    searchQuery.value = tag.trim();
  }
  loadProblems();
  loadFavorites();
});
</script>

<template>
  <div class="problems-page bg-[#F6F8FC] dark:bg-[#0F172A]">
    <div class="app-container py-6">
      <div class="flex items-start gap-4 lg:gap-6">
        <!-- 左侧筛选 -->
        <aside data-testid="problem-filter-card" class="problem-filter-card hidden w-60 shrink-0 lg:block">
          <div class="space-y-6">
            <section>
              <div class="ui-section-title mb-2 text-sm">状态</div>
              <div class="flex flex-col gap-1">
                <button
                  v-for="opt in [
                    { v: '', label: '全部题目' },
                    { v: 'solved', label: '已解决' },
                    { v: 'attempted', label: '尝试解决' },
                    { v: 'unsolved', label: '未解决' },
                    { v: 'favorite', label: '我的收藏' },
                  ]"
                  :key="opt.v"
                  class="filter-item"
                  :class="{ active: statusFilter === opt.v }"
                  @click="statusFilter = opt.v as any"
                >
                  {{ opt.label }}
                </button>
              </div>
            </section>
            <section>
              <div class="ui-section-title mb-2 text-sm">难度</div>
              <div class="flex flex-col gap-1">
                <button
                  class="filter-item"
                  :class="{ active: difficultyFilter === '' }"
                  @click="difficultyFilter = ''"
                >
                  全部难度
                </button>
                <button
                  v-for="d in ['简单', '中等', '困难']"
                  :key="d"
                  class="filter-item"
                  :class="{ active: difficultyFilter === d }"
                  @click="difficultyFilter = difficultyFilter === d ? '' : (d as any)"
                >
                  <span :class="difficultyClass(d)" class="!px-2 !py-0">{{ d }}</span>
                </button>
              </div>
            </section>
            <section>
              <div class="ui-section-title mb-2 text-sm">分类</div>
              <div class="filter-scroll flex max-h-72 flex-col gap-1 overflow-y-auto pr-1">
                <button class="filter-item" :class="{ active: categoryFilter === '' }" @click="categoryFilter = ''">全部分类</button>
                <button
                  v-for="c in categories"
                  :key="c.key"
                  class="filter-item"
                  :class="{ active: categoryFilter === c.key }"
                  @click="categoryFilter = categoryFilter === c.key ? '' : c.key"
                >
                  {{ c.label }}
                </button>
              </div>
            </section>
          </div>
        </aside>

        <!-- 右侧内容 -->
        <section class="min-w-0 flex-1">
          <div class="problem-intro-card mb-4">
            <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <h1 class="text-2xl font-semibold text-[#1E293B] dark:text-[#E5E7EB]">在线题库</h1>
                <p class="ui-section-sub mt-1">精选编程题目，持续提升你的编程能力。</p>
              </div>
              <div class="relative w-full xl:w-64">
                <Icon icon="material-symbols:search" class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
                <input
                  v-model="searchQuery"
                  type="text"
                  class="ui-input h-10 pl-9"
                  placeholder="搜索题号、名称或标签"
                />
              </div>
            </div>

            <div data-testid="problem-toolbar" class="problem-toolbar mt-5">
              <div class="flex flex-wrap gap-2">
                <button class="problem-toolbar-tab" :class="{ active: statusFilter === '' }" @click="statusFilter = ''">全部题目</button>
                <button class="problem-toolbar-tab" :class="{ active: statusFilter === 'favorite' }" @click="statusFilter = 'favorite'">我的收藏</button>
                <button class="problem-toolbar-tab" :class="{ active: statusFilter === 'unsolved' }" @click="statusFilter = 'unsolved'">未解决</button>
                <button class="problem-toolbar-tab" :class="{ active: statusFilter === 'solved' }" @click="statusFilter = 'solved'">已解决</button>
              </div>
              <div class="flex items-center gap-2">
                <select v-model="sortMode" class="problem-sort" aria-label="题目排序">
                  <option value="latest">按最新发布</option>
                  <option value="number">按题号排序</option>
                </select>
                <button class="ui-btn ui-btn-primary ui-btn-sm" @click="openRandomProblem">
                  <Icon icon="material-symbols:shuffle-rounded" class="h-4 w-4" />
                  随机一题
                </button>
              </div>
            </div>
          </div>

          <!-- 移动端筛选 -->
          <div class="mb-4 flex flex-wrap gap-2 lg:hidden">
            <button
              class="rounded-md border px-3 py-1 text-xs font-medium transition-colors"
              :class="difficultyFilter === '' ? 'border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] dark:border-[#60A5FA] dark:bg-[#172554] dark:text-[#60A5FA]' : 'border-[#E2E8F0] text-[#64748B] dark:border-[#334155] dark:text-[#94A3B8]'"
              @click="difficultyFilter = ''"
            >
              全部
            </button>
            <button
              v-for="d in ['简单', '中等', '困难']"
              :key="d"
              class="rounded-md border px-3 py-1 text-xs font-medium transition-colors"
              :class="difficultyFilter === d ? 'border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] dark:border-[#60A5FA] dark:bg-[#172554] dark:text-[#60A5FA]' : 'border-[#E2E8F0] text-[#64748B] dark:border-[#334155] dark:text-[#94A3B8]'"
              @click="difficultyFilter = difficultyFilter === d ? '' : (d as any)"
            >
              {{ d }}
            </button>
            <button
              class="rounded-md border px-3 py-1 text-xs font-medium transition-colors"
              :class="statusFilter === 'favorite' ? 'border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] dark:border-[#60A5FA] dark:bg-[#172554] dark:text-[#60A5FA]' : 'border-[#E2E8F0] text-[#64748B] dark:border-[#334155] dark:text-[#94A3B8]'"
              @click="statusFilter = statusFilter === 'favorite' ? '' : 'favorite'"
            >
              收藏
            </button>
          </div>

          <div class="overflow-hidden rounded-md border border-[#E2E8F0] bg-white dark:border-[#1E293B] dark:bg-[#111827]">
            <!-- 表头 48px -->
             <div class="hidden grid-cols-[2.5rem_minmax(0,1fr)_5rem_5rem_5rem] items-center gap-4 border-b border-[#E2E8F0] px-4 text-xs font-medium text-[#64748B] dark:border-[#1E293B] sm:grid" style="height:40px">
              <span>状态</span>
              <span>题目</span>
              <span class="text-center">难度</span>
              <span class="text-center">通过率</span>
              <span class="text-center">提交</span>
            </div>

            <div v-if="isLoading" class="space-y-2 p-4">
              <div v-for="i in 6" :key="i" class="ui-skeleton h-12 w-full"></div>
            </div>

            <div v-else-if="loadError" class="ui-empty m-4">
              <Icon icon="material-symbols:cloud-off-rounded" class="mb-2 h-10 w-10 text-rose-400" />
              <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">加载失败</p>
              <p class="text-sm text-[#64748B] dark:text-[#94A3B8]">{{ loadError }}</p>
              <button class="ui-btn ui-btn-primary ui-btn-sm mt-2" @click="loadProblems">重新加载</button>
            </div>

            <div v-else-if="filteredProblems.length === 0" class="ui-empty m-4">
              <Icon icon="material-symbols:search-off" class="mb-2 h-10 w-10 text-[#94A3B8]" />
              <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">没有找到匹配的题目</p>
              <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="resetFilters">清除筛选</button>
            </div>

            <div v-else class="divide-y divide-[#F1F5F9] dark:divide-[#1E293B]">
              <button
                v-for="p in filteredProblems"
                :key="p.id"
                 class="problem-row grid w-full grid-cols-[2.5rem_minmax(0,1fr)] items-center gap-4 px-4 py-2.5 text-left transition-colors hover:bg-[#EFF6FF] dark:hover:bg-[#172554] sm:grid-cols-[2.5rem_minmax(0,1fr)_5rem_5rem_5rem]"
                @click="openProblem(p.id)"
              >
                <span class="flex justify-center">
                  <Icon
                    v-if="p.isAccepted"
                    icon="material-symbols:check-circle"
                    class="h-5 w-5 text-emerald-500"
                  />
                  <Icon
                    v-else-if="p.stat.attempted"
                    icon="material-symbols:pending"
                    class="h-5 w-5 text-amber-500"
                  />
                  <Icon v-else icon="material-symbols:circle" class="h-4 w-4 text-[#CBD5E1] dark:text-[#475569]" />
                </span>
                <span class="min-w-0">
                  <span class="flex items-center gap-2">
                    <span class="shrink-0 text-xs font-mono text-[#94A3B8]">#{{ p.sourceNumber ?? p.id }}</span>
                    <span class="truncate font-semibold text-[#1E293B] dark:text-[#E5E7EB]">{{ p.title }}</span>
                  </span>
                  <span class="mt-1 flex flex-wrap gap-1.5">
                    <span
                      v-for="tag in p.tags.slice(0, 3)"
                      :key="tag"
                      class="rounded-md bg-[#F1F5F9] px-2 py-0.5 text-[11px] font-medium text-[#64748B] dark:bg-[#1E293B] dark:text-[#94A3B8]"
                    >{{ tag }}</span>
                  </span>
                </span>
                <span class="hidden justify-center sm:flex">
                  <span :class="difficultyClass(p.difficulty)">{{ p.difficulty }}</span>
                </span>
                <span class="hidden text-center text-sm font-semibold text-[#475569] dark:text-[#CBD5E1] sm:block">
                  {{ p.acceptRate != null ? p.acceptRate + '%' : '—' }}
                </span>
                <span class="hidden text-center text-sm text-[#94A3B8] sm:block">{{ p.stat.submissions }}</span>
                <span class="col-span-2 flex justify-end sm:col-span-1">
                  <button
                    class="ui-icon-btn !h-8 !w-8"
                    :class="isFavorited(p.id) ? 'text-amber-400' : 'text-[#94A3B8]'"
                    :title="isFavorited(p.id) ? '取消收藏' : '收藏题目'"
                    @click="toggleFavorite(p, $event)"
                  >
                    <Icon :icon="isFavorited(p.id) ? 'material-symbols:star-rounded' : 'material-symbols:star-outline-rounded'" class="h-5 w-5" />
                  </button>
                </span>
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.filter-item {
  @apply flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors;
  color: #475569;
}
.problem-filter-card,
.problem-intro-card {
  @apply rounded-md border border-[#E2E8F0] bg-white p-4 dark:border-[#1E293B] dark:bg-[#111827];
}
.problem-intro-card {
  @apply p-5;
}
.problem-toolbar {
  @apply flex flex-col gap-3 border-t border-[#E2E8F0] pt-4 sm:flex-row sm:items-center sm:justify-between dark:border-[#1E293B];
}
.problem-toolbar-tab {
  @apply inline-flex h-8 items-center justify-center rounded-md border border-[#E2E8F0] bg-white px-3 text-xs font-medium text-[#475569] transition-colors hover:border-[#CBD5E1] hover:bg-[#F8FAFC] dark:border-[#334155] dark:bg-[#111827] dark:text-[#CBD5E1] dark:hover:bg-[#1E293B];
}
.problem-toolbar-tab.active {
  @apply border-[#2563EB] bg-[#2563EB] text-white hover:border-[#1D4ED8] hover:bg-[#1D4ED8] dark:border-[#3B82F6] dark:bg-[#2563EB];
}
.problem-sort {
  @apply h-8 rounded-md border border-[#E2E8F0] bg-white px-2.5 text-xs font-medium text-[#475569] outline-none transition-colors focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]/25 dark:border-[#334155] dark:bg-[#111827] dark:text-[#CBD5E1];
}
html:not(.dark) .filter-item:hover {
  background: #F1F5F9;
}
.dark .filter-item {
  color: #CBD5E1;
}
.dark .filter-item:hover {
  background: #1E293B;
}
.filter-item.active {
  background: #EFF6FF;
  color: #2563EB;
}
.dark .filter-item.active {
  background: #172554;
  color: #60A5FA;
}
.filter-scroll::-webkit-scrollbar {
  width: 6px;
}
.filter-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.dark .filter-scroll::-webkit-scrollbar-thumb {
  background: #334155;
}
</style>
