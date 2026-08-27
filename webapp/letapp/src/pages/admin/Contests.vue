<script setup lang="ts">
import { ref, computed, nextTick, watch, defineAsyncComponent, onMounted } from 'vue';
import { Icon } from '@iconify/vue';
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

// 代码编辑器语言选项
const languageOptions = [
  { value: 'c', label: 'C' },
  { value: 'cpp', label: 'C++' },
  { value: 'python', label: 'Python' },
  { value: 'java', label: 'Java' },
  { value: 'javascript', label: 'JavaScript' },
];
const languageLabel = (v: string) =>
  languageOptions.find((o) => o.value === v)?.label || v;

const defaultProblemForm = () => ({
  problem_index: '',
  title: '',
  description: '',
  input_desc: '',
  output_desc: '',
  correct_answer: '',
  time_limit: 1000,
  memory_limit: 256,
  difficulty: '中等',
  language: 'cpp',
  samples: [] as { uid: string; input: string; output: string }[],
});

const problemForm = ref(defaultProblemForm());
const isGeneratingTestcases = ref(false);

// 表单校验状态
const formErrors = ref({
  problem_index: '',
  title: '',
  description: '',
  correct_answer: '',
});

// 校验单个字段
const validateField = (field: string) => {
  const f = problemForm.value;
  switch (field) {
    case 'problem_index':
      formErrors.value.problem_index = f.problem_index.trim() ? '' : '请输入题目编号';
      break;
    case 'title':
      formErrors.value.title = f.title.trim() ? '' : '请输入题目标题';
      break;
    case 'description':
      formErrors.value.description = f.description.trim() ? '' : '请输入题目描述';
      break;
    case 'correct_answer':
      formErrors.value.correct_answer = f.correct_answer.trim() ? '' : '请输入参考代码';
      break;
  }
};

// 校验所有字段
const validateAllFields = () => {
  validateField('problem_index');
  validateField('title');
  validateField('description');
  validateField('correct_answer');
  return !formErrors.value.problem_index && !formErrors.value.title && !formErrors.value.description && !formErrors.value.correct_answer;
};

// 清除校验状态
const clearFormErrors = () => {
  formErrors.value = {
    problem_index: '',
    title: '',
    description: '',
    correct_answer: '',
  };
};

// 代码编辑器全屏
const codeFullscreen = ref(false);

// 文本域引用
const descTextarea = ref<HTMLTextAreaElement | null>(null);
const codeTextarea = ref<HTMLTextAreaElement | null>(null);
const codeGutter = ref<HTMLDivElement | null>(null);
const codeGutterFs = ref<HTMLDivElement | null>(null);

// 代码行号
const codeLineCount = computed(() => {
  const v = problemForm.value.correct_answer || '';
  return v.split('\n').length;
});

// 题目描述字符数
const descCharCount = computed(() => (problemForm.value.description || '').length);

// Markdown 工具栏
const applyMd = (type: string) => {
  const ta = descTextarea.value;
  if (!ta) return;
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  const val = problemForm.value.description;
  const sel = val.slice(start, end);
  let before = '', after = '', placeholder = '';
  switch (type) {
    case 'bold': before = '**'; after = '**'; placeholder = '加粗文本'; break;
    case 'italic': before = '*'; after = '*'; placeholder = '斜体文本'; break;
    case 'code': before = '`'; after = '`'; placeholder = '代码'; break;
    case 'link': before = '['; after = '](https://)'; placeholder = '链接文本'; break;
    case 'list': before = '- '; after = ''; placeholder = '列表项'; break;
    default: return;
  }
  const insert = before + (sel || placeholder) + after;
  problemForm.value.description = val.slice(0, start) + insert + val.slice(end);
  nextTick(() => {
    ta.focus();
    const pos = start + before.length;
    ta.setSelectionRange(pos, pos + (sel || placeholder).length);
  });
};

// 代码滚动同步行号
const onCodeScroll = (e: Event) => {
  if (codeGutter.value) {
    codeGutter.value.scrollTop = (e.target as HTMLTextAreaElement).scrollTop;
  }
};
const onCodeScrollFs = (e: Event) => {
  if (codeGutterFs.value) {
    codeGutterFs.value.scrollTop = (e.target as HTMLTextAreaElement).scrollTop;
  }
};

// 复制参考代码
const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(problemForm.value.correct_answer);
    message.success('代码已复制');
  } catch {
    message.error('复制失败');
  }
};

// 样例管理
let sampleUidSeq = 0;
const nextSampleUid = () => `s_${Date.now().toString(36)}_${(sampleUidSeq++).toString(36)}`;
const addSample = () => {
  problemForm.value.samples.push({ uid: nextSampleUid(), input: '', output: '' });
};
const removeSample = (uid: string) => {
  const idx = problemForm.value.samples.findIndex((s) => s.uid === uid);
  if (idx === -1) return;
  if (!confirm(`确认删除样例 ${idx + 1}？`)) return;
  problemForm.value.samples.splice(idx, 1);
};
const moveSample = (uid: string, dir: number) => {
  const list = problemForm.value.samples;
  const index = list.findIndex((s) => s.uid === uid);
  const target = index + dir;
  if (index === -1 || target < 0 || target >= list.length) return;
  const a = list[index];
  const b = list[target];
  if (!a || !b) return;
  list[index] = b;
  list[target] = a;
};
const copySample = async (s: { input: string; output: string }) => {
  try {
    await navigator.clipboard.writeText(`输入:\n${s.input}\n输出:\n${s.output}`);
    message.success('样例已复制');
  } catch {
    message.error('复制失败');
  }
};

// 完成度
const completionItems = computed(() => {
  const f = problemForm.value;
  const sampleDone = f.samples.some((s) => s.input.trim() && s.output.trim());
  return [
    { key: 'base', label: '基础信息', done: !!(f.problem_index.trim() && f.title.trim()) },
    { key: 'desc', label: '题目描述', done: !!f.description.trim() },
    { key: 'sample', label: '样例测试', done: sampleDone, optional: true },
    { key: 'code', label: '参考代码', done: !!f.correct_answer.trim() },
  ];
});
const completionDone = computed(() => completionItems.value.filter((i) => i.done).length);
const completionTotal = computed(() => completionItems.value.length);
const completionPercent = computed(() =>
  Math.round((completionDone.value / completionTotal.value) * 100),
);
const allRequiredDone = computed(() => completionItems.value.every((i) => i.done));

