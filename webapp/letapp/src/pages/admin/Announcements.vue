<script setup lang="ts">
import { Icon } from '@iconify/vue';
import {
  NButton,
  NInput,
  NSwitch,
  useDialog,
  useMessage,
} from 'naive-ui';
import { computed, defineAsyncComponent, onMounted, ref } from 'vue';
import { formatDateTime as formatCSTDateTime } from '../../utils/time';

const MarkdownComponent = defineAsyncComponent(
  () => import('../../components/MarkdownComponent.vue'),
);

import {
  ApiError,
  createAnnouncement,
  deleteAnnouncement,
  listAnnouncements,
  updateAnnouncement,
  type AnnouncementData,
  type AnnouncementForm,
  type AnnouncementInput,
} from '../../services/api';
import { useAuthStore } from '../../stores/auth';
import {
  announcementToForm,
  canSaveAnnouncement,
} from '../../utils/announcement-access';

const EMPTY_FORM: AnnouncementForm = {
  id: 0,
  title: '',
  content: '',
  category: '系统公告',
  permission: 'member',
  is_published: true,
};

const announcementCategories = [
  { value: '系统公告', label: '系统公告', emoji: '📢' },
  { value: '比赛公告', label: '比赛公告', emoji: '🏆' },
  { value: '更新公告', label: '更新公告', emoji: '🔄' },
  { value: '活动通知', label: '活动通知', emoji: '🎉' },
];

const authStore = useAuthStore();
const dialog = useDialog();
const message = useMessage();
const isManager = computed(
  () => authStore.userRole === 'manager',
);
const loading = ref(true);
const loadError = ref('');
const saving = ref(false);
const deletingId = ref<number | null>(null);
const announcements = ref<AnnouncementData[]>([]);
const editingId = ref<number | null>(null);
const form = ref<AnnouncementForm>({ ...EMPTY_FORM });

const canSave = computed(() => canSaveAnnouncement(form.value));
const previewContent = computed(() => ({
  title: form.value.title.trim() || '未命名公告',
  content: form.value.content,
}));

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '时间未提供';
  const date = formatCSTDateTime(dateStr, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
  return date || '时间未提供';
};

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError && error.status === 403) {
    return '权限不足，仅部长及以上身份可执行此操作';
  }
  return error instanceof Error ? error.message : fallback;
};

const loadList = async () => {
  loading.value = true;
  loadError.value = '';
  try {
    announcements.value = await listAnnouncements({ includeUnpublished: true });
  } catch (error) {
    loadError.value = getErrorMessage(error, '公告列表加载失败');
  } finally {
    loading.value = false;
  }
};

const startCreate = () => {
  editingId.value = 0;
  form.value = { ...EMPTY_FORM };
};

const startEdit = (item: AnnouncementData) => {
  editingId.value = item.id;
  form.value = announcementToForm(item);
};

const cancelEdit = () => {
  if (saving.value) return;
  editingId.value = null;
};

const save = async () => {
  if (!canSave.value || saving.value) return;

  const input: AnnouncementInput = {
    title: form.value.title.trim(),
    content: form.value.content,
    category: form.value.category,
    permission: form.value.permission,
    is_published: form.value.is_published,
  };

  saving.value = true;
  try {
    if (editingId.value && editingId.value > 0) {
      await updateAnnouncement(editingId.value, input);
      message.success('公告已更新');
    } else {
      await createAnnouncement(input);
      message.success('公告已创建');
    }
    editingId.value = null;
    await loadList();
  } catch (error) {
    message.error(getErrorMessage(error, '保存失败'));
  } finally {
    saving.value = false;
  }
};

const performDelete = async (item: AnnouncementData) => {
  if (deletingId.value !== null) return;
  deletingId.value = item.id;
  try {
    await deleteAnnouncement(item.id);
    message.success('公告已删除');
    await loadList();
  } catch (error) {
    message.error(getErrorMessage(error, '删除失败'));
  } finally {
    deletingId.value = null;
  }
};

