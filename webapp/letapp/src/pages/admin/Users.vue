<script setup lang="ts">
import { computed, ref } from 'vue';
import { Icon } from '@iconify/vue';

interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  last_login: string;
}

const users = ref<User[]>([
  { id: 1, username: 'admin', email: 'admin@example.com', role: 'admin', status: 'active', created_at: '2026-06-01T12:00:00Z', last_login: '2026-06-12T12:00:00Z' },
  { id: 2, username: 'user1', email: 'user1@example.com', role: 'user', status: 'active', created_at: '2026-06-03T12:00:00Z', last_login: '2026-06-11T12:00:00Z' },
  { id: 3, username: 'user2', email: 'user2@example.com', role: 'user', status: 'inactive', created_at: '2026-06-05T12:00:00Z', last_login: '2026-06-08T12:00:00Z' },
  { id: 4, username: 'guest1', email: 'guest1@example.com', role: 'guest', status: 'active', created_at: '2026-06-08T12:00:00Z', last_login: '2026-06-10T12:00:00Z' },
  { id: 5, username: 'user3', email: 'user3@example.com', role: 'user', status: 'suspended', created_at: '2026-06-09T12:00:00Z', last_login: '2026-06-09T12:00:00Z' },
]);

const searchKeyword = ref('');
const filterRole = ref('all');
const filterStatus = ref('all');
const currentPage = ref(1);
const pageSize = ref(10);

const filteredUsers = computed(() => {
  let result = [...users.value];

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter((user) => user.username.toLowerCase().includes(keyword) || user.email.toLowerCase().includes(keyword));
  }

  if (filterRole.value !== 'all') {
    result = result.filter((user) => user.role === filterRole.value);
  }

  if (filterStatus.value !== 'all') {
    result = result.filter((user) => user.status === filterStatus.value);
  }

  return result;
});

const totalPages = computed(() => Math.ceil(filteredUsers.value.length / pageSize.value));
const totalUsers = computed(() => filteredUsers.value.length);
const paginatedUsers = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value;
  return filteredUsers.value.slice(startIndex, startIndex + pageSize.value);
});

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
  currentPage.value = Math.min(Math.max(page, 1), totalPages.value || 1);
};

const handleStatusChange = (userId: number, status: User['status']) => {
  const user = users.value.find((item) => item.id === userId);
  if (user) {
    user.status = status;
  }
};

const handleDeleteUser = (userId: number) => {
  users.value = users.value.filter((user) => user.id !== userId);
};

const handleEditUser = (userId: number) => {
  window.alert(`编辑用户 ${userId} 的功能正在开发中。`);
};

const getRoleDisplayName = (role: User['role']) => {
  const roleMap = {
    admin: '管理员',
    user: '普通用户',
    guest: '访客',
  };
  return roleMap[role];
};

