# 新手开发手册

欢迎使用 LetApp 开发手册！本手册将帮助你快速上手这个基于 Vue 3 + TypeScript + Vite 的前端项目。

## 📖 目录

1. [环境准备](#环境准备)
2. [项目概览](#项目概览)
3. [快速开始](#快速开始)
4. [开发流程](#开发流程)
5. [代码规范](#代码规范)
6. [核心功能](#核心功能)
7. [常见问题](#常见问题)
8. [进阶指南](#进阶指南)

## 🔧 环境准备

### 必需软件
- **Node.js**: 版本 18.0 或更高
- **npm**: 通常随 Node.js 一起安装
- **代码编辑器**: 推荐使用 VS Code

### VS Code 推荐插件
- Vue Language Features (Volar)
- TypeScript Vue Plugin (Volar)
- Tailwind CSS IntelliSense
- Vue VSCode Snippets

### 验证环境
```bash
node --version    # 应该显示 v18.0.0 或更高
npm --version     # 应该显示 npm 版本
```

## 🏗️ 项目概览

### 技术栈
- **前端框架**: Vue 3.5+ (Composition API)
- **编程语言**: TypeScript 5.9+
- **构建工具**: Vite 7.1+
- **状态管理**: Pinia 3.0+
- **路由**: Vue Router 4.6+
- **样式**: Tailwind CSS 4.1+
- **Markdown**: markdown-it 14.1+ 及插件生态
- **UI 组件**: Naive UI 2.43+

### 项目结构
```
letapp/
├── public/              # 静态资源
│   └── assets/         # 图片、图标等
├── src/                # 源代码
│   ├── components/     # 可复用组件
│   ├── layouts/        # 布局组件
│   ├── pages/         # 页面组件
│   ├── stores/        # Pinia 状态管理
│   ├── types/         # TypeScript 类型定义
│   ├── App.vue        # 根组件
│   ├── main.ts        # 应用入口
│   ├── router.ts      # 路由配置
│   └── style.css      # 全局样式
├── index.html         # HTML 模板
├── package.json       # 项目配置
├── vite.config.ts     # Vite 配置
└── tsconfig.json      # TypeScript 配置
```

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <项目地址>
cd letapp
```

### 2. 安装依赖
```bash
npm install
```

### 3. 启动开发服务器
```bash
npm run dev
```
服务器将在 `http://localhost:5173` 启动，支持热重载。

### 4. 构建生产版本
```bash
npm run build
```

### 5. 预览生产构建
```bash
npm run preview
```

## 🔄 开发流程

### 日常开发工作流
1. **拉取最新代码**: `git pull`
2. **创建功能分支**: `git checkout -b feature/新功能名称`
3. **开发**: 编写代码、测试功能
4. **类型检查**: `vue-tsc -b`
5. **构建测试**: `npm run build`
6. **提交代码**: `git add . && git commit -m "描述"`
7. **推送分支**: `git push origin feature/新功能名称`

### 标准开发流程

当需要添加新功能时，请按照以下标准流程进行：

#### 第一步：添加服务层 (@src/services/)

如果功能需要与后端 API 交互或处理业务逻辑，首先在 `src/services/` 目录中创建对应的服务文件：

```typescript
// src/services/user.ts
import type { User, ApiResponse } from '@/types'

export class UserService {
  private baseURL = '/api/users'
  
  // 获取用户列表
  async getUsers(): Promise<ApiResponse<User[]>> {
    const response = await fetch(this.baseURL)
    return response.json()
  }
  
  // 获取单个用户
  async getUser(id: number): Promise<ApiResponse<User>> {
    const response = await fetch(`${this.baseURL}/${id}`)
    return response.json()
  }
  
  // 创建用户
  async createUser(userData: Omit<User, 'id'>): Promise<ApiResponse<User>> {
    const response = await fetch(this.baseURL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    })
    return response.json()
  }
  
  // 更新用户
  async updateUser(id: number, userData: Partial<User>): Promise<ApiResponse<User>> {
    const response = await fetch(`${this.baseURL}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    })
    return response.json()
  }
  
  // 删除用户
  async deleteUser(id: number): Promise<ApiResponse<void>> {
    const response = await fetch(`${this.baseURL}/${id}`, {
      method: 'DELETE'
    })
    return response.json()
  }
}

// 导出单例实例
export const userService = new UserService()
```

#### 第二步：添加状态管理 (@src/stores/)

如果功能需要全局状态管理，在 `src/stores/` 目录中创建对应的 store 文件：

```typescript
// src/stores/user.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userService } from '@/services/user'
import type { User } from '@/types'

export const useUserStore = defineStore('user', () => {
  // 状态定义
  const users = ref<User[]>([])
  const currentUser = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  
  // 计算属性
  const userCount = computed(() => users.value.length)
  const activeUsers = computed(() => users.value.filter(user => user.isActive))
  
  // 异步操作
  async function fetchUsers() {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await userService.getUsers()
      if (response.success) {
        users.value = response.data
      } else {
        error.value = response.message
      }
    } catch (err) {
      error.value = '获取用户列表失败'
      console.error('fetchUsers error:', err)
    } finally {
      isLoading.value = false
    }
  }
  
  async function fetchUser(id: number) {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await userService.getUser(id)
      if (response.success) {
        currentUser.value = response.data
      } else {
        error.value = response.message
      }
    } catch (err) {
      error.value = '获取用户信息失败'
      console.error('fetchUser error:', err)
    } finally {
      isLoading.value = false
    }
  }
  
  async function createUser(userData: Omit<User, 'id'>) {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await userService.createUser(userData)
      if (response.success) {
        users.value.push(response.data)
        return response.data
      } else {
        error.value = response.message
        throw new Error(response.message)
      }
    } catch (err) {
      error.value = '创建用户失败'
      console.error('createUser error:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  async function updateUser(id: number, userData: Partial<User>) {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await userService.updateUser(id, userData)
      if (response.success) {
        const index = users.value.findIndex(user => user.id === id)
        if (index !== -1) {
          users.value[index] = response.data
        }
        if (currentUser.value?.id === id) {
          currentUser.value = response.data
        }
        return response.data
      } else {
        error.value = response.message
        throw new Error(response.message)
      }
    } catch (err) {
      error.value = '更新用户失败'
      console.error('updateUser error:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  async function deleteUser(id: number) {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await userService.deleteUser(id)
      if (response.success) {
        users.value = users.value.filter(user => user.id !== id)
        if (currentUser.value?.id === id) {
          currentUser.value = null
        }
      } else {
        error.value = response.message
        throw new Error(response.message)
      }
    } catch (err) {
      error.value = '删除用户失败'
      console.error('deleteUser error:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  // 同步操作
  function setCurrentUser(user: User | null) {
    currentUser.value = user
  }
  
  function clearUsers() {
    users.value = []
    currentUser.value = null
    error.value = null
  }
  
  function clearError() {
    error.value = null
  }
  
  return {
    // 状态
    users,
    currentUser,
    isLoading,
    error,
    
    // 计算属性
    userCount,
    activeUsers,
    
    // 方法
    fetchUsers,
    fetchUser,
    createUser,
    updateUser,
    deleteUser,
    setCurrentUser,
    clearUsers,
    clearError
  }
})
```

#### 第三步：添加相关页面 (@src/pages/)

在 `src/pages/` 目录中创建对应的页面组件：

```vue
<!-- src/pages/UserManagement.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import type { User } from '@/types'

// Store 实例
const userStore = useUserStore()

// 响应式数据
const searchKeyword = ref('')
const showCreateModal = ref(false)
const editingUser = ref<User | null>(null)

// 计算属性
const filteredUsers = computed(() => {
  if (!searchKeyword.value) return userStore.users
  return userStore.users.filter(user => 
    user.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
    user.email.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 方法
async function loadUsers() {
  await userStore.fetchUsers()
}

async function handleCreateUser(userData: Omit<User, 'id'>) {
  try {
    await userStore.createUser(userData)
    showCreateModal.value = false
    // 显示成功消息
  } catch (error) {
    // 显示错误消息
  }
}

async function handleUpdateUser(userData: Partial<User>) {
  if (!editingUser.value) return
  
  try {
    await userStore.updateUser(editingUser.value.id, userData)
    editingUser.value = null
    // 显示成功消息
  } catch (error) {
    // 显示错误消息
  }
}

async function handleDeleteUser(userId: number) {
  if (confirm('确定要删除这个用户吗？')) {
    try {
      await userStore.deleteUser(userId)
      // 显示成功消息
    } catch (error) {
      // 显示错误消息
    }
  }
}

function openEditModal(user: User) {
  editingUser.value = { ...user }
}

function closeModals() {
  showCreateModal.value = false
  editingUser.value = null
}

// 生命周期
onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="user-management">
    <!-- 页面标题 -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">用户管理</h1>
      <button 
        @click="showCreateModal = true"
        class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
      >
        新增用户
      </button>
    </div>
    
    <!-- 搜索栏 -->
    <div class="mb-6">
      <input
        v-model="searchKeyword"
        type="text"
        placeholder="搜索用户..."
        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
      />
    </div>
    
    <!-- 加载状态 -->
    <div v-if="userStore.isLoading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      <p class="mt-2 text-gray-600 dark:text-gray-400">加载中...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="userStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ userStore.error }}
      <button @click="userStore.clearError()" class="ml-2 text-red-500 hover:text-red-700">×</button>
    </div>
    
    <!-- 用户列表 -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              姓名
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              邮箱
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              状态
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="user in filteredUsers" :key="user.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
              {{ user.name }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
              {{ user.email }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span 
                :class="[
                  'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
                  user.isActive 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                ]"
              >
                {{ user.isActive ? '活跃' : '非活跃' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <button 
                @click="openEditModal(user)"
                class="text-blue-600 hover:text-blue-900 mr-3"
              >
                编辑
              </button>
              <button 
                @click="handleDeleteUser(user.id)"
                class="text-red-600 hover:text-red-900"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- 空状态 -->
      <div v-if="filteredUsers.length === 0" class="text-center py-8">
        <p class="text-gray-500 dark:text-gray-400">暂无用户数据</p>
      </div>
    </div>
    
    <!-- 创建用户模态框 -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">新增用户</h2>
        <UserForm 
          @submit="handleCreateUser" 
          @cancel="closeModals"
        />
      </div>
    </div>
    
    <!-- 编辑用户模态框 -->
    <div v-if="editingUser" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">编辑用户</h2>
        <UserForm 
          :user="editingUser"
          @submit="handleUpdateUser" 
          @cancel="closeModals"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-management {
  @apply p-6 max-w-7xl mx-auto;
}
</style>
```

#### 第四步：添加路由配置

在 `src/router.ts` 中添加新页面的路由：

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from './layouts/MainLayout.vue'
import Home from './pages/Home.vue'
import UserManagement from './pages/UserManagement.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'Home',
          component: Home
        },
        {
          path: 'users',
          name: 'UserManagement',
          component: UserManagement
        }
      ]
    }
  ]
})

export default router
```

#### 第五步：添加类型定义

在 `src/types/` 目录中添加相关的类型定义：

```typescript
// src/types/user.ts
export interface User {
  id: number
  name: string
  email: string
  isActive: boolean
  avatar?: string
  createdAt: string
  updatedAt: string
}

export interface CreateUserRequest {
  name: string
  email: string
  isActive?: boolean
}

export interface UpdateUserRequest {
  name?: string
  email?: string
  isActive?: boolean
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  message: string
  code?: number
}
```

### 开发流程总结

1. **服务层** (`src/services/`): 处理 API 调用和业务逻辑
2. **状态管理** (`src/stores/`): 管理全局状态和异步操作
3. **页面组件** (`src/pages/`): 实现 UI 界面和用户交互
4. **路由配置** (`router.ts`): 添加页面路由
5. **类型定义** (`src/types/`): 定义 TypeScript 类型

这种分层架构确保了：
- **关注点分离**: 每层职责明确
- **代码复用**: 服务和状态可以在多个组件中共享
- **易于测试**: 每层可以独立测试
- **维护性**: 修改某一层不会影响其他层

### 必要的检查步骤
- **类型检查**: 提交前必须运行 `vue-tsc -b` 确保无类型错误
- **构建验证**: 运行 `npm run build` 确保生产构建成功
- **功能测试**: 在开发环境中测试所有相关功能

## 📝 代码规范

### Vue 组件规范

#### 组件结构
```vue
<script setup lang="ts">
// 1. 导入 Vue 相关
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// 2. 第三方库导入
import MarkdownIt from 'markdown-it'

// 3. 内部导入
import { useThemeStore } from './stores/theme'
import type { Content } from './types'

// 4. 接口定义
interface Props {
  title: string
  content?: string
}

// 5. Props 定义
const props = withDefaults(defineProps<Props>(), {
  content: ''
})

// 6. Store 实例
const themeStore = useThemeStore()

// 7. 响应式数据
const isLoading = ref(false)

// 8. 计算属性
const formattedTitle = computed(() => props.title.toUpperCase())

// 9. 方法定义
function handleClick() {
  // 方法逻辑
}

// 10. 生命周期
onMounted(() => {
  // 初始化逻辑
})
</script>

<template>
  <!-- 模板内容 -->
  <div class="component-wrapper">
    <h1>{{ formattedTitle }}</h1>
    <p>{{ content }}</p>
  </div>
</template>

<style scoped>
/* 使用 Tailwind 类为主，自定义 CSS 为辅 */
.component-wrapper {
  @apply p-4 bg-white rounded-lg shadow-md;
}

/* 深色模式支持 */
.dark .component-wrapper {
  @apply bg-gray-800 text-white;
}
</style>
```

#### 命名规范
- **组件**: PascalCase (`MarkdownComponent.vue`)
- **文件**: kebab-case (`markdown-utils.ts`)
- **变量**: camelCase (`userName`, `isLoading`)
- **常量**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **类型/接口**: PascalCase (`User`, `ApiResponse`)

### TypeScript 规范

#### 类型定义
```typescript
// 基础类型
interface User {
  id: number
  name: string
  email: string
  avatar?: string  // 可选属性
}

// 泛型类型
interface ApiResponse<T> {
  data: T
  message: string
  success: boolean
}

// 联合类型
type Theme = 'light' | 'dark' | 'auto'

// 枚举
enum HttpStatus {
  OK = 200,
  NOT_FOUND = 404,
  INTERNAL_ERROR = 500
}
```

### 样式规范

#### Tailwind 优先
```vue
<template>
  <!-- 优先使用 Tailwind 类 -->
  <div class="flex items-center justify-between p-4 bg-white rounded-lg shadow-md">
    <h2 class="text-xl font-semibold text-gray-800">标题</h2>
    <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
      按钮
    </button>
  </div>
</template>
```

#### 自定义 CSS 使用场景
```vue
<style scoped>
/* 仅在 Tailwind 无法满足时使用自定义 CSS */
.markdown-content :deep(h1) {
  @apply text-3xl mt-8 mb-4 font-semibold;
}

/* 复杂动画或特殊效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
</style>
```

## 🎯 核心功能

### 1. Markdown 渲染系统

项目集成了强大的 Markdown 渲染引擎：

```typescript
// 在 MarkdownComponent.vue 中的配置示例
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})
  .use(markdownItAttrs)      // 属性支持 {.class #id}
  .use(markdownItTaskLists) // 任务列表 - [x]
  .use(markdownItMark)       // 标记文本 ==文本==
  .use(markdownItSub)        // 下标 H~2~O
  .use(markdownItSup)        // 上标 E=mc^2^
  .use(markdownItFootnote)   // 脚注
  .use(markdownItAnchor)     // 锚点导航
  .use(markdownItContainer)  // 自定义容器
```

#### 支持的语法
- **任务列表**: `- [ ] 未完成`、`- [x] 已完成`
- **标记文本**: `==高亮文本==`
- **上下标**: `H~2~O`、`X^2^`
- **属性**: `# 标题 {.red .large}`
- **自定义容器**: `:::warning 提示内容 :::`

### 2. 主题切换系统

```typescript
// stores/theme.ts 中的实现
export const useThemeStore = defineStore('theme', () => {
  const theme = ref<'light' | 'dark'>('light')
  
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    document.documentElement.classList.toggle('dark')
    localStorage.setItem('theme', theme.value)
  }
  
  function initTheme() {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      theme.value = savedTheme as 'light' | 'dark'
    } else {
      theme.value = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    
    if (theme.value === 'dark') {
      document.documentElement.classList.add('dark')
    }
  }
  
  return { theme, toggleTheme, initTheme }
})
```

### 3. 路由系统

```typescript
// router.ts 配置
import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from './layouts/MainLayout.vue'
import Home from './pages/Home.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'Home',
          component: Home
        }
      ]
    }
  ]
})

export default router
```

## ❓ 常见问题

### Q: 如何添加新页面？
A: 在 `src/pages/` 创建新组件，然后在 `router.ts` 中添加路由配置。

### Q: 如何添加新的状态管理？
A: 在 `src/stores/` 创建新文件，使用 Pinia 的 Composition API 模式。

### Q: 类型检查失败怎么办？
A: 运行 `vue-tsc -b` 查看具体错误，确保所有类型定义正确。

### Q: 如何自定义 Markdown 样式？
A: 在组件的 `<style scoped>` 中使用 `:deep()` 选择器修改 Markdown 渲染后的样式。

### Q: 开发服务器端口冲突？
A: 修改 `vite.config.ts` 中的端口配置，或在命令行指定端口：`npm run dev -- --port 3000`

## 📈 进阶指南

### 性能优化
- 使用 `defineAsyncComponent` 懒加载组件
- 合理使用 `computed` 缓存计算结果
- 避免不必要的响应式数据
- 使用 `v-memo` 优化列表渲染

### 代码分割
```typescript
// 路由级别的代码分割
const Home = defineAsyncComponent(() => import('./pages/Home.vue'))
```

### 错误处理
```typescript
// 全局错误处理 (main.ts)
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err)
  // 发送错误报告到监控服务
}
```

### 测试策略
- 组件单元测试：使用 Vue Test Utils
- E2E 测试：使用 Playwright 或 Cypress
- 类型检查：`vue-tsc -b` 作为第一道防线

## 🔗 有用链接

- [Vue 3 官方文档](https://vuejs.org/)
- [TypeScript 手册](https://www.typescriptlang.org/docs/)
- [Vite 文档](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Pinia 状态管理](https://pinia.vuejs.org/)
- [Vue Router](https://router.vuejs.org/)

## 💡 最佳实践

1. **保持组件小而专注**: 单一职责原则
2. **优先使用组合式 API**: 更好的逻辑复用
3. **合理使用 TypeScript**: 严格类型检查
4. **响应式设计**: 移动端优先
5. **性能优先**: 避免不必要的重渲染
6. **代码可读性**: 清晰的命名和注释

---

🎉 **恭喜！** 你已经掌握了 LetApp 项目的开发基础知识。现在可以开始你的开发之旅了！

如有问题，请查看项目的 `AGENTS.md` 文件获取更详细的开发指南，或者联系项目维护者获取帮助。