<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { listRankings, type RankingData } from '../services/api';
import { Icon } from '@iconify/vue';

interface RankingItem extends RankingData {
  easy_count?: number;
  medium_count?: number;
  hard_count?: number;
}

const rankings = ref<RankingItem[]>([]);
const isLoading = ref(false);
const error = ref('');

const rankIcons = ['military-tech', 'military-tech', 'military-tech'];

const loadData = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    rankings.value = await listRankings();
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
    <div class="app-container max-w-[1200px] py-6">
      <div class="mb-6">
        <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">排行榜</h1>

      </div>

      <!-- 加载中 -->
      <div v-if="isLoading" class="space-y-4">
        <div v-for="i in 5" :key="i" class="ui-skeleton h-16 w-full rounded-xl"></div>
      </div>

      <!-- 错误 -->
      <div v-else-if="error" class="ui-empty">
        <Icon icon="material-symbols:error-outline-rounded" class="mb-2 h-12 w-12 text-rose-500" />
        <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">加载失败</p>
        <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="loadData">重试</button>
      </div>

      <!-- 排行榜列表 -->
      <div v-else class="space-y-3">
        <div
          v-for="user in rankings"
          :key="user.user_id"
          class="ui-card flex items-center gap-4 p-4 transition hover:shadow-md"
          :class="user.rank <= 3 ? 'ring-2 ring-amber-200 dark:ring-amber-800' : ''"
        >
          <!-- 排名 -->
          <div class="w-12 shrink-0 text-center">
            <Icon v-if="user.rank <= 3" :icon="`material-symbols:${rankIcons[user.rank - 1]}`" class="h-9 w-9 text-amber-500" />
            <span v-else class="text-lg font-black text-[#64748B] dark:text-[#94A3B8]">#{{ user.rank }}</span>
          </div>

          <!-- 头像 -->
          <div class="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA] text-xl">
             <Icon icon="material-symbols:person-rounded" class="h-6 w-6" />
          </div>

          <!-- 用户信息 -->
          <div class="min-w-0 flex-1">
            <div class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ user.username }}</div>
            <div class="mt-1 flex items-center gap-3 text-xs text-[#94A3B8]">
               <span class="inline-flex items-center gap-1"><Icon icon="material-symbols:circle" class="h-2.5 w-2.5 text-emerald-500" />简单 {{ user.easy_count || 0 }}</span>
               <span class="inline-flex items-center gap-1"><Icon icon="material-symbols:circle" class="h-2.5 w-2.5 text-amber-500" />中等 {{ user.medium_count || 0 }}</span>
               <span class="inline-flex items-center gap-1"><Icon icon="material-symbols:circle" class="h-2.5 w-2.5 text-rose-500" />困难 {{ user.hard_count || 0 }}</span>
            </div>
          </div>

          <!-- 解题数 -->
          <div class="shrink-0 text-center">
            <div class="text-lg font-black text-[#1E293B] dark:text-[#E5E7EB]">{{ user.solved_count }}</div>
            <div class="text-[11px] text-[#94A3B8]">解题</div>
          </div>

          <!-- 积分 -->
          <div class="shrink-0 text-center">
            <div class="text-2xl font-black text-[#2563EB] dark:text-[#60A5FA]">{{ user.rating }}</div>
            <div class="text-[11px] text-[#94A3B8]">积分</div>
          </div>
        </div>
      </div>

      <!-- 空态 -->
      <div v-if="!isLoading && !error && rankings.length === 0" class="ui-empty mt-6">
        <Icon icon="material-symbols:leaderboard-rounded" class="mb-2 h-12 w-12 text-slate-400" />
        <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">暂无排名数据</p>
        <p class="text-sm text-[#64748B] dark:text-[#94A3B8]">提交代码通过后即可上榜</p>
      </div>
    </div>
  </div>
</template>
