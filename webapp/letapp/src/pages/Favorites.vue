<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useMessage } from 'naive-ui';
import {
  listFavorites,
  removeFavorite,
  type FavoriteItem,
} from '../services/api';

const router = useRouter();
const message = useMessage();

const favorites = ref<FavoriteItem[]>([]);
const loading = ref(true);
const loadError = ref('');
const removingId = ref<number | null>(null);

const formatDate = (dateString: string | null) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};

const loadFavorites = async () => {
  loading.value = true;
  loadError.value = '';
  try {
    const result = await listFavorites();
    favorites.value = result.data;
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '加载收藏失败';
    favorites.value = [];
  } finally {
    loading.value = false;
  }
};

const removeFavoriteItem = async (item: FavoriteItem) => {
  removingId.value = item.problem_id;
  try {
    await removeFavorite(item.problem_id);
    favorites.value = favorites.value.filter(
      (favorite) => favorite.problem_id !== item.problem_id,
    );
    message.success(`已取消收藏「${item.problem_title}」`);
  } catch (error) {
    message.error(error instanceof Error ? error.message : '取消收藏失败');
  } finally {
    removingId.value = null;
  }
};

const openProblem = (problemId: number) => {
  router.push(`/problems/${problemId}`);
};

onMounted(loadFavorites);
</script>

<template>
  <div class="favorites-page flex min-h-[calc(100vh-var(--header-h,5rem))] flex-col bg-[#F6F8FC] dark:bg-[#0F172A] text-[#1E293B] dark:text-[#E5E7EB] ">
    <div class="favorites-hero border-b border-slate-200/60 bg-white/60 backdrop-blur-2xl dark:border-slate-800/50 dark:bg-slate-950/50">
      <div class="mx-auto flex w-full max-w-6xl flex-wrap items-end justify-between gap-4 px-4 py-8 sm:px-6 lg:px-8">
        <div>
          <p class="text-sm font-black uppercase tracking-[0.22em] text-amber-600 dark:text-amber-300">Favorites</p>
          <h1 class="mt-1 text-3xl font-black tracking-tight">收藏题目</h1>
          <p class="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
            你的私人题单，把想练的题都收进来。
          </p>
        </div>
        <span class="rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-black text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/50 dark:text-amber-300">
          共 {{ favorites.length }} 道题目
        </span>
      </div>
    </div>

    <div class="favorites-content mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
      <div v-if="loadError" class="flex flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white/85 py-16 text-center shadow-lg backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85">
        <Icon icon="material-symbols:cloud-off-rounded" class="mb-3 h-12 w-12 text-rose-400" />
        <p class="font-black">收藏列表加载失败</p>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ loadError }}</p>
        <button class="mt-4 rounded-full bg-amber-400 px-5 py-2.5 text-sm font-black text-slate-950 transition hover:bg-amber-300" @click="loadFavorites">
          重新加载
        </button>
      </div>

      <div v-else-if="loading" class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="i in 6" :key="i" class="h-40 animate-pulse rounded-3xl bg-white/70 dark:bg-slate-900/70"></div>
      </div>

      <div v-else-if="favorites.length === 0" class="flex flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white/85 py-16 text-center shadow-lg backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85">
        <Icon icon="material-symbols:star-outline-rounded" class="mb-3 h-14 w-14 text-slate-300 dark:text-slate-600" />
        <p class="font-black">还没有收藏任何题目</p>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">在题目页点击星标，就能把题目收进这里。</p>
        <button class="mt-4 rounded-full bg-amber-400 px-5 py-2.5 text-sm font-black text-slate-950 transition hover:bg-amber-300" @click="router.push('/problems')">
          前往题库
        </button>
      </div>

      <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="item in favorites"
          :key="item.problem_id"
          class="favorite-card group relative flex flex-col rounded-3xl border border-slate-200 bg-white/85 p-5 shadow-lg shadow-slate-200/50 backdrop-blur-2xl transition hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-amber-200/40 dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20 dark:hover:border-amber-800"
        >
          <button
            class="absolute right-4 top-4 z-10 rounded-xl p-2 text-amber-500 transition hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-40 dark:hover:bg-amber-950/50"
            :class="{ 'opacity-50': removingId === item.problem_id }"
            :disabled="removingId === item.problem_id"
            title="取消收藏"
            @click.stop="removeFavoriteItem(item)"
          >
            <Icon icon="material-symbols:delete-forever-rounded" class="h-5 w-5" />
          </button>

          <button class="flex flex-1 flex-col text-left" @click="openProblem(item.problem_id)">
            <span class="text-xs font-bold text-slate-400">#{{ item.problem_id }}</span>
            <h3 class="mt-1 line-clamp-2 pr-10 text-lg font-black transition group-hover:text-amber-600 dark:group-hover:text-amber-300">
              {{ item.problem_title }}
            </h3>

            <div class="mt-3 flex flex-wrap items-center gap-2">
              <span
                v-if="item.difficulty"
                class="rounded-full px-2.5 py-0.5 text-xs font-bold"
                :class="item.difficulty === '简单' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400' : item.difficulty === '中等' ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-rose-50 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400'"
              >
                {{ item.difficulty }}
              </span>
              <span
                v-for="tag in item.tags.slice(0, 3)"
                :key="tag"
                class="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300"
              >
                {{ tag }}
              </span>
            </div>

            <p v-if="item.favorited_at" class="mt-4 text-xs font-medium text-slate-400">
              收藏于 {{ formatDate(item.favorited_at) }}
            </p>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';
</style>
