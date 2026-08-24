<script setup lang="ts">
import { ref, defineAsyncComponent, onMounted } from 'vue';
import { useMessage } from 'naive-ui';
import {
  listContests, createContest, getContest,
  type ContestData
} from '../../services/api';
import { apiRequest } from '../../services/api';

const MarkdownComponent = defineAsyncComponent(
  () => import('../../components/MarkdownComponent.vue'),
);

const message = useMessage();

// 比赛列表
const contests = ref<ContestData[]>([]);
const isLoadingContests = ref(false);
const selectedContestId = ref<number | null>(null);
const selectedContest = ref<ContestData | null>(null);

// 比赛表单
const showContestForm = ref(false);
const contestForm = ref({
  title: '',
  description: '',
  contest_type: 'ACM',
  start_time: '',
  end_time: '',
});

// 题目列表
const problems = ref<any[]>([]);
const isLoadingProblems = ref(false);
const showProblemForm = ref(false);
const editingProblem = ref(false);
const editingProblemId = ref<number | null>(null);
const problemForm = ref({
  problem_index: '',
  title: '',
  description: '',
  input_desc: '',
  output_desc: '',
  correct_answer: '',
  time_limit: 1000,
  memory_limit: 256,
  difficulty: '中等',
});
const isGeneratingTestcases = ref(false);

// 加载比赛列表
const loadContests = async () => {
  isLoadingContests.value = true;
  try {
    contests.value = await listContests();
  } catch (e) {
    message.error('加载比赛列表失败');
  } finally {
    isLoadingContests.value = false;
  }
};

// 选择比赛
const selectContest = async (id: number) => {
  selectedContestId.value = id;
  try {
    selectedContest.value = await getContest(id);
    await loadProblems(id);
  } catch (e) {
    message.error('加载比赛详情失败');
  }
};

// 加载比赛题目
const loadProblems = async (contestId: number) => {
  isLoadingProblems.value = true;
  try {
    problems.value = await apiRequest<any[]>(`/admin/contests/?contest_id=${contestId}`);
  } catch (e) {
    message.error('加载题目列表失败');
  } finally {
    isLoadingProblems.value = false;
  }
};

// 创建/更新比赛
const saveContest = async () => {
  if (!contestForm.value.title.trim()) {
    message.warning('请输入比赛标题');
    return;
  }
  try {
    await createContest(contestForm.value);
    message.success('比赛创建成功');
    showContestForm.value = false;
    contestForm.value = { title: '', description: '', contest_type: 'ACM', start_time: '', end_time: '' };
    await loadContests();
  } catch (e) {
    message.error(e instanceof Error ? e.message : '创建失败');
  }
};

// 打开题目表单
const openProblemForm = (problem?: any) => {
  if (problem) {
    editingProblem.value = true;
    editingProblemId.value = problem.id;
    problemForm.value = {
      problem_index: problem.problem_index,
      title: problem.title,
      description: problem.description,
      input_desc: problem.input_desc || '',
      output_desc: problem.output_desc || '',
      correct_answer: problem.correct_answer,
      time_limit: problem.time_limit,
      memory_limit: problem.memory_limit,
      difficulty: problem.difficulty,
    };
  } else {
    editingProblem.value = false;
    editingProblemId.value = null;
    problemForm.value = {
      problem_index: String.fromCharCode(65 + problems.value.length),
      title: '',
      description: '',
      input_desc: '',
      output_desc: '',
      correct_answer: '',
      time_limit: 1000,
      memory_limit: 256,
      difficulty: '中等',
    };
  }
  showProblemForm.value = true;
};

// 保存题目
const saveProblem = async () => {
  if (!selectedContestId.value) return;
  const f = problemForm.value;
  if (!f.problem_index.trim() || !f.title.trim() || !f.description.trim() || !f.correct_answer.trim()) {
    message.warning('请填写所有必填字段');
    return;
  }

  isGeneratingTestcases.value = true;
  try {
    if (editingProblem.value && editingProblemId.value) {
      await apiRequest(`/admin/contests/${editingProblemId.value}`, {
        method: 'PUT',
        body: JSON.stringify(f),
      });
      message.success('题目更新成功');
    } else {
      await apiRequest(`/admin/contests/?contest_id=${selectedContestId.value}`, {
        method: 'POST',
        body: JSON.stringify(f),
      });
      message.success('题目创建成功，测试用例已自动生成');
    }
    showProblemForm.value = false;
    await loadProblems(selectedContestId.value);
  } catch (e) {
    message.error(e instanceof Error ? e.message : '保存失败');
  } finally {
    isGeneratingTestcases.value = false;
  }
};

