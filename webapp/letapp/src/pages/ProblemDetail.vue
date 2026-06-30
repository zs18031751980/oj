<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { NButton, useMessage } from 'naive-ui';

interface Problem {
  id: number;
  title: string;
  difficulty: '简单' | '中等' | '困难';
  tags: string[];
  description: string;
  inputFormat: string;
  outputFormat: string;
  samples: { input: string; output: string }[];
  timeLimit: number;
  memoryLimit: number;
}

const route = useRoute();
const router = useRouter();
const message = useMessage();

const language = ref('cpp');
const code = ref('');
const isSubmitting = ref(false);
const submitResult = ref<string | null>(null);


const problems: Record<number, Problem> = {
  1001: {
    id: 1001, title: '两数之和', difficulty: '简单', tags: ['数组', '哈希表'],
    description: '给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出和为目标值 target 的那两个整数，并返回它们的数组下标。\n\n你可以假设每种输入只会对应一个答案，并且你不能使用两次相同的元素。',
    inputFormat: '第一行包含两个整数 n 和 target，分别表示数组长度和目标值。\n第二行包含 n 个整数，表示数组 nums。',
    outputFormat: '输出两个整数，表示两个数的下标（从 0 开始），用空格分隔。',
    samples: [
      { input: '4 9\n2 7 11 15', output: '0 1' },
      { input: '3 6\n3 2 4', output: '1 2' },
    ],
    timeLimit: 1000, memoryLimit: 256,
  },
  1002: {
    id: 1002, title: '反转字符串', difficulty: '简单', tags: ['字符串', '双指针'],
    description: '编写一个函数，其作用是将输入的字符串反转过来。输入字符串以字符数组的形式给出。\n\n不要给另外的数组分配额外的空间，你必须原地修改输入数组。',
    inputFormat: '一行字符串 s，只包含可打印 ASCII 字符。',
    outputFormat: '输出反转后的字符串。',
    samples: [
      { input: 'hello', output: 'olleh' },
      { input: 'A man', output: 'nam A' },
    ],
    timeLimit: 1000, memoryLimit: 256,
  },
  1003: {
    id: 1003, title: '斐波那契数列', difficulty: '简单', tags: ['递归', '动态规划'],
    description: '斐波那契数列的定义如下：\nF(0) = 0, F(1) = 1\nF(n) = F(n-1) + F(n-2)（n ≥ 2）\n\n给定 n，请计算 F(n)。',
    inputFormat: '一个整数 n（0 ≤ n ≤ 30）。',
    outputFormat: '输出 F(n) 的值。',
    samples: [
      { input: '4', output: '3' },
      { input: '10', output: '55' },
    ],
    timeLimit: 1000, memoryLimit: 256,
  },
};

const problem = computed(() => {
  const id = Number(route.params.id);
  return problems[id] || null;
});

const languageTemplates: Record<string, string> = {
  cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n  // 在此编写代码\n  return 0;\n}',
  python: '# 在此编写代码\n',
  java: 'public class Main {\n  public static void main(String[] args) {\n    // 在此编写代码\n  }\n}',
};

if (!code.value) {
  code.value = languageTemplates[language.value] || '';
}

const updateLanguage = (lang: string) => {
  language.value = lang;
  code.value = languageTemplates[lang] || '';
  submitResult.value = null;
};

const submitCode = async () => {
  if (!code.value.trim()) {
    message.warning('请先编写代码');
    return;
  }
  isSubmitting.value = true;
  submitResult.value = null;
  await new Promise(r => setTimeout(r, 1500));
  const outcomes = ['AC', 'WA', 'RE'];
  submitResult.value = outcomes[Math.floor(Math.random() * outcomes.length)] || 'RE';
  isSubmitting.value = false;
};

const statusColor = (s: string) => {
  if (s === 'AC') return { color: '#10b981', bg: '#d1fae5' };
  return { color: '#ef4444', bg: '#fee2e2' };
};
</script>

