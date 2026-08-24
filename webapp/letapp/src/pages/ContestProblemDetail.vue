<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getContestProblem, type ContestProblemData } from '../services/api';
import MarkdownComponent from '../components/MarkdownComponent.vue';

const route = useRoute();
const router = useRouter();
const contestId = Number(route.params.contestId);
const problemId = Number(route.params.problemId);

const problem = ref<ContestProblemData | null>(null);
const isLoading = ref(true);
const error = ref('');

const difficultyClass = (d: string) =>
  d === '简单' ? 'ui-diff ui-diff-easy'
  : d === '中等' ? 'ui-diff ui-diff-mid'
  : 'ui-diff ui-diff-hard';

const loadData = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    problem.value = await getContestProblem(problemId);
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败';
  } finally {
    isLoading.value = false;
  }
};

const openEditor = () => {
  router.push(`/playground?contest=${contestId}&problem=${problemId}`);
};

onMounted(loadData);
</script>

<template>
  <div class="min-h-[calc(100vh-var(--header-h,4rem))] bg-[#F6F8FC] dark:bg-[#0F172A]">
    <div class="mx-auto max-w-[960px] px-6 py-8">
      <button class="ui-btn ui-btn-secondary ui-btn-sm mb-6" @click="router.push(`/contests/${contestId}`)">
        ← 返回题目列表
      </button>

      <div v-if="isLoading" class="space-y-4">
        <div class="ui-skeleton h-10 w-64 rounded-lg"></div>
        <div class="ui-skeleton h-64 w-full rounded-xl"></div>
      </div>

      <div v-else-if="error" class="ui-empty">
        <span class="mb-2 text-5xl">❌</span>
        <p class="font-bold">{{ error }}</p>
        <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="loadData">重试</button>
      </div>

      <template v-else-if="problem">
        <!-- 题目摘要 -->
        <div class="mb-6 border-b border-[#E2E8F0] pb-4 dark:border-[#1E293B]">
          <div class="flex items-center gap-3">
            <span class="text-sm font-black text-[#2563EB] dark:text-[#60A5FA]">{{ problem.problem_index }}</span>
            <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">{{ problem.title }}</h1>
          </div>
          <div class="mt-3 flex flex-wrap items-center gap-3">
            <span :class="difficultyClass(problem.difficulty)">{{ problem.difficulty }}</span>
            <span class="text-sm text-[#64748B] dark:text-[#94A3B8]">⏱ {{ problem.time_limit }}ms</span>
            <span class="text-sm text-[#64748B] dark:text-[#94A3B8]">💾 {{ problem.memory_limit }}MB</span>
          </div>
        </div>

        <!-- 题目正文 -->
        <div class="prose-wrapper">
          <MarkdownComponent
            :content="{ content: problem.description }"
            :show-nav="false"
            :show-heading-links="false"
          />
        </div>

        <!-- 输入格式 -->
        <div v-if="problem.input_desc" class="mt-6">
          <h2 class="mb-2 text-lg font-bold text-[#1E293B] dark:text-[#E5E7EB]">输入格式</h2>
          <div class="rounded-lg bg-[#F8FAFC] p-4 text-sm dark:bg-[#1E293B]">{{ problem.input_desc }}</div>
        </div>

        <!-- 输出格式 -->
        <div v-if="problem.output_desc" class="mt-6">
          <h2 class="mb-2 text-lg font-bold text-[#1E293B] dark:text-[#E5E7EB]">输出格式</h2>
          <div class="rounded-lg bg-[#F8FAFC] p-4 text-sm dark:bg-[#1E293B]">{{ problem.output_desc }}</div>
        </div>

        <!-- 提交按钮 -->
        <div class="mt-8 flex justify-center">
          <button class="ui-btn ui-btn-primary px-8 py-3 text-base" @click="openEditor">
            🚀 开始答题
          </button>
        </div>
      </template>
    </div>
  </div>
</template>