const getStatusInfo = (status: User['status']) => {
  const statusMap = {
    active: { name: '活跃', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' },
    inactive: { name: '未激活', color: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300' },
    suspended: { name: '已封禁', color: 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300' },
  };
  return statusMap[status];
};

const formatDate = (dateString: string) => new Date(dateString).toLocaleString('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-black tracking-tight">用户管理</h1>
        <p class="mt-2 text-slate-600 dark:text-slate-300">管理平台用户，包括筛选、状态调整和删除。</p>
      </div>
      <button class="inline-flex items-center gap-2 rounded-full bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950 transition hover:bg-cyan-300">
        <Icon icon="material-symbols:add" class="h-5 w-5" />
        新增用户
      </button>
    </div>

    <section class="admin-card">
      <div class="grid gap-4 md:grid-cols-4">
        <label class="md:col-span-2">
          <span class="mb-2 block text-sm font-bold text-slate-600 dark:text-slate-300">搜索用户</span>
          <div class="relative">
            <input v-model="searchKeyword" type="text" placeholder="输入用户名或邮箱搜索..." class="form-control pl-11" @input="resetPage" />
            <Icon icon="material-symbols:search" class="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          </div>
        </label>

        <label>
          <span class="mb-2 block text-sm font-bold text-slate-600 dark:text-slate-300">角色</span>
          <select v-model="filterRole" class="form-control" @change="resetPage">
            <option value="all">全部角色</option>
            <option value="admin">管理员</option>
            <option value="user">普通用户</option>
            <option value="guest">访客</option>
          </select>
        </label>

        <label>
          <span class="mb-2 block text-sm font-bold text-slate-600 dark:text-slate-300">状态</span>
          <select v-model="filterStatus" class="form-control" @change="resetPage">
            <option value="all">全部状态</option>
            <option value="active">活跃</option>
            <option value="inactive">未激活</option>
            <option value="suspended">已封禁</option>
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

    <section class="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white/85 shadow-lg shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-900/85 dark:shadow-black/20">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
          <thead class="bg-slate-50 dark:bg-slate-950">
            <tr>
              <th class="table-head">ID</th>
              <th class="table-head">用户名</th>
              <th class="table-head">邮箱</th>
              <th class="table-head">角色</th>
              <th class="table-head">状态</th>
              <th class="table-head">创建时间</th>
              <th class="table-head">最后登录</th>
              <th class="table-head text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-800">
            <tr v-for="user in paginatedUsers" :key="user.id" class="transition hover:bg-slate-50 dark:hover:bg-slate-800/70">
              <td class="table-cell font-black">{{ user.id }}</td>
              <td class="table-cell">
                <div class="flex items-center gap-3">
                  <div class="grid h-9 w-9 place-items-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300">
                    <Icon icon="material-symbols:person" class="h-5 w-5" />
                  </div>
                  <span class="font-black">{{ user.username }}</span>
                </div>
              </td>
              <td class="table-cell text-slate-600 dark:text-slate-300">{{ user.email }}</td>
              <td class="table-cell">
                <span class="rounded-full bg-cyan-100 px-2.5 py-1 text-xs font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300">
                  {{ getRoleDisplayName(user.role) }}
                </span>
              </td>
              <td class="table-cell">
                <span :class="['rounded-full px-2.5 py-1 text-xs font-black', getStatusInfo(user.status).color]">
                  {{ getStatusInfo(user.status).name }}
                </span>
              </td>
              <td class="table-cell text-slate-600 dark:text-slate-300">{{ formatDate(user.created_at) }}</td>
              <td class="table-cell text-slate-600 dark:text-slate-300">{{ formatDate(user.last_login) }}</td>
              <td class="table-cell">
                <div class="flex items-center justify-end gap-2">
                  <button class="action-button text-cyan-600 dark:text-cyan-300" title="编辑" @click="handleEditUser(user.id)">
                    <Icon icon="material-symbols:edit" class="h-4 w-4" />
                  </button>
                  <button class="action-button text-rose-600 dark:text-rose-300" title="删除" @click="handleDeleteUser(user.id)">
                    <Icon icon="material-symbols:delete" class="h-4 w-4" />
                  </button>
                  <select class="rounded-xl border border-slate-200 bg-white px-2 py-1 text-xs dark:border-slate-800 dark:bg-slate-950" :value="user.status" @change="handleStatusChange(user.id, ($event.target as HTMLSelectElement).value as User['status'])">
                    <option value="active">活跃</option>
                    <option value="inactive">未激活</option>
                    <option value="suspended">封禁</option>
                  </select>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="filteredUsers.length === 0" class="px-6 py-12 text-center">
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
  @apply rounded-xl p-2 transition hover:bg-slate-100 dark:hover:bg-slate-800;
}

.page-button {
  @apply rounded-xl bg-slate-100 px-3 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700;
}

.page-button-active {
  @apply bg-cyan-400 text-slate-950 hover:bg-cyan-300 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300;
}
</style>
