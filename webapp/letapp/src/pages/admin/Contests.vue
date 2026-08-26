<script setup lang="ts">
import { ref, defineAsyncComponent, onMounted } from 'vue';
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
  if (!validateAllFields()) {
    message.warning('请填写所有必填字段');
    return;
  }

  const f = problemForm.value;
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
          <h2 class="problem-modal-title">{{ editingProblem ? '编辑题目' : '添加题目' }}</h2>
          <button class="problem-modal-close" @click="showProblemForm = false">
            <Icon icon="material-symbols:close" class="h-5 w-5" />
          </button>
        </div>

        <!-- 内容区域 -->
        <div class="problem-modal-body">
          <!-- 左侧：表单区 (58%) -->
          <div class="problem-form-section">
            <!-- 分组1：基础信息 -->
            <div class="problem-form-group">
              <div class="problem-form-group-header">
                <Icon icon="material-symbols:info" class="h-4 w-4 text-[#2563EB]" />
                <span class="problem-form-group-title">基础信息</span>
              </div>
              <div class="problem-form-group-content">
                <div class="problem-form-row">
                  <div class="problem-form-field">
                    <label class="problem-label">
                      题目编号 <span class="problem-required">*</span>
                    </label>
                    <input
                      v-model="problemForm.problem_index"
                      class="problem-input"
                      :class="{ 'problem-input-error': formErrors.problem_index }"
                      placeholder="例如：A"
                      maxlength="10"
                      @blur="validateField('problem_index')"
                    />
                    <span v-if="formErrors.problem_index" class="problem-form-error">{{ formErrors.problem_index }}</span>
                  </div>
                  <div class="problem-form-field">
                    <label class="problem-label">难度</label>
                    <select v-model="problemForm.difficulty" class="problem-input">
                      <option value="简单">简单</option>
                      <option value="中等">中等</option>
                      <option value="困难">困难</option>
                    </select>
                  </div>
                </div>
                <div class="problem-form-field">
                  <label class="problem-label">
                    题目标题 <span class="problem-required">*</span>
                  </label>
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

            <!-- 分组2：题目内容 -->
            <div class="problem-form-group">
              <div class="problem-form-group-header">
                <Icon icon="material-symbols:description" class="h-4 w-4 text-[#2563EB]" />
                <span class="problem-form-group-title">题目内容</span>
              </div>
              <div class="problem-form-group-content">
                <div class="problem-form-field">
                  <label class="problem-label">
                    题目描述 <span class="problem-required">*</span>
                  </label>
                  <div class="problem-textarea-wrapper">
                    <textarea
                      v-model="problemForm.description"
                      class="problem-textarea font-mono"
                      :class="{ 'problem-input-error': formErrors.description }"
                      rows="10"
                      placeholder="## 题目描述&#10;&#10;给定一个整数数组..."
                      @blur="validateField('description')"
                    ></textarea>
                    <div class="problem-textarea-hint">
                      <Icon icon="material-symbols:code" class="h-3.5 w-3.5" />
                      <span>支持 Markdown 格式</span>
                    </div>
                    <span v-if="formErrors.description" class="problem-form-error">{{ formErrors.description }}</span>
                  </div>
                </div>
                <div class="problem-form-row">
                  <div class="problem-form-field">
                    <label class="problem-label">输入格式</label>
                    <textarea v-model="problemForm.input_desc" class="problem-textarea" rows="5" placeholder="第一行包含..."></textarea>
                  </div>
                  <div class="problem-form-field">
                    <label class="problem-label">输出格式</label>
                    <textarea v-model="problemForm.output_desc" class="problem-textarea" rows="5" placeholder="输出一个整数..."></textarea>
                  </div>
                </div>
              </div>
            </div>

            <!-- 分组3：判题配置 -->
            <div class="problem-form-group">
              <div class="problem-form-group-header">
                <Icon icon="material-symbols:settings" class="h-4 w-4 text-[#2563EB]" />
                <span class="problem-form-group-title">判题配置</span>
              </div>
              <div class="problem-form-group-content">
                <div class="problem-form-field">
                  <label class="problem-label">
                    正确答案（参考代码） <span class="problem-required">*</span>
                  </label>
                  <textarea
                    v-model="problemForm.correct_answer"
                    class="problem-textarea font-mono"
                    :class="{ 'problem-input-error': formErrors.correct_answer }"
                    rows="8"
                    placeholder="# Python 示例&#10;def solve(n, nums):&#10;    return sum(nums)"
                    @blur="validateField('correct_answer')"
                  ></textarea>
                  <span v-if="formErrors.correct_answer" class="problem-form-error">{{ formErrors.correct_answer }}</span>
                </div>
                <div class="problem-form-row">
                  <div class="problem-form-field">
                    <label class="problem-label">时间限制</label>
                    <div class="problem-input-with-unit">
                      <input v-model.number="problemForm.time_limit" type="number" class="problem-input" min="100" max="10000" />
                      <span class="problem-input-unit">ms</span>
                    </div>
                  </div>
                  <div class="problem-form-field">
                    <label class="problem-label">内存限制</label>
                    <div class="problem-input-with-unit">
                      <input v-model.number="problemForm.memory_limit" type="number" class="problem-input" min="64" max="1024" />
                      <span class="problem-input-unit">MB</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧：实时预览区 (42%) -->
          <div class="problem-preview-section">
            <div class="problem-preview-header">
              <Icon icon="material-symbols:visibility" class="h-4 w-4 text-[#2563EB]" />
              <span class="problem-preview-title">预览效果</span>
            </div>
            <div class="problem-preview-content">
              <template v-if="problemForm.title || problemForm.description">
                <div class="problem-preview-card">
                  <div v-if="problemForm.title" class="problem-preview-title-area">
                    <h3 class="problem-preview-problem-title">{{ problemForm.title }}</h3>
                    <span class="problem-preview-difficulty" :class="difficultyClass(problemForm.difficulty)">
                      {{ problemForm.difficulty }}
                    </span>
                  </div>
                  <div v-if="problemForm.description" class="problem-preview-description">
                    <MarkdownComponent
                      :content="{ content: problemForm.description }"
                      :show-nav="false"
                      :show-heading-links="false"
                    />
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
            <Icon icon="material-symbols:check-circle" class="h-4 w-4 text-emerald-500" />
            <span>表单已准备就绪</span>
          </div>
          <div class="problem-modal-footer-actions">
            <button class="problem-btn problem-btn-cancel" @click="showProblemForm = false">取消</button>
            <button class="problem-btn problem-btn-primary" :disabled="isGeneratingTestcases" @click="saveProblem">
              <Icon v-if="isGeneratingTestcases" icon="svg-spinners:ring-resize" class="h-4 w-4" />
              <Icon v-else icon="material-symbols:add-circle" class="h-4 w-4" />
              {{ isGeneratingTestcases ? '正在生成测试用例...' : (editingProblem ? '保存修改' : '创建题目') }}
            </button>
          </div>
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
  max-width: 1160px;
  max-height: 90vh;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}
