<script setup lang="ts">
// import { ref } from 'vue'; // 未使用，注释掉
import { Icon } from '@iconify/vue';

// 统计数据
const stats = [
  { 
    title: '总用户数', 
    value: 1250, 
    icon: 'material-symbols:people', 
    color: 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400',
    trend: '+15%',
    trendType: 'up'
  },
  { 
    title: '活跃用户', 
    value: 890, 
    icon: 'material-symbols:person', 
    color: 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400',
    trend: '+8%',
    trendType: 'up'
  },
  { 
    title: '代码执行次数', 
    value: 5680, 
    icon: 'material-symbols:code', 
    color: 'bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400',
    trend: '+22%',
    trendType: 'up'
  },
  { 
    title: '学习资源数', 
    value: 120, 
    icon: 'material-symbols:school', 
    color: 'bg-orange-100 dark:bg-orange-900 text-orange-600 dark:text-orange-400',
    trend: '+5%',
    trendType: 'up'
  },
];

// 最近用户
const recentUsers = [
  { id: 1, name: 'admin', email: 'admin@example.com', role: '管理员', status: 'active', joined: '2023-01-01' },
  { id: 2, name: 'user1', email: 'user1@example.com', role: '普通用户', status: 'active', joined: '2023-12-30' },
  { id: 3, name: 'user2', email: 'user2@example.com', role: '普通用户', status: 'inactive', joined: '2023-12-29' },
  { id: 4, name: 'guest1', email: 'guest1@example.com', role: '访客', status: 'active', joined: '2023-12-28' },
  { id: 5, name: 'user3', email: 'user3@example.com', role: '普通用户', status: 'suspended', joined: '2023-12-27' },
];

// 最近代码执行
const recentExecutions = [
  { id: 1, user: 'user1', language: 'JavaScript', status: 'success', executedAt: '2023-12-31 14:30:00' },
  { id: 2, user: 'user2', language: 'Python', status: 'error', executedAt: '2023-12-31 14:25:00' },
  { id: 3, user: 'admin', language: 'Java', status: 'success', executedAt: '2023-12-31 14:20:00' },
  { id: 4, user: 'guest1', language: 'JavaScript', status: 'success', executedAt: '2023-12-31 14:15:00' },
  { id: 5, user: 'user3', language: 'Python', status: 'success', executedAt: '2023-12-31 14:10:00' },
];
</script>

<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div>
      <h1 class="text-2xl font-bold mb-1">仪表盘</h1>
      <p class="text-gray-600 dark:text-gray-300">欢迎来到 Let Coding 管理后台</p>
    </div>
    
    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div 
        v-for="(stat, index) in stats" 
        :key="index"
        class="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 dark:text-gray-300 mb-1">{{ stat.title }}</p>
            <h3 class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ stat.value }}</h3>
            <div class="flex items-center gap-1 mt-2 text-sm">
              <Icon 
                :icon="stat.trendType === 'up' ? 'material-symbols:trending-up' : 'material-symbols:trending-down'" 
                class="w-4 h-4 text-green-600 dark:text-green-400"
              />
              <span class="text-green-600 dark:text-green-400 font-medium">{{ stat.trend }}</span>
              <span class="text-gray-500 dark:text-gray-400">较上月</span>
            </div>
          </div>
          <div :class="['w-12 h-12 rounded-lg flex items-center justify-center', stat.color]">
            <Icon :icon="stat.icon" class="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据图表 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 最近用户 -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">最近用户</h2>
          <button class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors">
            查看全部
          </button>
        </div>
        <div class="space-y-4">
          <div 
            v-for="(user, index) in recentUsers" 
            :key="index"
            class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                <Icon icon="material-symbols:person" class="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-medium text-gray-900 dark:text-gray-100">{{ user.name }}</span>
                  <span class="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                    {{ user.role }}
                  </span>
                </div>
                <p class="text-sm text-gray-600 dark:text-gray-300">{{ user.email }}</p>
              </div>
            </div>
            <div class="text-right">
              <div class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ user.joined }}</div>
              <span 
                class="text-xs px-2 py-0.5 rounded-full mt-1 inline-block"
                :class="[
                  user.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 
                  user.status === 'inactive' ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' : 
                  'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                ]"
              >
                {{ user.status === 'active' ? '活跃' : user.status === 'inactive' ? '未激活' : '已封禁' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 最近代码执行 -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">最近代码执行</h2>
          <button class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors">
            查看全部
          </button>
        </div>
        <div class="space-y-4">
          <div 
            v-for="(execution, index) in recentExecutions" 
            :key="index"
            class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                <Icon icon="material-symbols:code" class="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-medium text-gray-900 dark:text-gray-100">{{ execution.user }}</span>
                  <span class="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200">
                    {{ execution.language }}
                  </span>
                </div>
                <p class="text-sm text-gray-600 dark:text-gray-300">{{ execution.executedAt }}</p>
              </div>
            </div>
            <div>
              <span 
                class="text-xs px-2 py-0.5 rounded-full mt-1 inline-block"
                :class="[
                  execution.status === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 
                  'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                ]"
              >
                {{ execution.status === 'success' ? '成功' : '失败' }}
              </span>
            </div>
          </div>
        </div>
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