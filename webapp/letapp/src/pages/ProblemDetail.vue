<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { NButton, useMessage } from 'naive-ui';
import { useThemeStore } from '../stores/theme';
import { storeToRefs } from 'pinia';
import MonacoEditor from '../components/MonacoEditor.vue';
import SelfTestPanel from '../components/SelfTestPanel.vue';
import { apiRequest } from '../services/api';

interface TestCase {
  input: string;
  output: string;
}

interface Problem {
  id: number;
  title: string;
  difficulty: '简单' | '中等' | '困难';
  tags: string[];
  description: string;
  inputFormat: string;
  outputFormat: string;
  samples: TestCase[];
  testCases: TestCase[];
  timeLimit: number;
  memoryLimit: number;
}

const route = useRoute();
const router = useRouter();
const message = useMessage();
const themeStore = useThemeStore();
const { isDark } = storeToRefs(themeStore);

const leftPanelOpen = ref(true);
const language = ref('cpp');
const code = ref('');
const isSubmitting = ref(false);
const submitResult = ref<string | null>(null);
const activeTab = ref<'desc' | 'testcases'>('desc');

interface TestResult {
  testCaseIndex: number;
  passed: boolean;
  actualOutput: string;
}

const testResults = ref<TestResult[]>([]);
const currentResultPage = ref(0);
const failedTestCaseIndex = ref<number | null>(null);

const stdin = ref('');
const expectedOutput = ref('');
const selfTestOutput = ref('');
const selfTestStatus = ref('');
const isSelfTesting = ref(false);
const selfTestVerdict = ref<'pass' | 'fail' | null>(null);

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
    testCases: [
      { input: '5 10\n1 3 5 7 9', output: '2 4' },
      { input: '4 0\n0 2 4 6', output: '0 0' },
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
    testCases: [
      { input: 'abc123', output: '321cba' },
      { input: 'x', output: 'x' },
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
    testCases: [
      { input: '0', output: '0' },
      { input: '20', output: '6765' },
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
  if (pollTimer.value) {
    clearInterval(pollTimer.value);
    pollTimer.value = null;
  }
};

interface SubmissionResponse {
  id: number;
  status: string;
  testcase_results?: any[];
  fail_testcase_index?: number | null;
  time_used?: number;
}

const pollTimer = ref<ReturnType<typeof setInterval> | null>(null);

const submitCode = async () => {
  if (!code.value.trim()) {
    message.warning('请先编写代码');
    return;
  }
  if (pollTimer.value) {
    clearInterval(pollTimer.value);
    pollTimer.value = null;
  }
  isSubmitting.value = true;
  submitResult.value = null;
  testResults.value = [];
  failedTestCaseIndex.value = null;
  currentResultPage.value = 0;

  const p = problem.value;
  if (!p) return;

  try {
    const created = await apiRequest<SubmissionResponse>('/submissions', {
      method: 'POST',
      body: JSON.stringify({
        problem_id: p.id,
        code: code.value,
        language: language.value,
      }),
    });

    if (created.status === 'Pending' || created.status === 'Running') {
      pollTimer.value = setInterval(async () => {
        try {
          const res = await apiRequest<SubmissionResponse>(`/submissions/${created.id}`);
          if (res.status !== 'Pending' && res.status !== 'Running') {
            if (pollTimer.value) {
              clearInterval(pollTimer.value);
              pollTimer.value = null;
            }
            _handleJudgeResult(res, p);
          }
        } catch {
          if (pollTimer.value) {
            clearInterval(pollTimer.value);
            pollTimer.value = null;
          }
          isSubmitting.value = false;
          message.error('查询判题结果失败');
        }
      }, 1000);
    } else {
      _handleJudgeResult(created, p);
    }
  } catch (e: any) {
    message.error(e?.message || '提交失败');
    isSubmitting.value = false;
  }
};

const _handleJudgeResult = (res: SubmissionResponse, p: Problem) => {
  const results: TestResult[] = [];

  if (res.testcase_results && res.testcase_results.length > 0) {
    for (const tr of res.testcase_results) {
      const idx = tr.testCaseIndex ?? 0;
      results.push({
        testCaseIndex: idx,
        passed: tr.passed,
        actualOutput: tr.actualOutput || tr.stdout || '',
      });
    }
  } else {
    const total = p.testCases.length;
    const firstFailedIdx = res.fail_testcase_index;
    for (let i = 0; i < total; i++) {
      const passed = firstFailedIdx === null || firstFailedIdx === undefined || i < firstFailedIdx;
      results.push({
        testCaseIndex: i,
        passed,
        actualOutput: passed ? (p.testCases[i]?.output ?? '') : '(实际输出未记录)',
      });
    }
  }

  testResults.value = results;

  if (res.status === 'AC') {
    submitResult.value = 'AC';
    currentResultPage.value = 0;
  } else {
    submitResult.value = 'WA';
    const failedIdx = res.fail_testcase_index ?? 0;
    failedTestCaseIndex.value = failedIdx;
    currentResultPage.value = failedIdx;
  }

  isSubmitting.value = false;
};

const editorLanguageMap: Record<string, string> = {
  cpp: 'cpp', python: 'python', java: 'java',
};

const runSelfTest = async () => {
  if (!code.value.trim()) {
    message.warning('请先编写代码');
    return;
  }
  isSelfTesting.value = true;
  selfTestOutput.value = '';
  selfTestStatus.value = '';
  selfTestVerdict.value = null;
  try {
    const res = await apiRequest<any>('/code/run', {
      method: 'POST',
      body: JSON.stringify({
        code: code.value,
        language: editorLanguageMap[language.value] || language.value,
        stdin: stdin.value,
      }),
    });
    const stderr = (res.stderr || '').trim();
    let stdout = (res.stdout || '').trim();
    if (stderr) {
      selfTestOutput.value = stderr;
      selfTestStatus.value = '运行出错';
      selfTestVerdict.value = 'fail';
    } else {
      selfTestOutput.value = stdout;
      const expected = expectedOutput.value.trim();
      if (expected) {
        if (stdout === expected) {
          selfTestStatus.value = '通过';
          selfTestVerdict.value = 'pass';
        } else {
          selfTestStatus.value = '未通过';
          selfTestVerdict.value = 'fail';
        }
      } else {
        selfTestStatus.value = stdout ? '执行成功' : '程序无输出';
      }
    }
  } catch {
    selfTestOutput.value = '请求失败，请重试';
    selfTestStatus.value = '网络错误';
    selfTestVerdict.value = 'fail';
  }
  isSelfTesting.value = false;
};

const handleKeyboard = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !isSubmitting.value) {
    e.preventDefault();
    submitCode();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyboard);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard);
  if (pollTimer.value) {
    clearInterval(pollTimer.value);
    pollTimer.value = null;
  }
});
</script>

