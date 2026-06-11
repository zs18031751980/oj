<<<<<<< HEAD
<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { Icon } from '@iconify/vue';
import { NButton } from 'naive-ui';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const authStore = useAuthStore();

const safeNext = computed(() => {
  const nextValue = Array.isArray(route.query.next)
    ? String(route.query.next[0] || '/')
    : String(route.query.next || '/');
  return nextValue.startsWith('/') ? nextValue : '/';
});

const startClubLogin = () => {
  authStore.startOAuthLogin('iOSClub', safeNext.value, true);
};

const handleLogout = async () => {
  await authStore.logout();
};
</script>

<template>
  <div class="min-h-screen bg-gray-50 px-4 py-12 text-gray-900 dark:bg-gray-900 dark:text-gray-100 sm:px-6 lg:px-8">
    <div class="mx-auto flex w-full max-w-2xl flex-col gap-8">
      <div class="text-center">
        <div class="mb-4 flex justify-center">
          <img src="/assets/logo.png" alt="Let Coding" class="h-16 w-16" />
        </div>
        <h1 class="text-3xl font-bold tracking-tight sm:text-4xl">登录 Let Coding</h1>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">
          直接使用社团官网统一认证登录，完成后会自动返回当前页面。
        </p>
      </div>

      <div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div class="space-y-6 p-8">
          <div
            v-if="authStore.isAuthenticated"
            class="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-100"
          >
            当前已登录：{{ authStore.displayName }}。你可以直接进入系统，或者先退出后切换社团账号。
            <div class="mt-3">
              <NButton size="small" tertiary type="error" @click="handleLogout">
                退出当前账号
              </NButton>
            </div>
          </div>

          <div class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm leading-6 text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200">
            点击下方按钮后，会跳转到社团官网的统一登录页面。你在社团官网完成账号密码验证后，会带着登录结果自动回到 Let Coding。
          </div>

          <NButton
            block
            :bordered="false"
            class="w-full rounded-lg bg-gray-900 px-4 py-3.5 font-medium text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-white"
            @click="startClubLogin"
          >
            <template #icon>
              <Icon icon="material-symbols:login" class="h-5 w-5" />
            </template>
            使用社团官网登录
          </NButton>
        </div>
      </div>

      <div class="text-center text-sm text-gray-500 dark:text-gray-400">
        <p>登录完成后会自动回到你原本要访问的页面。</p>
      </div>
    </div>
  </div>
</template>
=======
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { NInput, NButton, NCheckbox, useMessage } from 'naive-ui';

const router = useRouter();
const message = useMessage(); // 创建 message 实例

// 表单数据
const formData = ref({
  username: '',
  password: '',
  remember: false
});

// 加载状态
const isLoading = ref(false);

// 表单错误信息
const errors = ref({
  username: '',
  password: ''
});

// 密码可见性
const showPassword = ref(false);

// 处理登录
const handleLogin = async () => {
  // 重置错误信息
  errors.value = {
    username: '',
    password: ''
  };
  
  // 表单验证
  let isValid = true;
  
  if (!formData.value.username.trim()) {
    errors.value.username = '请输入用户名或邮箱';
    isValid = false;
  }
  
  if (!formData.value.password) {
    errors.value.password = '请输入密码';
    isValid = false;
  }
  
  if (!isValid) {
    return;
  }
  
  isLoading.value = true;
  
  try {
    // 这里需要调用后端 API 来登录
    // 暂时使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    message.success('登录成功');
    // 登录成功后跳转到首页
    router.push('/');
  } catch (error) {
    message.error(`登录失败: ${error instanceof Error ? error.message : '未知错误'}`);
  } finally {
    isLoading.value = false;
  }
};

// 密码可见性切换
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value;
};

// 自动聚焦用户名输入框
onMounted(() => {
  const usernameInput = document.getElementById('username') as HTMLInputElement;
  if (usernameInput) {
    usernameInput.focus();
  }
});