:global(.dark) .problem-modal {
  background: #111827;
  border: 1px solid #1E293B;
}

/* 顶部标题栏 */
.problem-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 28px;
  border-bottom: 1px solid #E2E8F0;
  flex-shrink: 0;
}
:global(.dark) .problem-modal-header {
  border-bottom-color: #1E293B;
}
.problem-modal-title {
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  margin: 0;
}
:global(.dark) .problem-modal-title {
  color: #E5E7EB;
}
.problem-modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
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
  background: #1E293B;
  color: #E5E7EB;
}

/* 内容区域 */
.problem-modal-body {
  display: flex;
  gap: 24px;
  flex: 1;
  overflow: hidden;
  padding: 24px;
}

/* 左侧表单区 */
.problem-form-section {
  flex: 0 0 58%;
  display: flex;
  flex-direction: column;
  gap: 28px;
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

/* 表单分组 */
.problem-form-group {
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  overflow: hidden;
}
:global(.dark) .problem-form-group {
  border-color: #1E293B;
}
.problem-form-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #F8FAFC;
  border-bottom: 1px solid #E2E8F0;
}
:global(.dark) .problem-form-group-header {
  background: #1E293B;
  border-bottom-color: #1E293B;
}
.problem-form-group-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}
:global(.dark) .problem-form-group-title {
  color: #E5E7EB;
}
.problem-form-group-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 表单行 */
.problem-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* 表单字段 */
.problem-form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 标签 */
.problem-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}
:global(.dark) .problem-label {
  color: #94A3B8;
}
.problem-required {
  color: #EF4444;
  font-weight: 500;
}

