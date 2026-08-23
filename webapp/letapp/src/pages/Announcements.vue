<script setup lang="ts">
import { Icon } from '@iconify/vue';
import { NButton } from 'naive-ui';
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import MarkdownComponent from '../components/MarkdownComponent.vue';
import {
  getAnnouncement,
  listAnnouncements,
  type AnnouncementData,
} from '../services/api';
import { useAuthStore } from '../stores/auth';
import {
  parseAnnouncementId,
  sortAnnouncementsNewestFirst,
} from '../utils/announcement-access';

interface Content {
  title?: string;
  date?: string;
  content: string;
}

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const announcements = ref<AnnouncementData[]>([]);
const selectedContent = ref<Content>();
const isLoadingList = ref(false);
const isLoadingDoc = ref(false);
const listError = ref('');
const detailError = ref('');

const sortedAnnouncements = computed(() =>
  sortAnnouncementsNewestFirst(announcements.value),
);
const currentAnnouncementId = computed(() => parseAnnouncementId(route.query.id));
const isDetailMode = computed(() => route.query.id !== undefined);
const canManageAnnouncements = computed(
  () => authStore.userRole === 'manager' || authStore.userRole === 'staff',
);

const formatTime = (dateStr?: string) => {
  if (!dateStr) return '时间未提供';
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return '时间未提供';
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const loadAnnouncements = async () => {
  isLoadingList.value = true;
  listError.value = '';
  try {
    announcements.value = await listAnnouncements();
  } catch (error) {
    listError.value = error instanceof Error ? error.message : '公告列表加载失败';
  } finally {
    isLoadingList.value = false;
  }
};

const loadSelectedAnnouncement = async () => {
  selectedContent.value = undefined;
  detailError.value = '';

  const id = currentAnnouncementId.value;
  if (id === null) {
    detailError.value = '公告地址无效，请返回列表重新选择。';
    return;
  }

  isLoadingDoc.value = true;
  try {
    const announcement = await getAnnouncement(id);
    selectedContent.value = {
      title: announcement.title,
      date: announcement.published_at || announcement.created_at,
      content: announcement.content,
    };
  } catch (error) {
    detailError.value = error instanceof Error ? error.message : '公告内容加载失败';
  } finally {
    isLoadingDoc.value = false;
  }
};

const openAnnouncement = (item: AnnouncementData) =>
  router.push({ path: '/announcements', query: { id: String(item.id) } });

const goBackToList = () => router.push('/announcements');
const openManager = () => router.push('/admin/announcements');

onMounted(async () => {
  await loadAnnouncements();
  if (isDetailMode.value) {
    await loadSelectedAnnouncement();
  }
});

watch(
  () => route.query.id,
  async (id, previousId) => {
    if (id === previousId) return;
    if (id === undefined) {
      selectedContent.value = undefined;
      detailError.value = '';
      return;
    }
    await loadSelectedAnnouncement();
  },
);
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
              <NButton v-if="canManageAnnouncements" secondary @click="openManager">
                <template #icon>
                  <Icon icon="material-symbols:settings-outline-rounded" />
                </template>
                管理公告
              </NButton>
              <span class="rounded-full bg-cyan-100 px-3 py-1.5 text-xs font-bold text-cyan-700 dark:bg-cyan-900/60 dark:text-cyan-300">
                {{ sortedAnnouncements.length }} 条公告
              </span>
            </div>
          </div>
        </div>
      </div>

        <div class="announcements-content flex-1 overflow-y-auto">
          <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            <div v-if="isLoadingList" class="flex min-h-72 items-center justify-center text-slate-500 dark:text-slate-400">
              正在加载公告列表...
            </div>
            <div v-else-if="listError" class="flex min-h-72 flex-col items-center justify-center gap-4 px-4 text-center">
              <Icon icon="material-symbols:error-outline-rounded" class="h-10 w-10 text-rose-500" />
              <p class="max-w-xl text-sm text-rose-600 dark:text-rose-400">{{ listError }}</p>
              <NButton secondary @click="loadAnnouncements">
                <template #icon>
                  <Icon icon="material-symbols:refresh-rounded" />
                </template>
                重试
              </NButton>
            </div>
            <div v-else-if="sortedAnnouncements.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
              <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-[2rem] border-2 border-dashed border-slate-300 bg-slate-100 dark:border-slate-700 dark:bg-slate-900">
                <Icon icon="material-symbols:campaign-outline" width="32" height="32" class="text-slate-400 dark:text-slate-500" />
              </div>
              <p class="text-lg font-bold text-slate-500 dark:text-slate-400">暂无公告</p>
              <p class="mt-2 text-sm text-slate-400 dark:text-slate-500">请稍后再来看看</p>
            </div>
            <div v-else class="announcements-grid grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              <button
                v-for="item in sortedAnnouncements"
                :key="item.id"
                type="button"
                class="announcement-card group"
                @click="openAnnouncement(item)"
              >
                <div class="card-content">
                  <div class="card-title">{{ item.title }}</div>
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="card-time">
                      {{ formatTime(item.updated_at || item.published_at || item.created_at) }}
                    </span>
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
            <div v-else-if="detailError" class="flex min-h-[320px] flex-col items-center justify-center gap-4 p-8 text-center">
              <Icon icon="material-symbols:error-outline-rounded" class="h-10 w-10 text-rose-500" />
              <p class="text-rose-600 dark:text-rose-400">{{ detailError }}</p>
              <NButton v-if="currentAnnouncementId" secondary @click="loadSelectedAnnouncement">
                <template #icon>
                  <Icon icon="material-symbols:refresh-rounded" />
                </template>
                重试
              </NButton>
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
