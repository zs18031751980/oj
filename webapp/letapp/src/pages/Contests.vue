<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { listContests, joinContest, type ContestData } from '../services/api';
import { useMessage } from 'naive-ui';
import { useAuthStore } from '../stores/auth';
import { formatDateTime, isWithinTimeRange } from '../utils/time';
import { Icon } from '@iconify/vue';

const router = useRouter();
const message = useMessage();
const authStore = useAuthStore();
const isManager = computed(() => authStore.userRole === 'manager');
const activeTab = ref<'ongoing' | 'upcoming' | 'past'>('ongoing');
const entering = ref(false);
const goManage = () => {
  if (entering.value) return;
  entering.value = true;
  router.push('/admin/contests');
};
const contests = ref<ContestData[]>([]);
const isLoading = ref(false);
const error = ref('');

// 定时刷新“当前时间”，使按钮的可用/置灰状态随时间实时切换
const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | null = null;
onMounted(() => {
  timer = setInterval(() => { now.value = Date.now(); }, 30_000);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});

const isContestOpen = (c: ContestData) =>
  isWithinTimeRange(c.start_time, c.end_time, now.value);

const filteredContests = computed(() =>
  contests.value.filter(c => c.status === activeTab.value)
);

const statusLabel = (status: string) => {
  if (status === 'ongoing') return '进行中';
  if (status === 'upcoming') return '即将开始';
  return '已结束';
};

const statusBadgeClass = (status: string) => {
  if (status === 'ongoing') return 'ui-badge-green';
  if (status === 'upcoming') return 'ui-badge-blue';
  return 'ui-badge-slate';
};

const formatTimeRange = (start?: string | null, end?: string | null) => {
  if (!start && !end) return '时间待定';
  const s = start ? new Date(start) : null;
  const e = end ? new Date(end) : null;
  const fmt = (d: Date) => formatDateTime(d, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  if (s && e) return `${fmt(s)} ~ ${fmt(e)}`;
  if (s) return `${fmt(s)} 开始`;
  return `截止 ${fmt(e!)}`;
};

const enterContest = async (c: ContestData) => {
  if (!isWithinTimeRange(c.start_time, c.end_time)) {
    message.warning(c.status === 'upcoming' ? '比赛尚未开始，暂不能进入' : '比赛已结束，不能进入');
    return;
  }
  try {
    await joinContest(c.id);
  } catch (e: any) {
    const msg = e?.message || '';
    if (!msg.includes('already') && !msg.includes('已加入')) {
      message.warning('加入比赛失败：' + (msg || '请稍后重试'));
    }
  }
  router.push(`/contests/${c.id}`);
};

const loadData = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    contests.value = await listContests();
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败';
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadData);
</script>

