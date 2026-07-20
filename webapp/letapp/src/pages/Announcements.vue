<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';
import MarkdownComponent from '../components/MarkdownComponent.vue';

interface Content {
  title?: string;
  date?: string;
  content: string;
}

interface ManifestItem {
  file: string;
  title: string;
  updatedAt: string;
}

const route = useRoute();
const router = useRouter();
const manifest = ref<ManifestItem[]>([]);
const selectedContent = ref<Content | undefined>();
const isLoadingDoc = ref(false);
const docError = ref('');

const sortedAnnouncements = computed(() =>
  [...manifest.value].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
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

const openAnnouncement = async (item: ManifestItem) => {
  await router.push({ path: '/announcements', query: { doc: item.file } });
};

const goBackToList = async () => {
  await router.push('/announcements');
};

function parseMarkdown(raw: string): { title?: string; date?: string; content: string } {
  const idx = raw.indexOf('---');
  if (idx !== 0) return { content: raw };
  const end = raw.indexOf('---', 3);
  if (end === -1) return { content: raw };
  const front = raw.slice(3, end).trim();
  const body = raw.slice(end + 3).trim();
  const titleMatch = front.match(/^title:\s*(.+)/m);
  const dateMatch = front.match(/^date:\s*(.+)/m);
  return {
    title: titleMatch ? titleMatch[1]!.trim() : undefined,
    date: dateMatch ? dateMatch[1]!.trim() : undefined,
    content: body,
  };
}

const loadMarkdown = async (file: string) => {
  isLoadingDoc.value = true;
  docError.value = '';

  try {
    const res = await fetch(`/announcements/${encodeURIComponent(file)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const raw = await res.text();
    const { title, date, content } = parseMarkdown(raw);
    selectedContent.value = {
      title,
      content,
      date,
    };
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
  <div class="announcements-page flex min-h-[calc(100vh-var(--header-h,5rem))] flex-col bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.24),_transparent_34%),radial-gradient(circle_at_85%_18%,_rgba(250,204,21,0.18),_transparent_22%),linear-gradient(180deg,_#ecfeff_0%,_#f8fafc_52%,_#f8fafc_100%)] text-slate-950 transition-colors duration-300 dark:bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_32%),radial-gradient(circle_at_85%_18%,_rgba(250,204,21,0.08),_transparent_22%),linear-gradient(180deg,_#020617_0%,_#020617_100%)] dark:text-slate-50">
    <template v-if="!isDetailMode">
      <div class="announcements-hero border-b border-slate-200/60 bg-white/60 backdrop-blur-2xl dark:border-slate-800/50 dark:bg-slate-950/50">
        <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="max-w-3xl">
              <p class="text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Announcements</p>
              <h1 class="mt-3 text-4xl font-black tracking-tight sm:text-5xl">公告</h1>
            </div>
            <div class="flex items-center gap-3">
              <span class="rounded-full bg-cyan-100 px-3 py-1.5 text-xs font-bold text-cyan-700 dark:bg-cyan-900/60 dark:text-cyan-300">
                {{ sortedAnnouncements.length }} 条公告
              </span>
            </div>
          </div>
        </div>
      </div>

        <div class="announcements-content flex-1 overflow-y-auto">
          <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            <div v-if="sortedAnnouncements.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
              <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-[2rem] border-2 border-dashed border-slate-300 bg-slate-100 dark:border-slate-700 dark:bg-slate-900">
                <Icon icon="material-symbols:campaign-outline" width="32" height="32" class="text-slate-400 dark:text-slate-500" />
              </div>
              <p class="text-lg font-bold text-slate-500 dark:text-slate-400">暂无公告</p>
              <p class="mt-2 text-sm text-slate-400 dark:text-slate-500">请稍后再来看看</p>
            </div>
            <div v-else class="announcements-grid grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              <button
                v-for="item in sortedAnnouncements"
                :key="item.file"
                type="button"
                class="announcement-card group"
                @click="openAnnouncement(item)"
              >
                <div class="card-content">
                  <div class="card-title">{{ item.title }}</div>
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="card-time">{{ formatTime(item.updatedAt) }}</span>
                  </div>
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
        <div class="announcement-detail mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
          <div class="detail-toolbar mb-6 flex flex-wrap items-center justify-between gap-4">
            <button
              class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
              @click="goBackToList"
            >
              <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4" />
              返回公告列表
            </button>
          </div>

          <div class="announcement-document overflow-hidden rounded-[2rem] border border-slate-200 bg-white/85 shadow-xl shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20">
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

    <template v-if="!isDetailMode">
      <footer class="border-t border-slate-200/60 bg-white/60 backdrop-blur-2xl dark:border-slate-800/50 dark:bg-slate-950/50">
        <div class="mx-auto max-w-7xl px-4 py-6 text-center text-sm text-slate-400 dark:text-slate-500">
          Let Coding — Announcements
        </div>
      </footer>
    </template>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.announcement-card {
  @apply relative flex min-h-[7.5rem] items-start justify-between rounded-[1.75rem] border border-slate-200 bg-white/85 p-6 text-left shadow-lg shadow-slate-200/60 backdrop-blur-2xl transition hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20;
}

.card-content {
  @apply flex min-w-0 flex-1 flex-col gap-2;
}

.card-title {
  @apply text-base font-black leading-snug text-slate-950 transition group-hover:text-cyan-600 dark:text-white dark:group-hover:text-cyan-400 line-clamp-3;
}

.card-time {
  @apply text-xs font-medium text-slate-400 dark:text-slate-500;
}

.card-arrow {
  @apply ml-3 mt-1 shrink-0 text-slate-300 transition group-hover:text-cyan-500 dark:text-slate-600 dark:group-hover:text-cyan-400;
}
</style>

<style>
.announcements-page {
  --page-border: #c7d2da;
  background: #e8ecef !important;
}

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

.announcements-hero {
  position: relative;
  overflow: hidden;
  background: #f1f4f6 !important;
}

.announcements-hero::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: "";
  opacity: 0.42;
  background-image:
    linear-gradient(rgba(14, 116, 144, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14, 116, 144, 0.08) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: linear-gradient(90deg, #000, transparent 78%);
}

.announcements-hero > div {
  position: relative;
  z-index: 1;
}

.announcements-content {
  padding-top: 2rem;
}

.announcements-grid {
  align-items: stretch;
}

.announcement-card {
  min-height: 10rem;
  justify-content: space-between;
  border-radius: 0.75rem !important;
  border-color: #c6cfd5 !important;
  background: #f7f9fa !important;
  box-shadow: 0 16px 35px rgba(51, 65, 85, 0.1) !important;
}

.announcement-card::before {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  content: "";
  background: #22d3ee;
  transform: scaleX(0.2);
  transform-origin: left;
  transition: transform 0.25s ease;
}

.announcement-card:hover {
  transform: translateY(-4px);
  border-color: #06b6d4 !important;
  background: #eef7f9 !important;
  box-shadow: 0 20px 42px rgba(14, 116, 144, 0.16) !important;
}

.announcement-card:hover::before {
  transform: scaleX(1);
}

.card-title {
  max-width: 26rem;
  line-height: 1.35;
}

.card-time {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 0.04em;
}

.card-time::before {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 50%;
  background: #22d3ee;
  content: "";
}

.announcement-detail {
  padding-top: 2rem;
}

.announcement-detail > .detail-toolbar {
  padding-bottom: 1rem;
  border-bottom: 1px solid #c6cfd5;
}

.announcement-document {
  border-radius: 0.75rem !important;
  border-color: #c6cfd5 !important;
  background: #f7f9fa !important;
  box-shadow: 0 20px 50px rgba(51, 65, 85, 0.1) !important;
}

html.dark .announcements-hero {
  background: #151b20 !important;
}

html.dark .announcements-page {
  --page-border: #35414a;
  background: #101418 !important;
}

html.dark .announcements-hero::after {
  opacity: 0.3;
  background-image:
    linear-gradient(rgba(103, 232, 249, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(103, 232, 249, 0.08) 1px, transparent 1px);
}

html.dark .announcement-card {
  border-color: #35414a !important;
  background: #151b20 !important;
  box-shadow: none !important;
}

html.dark .announcement-card:hover {
  border-color: #0891b2 !important;
  background: #1d2930 !important;
  box-shadow: 0 20px 42px rgba(0, 0, 0, 0.24) !important;
}

html.dark .announcement-detail > .detail-toolbar {
  border-color: #35414a;
}

html.dark .announcement-document {
  border-color: #35414a !important;
  background: #151b20 !important;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.22) !important;
}

@media (max-width: 640px) {
  .announcement-card {
    min-height: 8.5rem;
  }
}
</style>