// 草稿
const draftKey = (id: number | null) => `problem_draft_${id ?? 'tmp'}`;
const saveDraft = () => {
  if (!selectedContestId.value) return;
  try {
    localStorage.setItem(
      draftKey(selectedContestId.value),
      JSON.stringify(problemForm.value),
    );
    message.success('草稿已保存');
  } catch {
    message.error('草稿保存失败');
  }
};
const loadDraft = () => {
  if (!selectedContestId.value) return;
  const raw = localStorage.getItem(draftKey(selectedContestId.value));
  if (!raw) return;
  try {
    const d = JSON.parse(raw);
    const base = defaultProblemForm();
    problemForm.value = {
      ...base,
      ...d,
      samples: Array.isArray(d.samples) && d.samples.length
        ? d.samples
        : base.samples,
    };
    message.info('已恢复上次保存的草稿');
  } catch {
    /* ignore */
  }
};
const clearDraft = () => {
  if (!selectedContestId.value) return;
  localStorage.removeItem(draftKey(selectedContestId.value));
};

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
    message.warning('请输入比赛名称');
    return;
  }
  if (!contestForm.value.description.trim()) {
    message.warning('请填写比赛简介');
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
  clearFormErrors();
  if (problem) {
    editingProblem.value = true;
    editingProblemId.value = problem.id;
    const samples = Array.isArray(problem.samples) && problem.samples.length
      ? problem.samples.map((s: any) => ({ uid: nextSampleUid(), input: s.input || '', output: s.output || '' }))
      : [];
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
      language: problem.language || 'cpp',
      samples,
    };
  } else {
    editingProblem.value = false;
    editingProblemId.value = null;
    problemForm.value = defaultProblemForm();
    problemForm.value.problem_index = String.fromCharCode(
      65 + problems.value.length,
    );
    loadDraft();
  }
  showProblemForm.value = true;
};

