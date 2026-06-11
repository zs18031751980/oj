<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';

const router = useRouter();

// 侧边栏展开状态
const sidebarExpanded = ref(true);

// 导航菜单
const navMenu = [
  {
    title: '仪表盘',
    icon: 'material-symbols:dashboard',
    route: '/admin/dashboard',
    active: true
  },
  {
    title: '用户管理',
    icon: 'material-symbols:people',
    route: '/admin/users',
    active: false
  },
  {
    title: '代码管理',
    icon: 'material-symbols:code',
    route: '/admin/codes',
    active: false
  },
  {
    title: '学习资源管理',
    icon: 'material-symbols:school',
    route: '/admin/learning',
    active: false
  },
  {
    title: '系统设置',
    icon: 'material-symbols:settings',
    route: '/admin/settings',
    active: false
  }
];

// 切换侧边栏展开状态
const toggleSidebar = () => {
  sidebarExpanded.value = !sidebarExpanded.value;
};

// 导航到指定路由
const navigateTo = (route: string) => {
  router.push(route);
  // 更新菜单项的激活状态
  navMenu.forEach(item => {
    item.active = item.route === route;
  });
};

// 退出登录
const logout = () => {
  // 这里需要实现退出登录的逻辑
  console.log('退出登录');
  // 暂时跳转到首页
  router.push('/');
};
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <!-- 顶部导航栏 -->
    <header class="bg-white dark:bg-gray-800 shadow-md sticky top-0 z-50">
      <div class="flex items-center justify-between h-16 px-4">
        <!-- 左侧：切换侧边栏按钮 + 标题 -->
        <div class="flex items-center gap-3">
          <button 
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" 
            @click="toggleSidebar"
            aria-label="切换侧边栏"
          >
            <Icon 
              :icon="sidebarExpanded ? 'material-symbols:menu-open' : 'material-symbols:menu'" 
              class="w-6 h-6"
            />
          </button>
          <h1 class="text-xl font-semibold">Let Coding 管理后台</h1>
        </div>
        
        <!-- 右侧：用户信息 + 退出登录 -->
        <div class="flex items-center gap-4">
          <!-- 搜索框（可选） -->
          <div class="relative hidden md:block">
            <input 
              type="text" 
              placeholder="搜索..." 
              class="pl-10 pr-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-sm"
            />
            <Icon icon="material-symbols:search" class="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400" />
          </div>
          
          <!-- 通知图标（可选） -->
          <button class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors relative" aria-label="通知">
            <Icon icon="material-symbols:notifications" class="w-6 h-6" />
            <span class="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
          
          <!-- 用户信息 -->
          <div class="flex items-center gap-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded-lg transition-colors">
            <div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
              <Icon icon="material-symbols:person" class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <span class="font-medium hidden md:inline">管理员</span>
            <Icon icon="material-symbols:arrow-drop-down" class="w-5 h-5" />
          </div>
          
          <!-- 退出登录 -->
          <button 
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" 
            @click="logout"
            aria-label="退出登录"
          >
            <Icon icon="material-symbols:logout" class="w-6 h-6 text-red-600 dark:text-red-400" />
          </button>
        </div>
      </div>
    </header>
    
    <!-- 主内容区 -->
    <div class="flex">
      <!-- 侧边栏 -->
      <aside 
        :class="[
          'bg-white dark:bg-gray-800 shadow-md transition-all duration-300 fixed top-16 bottom-0 z-40 overflow-y-auto',
          sidebarExpanded ? 'w-64' : 'w-20',
          'border-r border-gray-200 dark:border-gray-700'
        ]"
      >
        <nav class="p-4">
          <ul class="space-y-2">
            <li 
              v-for="(item, index) in navMenu" 
              :key="index"
              class="group"
            >
              <button 
                class="flex items-center gap-3 w-full px-4 py-3 rounded-lg transition-colors"
                :class="[
                  item.active ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                ]"
                @click="navigateTo(item.route)"
              >
                <Icon :icon="item.icon" class="w-6 h-6" />
                <span v-if="sidebarExpanded" class="font-medium">{{ item.title }}</span>
              </button>
            </li>
          </ul>
          
          <!-- 分割线 -->
          <div class="my-6 border-t border-gray-200 dark:border-gray-700"></div>
          
          <!-- 快捷操作 -->
          <div v-if="sidebarExpanded" class="space-y-4">
            <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">快捷操作</h3>
            <div class="grid grid-cols-2 gap-3">
              <button class="flex flex-col items-center gap-2 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                <div class="w-10 h-10 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                  <Icon icon="material-symbols:add" class="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <span class="text-sm font-medium">新增用户</span>
              </button>
              <button class="flex flex-col items-center gap-2 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                  <Icon icon="material-symbols:upload" class="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <span class="text-sm font-medium">导入数据</span>
              </button>
            </div>
          </div>
        </nav>
      </aside>
      
      <!-- 内容区域 -->
      <main 
        :class="[
          'flex-1 transition-all duration-300',
          sidebarExpanded ? 'ml-64' : 'ml-20',
          'p-6'
        ]"
      >
        <router-view />
      </main>
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