<template>
  <div class="min-h-[calc(100vh-var(--header-h,4rem))] bg-[#F6F8FC] dark:bg-[#0F172A]">
    <div class="app-container py-6">
      <div class="contest-header mb-6 flex items-start justify-between gap-4">
        <div class="contest-header__main min-w-0">
          <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">比赛</h1>
          <p class="ui-section-sub mt-1">参与编程竞赛，挑战自我</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <button v-for="tab in (['ongoing','upcoming','past'] as const)" :key="tab"
              class="ui-btn ui-btn-sm"
              :class="activeTab === tab ? 'ui-btn-primary' : 'ui-btn-ghost'"
              @click="activeTab = tab"
            >
              {{ tab === 'ongoing' ? '进行中' : tab === 'upcoming' ? '即将开始' : '历史比赛' }}
            </button>
          </div>
        </div>

        <div class="contest-header__actions shrink-0 pt-1">
          <button
            v-if="isManager"
            class="contest-manage-btn"
            :disabled="entering"
            :aria-busy="entering"
            @click="goManage"
          >
            <svg class="contest-manage-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            <span>{{ entering ? '正在进入…' : '管理比赛' }}</span>
          </button>
        </div>
      </div>

      <div v-if="isLoading" class="space-y-4">
        <div v-for="i in 3" :key="i" class="ui-skeleton h-32 w-full rounded-xl"></div>
      </div>

      <div v-else-if="error" class="ui-empty">
        <Icon icon="material-symbols:error-outline-rounded" class="mb-2 h-12 w-12 text-rose-500" />
        <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">加载失败</p>
        <p class="text-sm text-[#64748B] dark:text-[#94A3B8]">{{ error }}</p>
        <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="loadData">重试</button>
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="c in filteredContests" :key="c.id" class="ui-card p-5">
          <div class="mb-3 flex items-center gap-2">
            <span class="ui-badge" :class="statusBadgeClass(c.status)">
              {{ statusLabel(c.status) }}
            </span>
            <span class="text-xs text-[#94A3B8]">{{ c.contest_type }}</span>
          </div>
          <h3 class="mb-2 font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ c.title }}</h3>
          <p class="mb-1 text-sm text-[#64748B] dark:text-[#94A3B8]">
            {{ formatTimeRange(c.start_time, c.end_time) }}
          </p>
          <p class="mb-3 text-xs text-[#94A3B8]">{{ c.participants_count }} 人参与</p>
          <button
            class="w-full ui-btn"
            :class="isContestOpen(c) ? 'ui-btn-primary' : 'ui-btn-disabled'"
            :disabled="!isContestOpen(c)"
            :title="isContestOpen(c) ? '' : (c.status === 'upcoming' ? '比赛尚未开始' : '比赛已结束')"
            @click="enterContest(c)"
          >
            <span v-if="isContestOpen(c)" class="inline-flex items-center gap-1.5"><Icon icon="material-symbols:play-arrow-rounded" class="h-4 w-4" />进入比赛</span>
            <span v-else>{{ c.status === 'upcoming' ? '未开始' : '已结束' }}</span>
          </button>
        </div>
      </div>

      <div v-if="!isLoading && !error && filteredContests.length === 0" class="ui-empty mt-6">
        <Icon icon="material-symbols:emoji-events" class="mb-2 h-12 w-12 text-amber-500" />
        <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">暂无比赛</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.contest-header__actions {
  /* 让按钮贴齐容器右侧内容边缘（容器自带内边距，约 24–32px） */
  align-self: flex-start;
}

.contest-manage-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px; /* 图标与文字间距 6–8px */
  min-width: 112px; /* 104–116px，按推荐取 112px */
  height: 40px;
  padding: 0 18px;
  border: none;
  border-radius: 8px; /* 不再使用胶囊圆角 */
  background: #2563eb; /* 品牌蓝实心主按钮 */
  color: #ffffff;
  font-size: 14px;
  font-weight: 600; /* 半粗，550–600 */
  white-space: nowrap;
  cursor: pointer;
  /* 极轻阴影，从浅色背景中自然突出，不似悬浮广告 */
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.18);
  transition: background-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.contest-manage-btn__icon {
  width: 16px;
  height: 16px;
  flex: none;
}

.contest-manage-btn:hover:not(:disabled) {
  background: #1d4ed8; /* Hover 轻微加深 */
  transform: translateY(-1px); /* 上移 1px，无缩放 */
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.22); /* 少量阴影反馈 */
}

.contest-manage-btn:active:not(:disabled) {
  transform: translateY(0); /* 取消上移，下压感 */
  background: #1e40af; /* 按下更深 */
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.15); /* 降低阴影 */
}

.contest-manage-btn:disabled {
  cursor: default;
  opacity: 0.85;
}

/* 暗色模式：与站点主操作按钮保持一致 */
:deep(.dark) .contest-manage-btn,
.dark .contest-manage-btn {
  background: #3b82f6;
  box-shadow: 0 1px 2px rgba(59, 130, 246, 0.25);
}

:deep(.dark) .contest-manage-btn:hover:not(:disabled),
.dark .contest-manage-btn:hover:not(:disabled) {
  background: #2563eb;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
}

:deep(.dark) .contest-manage-btn:active:not(:disabled),
.dark .contest-manage-btn:active:not(:disabled) {
  background: #1d4ed8;
}
</style>
