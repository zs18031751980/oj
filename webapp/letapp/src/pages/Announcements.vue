<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';
import MarkdownComponent from '../components/MarkdownComponent.vue';

interface ManifestItem {
  file: string;
  title: string;
  updatedAt: string;
}

interface MarkdownContent {
  content: string;
}

const route = useRoute();
const router = useRouter();

const manifest = ref<ManifestItem[]>([]);
const selectedContent = ref<MarkdownContent | undefined>();
const isLoadingDoc = ref(false);
const docError = ref('');

const sortedAnnouncements = computed(() =>
  [...manifest.value].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  )
);

const currentFile = computed(() => {
  const raw = route.query.doc;
  return Array.isArray(raw) ? raw[0] || '' : String(raw || '');
});

const isDetailMode = computed(() => Boolean(currentFile.value));

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  });
};

const openAnnouncement = (item: ManifestItem) => {
  const href = router.resolve({ path: '/announcements', query: { doc: item.file } }).href;
  window.open(href, '_blank', 'noopener,noreferrer');
};

const goBackToList = async () => {
  await router.push('/announcements');
};

const loadMarkdown = async (file: string) => {
  isLoadingDoc.value = true;
  docError.value = '';

  try {
    const res = await fetch(`/announcements/${encodeURIComponent(file)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    selectedContent.value = { content: await res.text() };
  } catch (error) {
    selectedContent.value = undefined;
    docError.value = `加载失败：${error instanceof Error ? error.message : '未知错误'}`;
  } finally {
    isLoadingDoc.value = false;
  }
};

onMounted(async () => {
  try {
    const res = await fetch('/announcements/manifest.json');
    manifest.value = await res.json();
    if (currentFile.value) {
      await loadMarkdown(currentFile.value);
    }
  } catch (e) {
    console.error('Failed to load manifest:', e);
  }
});

watch(currentFile, async (file) => {
  if (!file) {
    selectedContent.value = undefined;
    docError.value = '';
    return;
  }
  await loadMarkdown(file);
});
</script>

<template>
  <div class="flex min-h-[calc(100vh-5rem)] flex-col bg-slate-50 text-slate-950 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-50">
    <template v-if="!isDetailMode">
      <div class="border-b border-slate-200/80 bg-white/80 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/80">
        <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="max-w-3xl">
              <p class="text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Announcements</p>
              <h1 class="mt-3 text-4xl font-black tracking-tight sm:text-5xl">最新公告</h1>
            </div>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto">
        <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <button
              v-for="item in sortedAnnouncements"
              :key="item.file"
              type="button"
              class="announcement-card group"
              @click="openAnnouncement(item)"
            >
              <div class="card-content">
                <div class="card-title">{{ item.title }}</div>
                <div class="card-time">{{ formatTime(item.updatedAt) }}</div>
              </div>
              <div class="card-arrow">
                <Icon icon="material-symbols:open-in-new" class="h-4 w-4" />
              </div>
            </button>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
          <button
            class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            @click="goBackToList"
          >
            <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4" />
            返回公告列表
          </button>
        </div>

        <div class="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-xl shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20">
          <div v-if="isLoadingDoc" class="flex min-h-[320px] items-center justify-center p-8 text-slate-500 dark:text-slate-400">
            正在加载公告内容...
          </div>
          <div v-else-if="docError" class="flex min-h-[320px] items-center justify-center p-8 text-center text-rose-500">
            {{ docError }}
          </div>
          <MarkdownComponent v-else :content="selectedContent" :show-nav="false" :show-heading-links="false" />
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.announcement-card {
  @apply relative flex min-h-[7.5rem] items-start justify-between rounded-[1.75rem] border border-slate-200 bg-white p-6 text-left shadow-lg shadow-slate-200/60 transition hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20;
}

.card-content {
  @apply flex min-w-0 flex-1 flex-col gap-2;
}

.card-title {
  @apply text-base font-black leading-snug text-slate-950 transition group-hover:text-cyan-600 dark:text-white dark:group-hover:text-cyan-400;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-time {
  @apply mt-auto text-xs font-medium text-slate-400 dark:text-slate-500;
}

.card-arrow {
  @apply ml-3 mt-1 shrink-0 text-slate-300 transition group-hover:text-cyan-500 dark:text-slate-600 dark:group-hover:text-cyan-400;
}
</style>

<style>
html:not(.dark) .announcement-card {
  background-color: #ffffff !important;
  border-color: #e2e8f0 !important;
  color: #0f172a !important;
}

html.dark .announcement-card {
  background-color: #0f172a !important;
  border-color: #1e293b !important;
  color: #f8fafc !important;
}

html:not(.dark) .announcement-card:hover {
  border-color: #7dd3fc !important;
}

html.dark .announcement-card:hover {
  border-color: #155e75 !important;
}

html:not(.dark) .announcement-card .card-title {
  color: #0f172a !important;
}

html.dark .announcement-card .card-title {
  color: #f8fafc !important;
}

html:not(.dark) .announcement-card:hover .card-title {
  color: #0891b2 !important;
}

html.dark .announcement-card:hover .card-title {
  color: #67e8f9 !important;
}
</style>