<template>
  <div v-if="!problem" class="flex min-h-[calc(100vh-5rem)] items-center justify-center">
    <div class="text-center">
      <Icon icon="material-symbols:error-outline" class="mx-auto mb-4 h-12 w-12 text-slate-300 dark:text-slate-600" />
      <p class="text-lg font-bold text-slate-500 dark:text-slate-400">题目不存在</p>
      <NButton class="mt-4" @click="router.push('/problems')">返回题库</NButton>
    </div>
  </div>

  <div v-else class="flex min-h-[calc(100vh-5rem)] flex-col bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <div class="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:flex-row">
      <div class="flex-1 overflow-y-auto">
        <div class="mb-4 flex flex-wrap items-center gap-3">
          <button class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" @click="router.push('/problems')">
            <Icon icon="material-symbols:arrow-back" class="h-4 w-4" />返回
          </button>
          <span class="text-2xl font-black">{{ problem.id }}. {{ problem.title }}</span>
          <span class="rounded-full px-3 py-1 text-xs font-bold" :class="problem.difficulty === '简单' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400' : problem.difficulty === '中等' ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-rose-50 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400'">{{ problem.difficulty }}</span>
        </div>

        <div class="mb-6 flex flex-wrap gap-6 text-sm text-slate-500 dark:text-slate-400">
          <span>时间限制：{{ problem.timeLimit }}ms</span>
          <span>内存限制：{{ problem.memoryLimit }}MB</span>
        </div>

        <div class="prose prose-slate dark:prose-invert max-w-none">
          <h3 class="text-lg font-black">题目描述</h3>
          <p class="whitespace-pre-line leading-7 text-slate-700 dark:text-slate-300">{{ problem.description }}</p>

          <h3 class="mt-6 text-lg font-black">输入格式</h3>
          <p class="whitespace-pre-line leading-7 text-slate-700 dark:text-slate-300">{{ problem.inputFormat }}</p>

          <h3 class="mt-6 text-lg font-black">输出格式</h3>
          <p class="whitespace-pre-line leading-7 text-slate-700 dark:text-slate-300">{{ problem.outputFormat }}</p>

          <h3 class="mt-6 text-lg font-black">样例</h3>
          <div v-for="(sample, i) in problem.samples" :key="i" class="mb-4 grid gap-4 sm:grid-cols-2">
            <div>
              <div class="mb-1 text-xs font-bold uppercase tracking-wider text-slate-400">输入 #{{ i + 1 }}</div>
              <pre class="rounded-xl bg-slate-900 p-4 font-mono text-sm text-emerald-300 overflow-x-auto">{{ sample.input }}</pre>
            </div>
            <div>
              <div class="mb-1 text-xs font-bold uppercase tracking-wider text-slate-400">输出 #{{ i + 1 }}</div>
              <pre class="rounded-xl bg-slate-900 p-4 font-mono text-sm text-emerald-300 overflow-x-auto">{{ sample.output }}</pre>
            </div>
          </div>
        </div>
      </div>

      <div class="w-full shrink-0 lg:w-[480px]">
        <div class="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-lg dark:border-slate-800 dark:bg-slate-900">
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-3 dark:border-slate-800">
            <div class="flex gap-2">
              <button v-for="lang in [{v:'cpp',l:'C++'},{v:'python',l:'Python'},{v:'java',l:'Java'}]" :key="lang.v" class="rounded-lg px-3 py-1.5 text-xs font-bold transition" :class="language === lang.v ? 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'" @click="updateLanguage(lang.v)">{{ lang.l }}</button>
            </div>
            <NButton type="primary" size="small" :loading="isSubmitting" @click="submitCode">提交</NButton>
          </div>

          <textarea v-model="code" class="h-[400px] w-full resize-none border-none bg-slate-950 p-5 font-mono text-sm text-emerald-300 outline-none" spellcheck="false"></textarea>

          <div v-if="submitResult" class="border-t border-slate-100 px-5 py-4 dark:border-slate-800">
            <div class="flex items-center gap-3">
              <span class="rounded-full px-4 py-1.5 text-sm font-black tracking-wider" :style="{ background: statusColor(submitResult).bg, color: statusColor(submitResult).color }">{{ submitResult === 'AC' ? 'Accepted' : submitResult === 'WA' ? 'Wrong Answer' : 'Runtime Error' }}</span>
              <span class="text-xs text-slate-400">通过 {{ submitResult === 'AC' ? '全部' : '部分' }} 测试点</span>
            </div>
          </div>

          <div v-else class="border-t border-slate-100 px-5 py-4 text-center text-sm text-slate-400 dark:border-slate-800 dark:text-slate-500">
            编写代码后点击「提交」查看评测结果
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