// 删除题目
const deleteProblem = async (id: number) => {
  if (!confirm('确定删除此题目？')) return;
  try {
    await apiRequest(`/admin/contests/${id}`, { method: 'DELETE' });
    message.success('删除成功');
    if (selectedContestId.value) await loadProblems(selectedContestId.value);
  } catch (e) {
    message.error('删除失败');
  }
};

// 重新生成测试用例
const regenerateTestcases = async (problemId: number) => {
  try {
    const res = await apiRequest<{ count: number }>(`/admin/contests/${problemId}/regenerate-testcases`, {
      method: 'POST',
    });
    message.success(`已重新生成 ${res.count} 组测试用例`);
    if (selectedContestId.value) await loadProblems(selectedContestId.value);
  } catch (e) {
    message.error('重新生成失败');
  }
};

const difficultyClass = (d: string) =>
  d === '简单' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400'
  : d === '中等' ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400'
  : 'bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400';

onMounted(loadContests);
</script>

<template>
  <div class="p-6">
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-black">比赛管理</h1>
      <button class="ui-btn ui-btn-primary" @click="showContestForm = true">
        ➕ 创建比赛
      </button>
    </div>

    <!-- 创建比赛弹窗 -->
    <div v-if="showContestForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="ui-card w-full max-w-lg p-6">
        <h2 class="mb-4 text-lg font-bold">创建比赛</h2>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-bold">比赛标题 *</label>
            <input v-model="contestForm.title" class="ui-input w-full" placeholder="例：2026 春季算法竞赛" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-bold">比赛描述</label>
            <textarea v-model="contestForm.description" class="ui-input w-full" rows="3" placeholder="比赛简介..."></textarea>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1 block text-sm font-bold">比赛类型</label>
              <select v-model="contestForm.contest_type" class="ui-input w-full">
                <option value="ACM">ACM</option>
                <option value="周赛">周赛</option>
                <option value="决赛">决赛</option>
              </select>
            </div>
            <div></div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1 block text-sm font-bold">开始时间</label>
              <input v-model="contestForm.start_time" type="datetime-local" class="ui-input w-full" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-bold">结束时间</label>
              <input v-model="contestForm.end_time" type="datetime-local" class="ui-input w-full" />
            </div>
          </div>
        </div>
        <div class="mt-6 flex justify-end gap-3">
          <button class="ui-btn ui-btn-ghost" @click="showContestForm = false">取消</button>
          <button class="ui-btn ui-btn-primary" @click="saveContest">创建</button>
        </div>
      </div>
    </div>

    <!-- 比赛列表 -->
    <div v-if="isLoadingContests" class="space-y-3">
      <div v-for="i in 3" :key="i" class="ui-skeleton h-20 w-full rounded-xl"></div>
    </div>

    <div v-else-if="contests.length === 0" class="ui-empty">
      <span class="mb-2 text-5xl">🏆</span>
      <p class="font-bold">暂无比赛</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="c in contests"
        :key="c.id"
        class="ui-card cursor-pointer p-4 transition hover:shadow-md"
        :class="selectedContestId === c.id ? 'ring-2 ring-[#2563EB]' : ''"
        @click="selectContest(c.id)"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="font-bold">{{ c.title }}</h3>
              <span class="ui-badge" :class="c.status === 'ongoing' ? 'ui-badge-green' : c.status === 'upcoming' ? 'ui-badge-blue' : 'ui-badge-slate'">
                {{ c.status === 'ongoing' ? '进行中' : c.status === 'upcoming' ? '即将开始' : '已结束' }}
              </span>
              <span class="text-xs text-[#94A3B8]">{{ c.contest_type }}</span>
            </div>
            <p class="mt-1 text-sm text-[#64748B]">{{ c.participants_count || 0 }} 人参与</p>
          </div>
          <span class="text-[#94A3B8]">→</span>
        </div>
      </div>
    </div>

    <!-- 题目管理区 -->
    <div v-if="selectedContestId" class="mt-8">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-xl font-black">{{ selectedContest?.title }} - 题目管理</h2>
        <button class="ui-btn ui-btn-primary" @click="openProblemForm()">
          ➕ 添加题目
        </button>
      </div>

      <div v-if="isLoadingProblems" class="space-y-3">
        <div v-for="i in 3" :key="i" class="ui-skeleton h-16 w-full rounded-xl"></div>
      </div>

      <div v-else-if="problems.length === 0" class="ui-empty">
        <span class="mb-2 text-5xl">📝</span>
        <p class="font-bold">暂无题目</p>
        <p class="text-sm text-[#64748B]">点击"添加题目"开始出题</p>
      </div>

      <div v-else class="space-y-2">
        <div v-for="p in problems" :key="p.id" class="ui-card flex items-center gap-4 p-4">
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-[#EFF6FF] text-sm font-black text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            {{ p.problem_index }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="font-bold">{{ p.title }}</div>
            <div class="mt-1 flex items-center gap-3 text-xs text-[#94A3B8]">
              <span :class="difficultyClass(p.difficulty)" class="rounded px-1.5 py-0.5">{{ p.difficulty }}</span>
              <span>⏱ {{ p.time_limit }}ms</span>
              <span>💾 {{ p.memory_limit }}MB</span>
              <span>📊 {{ p.testcase_count || 0 }} 组测试用例</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button class="ui-btn ui-btn-ghost ui-btn-sm" @click="openProblemForm(p)">编辑</button>
            <button class="ui-btn ui-btn-ghost ui-btn-sm text-amber-500" @click="regenerateTestcases(p.id)">🔄 重生成用例</button>
            <button class="ui-btn ui-btn-ghost ui-btn-sm text-rose-500" @click="deleteProblem(p.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑题目弹窗 -->
    <div v-if="showProblemForm" class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 pt-10 pb-10">
      <div class="ui-card w-full max-w-4xl p-6">
        <h2 class="mb-4 text-lg font-bold">{{ editingProblem ? '编辑题目' : '添加题目' }}</h2>

        <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <!-- 左侧：表单 -->
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="mb-1 block text-sm font-bold">题目编号 *</label>
                <input v-model="problemForm.problem_index" class="ui-input w-full" placeholder="A" maxlength="10" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-bold">难度</label>
                <select v-model="problemForm.difficulty" class="ui-input w-full">
                  <option value="简单">简单</option>
                  <option value="中等">中等</option>
                  <option value="困难">困难</option>
                </select>
              </div>
            </div>

            <div>
              <label class="mb-1 block text-sm font-bold">题目标题 *</label>
              <input v-model="problemForm.title" class="ui-input w-full" placeholder="例：两数之和" />
            </div>

            <div>
              <label class="mb-1 block text-sm font-bold">题目描述 *（支持 Markdown）</label>
              <textarea v-model="problemForm.description" class="ui-input w-full font-mono text-sm" rows="8" placeholder="## 题目描述&#10;&#10;给定一个整数数组..."></textarea>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="mb-1 block text-sm font-bold">输入格式</label>
                <textarea v-model="problemForm.input_desc" class="ui-input w-full text-sm" rows="3" placeholder="第一行包含..."></textarea>
              </div>
              <div>
                <label class="mb-1 block text-sm font-bold">输出格式</label>
                <textarea v-model="problemForm.output_desc" class="ui-input w-full text-sm" rows="3" placeholder="输出一个整数..."></textarea>
              </div>
            </div>

            <div>
              <label class="mb-1 block text-sm font-bold">正确答案（参考代码） *</label>
              <textarea v-model="problemForm.correct_answer" class="ui-input w-full font-mono text-sm" rows="6" placeholder="# Python 示例&#10;def solve(n, nums):&#10;    return sum(nums)"></textarea>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="mb-1 block text-sm font-bold">时间限制(ms)</label>
                <input v-model.number="problemForm.time_limit" type="number" class="ui-input w-full" min="100" max="10000" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-bold">内存限制(MB)</label>
                <input v-model.number="problemForm.memory_limit" type="number" class="ui-input w-full" min="64" max="1024" />
              </div>
            </div>
          </div>

          <!-- 右侧：Markdown 实时预览 -->
          <div>
            <label class="mb-1 block text-sm font-bold">预览效果</label>
            <div class="ui-card max-h-[600px] overflow-y-auto p-4">
              <MarkdownComponent
                v-if="problemForm.description"
                :content="{ content: problemForm.description }"
                :show-nav="false"
                :show-heading-links="false"
              />
              <div v-else class="flex h-40 items-center justify-center text-[#94A3B8]">
                在左侧输入题目描述后，此处将实时显示渲染效果
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button class="ui-btn ui-btn-ghost" @click="showProblemForm = false">取消</button>
          <button class="ui-btn ui-btn-primary" :disabled="isGeneratingTestcases" @click="saveProblem">
            {{ isGeneratingTestcases ? '⏳ 正在生成测试用例...' : (editingProblem ? '保存修改' : '创建题目') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
