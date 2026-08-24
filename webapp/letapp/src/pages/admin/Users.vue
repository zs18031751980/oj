<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useDialog, useMessage } from 'naive-ui';
import {
  deleteAdminUser,
  listAdminUsers,
  updateAdminUserStatus,
  type AdminUserData,
} from '../../services/api';
import { useAuthStore } from '../../stores/auth';

const dialog = useDialog();
const message = useMessage();
const authStore = useAuthStore();

const roleDisplayNames: Record<string, string> = {
  manager: '管理员',
  staff: '干事',
  member: '成员',
};

interface StatusInfo {
  name: string;
  color: string;
}

const statusInfoMap: Record<'active' | 'inactive', StatusInfo> = {
  active: { name: '活跃', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' },
  inactive: { name: '未激活', color: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300' },
};

const users = ref<AdminUserData[]>([]);
const loading = ref(true);
const loadError = ref('');
const mutatingId = ref<number | null>(null);

const searchKeyword = ref('');
const filterRole = ref('all');
const filterStatus = ref('all');
const currentPage = ref(1);
const pageSize = 10;
const totalUsers = ref(0);

const totalPages = computed(() => Math.max(Math.ceil(totalUsers.value / pageSize), 1));

// 仅管理员可执行写操作（与后端权限保持一致）
const canMutate = computed(() => authStore.userRole === 'manager');

const loadUsers = async () => {
  loading.value = true;
  loadError.value = '';
  try {
    const result = await listAdminUsers({
      page: currentPage.value,
      per_page: pageSize,
      search: searchKeyword.value,
      role: filterRole.value,
      status: filterStatus.value,
    });
    users.value = result.data;
    totalUsers.value = result.total;
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '加载用户列表失败';
    users.value = [];
    totalUsers.value = 0;
  } finally {
    loading.value = false;
  }
};

const resetPage = () => {
  currentPage.value = 1;
};

const handleResetFilter = () => {
  searchKeyword.value = '';
  filterRole.value = 'all';
  filterStatus.value = 'all';
  resetPage();
};

const handlePageChange = (page: number) => {
  currentPage.value = Math.min(Math.max(page, 1), totalPages.value);
};

const handleStatusChange = async (user: AdminUserData, isActive: boolean) => {
  mutatingId.value = user.id;
  try {
    await updateAdminUserStatus(user.id, isActive);
    user.is_active = isActive;
    message.success(`已${isActive ? '启用' : '停用'}用户 ${user.username || user.id}`);
  } catch (error) {
    message.error(error instanceof Error ? error.message : '状态更新失败');
  } finally {
    mutatingId.value = null;
  }
};

const handleDeleteUser = (user: AdminUserData) => {
  dialog.warning({
    title: '确认删除用户',
    content: `将删除用户「${user.username || user.id}」及其关联的代码记录，提交记录会解除关联。此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      mutatingId.value = user.id;
      try {
        await deleteAdminUser(user.id);
        message.success(`已删除用户 ${user.username || user.id}`);
        // 当前页删空后回退一页
        if (users.value.length === 1 && currentPage.value > 1) {
          currentPage.value -= 1;
        } else {
          await loadUsers();
        }
      } catch (error) {
        message.error(error instanceof Error ? error.message : '删除失败');
      } finally {
        mutatingId.value = null;
      }
    },
  });
};

const getRoleDisplayName = (role: string): string =>
  roleDisplayNames[role as keyof typeof roleDisplayNames] ?? (role || '未知');

const getStatusKey = (user: AdminUserData): keyof typeof statusInfoMap =>
  user.is_active ? 'active' : 'inactive';

const formatDate = (dateString: string | null) => {
  if (!dateString) return '—';
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

watch([searchKeyword, filterRole, filterStatus], resetPage);
watch([currentPage, searchKeyword, filterRole, filterStatus], loadUsers);

onMounted(loadUsers);
</script>

<template>
  <div class="space-y-6">
    <div v-once class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-black tracking-tight">用户管理</h1>
        <p class="mt-2 text-slate-600 dark:text-slate-300">管理平台用户，包括筛选、状态调整和删除。</p>
      </div>
    </div>

    <section class="admin-card">
      <div class="grid gap-4 md:grid-cols-4">
        <label class="md:col-span-2">
          <span class="mb-2 block text-sm font-bold text-slate-600 dark:text-slate-300">搜索用户</span>
          <div class="relative">
            <input v-model="searchKeyword" type="text" placeholder="输入用户名或邮箱搜索..." class="form-control pl-11" />
            <Icon icon="material-symbols:search" class="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          </div>
        </label>

        <label>
          <span class="mb-2 block text-sm font-bold text-slate-600 dark:text-slate-300">角色</span>
          <select v-model="filterRole" class="form-control">
            <option value="all">全部角色</option>
            <option value="manager">管理员</option>
            <option value="staff">干事</option>
            <option value="member">成员</option>
          </select>
        </label>

        <label>
          <span class="mb-2 block text-sm font-bold text-slate-600 dark:text-slate-300">状态</span>
          <select v-model="filterStatus" class="form-control">
            <option value="all">全部状态</option>
            <option value="active">活跃</option>
            <option value="inactive">未激活</option>
          </select>
        </label>
      </div>

      <div class="mt-5 flex items-center justify-between border-t border-slate-200 pt-5 dark:border-slate-800">
        <div class="text-sm text-slate-600 dark:text-slate-300">
          共 <span class="font-black">{{ totalUsers }}</span> 个用户
        </div>
        <button class="inline-flex items-center gap-2 rounded-full bg-slate-100 px-4 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700" @click="handleResetFilter">
          <Icon icon="material-symbols:refresh" class="h-4 w-4" />
          重置筛选
        </button>
      </div>
    </section>

    <div v-if="loadError" class="admin-card flex flex-col items-center gap-3 py-10 text-center">
      <Icon icon="material-symbols:cloud-off-rounded" class="h-12 w-12 text-rose-400" />
      <p class="font-bold text-slate-700 dark:text-slate-200">用户列表加载失败</p>
      <p class="text-sm text-slate-500 dark:text-slate-400">{{ loadError }}</p>
      <button
        class="mt-1 rounded-full bg-cyan-400 px-5 py-2.5 text-sm font-black text-slate-950 transition hover:bg-cyan-300"
        @click="loadUsers"
      >
        重新加载
      </button>
    </div>

    <div v-else-if="loading" class="admin-card animate-pulse space-y-3">
      <div v-for="i in 5" :key="i" class="h-12 rounded-2xl bg-slate-100 dark:bg-slate-800"></div>
    </div>

    <section v-else class="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white/85 shadow-lg shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
          <thead v-once class="bg-slate-50 dark:bg-slate-950">
            <tr>
              <th class="table-head">ID</th>
              <th class="table-head">用户名</th>
              <th class="table-head">邮箱</th>
              <th class="table-head">登录方式</th>
              <th class="table-head">角色</th>
              <th class="table-head">状态</th>
              <th class="table-head">创建时间</th>
              <th class="table-head">最后登录</th>
              <th v-if="canMutate" class="table-head text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-800">
            <tr v-for="user in users" :key="user.id" class="transition hover:bg-slate-50 dark:hover:bg-slate-800/70">
              <td class="table-cell font-black">{{ user.id }}</td>
              <td class="table-cell">
                <div class="flex items-center gap-3">
                  <div class="grid h-9 w-9 place-items-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300">
                    <Icon icon="material-symbols:person" class="h-5 w-5" />
                  </div>
                  <span class="font-black">{{ user.username || `用户#${user.id}` }}</span>
                </div>
              </td>
              <td class="table-cell text-slate-600 dark:text-slate-300">{{ user.email || '—' }}</td>
              <td class="table-cell text-slate-600 dark:text-slate-300">{{ user.provider || 'password' }}</td>
              <td class="table-cell">
                <span class="rounded-full bg-cyan-100 px-2.5 py-1 text-xs font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300">
                  {{ getRoleDisplayName(user.role) }}
                </span>
              </td>
              <td class="table-cell">
                <span :class="['rounded-full px-2.5 py-1 text-xs font-black', statusInfoMap[getStatusKey(user)].color]">
                  {{ statusInfoMap[getStatusKey(user)].name }}
                </span>
              </td>
              <td class="table-cell text-slate-600 dark:text-slate-300">{{ formatDate(user.created_at) }}</td>
              <td class="table-cell text-slate-600 dark:text-slate-300">{{ formatDate(user.last_login) }}</td>
              <td v-if="canMutate" class="table-cell">
                <div class="flex items-center justify-end gap-2" :class="{ 'opacity-50': mutatingId === user.id }">
                  <select
                    class="rounded-xl border border-slate-200 bg-white px-2 py-1 text-xs dark:border-slate-800 dark:bg-slate-950"
                    :value="user.is_active ? 'active' : 'inactive'"
                    :disabled="mutatingId === user.id"
                    @change="handleStatusChange(user, ($event.target as HTMLSelectElement).value === 'active')"
                  >
                    <option value="active">活跃</option>
                    <option value="inactive">停用</option>
                  </select>
                  <button class="action-button text-rose-600 dark:text-rose-300" title="删除" :disabled="mutatingId === user.id" @click="handleDeleteUser(user)">
                    <Icon icon="material-symbols:delete" class="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="users.length === 0" class="px-6 py-12 text-center">
        <Icon icon="material-symbols:search-off" class="mx-auto mb-4 h-16 w-16 text-slate-400" />
        <h3 class="text-lg font-black">未找到用户</h3>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">请尝试调整筛选条件或搜索关键词。</p>
      </div>
    </section>

    <div v-if="totalPages > 1" class="admin-card flex items-center justify-between">
      <div class="text-sm text-slate-600 dark:text-slate-300">
        第 <span class="font-black">{{ currentPage }}</span> 页，共 <span class="font-black">{{ totalPages }}</span> 页
      </div>
      <div class="flex items-center gap-2">
        <button class="page-button" :disabled="currentPage === 1" @click="handlePageChange(currentPage - 1)">上一页</button>
        <button v-for="page in totalPages" :key="page" class="page-button" :class="{ 'page-button-active': currentPage === page }" @click="handlePageChange(page)">
          {{ page }}
        </button>
        <button class="page-button" :disabled="currentPage === totalPages" @click="handlePageChange(currentPage + 1)">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.admin-card {
  @apply rounded-[1.75rem] border border-slate-200 bg-white/85 p-6 shadow-lg shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20;
}

.form-control {
  @apply w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-950 outline-none transition focus:border-cyan-300 focus:ring-4 focus:ring-cyan-100 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-cyan-950;
}

.table-head {
  @apply px-6 py-3 text-left text-xs font-black uppercase tracking-wider text-slate-500 dark:text-slate-400;
}

.table-cell {
  @apply whitespace-nowrap px-6 py-4 text-sm;
}

.action-button {
  @apply rounded-xl p-2 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40 dark:hover:bg-slate-800;
}

.page-button {
  @apply rounded-xl bg-slate-100 px-3 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700;
}

.page-button-active {
  @apply bg-cyan-400 text-slate-950 hover:bg-cyan-300 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300;
}
</style>
