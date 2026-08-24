<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';
import {
  listDiscussions, getDiscussion, createDiscussion,
  likeDiscussion, replyToDiscussion, likeDiscussionReply,
  type DiscussionData, type DiscussionReplyData,
} from '../services/api';
import MarkdownComponent from '../components/MarkdownComponent.vue';

const authStore = useAuthStore();
const router = useRouter();

const discussions = ref<DiscussionData[]>([]);
const isLoading = ref(false);
const error = ref('');
const activeCategory = ref('全部');

// 详情弹窗
const showDetail = ref(false);
const currentDiscussion = ref<DiscussionData | null>(null);
const detailLoading = ref(false);
const newReply = ref('');
const submittingReply = ref(false);

// 发布弹窗
const showCreate = ref(false);
const createForm = ref({ title: '', content: '', category: '问答', tags: '' });
const submitting = ref(false);

const categories = ['全部', '问答', '分享', '闲聊', '综合'];
const categoryEmojis: Record<string, string> = {
  '全部': '💬',
  '问答': '❓',
  '分享': '🔗',
  '闲聊': '💭',
  '综合': '📋',
};

const tagColors: Record<string, string> = {
  '动态规划': 'bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400',
  '算法': 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400',
  'C++': 'bg-violet-50 text-violet-600 dark:bg-violet-950/40 dark:text-violet-400',
  '学习': 'bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400',
  '周赛': 'bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400',
  '讨论': 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
  '图论': 'bg-cyan-50 text-cyan-600 dark:bg-cyan-950/40 dark:text-cyan-400',
  '模板': 'bg-pink-50 text-pink-600 dark:bg-pink-950/40 dark:text-pink-400',
};

const getTags = (tags: string | null) => {
  if (!tags) return [];
  return tags.split(',').map(t => t.trim()).filter(Boolean);
};

const filteredDiscussions = computed(() => {
  if (activeCategory.value === '全部') return discussions.value;
  return discussions.value.filter(d => d.category === activeCategory.value);
});