<template>
  <div v-if="!problem" class="flex min-h-[calc(100vh-5rem)] items-center justify-center">
    <div class="text-center">
      <Icon icon="material-symbols:error-outline" class="mx-auto mb-4 h-12 w-12 text-slate-300 dark:text-slate-600" />
      <p class="text-lg font-bold text-slate-500 dark:text-slate-400">题目不存在</p>
      <NButton class="mt-4" @click="router.push('/problems')">返回题库</NButton>
    </div>
  </div>

  <div v-else class="flex min-h-[calc(100vh-5rem)] bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <div class="flex flex-1 flex-col lg:flex-row relative">
      <div class="relative flex flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" :class="leftPanelOpen ? 'w-full lg:w-[420px]' : 'w-0 lg:w-0 overflow-hidden'">
        <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4 dark:border-slate-800">
          <div class="flex items-center gap-3 min-w-0">
            <span class="text-lg font-black truncate">{{ problem.id }}. {{ problem.title }}</span>
            <span class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold" :class="problem.difficulty === '简单' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400' : problem.difficulty === '中等' ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-rose-50 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400'">{{ problem.difficulty }}</span>
          </div>
          <button class="shrink-0 rounded-xl p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" title="收起左侧" @click="leftPanelOpen = false">
            <Icon icon="material-symbols:chevron-left" class="h-5 w-5" />
          </button>
        </div>

        <div class="flex gap-1 border-b border-slate-100 px-5 dark:border-slate-800">
          <button class="px-3 py-3 text-sm font-bold border-b-2 transition" :class="activeTab === 'desc' ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400' : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'" @click="activeTab = 'desc'">题目</button>
          <button class="px-3 py-3 text-sm font-bold border-b-2 transition" :class="activeTab === 'testcases' ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400' : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'" @click="activeTab = 'testcases'">测试用例 ({{ problem.testCases.length }})</button>
        </div>

        <div v-show="activeTab === 'desc'" class="flex-1 overflow-y-auto px-5 py-5">
          <div class="mb-6 flex flex-wrap gap-6 text-sm text-slate-500 dark:text-slate-400">
            <span>时间限制：{{ problem.timeLimit }}ms</span>
            <span>内存限制：{{ problem.memoryLimit }}MB</span>
          </div>

          <h3 class="text-base font-black mb-2">题目描述</h3>
          <p class="whitespace-pre-line leading-7 text-sm text-slate-700 dark:text-slate-300">{{ problem.description }}</p>

          <h3 class="mt-5 text-base font-black mb-2">输入格式</h3>
          <p class="whitespace-pre-line leading-7 text-sm text-slate-700 dark:text-slate-300">{{ problem.inputFormat }}</p>

          <h3 class="mt-5 text-base font-black mb-2">输出格式</h3>
          <p class="whitespace-pre-line leading-7 text-sm text-slate-700 dark:text-slate-300">{{ problem.outputFormat }}</p>

          <h3 class="mt-5 text-base font-black mb-3">样例</h3>
          <div v-for="(sample, i) in problem.samples" :key="i" class="mb-3">
            <div class="mb-1 text-xs font-bold uppercase tracking-wider text-slate-400">样例 #{{ i + 1 }}</div>
            <div class="grid gap-3 sm:grid-cols-2">
              <pre class="rounded-xl bg-slate-900 p-3 font-mono text-xs text-emerald-300 overflow-x-auto">{{ sample.input }}</pre>
              <pre class="rounded-xl bg-slate-900 p-3 font-mono text-xs text-emerald-300 overflow-x-auto">{{ sample.output }}</pre>
            </div>
          </div>
        </div>

        <div v-show="activeTab === 'testcases'" class="flex-1 overflow-y-auto px-5 py-5">
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">以下为判题使用的测试数据（隐藏），提交代码后将自动运行这些测试点。</p>
          <div v-for="(tc, i) in problem.testCases" :key="i" class="mb-4 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/50">
            <div class="mb-1 text-xs font-bold text-slate-500 dark:text-slate-400">测试点 #{{ i + 1 }}</div>
            <div class="grid gap-2">
              <div>
                <div class="text-xs text-slate-400 mb-0.5">输入</div>
                <pre class="rounded-lg bg-slate-900 p-2 font-mono text-xs text-emerald-300 overflow-x-auto">{{ tc.input }}</pre>
              </div>
              <div>
                <div class="text-xs text-slate-400 mb-0.5">期望输出</div>
                <pre class="rounded-lg bg-slate-900 p-2 font-mono text-xs text-emerald-300 overflow-x-auto">{{ tc.output }}</pre>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 border-t border-slate-100 px-5 py-3 dark:border-slate-800">
          <button class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" @click="router.push('/problems')">
            <Icon icon="material-symbols:arrow-back" class="h-4 w-4" />返回
          </button>
        </div>
      </div>

      <div class="flex flex-1 min-w-0">
        <div class="flex flex-col flex-1 min-w-0">
          <div class="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3 dark:border-slate-800 dark:bg-slate-900">
            <div class="flex items-center gap-2">
              <button class="rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden" @click="leftPanelOpen = !leftPanelOpen">
                <Icon icon="material-symbols:menu" class="h-5 w-5" />
              </button>
              <div class="flex gap-2">
                <button v-for="lang in [{v:'cpp',l:'C++'},{v:'python',l:'Python'},{v:'java',l:'Java'}]" :key="lang.v" class="rounded-lg px-3 py-1.5 text-xs font-bold transition" :class="language === lang.v ? 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'" @click="updateLanguage(lang.v)">{{ lang.l }}</button>
              </div>
            </div>
            <NButton type="primary" size="small" :loading="isSubmitting" @click="submitCode">提交</NButton>
          </div>

          <MonacoEditor v-model="code" :language="editorLanguageMap[language] || 'cpp'" :is-dark="isDark" height="100%" />

          <SelfTestPanel
            :stdin="stdin"
            :expected-output="expectedOutput"
            :output="selfTestOutput"
            :status="selfTestStatus"
            :verdict="selfTestVerdict"
            :is-running="isSelfTesting"
            @update:stdin="stdin = $event"
            @update:expected-output="expectedOutput = $event"
            @run="runSelfTest"
          />
        </div>

        <div v-if="submitResult" class="w-96 shrink-0 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col">
          <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <span class="text-sm font-black text-slate-800 dark:text-slate-100">判题结果</span>
            <span class="rounded-full px-3 py-1 text-xs font-bold tracking-wider" :class="submitResult === 'AC' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-rose-50 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400'">{{ submitResult === 'AC' ? 'ACCEPTED' : 'WRONG ANSWER' }}</span>
          </div>

          <div class="flex flex-col flex-1 min-h-0">
            <div class="px-5 py-4 overflow-y-auto space-y-1.5">
              <div v-for="(tr, i) in testResults" :key="i" class="flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-bold cursor-pointer transition" :class="currentResultPage === i ? 'bg-slate-100 dark:bg-slate-800' : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'" @click="currentResultPage = i">
                <Icon :icon="tr.passed ? 'material-symbols:check-circle' : 'material-symbols:cancel'" :class="tr.passed ? 'text-emerald-500' : 'text-rose-500'" class="h-4 w-4 shrink-0" />
                <span class="text-slate-600 dark:text-slate-400">测试点 #{{ i + 1 }}</span>
                <span class="ml-auto" :class="tr.passed ? 'text-emerald-500' : 'text-rose-500'">{{ tr.passed ? '通过' : '未通过' }}</span>
              </div>
            </div>

            <div class="border-t border-slate-200 dark:border-slate-800 flex flex-col flex-1 min-h-0">
              <div class="flex items-center justify-between px-5 py-3">
                <span class="text-sm font-bold text-slate-700 dark:text-slate-300">测试点 #{{ currentResultPage + 1 }}</span>
                <div class="flex items-center gap-1">
                  <button class="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30" :disabled="currentResultPage === 0" @click="currentResultPage--">
                    <Icon icon="material-symbols:chevron-left" class="h-4 w-4" />
                  </button>
                  <span class="text-xs text-slate-400 px-1">{{ currentResultPage + 1 }} / {{ testResults.length }}</span>
                  <button class="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30" :disabled="currentResultPage >= testResults.length - 1" @click="currentResultPage++">
                    <Icon icon="material-symbols:chevron-right" class="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div v-if="testResults.length > 0" class="flex-1 overflow-y-auto px-5 pb-4 space-y-3">
                <div class="result-section">
                  <div class="result-header">输入</div>
                  <pre class="result-body">{{ problem.testCases[currentResultPage]?.input }}</pre>
                </div>
                <div class="result-section">
                  <div class="result-header">期望输出</div>
                  <pre class="result-body">{{ problem.testCases[currentResultPage]?.output }}</pre>
                </div>
                <div class="result-section">
                  <div class="result-header">
                    <span>实际输出</span>
                    <span class="result-badge" :class="(testResults[currentResultPage]?.passed ? 'badge-pass' : 'badge-fail')">{{ testResults[currentResultPage]?.passed ? '✓ PASS' : '✗ FAILED' }}</span>
                  </div>
                  <div class="result-body-wrap">
                    <pre class="result-body" :class="{ 'result-error': !testResults[currentResultPage]?.passed }">{{ testResults[currentResultPage]?.actualOutput }}</pre>
                    <div class="result-footer">
                      <span :class="submitResult === 'AC' ? 'text-emerald-500' : 'text-rose-500'">测试点 #{{ currentResultPage + 1 }} — {{ submitResult === 'AC' ? '通过全部' : testResults[currentResultPage]?.passed ? '通过' : '未通过' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <button v-if="!leftPanelOpen" class="fixed left-3 top-1/2 z-50 -translate-y-1/2 rounded-xl border border-slate-200 bg-white p-2 text-slate-400 shadow-lg hover:text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:hover:text-slate-300" title="展开左侧" @click="leftPanelOpen = true">
      <Icon icon="material-symbols:chevron-right" class="h-5 w-5" />
    </button>
  </div>
