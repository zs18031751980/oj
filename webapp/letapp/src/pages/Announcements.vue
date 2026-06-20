<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="mb-8">
      <h1 class="text-3xl font-black tracking-tight">公告</h1>
      <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">最新动态与更新通知</p>
    </div>

    <div class="announcements-scroll">
      <a
        v-for="item in sortedAnnouncements"
        :key="item.url"
        :href="item.url"
        target="_blank"
        rel="noopener noreferrer"
        class="announcement-card group"
      >
        <div class="card-content">
          <div class="card-title">{{ item.title }}</div>
          <div class="card-time">{{ formatTime(item.updatedAt) }}</div>
        </div>
        <div class="card-arrow">
          <Icon icon="material-symbols:open-in-new" class="h-4 w-4" />
        </div>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Icon } from '@iconify/vue';

interface Announcement {
  title: string;
  url: string;
  updatedAt: string;
}

const announcements = ref<Announcement[]>([]);

const sortedAnnouncements = computed(() => {
  return [...announcements.value].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );
});

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

onMounted(async () => {
  try {
    const res = await fetch('/announcements/data.json');
    announcements.value = await res.json();
  } catch (e) {
    console.error('Failed to load announcements:', e);
  }
});
</script>

<style scoped>
@reference 'tailwindcss';

.announcements-scroll {
  @apply grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3;
  max-height: calc(3 * (120px + 1rem));
  overflow-y: auto;
  padding-right: 4px;
}

.announcements-scroll::-webkit-scrollbar {
  width: 6px;
}

.announcements-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.announcements-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.dark .announcements-scroll::-webkit-scrollbar-thumb {
  background: #334155;
}

.announcement-card {
  @apply relative flex items-start justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/60 transition hover:-translate-y-0.5 hover:border-cyan-300 hover:shadow-md hover:shadow-cyan-100 dark:border-slate-800 dark:bg-slate-950 dark:shadow-black/20 dark:hover:border-cyan-500/50 dark:hover:shadow-cyan-950/20;
  min-height: 120px;
}

.card-content {
  @apply flex min-w-0 flex-1 flex-col gap-2;
}

.card-title {
  @apply text-base font-bold leading-snug text-slate-950 transition group-hover:text-cyan-600 dark:text-white dark:group-hover:text-cyan-400;
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
