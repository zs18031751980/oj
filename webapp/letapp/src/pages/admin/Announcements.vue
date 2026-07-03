<template>
  <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-black tracking-tight text-slate-950 dark:text-white">公告管理</h1>
      <button
        v-if="isManager && !editingId"
        class="inline-flex items-center gap-2 rounded-full bg-cyan-500 px-5 py-2.5 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/25 transition hover:bg-cyan-400"
        @click="startCreate"
      >
        <Icon icon="material-symbols:add-rounded" class="h-5 w-5" />
        新建公告
      </button>
    </div>

    <div v-if="!isManager" class="flex flex-col items-center justify-center py-20 text-slate-400">
      <Icon icon="material-symbols:lock-rounded" class="mb-4 h-16 w-16" />
      <p class="text-lg font-bold">权限不足</p>
      <p class="mt-1 text-sm">仅部长、社长、管理员可管理公告</p>
    </div>

    <div v-else-if="loading" class="flex items-center justify-center py-20 text-slate-400">
      加载中...
    </div>

    <template v-else-if="editingId !== null">
      <div class="mb-4 flex items-center gap-4">
        <button
          class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
          @click="cancelEdit"
        >
          <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4" />
          返回列表
        </button>
        <button
          class="inline-flex items-center gap-2 rounded-full bg-cyan-500 px-5 py-2.5 text-sm font-black text-slate-950 shadow-lg transition hover:bg-cyan-400 disabled:opacity-50"
          :disabled="!form.title.trim() || !form.content.trim()"
          @click="save"
        >
          <Icon icon="material-symbols:save-rounded" class="h-4 w-4" />
          保存
        </button>
      </div>

      <div class="mb-4">
        <input
          v-model="form.title"
          type="text"
          placeholder="公告标题"
          class="w-full rounded-2xl border border-slate-200 bg-white/85 px-5 py-3 text-lg font-black text-slate-950 shadow-sm backdrop-blur-2xl placeholder:text-slate-400 focus:border-cyan-400 focus:outline-none dark:border-slate-700 dark:bg-slate-900/85 dark:text-white dark:placeholder:text-slate-500"
        />
      </div>

      <div class="flex gap-4">
        <div class="flex-1">
          <textarea
            v-model="form.content"
            placeholder="输入 Markdown 内容..."
            class="h-[70vh] w-full resize-none rounded-2xl border border-slate-200 bg-white/85 p-5 font-mono text-sm leading-relaxed text-slate-950 shadow-sm backdrop-blur-2xl placeholder:text-slate-400 focus:border-cyan-400 focus:outline-none dark:border-slate-700 dark:bg-slate-900/85 dark:text-slate-100 dark:placeholder:text-slate-500"
          ></textarea>
        </div>
        <div class="flex-1 overflow-y-auto rounded-2xl border border-slate-200 bg-white/85 p-5 shadow-sm backdrop-blur-2xl dark:border-slate-700 dark:bg-slate-900/85">
          <div class="prose prose-slate max-w-none dark:prose-invert" v-html="previewHtml"></div>
        </div>
      </div>
    </template>

    <template v-else>
      <div v-if="announcements.length === 0" class="flex flex-col items-center justify-center py-20 text-slate-400">
        <Icon icon="material-symbols:campaign-rounded" class="mb-4 h-16 w-16" />
        <p class="text-lg font-bold">暂无公告</p>
        <p class="mt-1 text-sm">点击上方"新建公告"开始</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="item in announcements"
          :key="item.id"
          class="flex items-center justify-between rounded-2xl border border-slate-200 bg-white/85 px-6 py-4 shadow-sm backdrop-blur-2xl transition hover:bg-white dark:border-slate-800 dark:bg-slate-900/85 dark:hover:bg-slate-900"
        >
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-3">
              <h3 class="truncate text-base font-black text-slate-950 dark:text-white">{{ item.title }}</h3>
              <span
                class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold"
                :class="item.is_published ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'"
              >
                {{ item.is_published ? '已发布' : '草稿' }}
              </span>
            </div>
            <p class="mt-1 text-xs text-slate-400">
              更新于 {{ formatDate(item.updated_at) }}
            </p>
          </div>
          <div class="ml-4 flex shrink-0 gap-2">
            <button
              class="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
              @click="startEdit(item)"
            >
              编辑
            </button>
            <button
              class="rounded-2xl border border-rose-200 bg-white px-4 py-2 text-sm font-bold text-rose-500 transition hover:bg-rose-50 dark:border-rose-900/50 dark:bg-slate-900 dark:text-rose-400 dark:hover:bg-rose-950/30"
              @click="remove(item)"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { Icon } from '@iconify/vue';
import MarkdownIt from 'markdown-it';
import { useAuthStore } from '../../stores/auth';
import {
  listAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  type AnnouncementData,
} from '../../services/api';

const authStore = useAuthStore();
const isManager = computed(() => authStore.userRole === 'manager');

const md = new MarkdownIt({ html: true, linkify: true });

const loading = ref(true);
const announcements = ref<AnnouncementData[]>([]);
const editingId = ref<number | null>(null);
const form = ref({ title: '', content: '', permission: 'member', is_published: true });

const previewHtml = computed(() => {
  if (!form.value.content) return '<p style="color:#94a3b8">预览区域</p>';
  return md.render(form.value.content);
});

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
};

const loadList = async () => {
  loading.value = true;
  try {
    announcements.value = await listAnnouncements();
  } catch {
    announcements.value = [];
  } finally {
    loading.value = false;
  }
};

const startCreate = () => {
  editingId.value = 0;
  form.value = { title: '', content: '', permission: 'member', is_published: true };
};

const startEdit = (item: AnnouncementData) => {
  editingId.value = item.id ?? 0;
  form.value = {
    title: item.title,
    content: item.content,
    permission: item.permission || 'member',
    is_published: item.is_published ?? true,
  };
};

const cancelEdit = () => {
  editingId.value = null;
  loadList();
};

const save = async () => {
  if (!form.value.title.trim() || !form.value.content.trim()) return;
  try {
    if (editingId.value && editingId.value > 0) {
      await updateAnnouncement(editingId.value, form.value);
    } else {
      await createAnnouncement(form.value);
    }
    editingId.value = null;
    await loadList();
  } catch (e) {
    console.error('保存失败', e);
  }
};

const remove = async (item: AnnouncementData) => {
  if (!item.id) return;
  if (!confirm(`确定要删除「${item.title}」吗？`)) return;
  try {
    await deleteAnnouncement(item.id);
    await loadList();
  } catch (e) {
    console.error('删除失败', e);
  }
};

onMounted(loadList);
</script>