</template>

<style scoped>
.result-section {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  overflow: hidden;
}
:global(.dark) .result-section {
  border-color: #1e293b;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  font-weight: 800;
  color: #1e293b;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}
:global(.dark) .result-header {
  color: #f8fafc;
  background: #0f172a;
  border-color: #1e293b;
}

.result-body-wrap {
  overflow: hidden;
}

.result-body {
  min-height: 64px;
  padding: 14px 18px;
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
  background: linear-gradient(to bottom, #f1f5f9 95%, #e2e8f0 95%, #e2e8f0 100%);
  color: #1e293b;
}
:global(.dark) .result-body {
  background: linear-gradient(to bottom, #020617 95%, #0f172a 95%, #0f172a 100%);
  color: #6ee7b7;
}

.result-error {
  color: #dc2626;
}
:global(.dark) .result-error {
  color: #fca5a5;
}

.result-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0.35rem 0.75rem;
  font-size: 0.7rem;
  font-weight: 600;
  background: #e2e8f0;
  border-top: 1px dashed #94a3b8;
}
:global(.dark) .result-footer {
  background: #0f172a;
  border-color: #475569;
}

.result-badge {
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.05em;
  padding: 1px 8px;
  border-radius: 999px;
}
.badge-pass {
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
}
.badge-fail {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}
</style>