// 跳转到注册页面（实际跳转到社团官网）
const handleRegister = () => {
  window.location.href = 'https://www.xauat.site/SignUp';
};
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4 sm:px-6 lg:px-8">
    <div class="w-full max-w-md">
      <!-- Logo 和标题 -->
      <div class="text-center mb-10">
        <div class="flex justify-center mb-4">
          <img src="/assets/logo.png" alt="Let Coding" class="w-16 h-16" />
        </div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">欢迎回来</h1>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">
          登录你的 Let Coding 账户
        </p>
      </div>
      
      <!-- 登录表单 -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-xl">
        <div class="p-8 space-y-6">
          <!-- 用户名 -->
          <div class="space-y-2">
            <label for="username" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              用户名或邮箱
            </label>
            <div class="relative h-12">
              <div class="absolute left-0 top-0 bottom-0 w-12 flex items-center justify-center z-10">
                <Icon icon="material-symbols:person" class="w-5 h-5 text-gray-400 dark:text-gray-500" />
              </div>
              <NInput
                v-model:value="formData.username"
                placeholder="输入用户名或邮箱"
                id="username"
                :bordered="false"
                :class="[
                  'w-full h-full pl-12 pr-4 rounded-lg text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-all duration-200',
                  'bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600',
                  errors.username ? 'ring-2 ring-red-500 dark:ring-red-400' : 'focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400'
                ]"
              />
            </div>
            <!-- 错误信息 -->
            <p v-if="errors.username" class="text-xs text-red-600 dark:text-red-400 mt-1">{{ errors.username }}</p>
          </div>
          
          <!-- 密码 -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                密码
              </label>
              <a href="#" class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors">
                忘记密码？
              </a>
            </div>
            <div class="relative h-12">
              <div class="absolute left-0 top-0 bottom-0 w-12 flex items-center justify-center z-10">
                <Icon icon="material-symbols:lock" class="w-5 h-5 text-gray-400 dark:text-gray-500" />
              </div>
              <NInput
                v-model:value="formData.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="输入密码"
                id="password"
                :bordered="false"
                :class="[
                  'w-full h-full pl-12 pr-12 rounded-lg text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-all duration-200',
                  'bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600',
                  errors.password ? 'ring-2 ring-red-500 dark:ring-red-400' : 'focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400'
                ]"
              />
              <!-- 密码可见性切换按钮 -->
              <button 
                type="button"
                class="absolute right-0 top-0 bottom-0 w-12 flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors z-10"
                @click="togglePasswordVisibility"
              >
                <Icon 
                  :icon="showPassword ? 'material-symbols:visibility' : 'material-symbols:visibility-off'" 
                  class="w-5 h-5"
                />
              </button>
            </div>
            <!-- 错误信息 -->
            <p v-if="errors.password" class="text-xs text-red-600 dark:text-red-400 mt-1">{{ errors.password }}</p>
          </div>
          
          <!-- 记住我和登录按钮 -->
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <NCheckbox 
                v-model:checked="formData.remember"
                :bordered="false"
                :class="['text-sm text-gray-600 dark:text-gray-300']"
              >
                <span class="text-sm text-gray-600 dark:text-gray-300">记住我</span>
              </NCheckbox>
            </div>
          </div>
          
          <!-- 登录按钮 -->
          <NButton
            type="primary"
            block
            :loading="isLoading"
            :bordered="false"
            @click="handleLogin"
            :class="[
              'w-full py-3.5 px-4 rounded-lg font-medium transition-all duration-200',
              'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800',
              'shadow-md hover:shadow-lg active:shadow-sm',
              'transform hover:-translate-y-0.5 active:translate-y-0'
            ]"
          >
            登录
          </NButton>
          
          <!-- 分割线 -->
          <div class="relative my-8">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-200 dark:border-gray-700"></div>
            </div>
            <div class="relative flex justify-center">
              <span class="px-4 bg-white dark:bg-gray-800 text-sm text-gray-500 dark:text-gray-400">
                或使用其他方式登录
              </span>
            </div>
          </div>
          
          <!-- 第三方登录 -->
          <div class="grid grid-cols-2 gap-4">
            <button
              class="flex items-center justify-center gap-2 py-3.5 px-4 rounded-lg transition-all duration-200"
              :class="[
                'bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600',
                'hover:bg-gray-50 dark:hover:bg-gray-600 hover:border-gray-300 dark:hover:border-gray-500',
                'shadow-sm hover:shadow-md active:shadow-sm'
              ]"
            >
              <Icon icon="mdi:github" class="w-5 h-5" />
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">GitHub</span>
            </button>
            <button
              class="flex items-center justify-center gap-2 py-3.5 px-4 rounded-lg transition-all duration-200"
              :class="[
                'bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600',
                'hover:bg-gray-50 dark:hover:bg-gray-600 hover:border-gray-300 dark:hover:border-gray-500',
                'shadow-sm hover:shadow-md active:shadow-sm'
              ]"
            >
              <Icon icon="mdi:google" class="w-5 h-5" />
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Google</span>
            </button>
          </div>
        </div>
        
        <!-- 底部注册链接 -->
        <div class="bg-gray-50 dark:bg-gray-900 p-6 border-t border-gray-200 dark:border-gray-700">
          <div class="text-center">
            <span class="text-sm text-gray-600 dark:text-gray-300">
              还没有账户？
            </span>
            <button
              @click="handleRegister"
              class="ml-1 text-sm font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-all duration-200 transform hover:-translate-y-0.5"
            >
              立即注册
            </button>
          </div>
        </div>
      </div>
      
      <!-- 页脚 -->
      <div class="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>© {{ new Date().getFullYear() }} Let Coding. 保留所有权利。</p>
        <div class="flex justify-center gap-4 mt-2">
          <a href="#" class="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">隐私政策</a>
          <a href="#" class="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">使用条款</a>
          <a href="#" class="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">帮助中心</a>
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
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