/* 输入框 */
.problem-input {
  height: 42px;
  padding: 0 14px;
  font-size: 14px;
  color: #1E293B;
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  outline: none;
  transition: all 0.15s ease;
}
.problem-input::placeholder {
  color: #94A3B8;
}
.problem-input:focus {
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
:global(.dark) .problem-input {
  color: #E5E7EB;
  background: #0F172A;
  border-color: #1E293B;
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
  gap: 0;
}
.problem-input-with-unit .problem-input {
  flex: 1;
  border-radius: 8px 0 0 8px;
}
.problem-input-unit {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 42px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-left: none;
  border-radius: 0 8px 8px 0;
}
:global(.dark) .problem-input-unit {
  color: #94A3B8;
  background: #1E293B;
  border-color: #1E293B;
}

/* 文本域 */
.problem-textarea {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.6;
  color: #1E293B;
  background: #fff;
  border: 1px solid #E2E8F0;
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
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
:global(.dark) .problem-textarea {
  color: #E5E7EB;
  background: #0F172A;
  border-color: #1E293B;
}
:global(.dark) .problem-textarea::placeholder {
  color: #64748B;
}
:global(.dark) .problem-textarea:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

/* 文本域包装器 */
.problem-textarea-wrapper {
  position: relative;
}
.problem-textarea-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 12px;
  color: #94A3B8;
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
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  overflow: hidden;
}
:global(.dark) .problem-preview-section {
  border-color: #1E293B;
}
.problem-preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #F8FAFC;
  border-bottom: 1px solid #E2E8F0;
  flex-shrink: 0;
}
:global(.dark) .problem-preview-header {
  background: #1E293B;
  border-bottom-color: #1E293B;
}
.problem-preview-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}
:global(.dark) .problem-preview-title {
  color: #E5E7EB;
}
.problem-preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 480px;
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
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 20px;
}
:global(.dark) .problem-preview-card {
  background: #0F172A;
  border-color: #1E293B;
}
.problem-preview-title-area {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #E2E8F0;
}
:global(.dark) .problem-preview-title-area {
  border-bottom-color: #1E293B;
}
.problem-preview-problem-title {
  font-size: 18px;
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
.problem-preview-description {
  font-size: 14px;
  line-height: 1.7;
  color: #334155;
}
:global(.dark) .problem-preview-description {
  color: #CBD5E1;
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
  height: 72px;
  padding: 0 28px;
  border-top: 1px solid #E2E8F0;
  flex-shrink: 0;
}
:global(.dark) .problem-modal-footer {
  border-top-color: #1E293B;
}
.problem-modal-footer-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748B;
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
  height: 42px;
  padding: 0 20px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
}
.problem-btn-cancel {
  min-width: 80px;
  background: #fff;
  color: #475569;
  border: 1px solid #E2E8F0;
}
.problem-btn-cancel:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
}
:global(.dark) .problem-btn-cancel {
  background: #0F172A;
  color: #94A3B8;
  border-color: #1E293B;
}
:global(.dark) .problem-btn-cancel:hover {
  background: #1E293B;
}
.problem-btn-primary {
  min-width: 120px;
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
</style>
