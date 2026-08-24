<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const MarkdownComponent = defineAsyncComponent(
  () => import('../components/MarkdownComponent.vue'),
);

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

// 分类推断（后端暂无 category 字段，用关键词启发）
const categories = ['全部', '系统公告', '比赛公告', '更新日志', '活动通知'];
const activeCategory = ref('全部');
const categoryEmojis: Record<string, string> = {
  '全部': '📋',
  '系统公告': '📢',
  '比赛公告': '🏆',
  '更新日志': '🔄',
  '活动通知': '🎉',
};
const inferCategory = (title: string): string => {
  const t = title.toLowerCase();
  if (t.includes('比赛') || t.includes('contest')) return '比赛公告';
  if (t.includes('更新') || t.includes('update') || t.includes('日志')) return '更新日志';
  if (t.includes('活动') || t.includes('event')) return '活动通知';
  return '系统公告';
};
const getCategoryEmoji = (title: string) => categoryEmojis[inferCategory(title)] ?? '📢';
const getCategoryColor = (title: string): string => {
  const cat = inferCategory(title);
  if (cat === '比赛公告') return 'bg-amber-50 dark:bg-amber-950/40';
  if (cat === '更新日志') return 'bg-emerald-50 dark:bg-emerald-950/40';
  if (cat === '活动通知') return 'bg-violet-50 dark:bg-violet-950/40';
  return 'bg-[#EFF6FF] dark:bg-[#172554]';
};
const filteredAnnouncements = computed(() => {
  const list = sortedAnnouncements.value;
  if (activeCategory.value === '全部') return list;
  return list.filter((a) => inferCategory(a.title) === activeCategory.value);
});
const categoryCounts = computed(() => {
  const counts: Record<string, number> = { '全部': sortedAnnouncements.value.length };
  sortedAnnouncements.value.forEach((a) => {
    const cat = inferCategory(a.title);
    counts[cat] = (counts[cat] || 0) + 1;
  });
  return counts;
});

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
  <div class="announcements-page min-h-[calc(100vh-var(--header-h,4rem))] bg-[#F6F8FC] dark:bg-[#0F172A]">
    <!-- ===== 列表视图 ===== -->
    <template v-if="!isDetailMode">
      <div class="app-container-with-sidebar py-6 pt-8">
        <!-- 左侧分类栏 240px -->
        <aside class="app-sidebar-col">
          <div class="ui-card space-y-1 p-3">
            <button
              v-for="cat in categories"
              :key="cat"
              class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-left text-sm font-semibold transition"
              :class="activeCategory === cat
                ? 'bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]'
                : 'text-[#475569] hover:bg-[#F1F5F9] dark:text-[#94A3B8] dark:hover:bg-[#1E293B]'"
              @click="activeCategory = cat"
            >
              <span class="text-lg shrink-0">{{ categoryEmojis[cat] }}</span>
              <span class="min-w-0 flex-1">{{ cat }}</span>
              <span class="shrink-0 text-xs font-bold text-[#94A3B8]">{{ categoryCounts[cat] || 0 }}</span>
            </button>
          </div>
        </aside>

        <!-- 右侧内容区 -->
        <section class="min-w-0 flex-1">
          <!-- 标题区 -->
          <div class="mb-4">
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">公告中心</h1>
              <span class="ui-badge ui-badge-blue">{{ filteredAnnouncements.length }} 条</span>
            </div>
            <p class="ui-section-sub mt-1">平台通知与最新动态</p>
            <div v-if="canManageAnnouncements" class="mt-3">
              <button class="ui-btn ui-btn-secondary ui-btn-sm" @click="openManager">
                ⚙️ 管理公告
              </button>
            </div>
          </div>

          <!-- 加载骨架 -->
          <div v-if="isLoadingList" class="space-y-3">
            <div v-for="i in 5" :key="i" class="ui-skeleton h-24 w-full rounded-xl"></div>
          </div>

          <!-- 错误 -->
          <div v-else-if="listError" class="ui-empty">
            <span class="mb-2 text-5xl">❌</span>
            <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">加载失败</p>
            <p class="text-sm text-[#64748B] dark:text-[#94A3B8]">{{ listError }}</p>
            <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="loadAnnouncements">重试</button>
          </div>

          <!-- 空态 -->
          <div v-else-if="filteredAnnouncements.length === 0" class="ui-empty">
            <span class="mb-2 text-5xl">📭</span>
            <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">暂无公告</p>
          </div>

          <!-- 公告列表（条目 92-112px） -->
          <div v-else class="space-y-2">
            <button
              v-for="item in filteredAnnouncements"
              :key="item.id"
              type="button"
              class="announcement-item group flex w-full items-center gap-4 rounded-xl border border-[#E2E8F0] bg-white px-4 py-3 text-left transition hover:border-[#2563EB]/30 hover:shadow-sm dark:border-[#1E293B] dark:bg-[#111827] dark:hover:border-[#60A5FA]/30"
              @click="openAnnouncement(item)"
            >
              <!-- 左侧图标 48px -->
              <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl text-2xl" :class="getCategoryColor(item.title)">
                {{ getCategoryEmoji(item.title) }}
              </span>
              <!-- 中间标题+摘要 -->
              <div class="min-w-0 flex-1">
                <p class="truncate text-base font-bold text-[#1E293B] transition group-hover:text-[#2563EB] dark:text-[#E5E7EB] dark:group-hover:text-[#60A5FA]">{{ item.title }}</p>
                <p class="mt-0.5 line-clamp-1 text-xs text-[#64748B] dark:text-[#94A3B8]">{{ item.content }}</p>
              </div>
              <!-- 右侧日期 ~120px -->
              <span class="shrink-0 text-right text-xs text-[#94A3B8]" style="width:120px">
                {{ formatTime(item.updated_at || item.published_at || item.created_at) }}
              </span>
            </button>
          </div>
        </section>
      </div>
    </template>

    <!-- ===== 详情视图 ===== -->
    <template v-else>
      <div class="mx-auto max-w-[880px] px-6 py-8">
        <button class="ui-btn ui-btn-secondary ui-btn-md mb-6" @click="goBackToList">
          ← 返回公告列表
        </button>

        <div class="ui-card overflow-hidden !p-0">
          <div v-if="isLoadingDoc" class="flex min-h-[320px] items-center justify-center p-8 text-[#64748B] dark:text-[#94A3B8]">
            正在加载公告内容...
          </div>
          <div v-else-if="detailError" class="flex min-h-[320px] flex-col items-center justify-center gap-4 p-8 text-center">
            <span class="text-5xl">⚠️</span>
            <p class="text-rose-600 dark:text-rose-400">{{ detailError }}</p>
            <button v-if="currentAnnouncementId" class="ui-btn ui-btn-secondary ui-btn-sm" @click="loadSelectedAnnouncement">
              🔄 重试
            </button>
          </div>
          <div v-else class="px-10 py-10 sm:px-16">
            <div class="mb-6 border-b border-[#E2E8F0] pb-4 dark:border-[#1E293B]">
              <h2 class="text-[30px] font-black leading-tight text-[#1E293B] dark:text-[#E5E7EB]">{{ selectedContent?.title }}</h2>
              <p class="mt-2 text-sm font-medium text-[#64748B] dark:text-[#94A3B8]">
                {{ formatTime(selectedContent?.date) }}
              </p>
            </div>
            <MarkdownComponent :content="selectedContent" :show-nav="false" :show-heading-links="false" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';
</style>