const confirmDelete = (item: AnnouncementData) => {
  dialog.warning({
    title: '删除公告',
    content: `确定删除「${item.title}」吗？此操作不可撤销。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => performDelete(item),
  });
};

const categoryBadgeClass = (cat?: string) => {
  if (cat === '比赛公告') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300';
  if (cat === '更新公告') return 'bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300';
  if (cat === '活动通知') return 'bg-violet-100 text-violet-700 dark:bg-violet-900/50 dark:text-violet-300';
  return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300';
};

onMounted(loadList);
</script>

<template>
  <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
    <header class="admin-header">
      <div class="admin-header-left">
        <h1 class="admin-header-title">公告管理</h1>
        <p class="admin-header-desc">已发布与草稿</p>
      </div>
      <button
        v-if="isManager && editingId === null"
        class="admin-btn-primary"
        :disabled="deletingId !== null"
        @click="startCreate"
      >
        <Icon icon="material-symbols:add-rounded" class="admin-btn-icon" />
        新建公告
      </button>
    </header>

    <section v-if="!isManager" class="flex min-h-80 flex-col items-center justify-center text-center text-slate-400">
      <Icon icon="material-symbols:lock-rounded" class="mb-4 h-14 w-14" />
      <p class="text-lg font-bold">权限不足</p>
      <p class="mt-1 text-sm">仅部长及以上身份可管理公告</p>
    </section>

    <section v-else-if="editingId !== null" aria-label="公告编辑器">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <NButton secondary :disabled="saving" @click="cancelEdit">
          <template #icon>
            <Icon icon="material-symbols:arrow-back-rounded" />
          </template>
          返回列表
        </NButton>
        <div class="flex items-center gap-4">
          <label class="flex items-center gap-2 text-sm font-bold text-slate-600 dark:text-slate-300">
            <NSwitch v-model:value="form.is_published" :disabled="saving" />
            {{ form.is_published ? '发布' : '草稿' }}
          </label>
          <NButton
            type="primary"
            :loading="saving"
            :disabled="!canSave || saving"
            @click="save"
          >
            <template #icon>
              <Icon icon="material-symbols:save-rounded" />
            </template>
            保存
          </NButton>
        </div>
      </div>

      <NInput
        v-model:value="form.title"
        class="mb-4"
        size="large"
        placeholder="公告标题"
        :disabled="saving"
        maxlength="200"
        show-count
      />

      <div class="mb-4 flex flex-wrap items-center gap-3">
        <span class="text-sm font-bold text-slate-600 dark:text-slate-300">分类</span>
        <button
          v-for="cat in announcementCategories"
          :key="cat.value"
          type="button"
          class="cat-btn"
          :class="form.category === cat.value ? 'cat-btn-active' : ''"
          :disabled="saving"
          @click="form.category = cat.value"
        >
          <span class="cat-btn-emoji">{{ cat.emoji }}</span>
          {{ cat.label }}
        </button>
      </div>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section class="editor-pane" aria-label="原始 Markdown">
          <div class="pane-heading">
            <Icon icon="material-symbols:edit-note-rounded" />
            原始 Markdown
          </div>
          <NInput
            v-model:value="form.content"
            type="textarea"
            class="markdown-input"
            placeholder="输入 Markdown 内容..."
            :disabled="saving"
            :autosize="false"
          />
        </section>

        <section class="editor-pane" aria-label="渲染结果">
          <div class="pane-heading">
            <Icon icon="material-symbols:visibility-outline-rounded" />
            渲染结果
          </div>
          <div class="preview-scroll">
            <MarkdownComponent
              :content="previewContent"
              :show-nav="false"
              :show-heading-links="false"
            />
          </div>
        </section>
      </div>
    </section>

    <section v-else-if="loading" class="flex min-h-80 items-center justify-center text-slate-400">
      正在加载公告...
    </section>

    <section v-else-if="loadError" class="flex min-h-80 flex-col items-center justify-center gap-4 px-4 text-center">
      <Icon icon="material-symbols:error-outline-rounded" class="h-10 w-10 text-rose-500" />
      <p class="max-w-xl text-sm text-rose-600 dark:text-rose-400">{{ loadError }}</p>
      <NButton secondary @click="loadList">
        <template #icon>
          <Icon icon="material-symbols:refresh-rounded" />
        </template>
        重试
      </NButton>
    </section>

    <section v-else-if="announcements.length === 0" class="flex min-h-80 flex-col items-center justify-center text-center text-slate-400">
      <Icon icon="material-symbols:campaign-rounded" class="mb-4 h-14 w-14" />
      <p class="text-lg font-bold">暂无公告</p>
      <p class="mt-1 text-sm">点击上方“新建公告”开始</p>
    </section>

    <section v-else class="space-y-3" aria-label="公告列表">
      <article
        v-for="item in announcements"
        :key="item.id"
        class="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white px-5 py-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:flex-row sm:items-center sm:justify-between"
      >
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-3">
            <h2 class="min-w-0 truncate text-base font-black text-slate-950 dark:text-white">
              {{ item.title }}
            </h2>
            <span
              class="shrink-0 rounded px-2 py-0.5 text-xs font-bold"
              :class="categoryBadgeClass(item.category)"
            >
              {{ item.category || '系统公告' }}
            </span>
            <span
              class="shrink-0 rounded px-2 py-0.5 text-xs font-bold"
              :class="item.is_published
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300'
                : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'"
            >
              {{ item.is_published ? '已发布' : '草稿' }}
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-400">
            更新于 {{ formatDate(item.updated_at || item.created_at) }}
          </p>
        </div>
        <div class="flex shrink-0 gap-2">
          <NButton
            secondary
            :disabled="deletingId !== null"
            @click="startEdit(item)"
          >
            <template #icon>
              <Icon icon="material-symbols:edit-outline-rounded" />
            </template>
            编辑
          </NButton>
          <NButton
            secondary
            type="error"
            :loading="deletingId === item.id"
            :disabled="deletingId !== null"
            @click="confirmDelete(item)"
          >
            <template #icon>
              <Icon icon="material-symbols:delete-outline-rounded" />
            </template>
            删除
          </NButton>
        </div>
      </article>
    </section>
  </main>
</template>

<style scoped>
@reference 'tailwindcss';

.editor-pane {
  @apply flex min-h-[34rem] max-h-[70vh] flex-col overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900;
}

.pane-heading {
  @apply flex h-11 shrink-0 items-center gap-2 border-b border-slate-200 px-4 text-sm font-bold text-slate-600 dark:border-slate-800 dark:text-slate-300;
}

.markdown-input {
  height: 100%;
  min-height: 0;
  border-radius: 0;
}

.markdown-input :deep(textarea) {
  height: 100% !important;
  padding: 1rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  line-height: 1.65;
  resize: none;
}

.preview-scroll {
  min-height: 0;
  flex: 1;
  overflow: auto;
}

@media (max-width: 1023px) {
  .editor-pane {
    min-height: 30rem;
    max-height: 42rem;
  }
}

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
.cat-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.875rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.cat-btn:hover {
  background: #e2e8f0;
  color: #334155;
}
.cat-btn-active {
  color: #2563eb;
  background: #eff6ff;
  border-color: #2563eb;
}
:global(.dark) .cat-btn {
  background: #1e293b;
  border-color: #334155;
  color: #94a3b8;
}
:global(.dark) .cat-btn:hover {
  background: #334155;
  color: #cbd5e1;
}
:global(.dark) .cat-btn-active {
  color: #60a5fa;
  background: #172554;
  border-color: #2563eb;
}
.cat-btn-emoji {
  font-size: 0.875rem;
}
</style>
