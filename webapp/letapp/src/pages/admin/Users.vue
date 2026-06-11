<script setup lang="ts">
import { ref, computed } from 'vue';
import { Icon } from '@iconify/vue';

// 用户数据类型
interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  last_login: string;
}

// 模拟用户数据
const mockUsers: User[] = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    status: 'active',
    created_at: '2023-01-01T12:00:00Z',
    last_login: '2023-12-31T12:00:00Z'
  },
  {
    id: 2,
    username: 'user1',
    email: 'user1@example.com',
    role: 'user',
    status: 'active',
    created_at: '2023-02-01T12:00:00Z',
    last_login: '2023-12-30T12:00:00Z'
  },
  {
    id: 3,
    username: 'user2',
    email: 'user2@example.com',
    role: 'user',
    status: 'inactive',
    created_at: '2023-03-01T12:00:00Z',
    last_login: '2023-11-30T12:00:00Z'
  },
  {
    id: 4,
    username: 'guest1',
    email: 'guest1@example.com',
    role: 'guest',
    status: 'active',
    created_at: '2023-04-01T12:00:00Z',
    last_login: '2023-12-29T12:00:00Z'
  },
  {
    id: 5,
    username: 'user3',
    email: 'user3@example.com',
    role: 'user',
    status: 'suspended',
    created_at: '2023-05-01T12:00:00Z',
    last_login: '2023-10-30T12:00:00Z'
  },
];

// 搜索关键词
const searchKeyword = ref('');

// 筛选条件
const filterRole = ref('all');
const filterStatus = ref('all');

// 当前页码
const currentPage = ref(1);

// 每页显示数量
const pageSize = ref(10);

// 用户列表数据
const users = ref<User[]>([...mockUsers]);

// 计算属性：过滤后的用户列表
const filteredUsers = computed(() => {
  let result = [...users.value];
  
  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(user => 
      user.username.toLowerCase().includes(keyword) || 
      user.email.toLowerCase().includes(keyword)
    );
  }
  
  // 按角色过滤
  if (filterRole.value !== 'all') {
    result = result.filter(user => user.role === filterRole.value);
  }
  
  // 按状态过滤
  if (filterStatus.value !== 'all') {
    result = result.filter(user => user.status === filterStatus.value);
  }
  
  return result;
});

// 计算属性：分页后的用户列表
const paginatedUsers = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value;
  const endIndex = startIndex + pageSize.value;
  return filteredUsers.value.slice(startIndex, endIndex);
});

// 计算属性：总页数
const totalPages = computed(() => {
  return Math.ceil(filteredUsers.value.length / pageSize.value);
});

// 计算属性：总用户数
const totalUsers = computed(() => {
  return filteredUsers.value.length;
});

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1; // 搜索后回到第一页
};

// 处理重置筛选
const handleResetFilter = () => {
  searchKeyword.value = '';
  filterRole.value = 'all';
  filterStatus.value = 'all';
  currentPage.value = 1;
};

// 处理页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page;
};

// 处理用户状态变更
const handleStatusChange = (userId: number, status: User['status']) => {
  const userIndex = users.value.findIndex(user => user.id === userId);
  if (userIndex !== -1 && users.value[userIndex]) {
    users.value[userIndex].status = status;
  }
};

// 处理删除用户
const handleDeleteUser = (userId: number) => {
  // 这里需要调用后端 API 来删除用户
  console.log('删除用户:', userId);
  // 暂时使用模拟数据
  users.value = users.value.filter(user => user.id !== userId);
};

// 处理编辑用户
const handleEditUser = (userId: number) => {
  // 这里需要跳转到编辑用户页面
  console.log('编辑用户:', userId);
  // 暂时使用 alert
  alert(`编辑用户 ${userId}，功能开发中...`);
};

// 获取角色显示名称
const getRoleDisplayName = (role: User['role']) => {
  const roleMap = {
    admin: '管理员',
    user: '普通用户',
    guest: '访客'
  };
  return roleMap[role];
};