const formatTime = (dateStr?: string) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '';
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes} 分钟前`;
  if (hours < 24) return `${hours} 小时前`;
  if (days < 7) return `${days} 天前`;
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};

const formatFullTime = (dateStr?: string) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  });
};

// ===== 数据加载 =====
const loadData = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    discussions.value = await listDiscussions();
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败';
  } finally {
    isLoading.value = false;
  }
};

// ===== 查看详情 =====
const openDetail = async (d: DiscussionData) => {
  showDetail.value = true;
  detailLoading.value = true;
  try {
    currentDiscussion.value = await getDiscussion(d.id);
  } catch {
    currentDiscussion.value = d;
  } finally {
    detailLoading.value = false;
  }
};

const closeDetail = () => {
  showDetail.value = false;
  currentDiscussion.value = null;
  newReply.value = '';
};

// ===== 点赞 =====
const toggleLike = async (d: DiscussionData) => {
  if (!authStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  try {
    const res = await likeDiscussion(d.id);
    d.like_count = res.like_count;
    d.is_liked = res.liked;
  } catch {}
};

const toggleReplyLike = async (r: DiscussionReplyData) => {
  if (!authStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  try {
    const res = await likeDiscussionReply(r.id);
    r.like_count = res.like_count;
    r.is_liked = res.liked;
  } catch {};
};

// ===== 回复 =====
const submitReply = async () => {
  if (!authStore.isAuthenticated) { router.push('/login'); return; }
  if (!currentDiscussion.value || !newReply.value.trim()) return;
  submittingReply.value = true;
  try {
    const reply = await replyToDiscussion(currentDiscussion.value.id, newReply.value.trim());
    if (!currentDiscussion.value.replies) currentDiscussion.value.replies = [];
    currentDiscussion.value.replies.push(reply);
    currentDiscussion.value.reply_count = (currentDiscussion.value.reply_count || 0) + 1;
    newReply.value = '';
  } catch (e) {
    alert(e instanceof Error ? e.message : '回复失败');
  } finally {
    submittingReply.value = false;
  }
};

// ===== 发布 =====
const openCreate = () => {
  if (!authStore.isAuthenticated) { router.push('/login'); return; }
  createForm.value = { title: '', content: '', category: '问答', tags: '' };
  showCreate.value = true;
};

const submitCreate = async () => {
  if (!createForm.value.title.trim() || !createForm.value.content.trim()) return;
  submitting.value = true;
  try {
    const d = await createDiscussion(createForm.value);
    discussions.value.unshift(d);
    showCreate.value = false;
  } catch (e) {
    alert(e instanceof Error ? e.message : '发布失败');
  } finally {
    submitting.value = false;
  }
};

onMounted(loadData);
</script>

<template>
  <div class="min-h-[calc(100vh-var(--header-h,4rem))] bg-[#F6F8FC] dark:bg-[#0F172A]">
    <div class="app-container-with-sidebar py-6">
      <!-- 左侧分类 -->
      <aside class="app-sidebar-col">
        <div class="ui-card space-y-1 p-3">
          <button
            v-for="cat in categories"
            :key="cat"
            class="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm font-semibold transition"
            :class="activeCategory === cat
              ? 'bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]'
              : 'text-[#475569] hover:bg-[#F1F5F9] dark:text-[#94A3B8] dark:hover:bg-[#1E293B]'"
            @click="activeCategory = cat"
          >
            <span class="text-xl shrink-0 w-7 text-center">{{ categoryEmojis[cat] }}</span>
            <span class="flex-1">{{ cat }}</span>
          </button>
        </div>
      </aside>

      <!-- 右侧内容 -->
      <section class="min-w-0 flex-1">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">讨论区</h1>
            <p class="ui-section-sub mt-1">交流算法心得，分享学习经验</p>
          </div>
          <button class="ui-btn-primary rounded-xl px-6 py-3 text-base font-bold shadow-md transition hover:shadow-lg" @click="openCreate">
            ➕ 发布讨论
          </button>
        </div>

        <!-- 加载中 -->
        <div v-if="isLoading" class="space-y-3">
          <div v-for="i in 4" :key="i" class="ui-skeleton h-24 w-full rounded-xl"></div>
        </div>

        <!-- 错误 -->
        <div v-else-if="error" class="ui-empty">
          <span class="mb-2 text-5xl">❌</span>
          <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">加载失败</p>
          <button class="ui-btn ui-btn-secondary ui-btn-sm mt-2" @click="loadData">重试</button>
        </div>

        <!-- 讨论列表 -->
        <div v-else class="space-y-2">
          <div
            v-for="d in filteredDiscussions"
            :key="d.id"
            class="ui-card flex items-start gap-4 p-4 transition hover:border-[#2563EB]/30 dark:hover:border-[#60A5FA]/30 cursor-pointer"
            @click="openDetail(d)"
          >
            <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA] text-lg">
              👤
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span v-if="d.is_pinned" class="ui-badge ui-badge-amber text-[10px]">📌 置顶</span>
                <h3 class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ d.title }}</h3>
              </div>
              <div v-if="getTags(d.tags).length" class="mt-1.5 flex flex-wrap gap-1.5">
                <span v-for="tag in getTags(d.tags)" :key="tag" class="rounded-md px-2 py-0.5 text-[11px] font-medium" :class="tagColors[tag] || 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'">{{ tag }}</span>
              </div>
              <p class="mt-2 text-xs text-[#94A3B8]">{{ d.author_name }} · {{ formatTime(d.created_at) }}</p>
            </div>
            <div class="shrink-0 flex flex-col items-end gap-1 text-[#64748B] dark:text-[#94A3B8]">
              <button
                class="flex items-center gap-1 text-xs font-bold transition hover:text-[#2563EB] dark:hover:text-[#60A5FA]"
                :class="d.is_liked ? 'text-[#2563EB] dark:text-[#60A5FA]' : ''"
                @click.stop="toggleLike(d)"
              >
                <span>{{ d.is_liked ? '❤️' : '🤍' }}</span>
                {{ d.like_count || 0 }}
              </button>
              <span class="text-xs font-bold">💬 {{ d.reply_count || 0 }}</span>
              <span class="text-[10px] text-[#94A3B8]">👁 {{ d.view_count || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- 空态 -->
        <div v-if="!isLoading && !error && filteredDiscussions.length === 0" class="ui-empty mt-6">
          <span class="mb-2 text-5xl">💭</span>
          <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">暂无讨论</p>
          <p class="text-sm text-[#64748B] dark:text-[#94A3B8]">发布第一个讨论吧</p>
        </div>
      </section>
    </div>

    <!-- ===== 讨论详情弹窗 ===== -->
    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="showDetail" class="disc-modal-overlay" @click.self="closeDetail">
          <div class="disc-modal">
            <div class="disc-modal-header">
              <h3 class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">讨论详情</h3>
              <button class="disc-modal-close" @click="closeDetail">✕</button>
            </div>
            <div class="disc-modal-body">
              <template v-if="currentDiscussion">
                <!-- 标题 -->
                <div class="mb-4">
                  <div class="flex items-center gap-2 mb-2">
                    <span v-if="currentDiscussion.is_pinned" class="ui-badge ui-badge-amber text-[10px]">📌 置顶</span>
                    <span class="ui-badge ui-badge-blue text-[10px]">{{ currentDiscussion.category }}</span>
                  </div>
                  <h2 class="text-xl font-black text-[#1E293B] dark:text-[#E5E7EB]">{{ currentDiscussion.title }}</h2>
                  <p class="mt-1 text-xs text-[#94A3B8]">{{ currentDiscussion.author_name }} · {{ formatFullTime(currentDiscussion.created_at) }}</p>
                </div>

                <!-- 标签 -->
                <div v-if="getTags(currentDiscussion.tags).length" class="mb-4 flex flex-wrap gap-1.5">
                  <span v-for="tag in getTags(currentDiscussion.tags)" :key="tag" class="rounded-md px-2 py-0.5 text-[11px] font-medium" :class="tagColors[tag] || 'bg-slate-100 text-slate-600'">{{ tag }}</span>
                </div>

                <!-- 内容 -->
                <div class="disc-content prose-wrapper mb-4">
                  <MarkdownComponent :content="{ content: currentDiscussion.content }" :show-nav="false" :show-heading-links="false" />
                </div>

                <!-- 操作栏 -->
                <div class="flex items-center gap-4 border-t border-[#E2E8F0] dark:border-[#1E293B] pt-3 mb-4">
                  <button
                    class="flex items-center gap-1.5 text-sm font-bold transition"
                    :class="currentDiscussion.is_liked ? 'text-[#2563EB] dark:text-[#60A5FA]' : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#2563EB]'"
                    @click="toggleLike(currentDiscussion)"
                  >
                    <span>{{ currentDiscussion.is_liked ? '❤️' : '🤍' }}</span>
                    点赞 {{ currentDiscussion.like_count || 0 }}
                  </button>
                  <span class="text-sm text-[#94A3B8]">💬 回复 {{ currentDiscussion.reply_count || 0 }}</span>
                  <span class="text-sm text-[#94A3B8]">👁 浏览 {{ currentDiscussion.view_count || 0 }}</span>
                </div>

                <!-- 回复列表 -->
                <div class="border-t border-[#E2E8F0] dark:border-[#1E293B] pt-4">
                  <h4 class="text-sm font-bold text-[#1E293B] dark:text-[#E5E7EB] mb-3">回复 ({{ currentDiscussion.replies?.length || 0 }})</h4>
                  <div v-if="detailLoading" class="space-y-3">
                    <div v-for="i in 3" :key="i" class="ui-skeleton h-16 w-full rounded-lg"></div>
                  </div>
                  <div v-else-if="currentDiscussion.replies && currentDiscussion.replies.length" class="space-y-3">
                    <div v-for="r in currentDiscussion.replies" :key="r.id" class="rounded-lg border border-[#E2E8F0] dark:border-[#1E293B] p-3">
                      <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ r.author_name }}</span>
                        <span class="text-[11px] text-[#94A3B8]">{{ formatTime(r.created_at) }}</span>
                      </div>
                      <div class="text-sm text-[#374151] dark:text-[#D1D5DB]">
                        <MarkdownComponent :content="{ content: r.content }" :show-nav="false" :show-heading-links="false" />
                      </div>
                      <div class="mt-2 flex items-center gap-3">
                        <button
                          class="flex items-center gap-1 text-xs font-bold transition"
                          :class="r.is_liked ? 'text-[#2563EB] dark:text-[#60A5FA]' : 'text-[#94A3B8] hover:text-[#2563EB]'"
                          @click="toggleReplyLike(r)"
                        >
                          <span>{{ r.is_liked ? '❤️' : '🤍' }}</span>
                          {{ r.like_count || 0 }}
                        </button>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-sm text-[#94A3B8] text-center py-4">暂无回复</p>
                </div>

                <!-- 发表回复 -->
                <div v-if="authStore.isAuthenticated" class="border-t border-[#E2E8F0] dark:border-[#1E293B] pt-4 mt-4">
                  <textarea
                    v-model="newReply"
                    class="w-full rounded-lg border border-[#E2E8F0] dark:border-[#1E293B] bg-white dark:bg-[#0F172A] p-3 text-sm text-[#1E293B] dark:text-[#E5E7EB] outline-none transition focus:border-[#2563EB] dark:focus:border-[#60A5FA] resize-none"
                    rows="3"
                    placeholder="写下你的回复..."
                  ></textarea>
                  <div class="mt-2 flex justify-end">
                    <button
                      class="ui-btn ui-btn-primary ui-btn-sm"
                      :disabled="submittingReply || !newReply.trim()"
                      @click="submitReply"
                    >
                      {{ submittingReply ? '发送中...' : '发表回复' }}
                    </button>
                  </div>
                </div>
                <p v-else class="text-center text-sm text-[#94A3B8] py-4 border-t border-[#E2E8F0] dark:border-[#1E293B] mt-4">
                  <button class="font-bold text-[#2563EB] dark:text-[#60A5FA]" @click="router.push('/login')">登录</button> 后参与讨论
                </p>
              </template>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ===== 发布讨论弹窗 ===== -->
    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="showCreate" class="disc-modal-overlay" @click.self="showCreate = false">
          <div class="disc-modal">
            <div class="disc-modal-header">
              <h3 class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">发布讨论</h3>
              <button class="disc-modal-close" @click="showCreate = false">✕</button>
            </div>
            <div class="disc-modal-body">
              <div class="space-y-4">
                <div>
                  <label class="mb-1 block text-xs font-bold text-[#64748B]">标题</label>
                  <input v-model="createForm.title" class="ui-input" placeholder="请输入标题" />
                </div>
                <div>
                  <label class="mb-1 block text-xs font-bold text-[#64748B]">分类</label>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="cat in ['问答', '分享', '闲聊', '综合']"
                      :key="cat"
                      class="rounded-full border px-3 py-1 text-xs font-bold transition-colors"
                      :class="createForm.category === cat
                        ? 'border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] dark:border-[#60A5FA] dark:bg-[#172554] dark:text-[#60A5FA]'
                        : 'border-[#E2E8F0] text-[#64748B] dark:border-[#334155] dark:text-[#94A3B8]'"
                      @click="createForm.category = cat"
                    >{{ cat }}</button>
                  </div>
                </div>
                <div>
                  <label class="mb-1 block text-xs font-bold text-[#64748B]">标签（逗号分隔）</label>
                  <input v-model="createForm.tags" class="ui-input" placeholder="如：动态规划, 算法" />
                </div>
                <div>
                  <label class="mb-1 block text-xs font-bold text-[#64748B]">内容（支持 Markdown）</label>
                  <textarea
                    v-model="createForm.content"
                    class="ui-input min-h-[160px] resize-y"
                    placeholder="请输入内容..."
                  ></textarea>
                </div>
                <div class="flex justify-end gap-2">
                  <button class="ui-btn ui-btn-ghost ui-btn-sm" @click="showCreate = false">取消</button>
                  <button
                    class="ui-btn ui-btn-primary ui-btn-sm"
                    :disabled="submitting || !createForm.title.trim() || !createForm.content.trim()"
                    @click="submitCreate"
                  >
                    {{ submitting ? '发布中...' : '发布' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.disc-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}
.disc-modal {
  width: 94%;
  max-width: 680px;
  max-height: 85vh;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
html.dark .disc-modal { background: #1F2937; }
.disc-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #E2E8F0;
  flex-shrink: 0;
}
html.dark .disc-modal-header { border-color: #374151; }
.disc-modal-close {
  width: 28px; height: 28px;
  display: grid; place-items: center;
  border: none; border-radius: 6px;
  background: transparent; color: #6B7280;
  cursor: pointer; font-size: 14px;
}
.disc-modal-close:hover { background: #F3F4F6; }
.disc-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.disc-content :deep(p) { margin: 0 0 12px; }
.disc-content :deep(pre) {
  background: #F8FAFC;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  overflow-x: auto;
}
html.dark .disc-content :deep(pre) { background: #111827; color: #E5E7EB; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
