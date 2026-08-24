<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useAuthStore } from '../stores/auth';
import {
  listMySubmissions,
  listFavorites,
  updateUserProfile,
  uploadAvatar,
  type UserProfileUpdate,
} from '../services/api';

const router = useRouter();
const authStore = useAuthStore();

const isEditing = ref(false);
const isSaving = ref(false);
const saveMessage = ref('');
const saveError = ref('');

// 编辑表单
const editForm = ref<UserProfileUpdate>({
  name: '',
  email: '',
  bio: '',
});

// 数据统计
const statsLoading = ref(true);
const solvedCount = ref(0);
const submissionTotal = ref(0);
const favoriteCount = ref(0);

const startEdit = () => {
  editForm.value = {
    name: authStore.userInfo?.name || '',
    email: authStore.userInfo?.email || '',
    bio: (authStore.userInfo as any)?.bio || '',
  };
  isEditing.value = true;
  saveMessage.value = '';
  saveError.value = '';
};

const cancelEdit = () => {
  isEditing.value = false;
  saveMessage.value = '';
  saveError.value = '';
};

const saveProfile = async () => {
  isSaving.value = true;
  saveError.value = '';
  saveMessage.value = '';
  try {
    const result = await updateUserProfile(editForm.value);
    if (result.user_info) {
      authStore.updateUserInfo(result.user_info);
    }
    saveMessage.value = '资料已更新';
    isEditing.value = false;
  } catch (error) {
    saveError.value = error instanceof Error ? error.message : '更新失败，请稍后重试';
  } finally {
    isSaving.value = false;
  }
};

const handleAvatarUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  // 验证文件类型和大小
  if (!file.type.startsWith('image/')) {
    saveError.value = '请选择图片文件';
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    saveError.value = '图片大小不能超过 2MB';
    return;
  }

  isSaving.value = true;
  saveError.value = '';
  try {
    const result = await uploadAvatar(file);
    if (result.avatar_url && authStore.userInfo) {
      authStore.updateUserInfo({ ...authStore.userInfo, avatar_url: result.avatar_url });
    }
    saveMessage.value = '头像已更新';
  } catch (error) {
    saveError.value = error instanceof Error ? error.message : '上传失败，请稍后重试';
  } finally {
    isSaving.value = false;
    input.value = '';
  }
};

const loadStats = async () => {
  statsLoading.value = true;
  try {
    const [subRes, favRes] = await Promise.all([
      listMySubmissions(1, 1).catch(() => null),
      listFavorites().catch(() => null),
    ]);
    if (subRes) submissionTotal.value = subRes.total || 0;
    if (favRes) favoriteCount.value = Array.isArray(favRes.data) ? favRes.data.length : 0;
    // solvedCount 需要后端提供，暂用 submissions 推断
    if (subRes) {
      const allSubs = await listMySubmissions(1, 1000).catch(() => null);
      if (allSubs) {
        const solved = new Set<number>();
        allSubs.data.forEach((s: any) => {
          if (s.status === 'AC' && s.problem_id != null) solved.add(s.problem_id);
        });
        solvedCount.value = solved.size;
      }
    }
  } catch {
    // 统计加载失败不影响页面
  } finally {
    statsLoading.value = false;
  }
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};

const goSubmissions = () => router.push('/submissions');
const goFavorites = () => router.push('/favorites');

onMounted(loadStats);
</script>