// 获取状态显示名称和样式
const getStatusInfo = (status: User['status']) => {
  const statusMap = {
    active: { name: '活跃', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
    inactive: { name: '未激活', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' },
    suspended: { name: '已封禁', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' }
  };
  return statusMap[status];
};

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<template>
  <div class="space-y-6">
    <!-- 页面标题和操作按钮 -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h1 class="text-2xl font-bold mb-1">用户管理</h1>
        <p class="text-gray-600 dark:text-gray-300">管理平台用户，包括添加、编辑、删除和修改用户状态</p>
      </div>
      <button 
        class="flex items-center gap-2 px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors shadow-md"
      >
        <Icon icon="material-symbols:add" class="w-5 h-5" />
        新增用户
      </button>
    </div>
    
    <!-- 筛选和搜索区域 -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <!-- 搜索框 -->
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">搜索用户</label>
          <div class="relative">
            <input 
              type="text" 
              v-model="searchKeyword" 
              @input="handleSearch"
              placeholder="输入用户名或邮箱搜索..."
              class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
            />
            <Icon icon="material-symbols:search" class="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400" />
          </div>
        </div>
        
        <!-- 角色筛选 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">角色</label>
          <select 
            v-model="filterRole" 
            @change="handleSearch"
            class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
          >
            <option value="all">全部角色</option>
            <option value="admin">管理员</option>
            <option value="user">普通用户</option>
            <option value="guest">访客</option>
          </select>
        </div>
        
        <!-- 状态筛选 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">状态</label>
          <select 
            v-model="filterStatus" 
            @change="handleSearch"
            class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
          >
            <option value="all">全部状态</option>
            <option value="active">活跃</option>
            <option value="inactive">未激活</option>
            <option value="suspended">已封禁</option>
          </select>
        </div>
      </div>
      
      <!-- 筛选结果和重置按钮 -->
      <div class="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div class="text-sm text-gray-600 dark:text-gray-300">
          共 <span class="font-semibold">{{ totalUsers }}</span> 个用户
        </div>
        <button 
          class="flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm"
          @click="handleResetFilter"
        >
          <Icon icon="material-symbols:refresh" class="w-4 h-4" />
          重置筛选
        </button>
      </div>
    </div>
    
    <!-- 用户列表 -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-900">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">用户名</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">邮箱</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">角色</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">状态</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">创建时间</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">最后登录</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作</th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          <tr 
            v-for="user in paginatedUsers" 
            :key="user.id"
            class="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
          >
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">{{ user.id }}</td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                  <Icon icon="material-symbols:person" class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ user.username }}</span>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">{{ user.email }}</td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                {{ getRoleDisplayName(user.role) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="['px-2.5 py-0.5 rounded-full text-xs font-medium', getStatusInfo(user.status).color]">
                {{ getStatusInfo(user.status).name }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">{{ formatDate(user.created_at) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">{{ formatDate(user.last_login) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <div class="flex items-center justify-end gap-2">
                <button 
                  class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  @click="handleEditUser(user.id)"
                  title="编辑"
                >
                  <Icon icon="material-symbols:edit" class="w-4 h-4" />
                </button>
                <button 
                  class="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 transition-colors p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  @click="handleDeleteUser(user.id)"
                  title="删除"
                >
                  <Icon icon="material-symbols:delete" class="w-4 h-4" />
                </button>
                <div class="relative group">
                  <button 
                    class="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 transition-colors p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                    title="更多操作"
                  >
                    <Icon icon="material-symbols:more-vert" class="w-4 h-4" />
                  </button>
                  <!-- 下拉菜单 -->
                  <div class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                    <button 
                      class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      @click="handleStatusChange(user.id, 'active')"
                    >
                      设为活跃
                    </button>
                    <button 
                      class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      @click="handleStatusChange(user.id, 'inactive')"
                    >
                      设为未激活
                    </button>
                    <button 
                      class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      @click="handleStatusChange(user.id, 'suspended')"
                    >
                      封禁账号
                    </button>
                  </div>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- 空状态 -->
      <div v-if="filteredUsers.length === 0" class="px-6 py-12 text-center">
        <Icon icon="material-symbols:search-off" class="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">未找到用户</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          请尝试调整筛选条件或搜索关键词
        </p>
      </div>
    </div>
    
    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-between bg-white dark:bg-gray-800 px-6 py-4 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
      <div class="text-sm text-gray-600 dark:text-gray-300">
        显示第 <span class="font-semibold">{{ currentPage }}</span> 页，共 <span class="font-semibold">{{ totalPages }}</span> 页
      </div>
      <div class="flex items-center gap-2">
        <button 
          class="px-3 py-1.5 rounded-lg transition-colors text-sm font-medium"
          :class="[
            currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
          ]"
          @click="handlePageChange(currentPage - 1)"
          :disabled="currentPage === 1"
        >
          上一页
        </button>
        
        <!-- 页码列表 -->
        <div class="flex items-center gap-1">
          <button 
            v-for="page in totalPages" 
            :key="page"
            class="w-8 h-8 flex items-center justify-center rounded-lg transition-colors text-sm font-medium"
            :class="[
              currentPage === page ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            ]"
            @click="handlePageChange(page)"
          >
            {{ page }}
          </button>
        </div>
        
        <button 
          class="px-3 py-1.5 rounded-lg transition-colors text-sm font-medium"
          :class="[
            currentPage === totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
          ]"
          @click="handlePageChange(currentPage + 1)"
          :disabled="currentPage === totalPages"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 自定义滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  dark:bg-gray-800;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>