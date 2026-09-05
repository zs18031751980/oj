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
  return Array.from(seen, ([key, label]) => ({ key, label }));
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
    });
});

const openProblem = (id: number) => {
  router.push(`/problems/${id}`);
};

const isFavorited = (id: number) => favoriteIds.value.has(id);

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
      <!-- 标题区 -->
      <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">在线题库</h1>
          <p class="ui-section-sub mt-1">共 {{ problems.length }} 道题目 · 当前筛选出 {{ filteredProblems.length }} 道</p>
        </div>
        <div class="relative w-full sm:w-80">
          <Icon icon="material-symbols:search" class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
          <input
            v-model="searchQuery"
            type="text"
            class="ui-input pl-9"
            placeholder="搜索题号、名称或标签"
          />
        </div>
      </div>

      <div class="flex items-start gap-6">
        <!-- 左侧筛选 -->
        <aside class="hidden w-60 shrink-0 lg:block">
          <div class="ui-card space-y-6">
            <div>
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
            </div>
            <div>
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
            </div>
            <div>
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
            </div>
          </div>
        </aside>

        <!-- 右侧内容 -->
        <section class="min-w-0 flex-1">
          <!-- 移动端筛选 -->
          <div class="mb-4 flex flex-wrap gap-2 lg:hidden">
            <button
              class="rounded-full border px-3 py-1 text-xs font-bold transition-colors"
              :class="difficultyFilter === '' ? 'border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] dark:border-[#60A5FA] dark:bg-[#172554] dark:text-[#60A5FA]' : 'border-[#E2E8F0] text-[#64748B] dark:border-[#334155] dark:text-[#94A3B8]'"
              @click="difficultyFilter = ''"
            >
              全部
            </button>
            <button
              v-for="d in ['简单', '中等', '困难']"
              :key="d"
              class="rounded-full border px-3 py-1 text-xs font-bold transition-colors"
              :class="difficultyFilter === d ? 'border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] dark:border-[#60A5FA] dark:bg-[#172554] dark:text-[#60A5FA]' : 'border-[#E2E8F0] text-[#64748B] dark:border-[#334155] dark:text-[#94A3B8]'"
              @click="difficultyFilter = difficultyFilter === d ? '' : (d as any)"
            >
              {{ d }}
            </button>
            <button
              class="rounded-full border px-3 py-1 text-xs font-bold transition-colors"
              :class="statusFilter === 'favorite' ? 'border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] dark:border-[#60A5FA] dark:bg-[#172554] dark:text-[#60A5FA]' : 'border-[#E2E8F0] text-[#64748B] dark:border-[#334155] dark:text-[#94A3B8]'"
              @click="statusFilter = statusFilter === 'favorite' ? '' : 'favorite'"
            >
              收藏
            </button>
          </div>

          <div class="ui-card overflow-hidden !p-0">
            <!-- 表头 48px -->
            <div class="hidden grid-cols-[2.5rem_minmax(0,1fr)_5rem_5rem_5rem] items-center gap-4 border-b border-[#E2E8F0] px-4 text-xs font-bold text-[#64748B] dark:border-[#1E293B] sm:grid" style="height:48px">
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
                class="problem-row grid w-full grid-cols-[2.5rem_minmax(0,1fr)] items-center gap-4 px-4 py-3 text-left transition hover:bg-[#EFF6FF] dark:hover:bg-[#172554] sm:grid-cols-[2.5rem_minmax(0,1fr)_5rem_5rem_5rem]"
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
                    <span class="truncate font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ p.title }}</span>
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
  @apply flex items-center rounded-lg px-3 py-2 text-sm font-semibold transition-colors;
  color: #475569;
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