<template>
  <div class="min-h-[calc(100vh-var(--header-h,4rem))] bg-[#F6F8FC] dark:bg-[#0F172A]">
    <div class="app-container py-6">
      <!-- 用户信息卡 200-240px -->
      <div class="ui-card mb-6 flex flex-col gap-6 p-6 sm:flex-row sm:items-center" style="min-height:200px">
        <!-- 头像区 -->
        <div class="relative shrink-0">
          <div class="grid h-24 w-24 place-items-center rounded-full bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            <img
              v-if="authStore.userInfo?.avatar_url"
              :src="authStore.userInfo.avatar_url"
              :alt="authStore.displayName"
              class="h-full w-full rounded-full object-cover"
            />
            <Icon v-else icon="material-symbols:person-rounded" class="h-12 w-12" />
          </div>
          <label
            class="absolute bottom-0 right-0 grid h-8 w-8 cursor-pointer place-items-center rounded-full bg-[#2563EB] text-white shadow-lg transition hover:bg-[#1D4ED8]"
            title="更换头像"
          >
            <Icon icon="material-symbols:camera-alt-rounded" class="h-4 w-4" />
            <input type="file" accept="image/*" class="hidden" @change="handleAvatarUpload" />
          </label>
        </div>

        <!-- 资料区 -->
        <div class="min-w-0 flex-1">
          <template v-if="!isEditing">
            <h1 class="text-2xl font-black text-[#1E293B] dark:text-[#E5E7EB]">
              {{ authStore.userInfo?.name || authStore.displayName }}
            </h1>
            <p class="mt-1 text-sm text-[#64748B] dark:text-[#94A3B8]">@{{ authStore.userInfo?.username }}</p>
            <p v-if="authStore.userInfo?.email" class="mt-1 text-sm text-[#64748B] dark:text-[#94A3B8]">
              {{ authStore.userInfo.email }}
            </p>
          </template>
          <template v-else>
            <div class="space-y-3">
              <div>
                <label class="mb-1 block text-xs font-bold text-[#64748B] dark:text-[#94A3B8]">昵称</label>
                <input v-model="editForm.name" type="text" class="ui-input" placeholder="你的昵称" />
              </div>
              <div>
                <label class="mb-1 block text-xs font-bold text-[#64748B] dark:text-[#94A3B8]">邮箱</label>
                <input v-model="editForm.email" type="email" class="ui-input" placeholder="你的邮箱" />
              </div>
              <div>
                <label class="mb-1 block text-xs font-bold text-[#64748B] dark:text-[#94A3B8]">个人简介</label>
                <textarea v-model="editForm.bio" class="ui-input min-h-[80px] resize-y" placeholder="介绍一下自己"></textarea>
              </div>
            </div>
          </template>
        </div>

        <!-- 操作区 -->
        <div class="shrink-0 self-start">
          <template v-if="!isEditing">
            <button class="ui-btn ui-btn-secondary" @click="startEdit">
              <Icon icon="material-symbols:edit-rounded" class="h-4 w-4" />
              编辑资料
            </button>
          </template>
          <template v-else>
            <div class="flex gap-2">
              <button class="ui-btn ui-btn-primary" :disabled="isSaving" @click="saveProfile">
                <Icon v-if="isSaving" icon="material-symbols:progress-activity" class="h-4 w-4 animate-spin" />
                <Icon v-else icon="material-symbols:check-rounded" class="h-4 w-4" />
                保存
              </button>
              <button class="ui-btn ui-btn-ghost" @click="cancelEdit">取消</button>
            </div>
          </template>
        </div>
      </div>

      <!-- 提示消息 -->
      <div v-if="saveMessage" class="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300">
        {{ saveMessage }}
      </div>
      <div v-if="saveError" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300">
        {{ saveError }}
      </div>

      <!-- 数据概览 4 卡 -->
      <div class="ui-grid ui-grid-4 mb-6">
        <div class="ui-card flex items-center gap-3 p-5">
          <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            <Icon icon="material-symbols:check-circle-rounded" class="h-5 w-5" />
          </span>
          <div>
            <p class="text-xs font-bold text-[#64748B] dark:text-[#94A3B8]">已解决</p>
            <p class="text-2xl font-black leading-tight">{{ statsLoading ? '—' : solvedCount }}</p>
          </div>
        </div>
        <div class="ui-card flex items-center gap-3 p-5">
          <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            <Icon icon="material-symbols:history-rounded" class="h-5 w-5" />
          </span>
          <div>
            <p class="text-xs font-bold text-[#64748B] dark:text-[#94A3B8]">提交次数</p>
            <p class="text-2xl font-black leading-tight">{{ statsLoading ? '—' : submissionTotal }}</p>
          </div>
        </div>
        <div class="ui-card flex items-center gap-3 p-5">
          <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            <Icon icon="material-symbols:star-rounded" class="h-5 w-5" />
          </span>
          <div>
            <p class="text-xs font-bold text-[#64748B] dark:text-[#94A3B8]">收藏题目</p>
            <p class="text-2xl font-black leading-tight">{{ statsLoading ? '—' : favoriteCount }}</p>
          </div>
        </div>
        <div class="ui-card flex items-center gap-3 p-5">
          <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            <Icon icon="material-symbols:calendar-today-rounded" class="h-5 w-5" />
          </span>
          <div>
            <p class="text-xs font-bold text-[#64748B] dark:text-[#94A3B8]">注册时间</p>
            <p class="text-sm font-bold leading-tight">{{ formatDate(authStore.userInfo?.created_at) }}</p>
          </div>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <button class="ui-card ui-card-hover flex items-center gap-4 p-5 text-left" @click="goSubmissions">
          <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            <Icon icon="material-symbols:history-rounded" class="h-6 w-6" />
          </span>
          <div>
            <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">提交记录</p>
            <p class="text-xs text-[#64748B] dark:text-[#94A3B8]">查看所有判题记录</p>
          </div>
        </button>
        <button class="ui-card ui-card-hover flex items-center gap-4 p-5 text-left" @click="goFavorites">
          <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            <Icon icon="material-symbols:star-rounded" class="h-6 w-6" />
          </span>
          <div>
            <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">收藏题目</p>
            <p class="text-xs text-[#64748B] dark:text-[#94A3B8]">管理你的题单</p>
          </div>
        </button>
        <button class="ui-card ui-card-hover flex items-center gap-4 p-5 text-left" @click="router.push('/problems')">
          <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-[#EFF6FF] text-[#2563EB] dark:bg-[#172554] dark:text-[#60A5FA]">
            <Icon icon="material-symbols:library-books-rounded" class="h-6 w-6" />
          </span>
          <div>
            <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">去刷题</p>
            <p class="text-xs text-[#64748B] dark:text-[#94A3B8]">继续练习提升实力</p>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