// 保存题目
const saveProblem = async () => {
  if (!selectedContestId.value) return;
  if (!validateAllFields()) {
    message.warning('请填写所有必填字段');
    return;
  }

  const f = problemForm.value;
  const payload = {
    problem_index: f.problem_index,
    title: f.title,
    description: f.description,
    input_desc: f.input_desc,
    output_desc: f.output_desc,
    correct_answer: f.correct_answer,
    time_limit: f.time_limit,
    memory_limit: f.memory_limit,
    difficulty: f.difficulty,
    language: f.language,
    samples: JSON.stringify(f.samples.map((s) => ({ input: s.input, output: s.output }))),
  };

  isGeneratingTestcases.value = true;
  try {
    if (editingProblem.value && editingProblemId.value) {
      await apiRequest(`/admin/contests/${editingProblemId.value}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      message.success('题目更新成功');
    } else {
      await apiRequest(`/admin/contests/?contest_id=${selectedContestId.value}`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      message.success('题目创建成功，测试用例已自动生成');
    }
    clearDraft();
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

// 删除比赛
const deleteContest = async (id: number, title: string) => {
  if (!confirm(`确定删除比赛「${title}」？此操作不可恢复！`)) return;
  try {
    await apiRequest(`/contests/${id}`, { method: 'DELETE' });
    message.success('比赛已删除');
    if (selectedContestId.value === id) {
      selectedContestId.value = null;
      selectedContest.value = null;
    }
    await loadContests();
  } catch (e) {
    message.error(e instanceof Error ? e.message : '删除失败');
  }
};

const difficultyClass = (d: string) =>
  d === '简单' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400'
  : d === '中等' ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400'
  : 'bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400';

// 关闭弹窗时退出代码全屏，避免残留遮罩
watch(showProblemForm, (v) => {
  if (!v) codeFullscreen.value = false;
});

onMounted(loadContests);
</script>

<template>
  <div class="p-6">
    <header class="admin-header">
      <div class="admin-header-left">
        <h1 class="admin-header-title">比赛管理</h1>
        <p class="admin-header-desc">创建与管理所有比赛</p>
      </div>
      <button class="admin-btn-primary" @click="showContestForm = true">
        <Icon icon="material-symbols:add-rounded" class="admin-btn-icon" />
        创建比赛
      </button>
    </header>

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
            <label class="mb-1 block text-sm font-bold">比赛简介 *</label>
            <textarea v-model="contestForm.description" class="ui-input w-full" rows="4" placeholder="介绍比赛背景、规则、奖励等..."></textarea>
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
          <div class="flex items-center gap-2">
            <button
              class="ui-btn ui-btn-ghost ui-btn-sm text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40"
              @click.stop="deleteContest(c.id, c.title)"
            >删除</button>
            <span class="text-[#94A3B8]">→</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 题目管理区 -->
    <div v-if="selectedContestId" class="mt-8">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-xl font-black">{{ selectedContest?.title }} - 题目管理</h2>
        <button class="add-problem-btn" @click="openProblemForm()">
          <Icon icon="material-symbols:add" class="h-4 w-4" />
          <span>添加题目</span>
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
    <div v-if="showProblemForm" class="problem-modal-overlay" @click.self="showProblemForm = false">
      <div class="problem-modal">
        <!-- 顶部标题栏 -->
        <div class="problem-modal-header">
          <div class="problem-modal-header-left">
            <button class="problem-back-btn" @click="showProblemForm = false" title="返回题目列表">
              <Icon icon="material-symbols:arrow-back" class="h-4 w-4" />
              <span>题目管理</span>
            </button>
            <div class="problem-modal-titles">
              <h2 class="problem-modal-title">{{ editingProblem ? '编辑题目' : '添加题目' }}</h2>
              <p class="problem-modal-subtitle">创建一道新的编程题，填写内容后即可发布到题库。</p>
            </div>
          </div>
          <button class="problem-modal-close" @click="showProblemForm = false" title="关闭">
            <Icon icon="material-symbols:close" class="h-5 w-5" />
          </button>
        </div>

        <!-- 内容区域 -->
        <div class="problem-modal-body">
          <!-- 左侧：统一编辑工作区 -->
          <div class="problem-form-section">
            <div class="problem-editor-surface">
              <!-- 分组1：基础信息 -->
              <section class="problem-section">
                <div class="problem-section-head">
                  <div>
                    <h3 class="problem-section-title">基础信息</h3>
                    <p class="problem-section-desc">设置题目的编号、难度与分类信息。</p>
                  </div>
                </div>
                <div class="problem-section-body">
                  <div class="problem-grid-12">
                    <div class="problem-col-3">
                      <label class="problem-label">题目编号 <span class="problem-required">*</span></label>
                      <input
                        v-model="problemForm.problem_index"
                        class="problem-input"
                        :class="{ 'problem-input-error': formErrors.problem_index }"
                        placeholder="A"
                        maxlength="10"
                        @blur="validateField('problem_index')"
                      />
                      <span v-if="formErrors.problem_index" class="problem-form-error">{{ formErrors.problem_index }}</span>
                    </div>
                    <div class="problem-col-3">
                      <label class="problem-label">难度</label>
                      <select v-model="problemForm.difficulty" class="problem-input">
                        <option value="简单">简单</option>
                        <option value="中等">中等</option>
                        <option value="困难">困难</option>
                      </select>
                    </div>
                    <div class="problem-col-3">
                      <label class="problem-label">时间限制</label>
                      <div class="problem-input-with-unit">
                        <input v-model.number="problemForm.time_limit" type="number" class="problem-input" min="100" max="10000" />
                        <span class="problem-input-unit">ms</span>
                      </div>
                    </div>
                    <div class="problem-col-3">
                      <label class="problem-label">内存限制</label>
                      <div class="problem-input-with-unit">
                        <input v-model.number="problemForm.memory_limit" type="number" class="problem-input" min="64" max="1024" />
                        <span class="problem-input-unit">MB</span>
                      </div>
                    </div>
                  </div>
                  <div class="problem-grid-12">
                    <div class="problem-col-12">
                      <label class="problem-label">题目标题 <span class="problem-required">*</span></label>
                      <input
                        v-model="problemForm.title"
                        class="problem-input"
                        :class="{ 'problem-input-error': formErrors.title }"
                        placeholder="请输入题目标题，例如：两数之和"
                        @blur="validateField('title')"
                      />
                      <span v-if="formErrors.title" class="problem-form-error">{{ formErrors.title }}</span>
                    </div>
                  </div>
                </div>
              </section>

              <!-- 分组2：题目描述 -->
              <section class="problem-section">
                <div class="problem-section-head">
                  <div>
                    <h3 class="problem-section-title">题目描述</h3>
                    <p class="problem-section-desc">使用 Markdown 描述题目的背景、要求与格式。</p>
                  </div>
                </div>
                <div class="problem-section-body">
                  <div class="problem-form-field">
                    <label class="problem-label">题目描述 <span class="problem-required">*</span></label>
                    <div class="problem-md-editor">
                      <div class="problem-md-toolbar">
                        <button class="problem-md-btn" title="加粗" @click="applyMd('bold')"><Icon icon="material-symbols:format-bold" class="h-4 w-4" /></button>
                        <button class="problem-md-btn" title="斜体" @click="applyMd('italic')"><Icon icon="material-symbols:format-italic" class="h-4 w-4" /></button>
                        <button class="problem-md-btn" title="代码" @click="applyMd('code')"><Icon icon="material-symbols:code" class="h-4 w-4" /></button>
                        <button class="problem-md-btn" title="链接" @click="applyMd('link')"><Icon icon="material-symbols:link" class="h-4 w-4" /></button>
                        <button class="problem-md-btn" title="列表" @click="applyMd('list')"><Icon icon="material-symbols:format-list-bulleted" class="h-4 w-4" /></button>
                      </div>
                      <textarea
                        ref="descTextarea"
                        v-model="problemForm.description"
                        class="problem-textarea problem-desc-textarea"
                        :class="{ 'problem-input-error': formErrors.description }"
                        placeholder="## 题目描述&#10;&#10;给定一个整数数组..."
                        @blur="validateField('description')"
                      ></textarea>
                      <div class="problem-desc-footer">
                        <span class="problem-hint"><Icon icon="material-symbols:code" class="h-3.5 w-3.5" /> 支持 Markdown</span>
                        <span class="problem-hint">{{ descCharCount }} / 10,000</span>
                      </div>
                    </div>
                    <span v-if="formErrors.description" class="problem-form-error">{{ formErrors.description }}</span>
                  </div>
                  <div class="problem-grid-12">
                    <div class="problem-col-6">
                      <label class="problem-label">输入格式</label>
                      <textarea v-model="problemForm.input_desc" class="problem-textarea" rows="4" placeholder="第一行包含..."></textarea>
                    </div>
                    <div class="problem-col-6">
                      <label class="problem-label">输出格式</label>
                      <textarea v-model="problemForm.output_desc" class="problem-textarea" rows="4" placeholder="输出一个整数..."></textarea>
                    </div>
                  </div>
                </div>
              </section>

              <!-- 分组3：样例测试 -->
              <section class="problem-section">
                <div class="problem-section-head">
                  <div>
                    <h3 class="problem-section-title">样例测试</h3>
                    <p class="problem-section-desc">填写题目的标准输入与标准输出，用于展示给用户查看。</p>
                  </div>
                </div>
                <div class="problem-section-body">
                  <div
                    v-for="(sample, idx) in problemForm.samples"
                    :key="sample.uid"
                    class="problem-sample-card"
                  >
                    <div class="problem-sample-head">
                      <div class="problem-sample-title">
                        <button
                          class="problem-sample-drag"
                          title="上移"
                          :disabled="idx === 0"
                          @click="moveSample(sample.uid, -1)"
                        ><Icon icon="material-symbols:arrow-upward" class="h-4 w-4" /></button>
                        <button
                          class="problem-sample-drag"
                          title="下移"
                          :disabled="idx === problemForm.samples.length - 1"
                          @click="moveSample(sample.uid, 1)"
                        ><Icon icon="material-symbols:arrow-downward" class="h-4 w-4" /></button>
                        <span>样例 {{ idx + 1 }}</span>
                      </div>
                      <div class="flex items-center gap-2">
                        <button class="problem-sample-copy" title="复制样例" @click="copySample(sample)">
                          <Icon icon="material-symbols:content-copy" class="h-3.5 w-3.5" /> 复制
                        </button>
                        <button class="problem-sample-del" title="删除样例" @click="removeSample(sample.uid)">
                          <Icon icon="material-symbols:delete-outline" class="h-3.5 w-3.5" /> 删除
                        </button>
                      </div>
                    </div>
                    <div class="problem-sample-body">
                      <div class="problem-sample-col">
                        <label class="problem-sample-label">
                          标准输入
                          <span class="problem-sample-sub">Input</span>
                        </label>
                        <textarea
                          v-model="sample.input"
                          class="problem-io-textarea"
                          rows="5"
                          placeholder="示例：&#10;10 20"
                          @keydown.tab.prevent="(e: any) => { const t = e.target; const s = t.selectionStart; sample.input = sample.input.slice(0,s) + '  ' + sample.input.slice(t.selectionEnd); nextTick(()=>{ t.selectionStart = t.selectionEnd = s+2 }) }"
                        ></textarea>
                        <div class="problem-sample-count">{{ sample.input.length }} / 2000</div>
                      </div>
                      <div class="problem-sample-col">
                        <label class="problem-sample-label">
                          标准输出
                          <span class="problem-sample-sub">Output</span>
                        </label>
                        <textarea
                          v-model="sample.output"
                          class="problem-io-textarea"
                          rows="5"
                          placeholder="示例：&#10;20"
                          @keydown.tab.prevent="(e: any) => { const t = e.target; const s = t.selectionStart; sample.output = sample.output.slice(0,s) + '  ' + sample.output.slice(t.selectionEnd); nextTick(()=>{ t.selectionStart = t.selectionEnd = s+2 }) }"
                        ></textarea>
                        <div class="problem-sample-count">{{ sample.output.length }} / 2000</div>
                      </div>
                    </div>
                  </div>
                  <div v-if="problemForm.samples.length === 0" class="problem-sample-empty">
                    <Icon icon="material-symbols:science-outline" class="h-5 w-5" />
                    <span>尚未添加样例，点击下方按钮新增标准输入/输出</span>
                  </div>
                  <button class="problem-add-sample" @click="addSample">
                    <Icon icon="material-symbols:add" class="h-4 w-4" />
                    添加样例
                  </button>
                </div>
              </section>

              <!-- 分组4：参考代码 -->
              <section class="problem-section">
                <div class="problem-section-head">
                  <div>
                    <h3 class="problem-section-title">参考代码</h3>
                    <p class="problem-section-desc">用于帮助用户理解题目，可选择不填写。</p>
                  </div>
                </div>
                <div class="problem-section-body">
                  <div class="problem-form-field">
                    <div class="problem-code-header">
                      <div class="problem-code-title">
                        <Icon icon="material-symbols:code" class="h-4 w-4" />
                        <span>参考代码</span>
                        <span class="problem-code-badge">{{ languageLabel(problemForm.language) }}</span>
                      </div>
                      <div class="problem-code-actions">
                        <select v-model="problemForm.language" class="problem-code-lang">
                          <option v-for="o in languageOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
                        </select>
                        <button class="problem-code-btn" title="复制" @click="copyCode"><Icon icon="material-symbols:content-copy" class="h-4 w-4" /></button>
                        <button class="problem-code-btn" title="全屏" @click="codeFullscreen = true"><Icon icon="material-symbols:fullscreen" class="h-4 w-4" /></button>
                      </div>
                    </div>
                    <div class="problem-code-editor">
                      <div ref="codeGutter" class="problem-code-gutter">
                        <div v-for="n in codeLineCount" :key="n" class="problem-code-lineno">{{ n }}</div>
                      </div>
                      <textarea
                        ref="codeTextarea"
                        v-model="problemForm.correct_answer"
                        class="problem-code-textarea"
                        :class="{ 'problem-input-error': formErrors.correct_answer }"
                        placeholder="# Python 示例&#10;def solve(n, nums):&#10;    return sum(nums)"
                        spellcheck="false"
                        @scroll="onCodeScroll"
                      ></textarea>
                    </div>
                    <span v-if="formErrors.correct_answer" class="problem-form-error">{{ formErrors.correct_answer }}</span>
                  </div>
                </div>
              </section>
            </div>
          </div>

          <!-- 右侧：实时预览区 -->
          <div class="problem-preview-section">
            <div class="problem-preview-header">
              <div class="problem-preview-header-left">
                <Icon icon="material-symbols:visibility" class="h-4 w-4 text-[#2563EB]" />
                <span class="problem-preview-title">题目预览</span>
              </div>
              <div class="problem-preview-live">
                <span class="problem-live-dot"></span>
                <span>实时更新</span>
              </div>
            </div>

            <!-- 完成度 -->
            <div class="problem-completion">
              <div class="problem-completion-head">
                <span class="problem-completion-label">题目完成度</span>
                <span class="problem-completion-percent">{{ completionPercent }}%</span>
              </div>
              <div class="problem-completion-bar">
                <div class="problem-completion-fill" :style="{ width: completionPercent + '%' }"></div>
              </div>
              <div class="problem-completion-items">
                <div
                  v-for="item in completionItems"
                  :key="item.key"
                  class="problem-completion-item"
                  :class="{ 'is-done': item.done }"
                >
                  <Icon
                    :icon="item.done ? 'material-symbols:check-circle' : (item.optional ? 'material-symbols:circle' : 'material-symbols:cancel')"
                    class="h-4 w-4"
                  />
                  <span>{{ item.label }}</span>
                </div>
              </div>
            </div>

            <div class="problem-preview-content">
              <template v-if="problemForm.title || problemForm.description || problemForm.samples.some(s => s.input || s.output)">
                <div class="problem-preview-card">
                  <div class="problem-preview-title-area">
                    <div class="problem-preview-index">#{{ problemForm.problem_index || 'A' }}</div>
                    <h3 class="problem-preview-problem-title">{{ problemForm.title || '题目标题' }}</h3>
                    <span class="problem-preview-difficulty" :class="difficultyClass(problemForm.difficulty)">
                      {{ problemForm.difficulty }}
                    </span>
                  </div>

                  <div v-if="problemForm.description" class="problem-preview-block">
                    <div class="problem-preview-block-title">题目描述</div>
                    <div class="problem-preview-description">
                      <MarkdownComponent
                        :content="{ content: problemForm.description }"
                        :show-nav="false"
                        :show-heading-links="false"
                      />
                    </div>
                  </div>

                  <div class="problem-preview-block">
                    <div class="problem-preview-block-title">知识点</div>
                    <div class="problem-preview-tags">
                      <span class="problem-preview-tag">{{ languageLabel(problemForm.language) }}</span>
                      <span class="problem-preview-tag">{{ problemForm.difficulty }}</span>
                    </div>
                  </div>

                  <div
                    v-for="(sample, idx) in problemForm.samples.filter(s => s.input || s.output)"
                    :key="idx"
                    class="problem-preview-block"
                  >
                    <div class="problem-preview-block-title">示例 {{ idx + 1 }}</div>
                    <div class="problem-preview-example">
                      <div class="problem-preview-ex-label">Input</div>
                      <pre class="problem-preview-ex-code">{{ sample.input || '—' }}</pre>
                      <div class="problem-preview-ex-label">Output</div>
                      <pre class="problem-preview-ex-code">{{ sample.output || '—' }}</pre>
                    </div>
                  </div>

                  <div v-if="problemForm.correct_answer" class="problem-preview-block">
                    <div class="problem-preview-block-title">参考代码</div>
                    <pre class="problem-preview-code">{{ problemForm.correct_answer }}</pre>
                  </div>
                </div>
              </template>
              <div v-else class="problem-preview-empty">
                <Icon icon="material-symbols:article-outline" class="h-12 w-12 text-[#CBD5E1] dark:text-[#475569]" />
                <p class="problem-preview-empty-text">在左侧输入题目内容后</p>
                <p class="problem-preview-empty-text">此处将实时显示渲染效果</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部操作栏 -->
        <div class="problem-modal-footer">
          <div class="problem-modal-footer-hint">
            <template v-if="allRequiredDone">
              <Icon icon="material-symbols:check-circle" class="h-4 w-4 text-emerald-500" />
              <span class="text-emerald-600 dark:text-emerald-400">所有必要信息已完成</span>
            </template>
            <template v-else>
              <span class="problem-hint-dot"></span>
              <span>已填写 {{ completionDone }} / {{ completionTotal }} 个必要信息</span>
            </template>
          </div>
          <div class="problem-modal-footer-actions">
            <button class="problem-btn problem-btn-cancel" @click="showProblemForm = false">取消</button>
            <button class="problem-btn problem-btn-secondary" @click="saveDraft">保存草稿</button>
            <button class="problem-btn problem-btn-primary" :disabled="isGeneratingTestcases" @click="saveProblem">
              <Icon v-if="isGeneratingTestcases" icon="svg-spinners:ring-resize" class="h-4 w-4" />
              <Icon v-else icon="material-symbols:upload" class="h-4 w-4" />
              {{ isGeneratingTestcases ? '正在生成测试用例...' : (editingProblem ? '保存修改' : '创建并发布') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 代码编辑器全屏 -->
    <div v-if="codeFullscreen" class="problem-fullscreen-overlay" @click.self="codeFullscreen = false">
      <div class="problem-fullscreen">
        <div class="problem-fullscreen-header">
          <div class="problem-code-title">
            <Icon icon="material-symbols:code" class="h-4 w-4" />
            <span>参考代码</span>
            <span class="problem-code-badge">{{ languageLabel(problemForm.language) }}</span>
          </div>
          <div class="problem-code-actions">
            <select v-model="problemForm.language" class="problem-code-lang">
              <option v-for="o in languageOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
            </select>
            <button class="problem-code-btn" title="复制" @click="copyCode"><Icon icon="material-symbols:content-copy" class="h-4 w-4" /></button>
            <button class="problem-code-btn" title="退出全屏" @click="codeFullscreen = false"><Icon icon="material-symbols:fullscreen-exit" class="h-4 w-4" /></button>
          </div>
        </div>
        <div class="problem-code-editor problem-code-editor-full">
          <div ref="codeGutterFs" class="problem-code-gutter">
            <div v-for="n in codeLineCount" :key="n" class="problem-code-lineno">{{ n }}</div>
          </div>
          <textarea
            v-model="problemForm.correct_answer"
            class="problem-code-textarea"
            placeholder="# Python 示例&#10;def solve(n, nums):&#10;    return sum(nums)"
            spellcheck="false"
            @scroll="onCodeScrollFs"
          ></textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 管理页头部样式 */
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  min-height: 5rem;
}
.admin-header-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.admin-header-title {
  font-size: 1.5rem;
  font-weight: 900;
  color: #0f172a;
}
:global(.dark) .admin-header-title {
  color: #f1f5f9;
}
.admin-header-desc {
  font-size: 0.875rem;
  color: #64748b;
}
:global(.dark) .admin-header-desc {
  color: #94a3b8;
}
.admin-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 7rem;
  height: 2.75rem;
  padding: 0 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #fff;
  background: #2563eb;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2);
}
.admin-btn-primary:hover {
  background: #1d4ed8;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
}
.admin-btn-primary:active {
  background: #1e40af;
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2);
  transform: translateY(0);
}
.admin-btn-primary:disabled {
  background: #93b4e0;
  box-shadow: none;
  transform: none;
  cursor: not-allowed;
}
.admin-btn-icon {
  width: 16px;
  height: 16px;
}

/* ========== 添加题目按钮样式 ========== */
.add-problem-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 110px;
  height: 40px;
  padding: 0 18px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  background: #2563EB;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.2);
}
.add-problem-btn:hover {
  background: #1D4ED8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
}
.add-problem-btn:active {
  background: #1E40AF;
  transform: translateY(0);
}

/* ========== 添加题目弹窗样式 ========== */

/* 遮罩层 */
.problem-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  padding: 24px;
}

/* 弹窗主体 */
.problem-modal {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1240px;
  height: calc(100vh - 48px);
  max-height: 92vh;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}
:global(.dark) .problem-modal {
  background: #0F141B;
  border: 1px solid #27313D;
}

/* 顶部标题栏 */
.problem-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 76px;
  padding: 12px 28px;
  border-bottom: 1px solid #E5EAF0;
  flex-shrink: 0;
}
:global(.dark) .problem-modal-header {
  border-bottom-color: #27313D;
}
.problem-modal-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.problem-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 10px 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  background: transparent;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.problem-back-btn:hover {
  background: #F1F5F9;
  color: #0F172A;
}
:global(.dark) .problem-back-btn {
  color: #94A3B8;
  border-color: #27313D;
}
:global(.dark) .problem-back-btn:hover {
  background: #1A222C;
  color: #E5E7EB;
}
.problem-modal-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.problem-modal-title {
  font-size: 24px;
  font-weight: 700;
  color: #0F172A;
  margin: 0;
  line-height: 1.2;
}
:global(.dark) .problem-modal-title {
  color: #E5E7EB;
}
.problem-modal-subtitle {
  font-size: 13px;
  color: #667085;
}
:global(.dark) .problem-modal-subtitle {
  color: #98A2B3;
}
.problem-modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #64748B;
  cursor: pointer;
  transition: all 0.15s ease;
}
.problem-modal-close:hover {
  background: #F1F5F9;
  color: #1E293B;
}
:global(.dark) .problem-modal-close:hover {
  background: #1A222C;
  color: #E5E7EB;
}

/* 内容区域 */
.problem-modal-body {
  display: flex;
  gap: 24px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 24px 28px;
}

/* 左侧表单区 */
.problem-form-section {
  flex: 0 0 58%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
}
.problem-form-section::-webkit-scrollbar {
  width: 6px;
}
.problem-form-section::-webkit-scrollbar-track {
  background: transparent;
}
.problem-form-section::-webkit-scrollbar-thumb {
  background: #CBD5E1;
  border-radius: 3px;
}
:global(.dark) .problem-form-section::-webkit-scrollbar-thumb {
  background: #475569;
}

/* 统一编辑 Surface */
.problem-editor-surface {
  background: #FFFFFF;
  border: 1px solid #E5EAF0;
  border-radius: 16px;
  padding: 4px 28px;
  overflow: hidden;
}
:global(.dark) .problem-editor-surface {
  background: #151B23;
  border-color: #27313D;
}

/* Section */
.problem-section {
  padding: 24px 0;
  border-bottom: 1px solid #EDF1F5;
}
.problem-section:last-child {
  border-bottom: none;
}
:global(.dark) .problem-section {
  border-bottom-color: #1F2935;
}
.problem-section-head {
  margin-bottom: 20px;
}
.problem-section-title {
  font-size: 18px;
  font-weight: 650;
  color: #344054;
  margin: 0;
}
:global(.dark) .problem-section-title {
  color: #D0D5DD;
}
.problem-section-desc {
  font-size: 13px;
  color: #98A2B3;
  margin: 6px 0 0;
}
.problem-section-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* 12 列网格 */
.problem-grid-12 {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}
.problem-col-3 { grid-column: span 3; }
.problem-col-6 { grid-column: span 6; }
.problem-col-12 { grid-column: span 12; }

/* 表单字段 */
.problem-form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.problem-label {
  font-size: 13px;
  font-weight: 600;
  color: #344054;
}
:global(.dark) .problem-label {
  color: #D0D5DD;
}
.problem-required {
  color: #EF4444;
  font-weight: 500;
}

/* 输入框 */
.problem-input {
  height: 44px;
  padding: 0 14px;
  font-size: 14px;
  color: #1E293B;
  background: #FFFFFF;
  border: 1px solid #D9E0E8;
  border-radius: 8px;
  outline: none;
  transition: all 0.15s ease;
}
.problem-input::placeholder {
  color: #94A3B8;
}
.problem-input:focus {
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.10);
}
:global(.dark) .problem-input {
  color: #E5E7EB;
  background: #10151C;
  border-color: #27313D;
}
:global(.dark) .problem-input::placeholder {
  color: #64748B;
}
:global(.dark) .problem-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

/* 带单位的输入框 */
.problem-input-with-unit {
  display: flex;
  align-items: center;
}
.problem-input-with-unit .problem-input {
  flex: 1;
  border-radius: 8px 0 0 8px;
  border-right: none;
}
.problem-input-unit {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 44px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  background: #F8FAFC;
  border: 1px solid #D9E0E8;
  border-radius: 0 8px 8px 0;
}
:global(.dark) .problem-input-unit {
  color: #94A3B8;
  background: #1A222C;
  border-color: #27313D;
}

/* 文本域 */
.problem-textarea {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.6;
  color: #1E293B;
  background: #FFFFFF;
  border: 1px solid #D9E0E8;
  border-radius: 8px;
  outline: none;
  resize: vertical;
  transition: all 0.15s ease;
}
.problem-textarea::placeholder {
  color: #94A3B8;
}
.problem-textarea:focus {
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.10);
}
:global(.dark) .problem-textarea {
  color: #E5E7EB;
  background: #10151C;
  border-color: #27313D;
}
:global(.dark) .problem-textarea::placeholder {
  color: #64748B;
}
:global(.dark) .problem-textarea:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

/* Markdown 编辑器 */
.problem-md-editor {
  border: 1px solid #D9E0E8;
  border-radius: 8px;
  overflow: hidden;
  background: #FFFFFF;
  transition: all 0.15s ease;
}
.problem-md-editor:focus-within {
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.10);
}
:global(.dark) .problem-md-editor {
  background: #10151C;
  border-color: #27313D;
}
.problem-md-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 40px;
  padding: 0 8px;
  background: #F8FAFC;
  border-bottom: 1px solid #E5EAF0;
}
:global(.dark) .problem-md-toolbar {
  background: #1A222C;
  border-bottom-color: #27313D;
}
.problem-md-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;
}
.problem-md-btn:hover {
  background: #E2E8F0;
  color: #0F172A;
}
:global(.dark) .problem-md-btn {
  color: #94A3B8;
}
:global(.dark) .problem-md-btn:hover {
  background: #27313D;
  color: #E5E7EB;
}
.problem-desc-textarea {
  border: none;
  border-radius: 0;
  resize: vertical;
  min-height: 260px;
  font-family: 'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
}
.problem-desc-textarea:focus {
  box-shadow: none;
}
.problem-desc-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #F8FAFC;
  border-top: 1px solid #E5EAF0;
}
:global(.dark) .problem-desc-footer {
  background: #1A222C;
  border-top-color: #27313D;
}
.problem-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #98A2B3;
}

/* 样例卡片 */
.problem-sample-card {
  border: 1px solid #E5EAF0;
  border-radius: 12px;
  overflow: hidden;
}
:global(.dark) .problem-sample-card {
  border-color: #27313D;
}
.problem-sample-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  padding: 0 12px;
  background: #F8FAFC;
  border-bottom: 1px solid #E5EAF0;
}
:global(.dark) .problem-sample-head {
  background: #1A222C;
  border-bottom-color: #27313D;
}
.problem-sample-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: #344054;
}
:global(.dark) .problem-sample-title {
  color: #D0D5DD;
}
.problem-sample-drag {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #94A3B8;
  cursor: pointer;
  transition: all 0.15s ease;
}
.problem-sample-drag:hover:not(:disabled) {
  background: #E2E8F0;
  color: #0F172A;
}
.problem-sample-drag:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
:global(.dark) .problem-sample-drag:hover:not(:disabled) {
  background: #27313D;
  color: #E5E7EB;
}
.problem-sample-copy {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  height: 26px;
  padding: 0 8px;
  font-size: 12px;
  color: #2563EB;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.problem-sample-copy:hover {
  background: rgba(37, 99, 235, 0.10);
}
.problem-sample-del {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  height: 26px;
  padding: 0 8px;
  font-size: 12px;
  color: #EF4444;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.problem-sample-del:hover {
  background: #FEE2E2;
  color: #DC2626;
}
.problem-sample-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 16px;
}
.problem-sample-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.problem-sample-label {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #344054;
}
:global(.dark) .problem-sample-label {
  color: #D0D5DD;
}
.problem-sample-sub {
  font-size: 11px;
  font-weight: 500;
  color: #98A2B3;
  font-family: 'JetBrains Mono', monospace;
}
.problem-io-textarea {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.7;
  color: #1E293B;
  background: #FAFBFC;
  border: 1px solid #D9E0E8;
  border-radius: 8px;
  outline: none;
  resize: vertical;
  font-family: 'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  transition: all 0.15s ease;
}
.problem-io-textarea::placeholder {
  color: #94A3B8;
}
.problem-io-textarea:focus {
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.10);
}
:global(.dark) .problem-io-textarea {
  color: #E5E7EB;
  background: #0D1117;
  border-color: #27313D;
}
.problem-sample-count {
  align-self: flex-end;
  font-size: 12px;
  color: #98A2B3;
}
.problem-add-sample {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 36px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 600;
  color: #2563EB;
  background: #FFFFFF;
  border: 1px dashed #D9E2EC;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.problem-add-sample:hover {
  background: #F8FAFF;
  border-color: #2563EB;
}
:global(.dark) .problem-add-sample {
  background: #151B23;
  border-color: #27313D;
}
.problem-sample-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  font-size: 13px;
  color: #98A2B3;
  background: #F8FAFC;
  border: 1px dashed #E2E8F0;
  border-radius: 10px;
}
:global(.dark) .problem-sample-empty {
  background: #10151C;
  border-color: #27313D;
}

/* 代码编辑器 */
.problem-code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 12px;
  background: #F1F5F9;
  border: 1px solid #D9E0E8;
  border-bottom: none;
  border-radius: 8px 8px 0 0;
}
:global(.dark) .problem-code-header {
  background: #1A222C;
  border-color: #27313D;
}
.problem-code-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}
:global(.dark) .problem-code-title {
  color: #E5E7EB;
}
.problem-code-badge {
  font-size: 11px;
  font-weight: 600;
  color: #2563EB;
  background: rgba(37, 99, 235, 0.10);
  padding: 2px 8px;
  border-radius: 9999px;
}
.problem-code-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.problem-code-lang {
  height: 30px;
  padding: 0 8px;
  font-size: 13px;
  color: #334155;
  background: #FFFFFF;
  border: 1px solid #D9E0E8;
  border-radius: 6px;
  outline: none;
  cursor: pointer;
}
:global(.dark) .problem-code-lang {
  color: #E5E7EB;
  background: #0D1117;
  border-color: #27313D;
}
.problem-code-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;
}
.problem-code-btn:hover {
  background: #E2E8F0;
  color: #0F172A;
}
:global(.dark) .problem-code-btn {
  color: #94A3B8;
}
:global(.dark) .problem-code-btn:hover {
  background: #27313D;
  color: #E5E7EB;
}
.problem-code-editor {
  display: flex;
  border: 1px solid #D9E0E8;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
  background: #FAFBFC;
}
:global(.dark) .problem-code-editor {
  background: #0D1117;
  border-color: #27313D;
}
.problem-code-gutter {
  flex-shrink: 0;
  width: 48px;
  padding: 14px 0;
  overflow: hidden;
  background: #F1F5F9;
  border-right: 1px solid #E5EAF0;
  user-select: none;
}
:global(.dark) .problem-code-gutter {
  background: #11161F;
  border-right-color: #1F2935;
}
.problem-code-lineno {
  height: 24px;
  line-height: 24px;
  text-align: right;
  padding-right: 12px;
  font-size: 13px;
  color: #98A2B3;
  font-family: 'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
}
.problem-code-textarea {
  flex: 1;
  min-height: 380px;
  height: 380px;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.75;
  color: #1E293B;
  background: #FAFBFC;
  border: none;
  outline: none;
  resize: none;
  font-family: 'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  white-space: pre;
  overflow: auto;
  tab-size: 4;
}
:global(.dark) .problem-code-textarea {
  color: #E5E7EB;
  background: #0D1117;
}
.problem-code-textarea:focus {
  box-shadow: none;
}
.problem-code-editor-full .problem-code-textarea {
  height: calc(100vh - 140px);
  min-height: calc(100vh - 140px);
}

/* 错误状态 */
.problem-input-error {
  border-color: #EF4444 !important;
}
.problem-input-error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
}
.problem-form-error {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #EF4444;
}

/* 右侧预览区 */
.problem-preview-section {
  flex: 0 0 42%;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  border: 1px solid #E5EAF0;
  border-radius: 16px;
  overflow: hidden;
  background: #FFFFFF;
}
:global(.dark) .problem-preview-section {
  border-color: #27313D;
  background: #0F141B;
}
.problem-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;
  background: #F8FAFC;
  border-bottom: 1px solid #E5EAF0;
  flex-shrink: 0;
}
:global(.dark) .problem-preview-header {
  background: #151B23;
  border-bottom-color: #27313D;
}
.problem-preview-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.problem-preview-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}
:global(.dark) .problem-preview-title {
  color: #E5E7EB;
}
.problem-preview-live {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #98A2B3;
}
.problem-live-dot {
  width: 7px;
  height: 7px;
  border-radius: 9999px;
  background: #22C55E;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
}

/* 完成度 */
.problem-completion {
  padding: 16px;
  background: #F8FAFC;
  border-bottom: 1px solid #E5EAF0;
  flex-shrink: 0;
}
:global(.dark) .problem-completion {
  background: #10151C;
  border-bottom-color: #27313D;
}
.problem-completion-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.problem-completion-label {
  font-size: 13px;
  font-weight: 600;
  color: #344054;
}
:global(.dark) .problem-completion-label {
  color: #D0D5DD;
}
.problem-completion-percent {
  font-size: 13px;
  font-weight: 700;
  color: #2563EB;
}
.problem-completion-bar {
  height: 6px;
  background: #E5EAF0;
  border-radius: 9999px;
  overflow: hidden;
}
:global(.dark) .problem-completion-bar {
  background: #27313D;
}
.problem-completion-fill {
  height: 100%;
  background: #2563EB;
  border-radius: 9999px;
  transition: width 0.3s ease;
}
.problem-completion-items {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
  margin-top: 12px;
}
.problem-completion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #98A2B3;
}
.problem-completion-item.is-done {
  color: #16A34A;
}

.problem-preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 0;
}
.problem-preview-content::-webkit-scrollbar {
  width: 6px;
}
.problem-preview-content::-webkit-scrollbar-track {
  background: transparent;
}
.problem-preview-content::-webkit-scrollbar-thumb {
  background: #CBD5E1;
  border-radius: 3px;
}
:global(.dark) .problem-preview-content::-webkit-scrollbar-thumb {
  background: #475569;
}

/* 预览卡片 */
.problem-preview-card {
  background: #fff;
  border: 1px solid #E5EAF0;
  border-radius: 12px;
  padding: 20px;
}
:global(.dark) .problem-preview-card {
  background: #0F141B;
  border-color: #27313D;
}
.problem-preview-title-area {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #E5EAF0;
}
:global(.dark) .problem-preview-title-area {
  border-bottom-color: #27313D;
}
.problem-preview-index {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: #2563EB;
  background: rgba(37, 99, 235, 0.10);
  padding: 2px 8px;
  border-radius: 6px;
  margin-top: 4px;
}
.problem-preview-problem-title {
  flex: 1;
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  margin: 0;
  line-height: 1.4;
}
:global(.dark) .problem-preview-problem-title {
  color: #E5E7EB;
}
.problem-preview-difficulty {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 9999px;
}
.problem-preview-block {
  margin-top: 18px;
}
.problem-preview-block-title {
  font-size: 14px;
  font-weight: 650;
  color: #0F172A;
  margin-bottom: 8px;
}
:global(.dark) .problem-preview-block-title {
  color: #E5E7EB;
}
.problem-preview-description {
  font-size: 15px;
  line-height: 1.8;
  color: #334155;
}
:global(.dark) .problem-preview-description {
  color: #CBD5E1;
}
.problem-preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.problem-preview-tag {
  height: 28px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  background: #F1F5F9;
  border-radius: 6px;
}
:global(.dark) .problem-preview-tag {
  color: #D0D5DD;
  background: #1A222C;
}
.problem-preview-example {
  background: #F8FAFC;
  border: 1px solid #E5EAF0;
  border-radius: 8px;
  padding: 14px;
}
:global(.dark) .problem-preview-example {
  background: #10151C;
  border-color: #27313D;
}
.problem-preview-ex-label {
  font-size: 12px;
  font-weight: 600;
  color: #667085;
  margin-bottom: 4px;
}
.problem-preview-ex-label:not(:first-child) {
  margin-top: 10px;
}
.problem-preview-ex-code {
  margin: 0;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.7;
  color: #1E293B;
  font-family: 'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  background: #FFFFFF;
  border: 1px solid #E5EAF0;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
}
:global(.dark) .problem-preview-ex-code {
  color: #E5E7EB;
  background: #0D1117;
  border-color: #27313D;
}
.problem-preview-code {
  margin: 0;
  padding: 14px;
  font-size: 14px;
  line-height: 1.7;
  color: #1E293B;
  font-family: 'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
  background: #FAFBFC;
  border: 1px solid #E5EAF0;
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-all;
}
:global(.dark) .problem-preview-code {
  color: #E5E7EB;
  background: #0D1117;
  border-color: #27313D;
}

/* 预览空状态 */
.problem-preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}
.problem-preview-empty-text {
  margin: 4px 0;
  font-size: 14px;
  color: #94A3B8;
}

/* 底部操作栏 */
.problem-modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 80px;
  padding: 0 28px;
  border-top: 1px solid #E5EAF0;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
}
:global(.dark) .problem-modal-footer {
  border-top-color: #27313D;
  background: rgba(11, 15, 20, 0.88);
}
.problem-modal-footer-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748B;
}
.problem-hint-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #F59E0B;
}
.problem-modal-footer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 按钮 */
.problem-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 44px;
  padding: 0 22px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
}
.problem-btn-cancel {
  min-width: 80px;
  background: #FFFFFF;
  color: #475569;
  border: 1px solid #D9E0E8;
}
.problem-btn-cancel:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
}
:global(.dark) .problem-btn-cancel {
  background: #0F172A;
  color: #94A3B8;
  border-color: #27313D;
}
:global(.dark) .problem-btn-cancel:hover {
  background: #1A222C;
}
.problem-btn-secondary {
  min-width: 96px;
  background: #FFFFFF;
  color: #2563EB;
  border: 1px solid #D9E0E8;
}
.problem-btn-secondary:hover {
  background: #EFF6FF;
  border-color: #2563EB;
}
:global(.dark) .problem-btn-secondary {
  background: #151B23;
  color: #60A5FA;
  border-color: #27313D;
}
:global(.dark) .problem-btn-secondary:hover {
  background: #1A222C;
}
.problem-btn-primary {
  min-width: 132px;
  background: #2563EB;
  color: #fff;
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2);
}
.problem-btn-primary:hover {
  background: #1D4ED8;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
}
.problem-btn-primary:active {
  background: #1E40AF;
  transform: translateY(0);
}
.problem-btn-primary:disabled {
  background: #93B4E0;
  box-shadow: none;
  transform: none;
  cursor: not-allowed;
}

/* 全屏代码编辑器 */
.problem-fullscreen-overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(4px);
  padding: 24px;
}
.problem-fullscreen {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1100px;
  height: calc(100vh - 48px);
  background: #FFFFFF;
  border-radius: 12px;
  overflow: hidden;
}
:global(.dark) .problem-fullscreen {
  background: #0D1117;
  border: 1px solid #27313D;
}
.problem-fullscreen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;
  background: #F1F5F9;
  border-bottom: 1px solid #E5EAF0;
}
:global(.dark) .problem-fullscreen-header {
  background: #151B23;
  border-bottom-color: #27313D;
}
.problem-code-editor-full {
  flex: 1;
  min-height: 0;
  border: none;
  border-radius: 0;
}
</style>
