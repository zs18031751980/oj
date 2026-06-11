<<<<<<< HEAD
<script setup lang="ts">
import { ref } from 'vue';
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const categories = [
  { id: 'beginner', name: '入门教程', icon: 'material-symbols:school', color: '#4CAF50' },
  { id: 'advanced', name: '进阶学习', icon: 'material-symbols:rocket-launch', color: '#2196F3' },
  { id: 'project', name: '实战项目', icon: 'material-symbols:build', color: '#FF9800' },
  { id: 'algorithm', name: '算法练习', icon: 'material-symbols:calculate', color: '#9C27B0' },
];

const popularCourses = [
  {
    id: 1,
    title: 'JavaScript 入门指南',
    description: '从零开始学习 JavaScript 编程语言，掌握基础语法和核心概念。',
    category: 'beginner',
    level: '入门',
    duration: '12 小时',
    author: 'Let Coding',
    language: 'JavaScript',
    url: 'https://plan.xauat.site/software/web-basic/javascript-basics.html',
  },
  {
    id: 2,
    title: 'Python 数据分析实战',
    description: '学习使用 Python 进行数据分析和可视化，掌握 pandas、numpy 和 matplotlib 等常用库。',
    category: 'advanced',
    level: '进阶',
    duration: '15 小时',
    author: 'Let Coding',
    language: 'Python',
  },
  {
    id: 3,
    title: 'Web 开发实战：Todo 应用',
    description: '使用 HTML、CSS 和 JavaScript 构建一个完整的 Todo 应用，学习前后端开发流程。',
    category: 'project',
    level: '入门',
    duration: '8 小时',
    author: 'Let Coding',
    language: 'JavaScript',
  },
  {
    id: 4,
    title: '算法基础：排序与搜索',
    description: '学习常见的排序和搜索算法，掌握算法分析和优化方法。',
    category: 'algorithm',
    level: '入门',
    duration: '10 小时',
    author: 'Let Coding',
    language: 'Python',
  },
];

const selectedCategory = ref('all');
const filteredCourses = ref([...popularCourses]);

const filterByCategory = (categoryId: string) => {
  selectedCategory.value = categoryId;
  filteredCourses.value = categoryId === 'all'
    ? [...popularCourses]
    : popularCourses.filter((course) => course.category === categoryId);
};

const startLearning = (course: typeof popularCourses[number]) => {
  if (course.url) {
    globalThis.open(course.url, '_blank', 'noopener noreferrer');
    return;
  }

  alert(`课程《${course.title}》正在建设中...`);
};
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-16 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <button class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" @click="router.back()">
            <Icon icon="material-symbols:arrow-back" class="w-5 h-5" />
          </button>
          <h1 class="text-2xl font-bold">学习资源</h1>
        </div>
      </div>
    </div>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="mb-8">
        <div class="flex flex-wrap items-center gap-3">
          <button
            class="filter-button"
            :class="selectedCategory === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'"
            @click="filterByCategory('all')"
          >
            <Icon icon="material-symbols:category" class="w-4 h-4" />
            全部
          </button>

          <button
            v-for="category in categories"
            :key="category.id"
            class="filter-button"
            :class="selectedCategory === category.id ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'"
            @click="filterByCategory(category.id)"
          >
            <Icon :icon="category.icon" class="w-4 h-4" :style="{ color: selectedCategory === category.id ? 'white' : category.color }" />
            {{ category.name }}
          </button>
        </div>
      </div>

      <section class="mb-12">
        <h2 class="text-2xl font-bold mb-6">热门教程</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <article
            v-for="course in filteredCourses"
            :key="course.id"
            class="bg-white dark:bg-gray-800 rounded-lg shadow-lg hover:shadow-xl transition border border-gray-200 dark:border-gray-700 overflow-hidden hover:-translate-y-1"
          >
            <div class="p-6 space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <span class="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                  {{ course.language }}
                </span>
                <span class="px-3 py-1 text-xs font-medium rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                  {{ course.level }}
                </span>
              </div>

              <h3 class="text-xl font-semibold line-clamp-2">{{ course.title }}</h3>
              <p class="text-gray-600 dark:text-gray-300 text-sm line-clamp-3">{{ course.description }}</p>

              <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mt-2">
                <div class="flex items-center gap-1">
                  <Icon icon="material-symbols:person" class="w-4 h-4" />
                  {{ course.author }}
                </div>
                <div class="flex items-center gap-1">
                  <Icon icon="material-symbols:schedule" class="w-4 h-4" />
                  {{ course.duration }}
                </div>
              </div>

              <button class="w-full mt-4 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors" @click="startLearning(course)">
                开始学习
              </button>
            </div>
          </article>
        </div>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-6">学习路径</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <article class="path-card">
            <div class="path-icon bg-blue-100 dark:bg-blue-900">
              <Icon icon="material-symbols:school" class="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 class="text-xl font-semibold">Web 开发路径</h3>
            <p class="text-gray-600 dark:text-gray-300">
              从 HTML、CSS 和 JavaScript 基础开始，逐步进入前端框架和后端开发。
            </p>
          </article>

          <article class="path-card">
            <div class="path-icon bg-green-100 dark:bg-green-900">
              <Icon icon="material-symbols:code" class="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <h3 class="text-xl font-semibold">数据科学路径</h3>
            <p class="text-gray-600 dark:text-gray-300">
              从 Python 基础开始，学习数据分析、可视化和机器学习核心方法。
            </p>
          </article>

          <article class="path-card">
            <div class="path-icon bg-orange-100 dark:bg-orange-900">
              <Icon icon="material-symbols:calculate" class="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
            <h3 class="text-xl font-semibold">算法与编程路径</h3>
            <p class="text-gray-600 dark:text-gray-300">
              系统练习数据结构、排序搜索、动态规划与常用算法优化技巧。
            </p>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.filter-button {
  @apply flex items-center gap-2 px-4 py-2 rounded-lg transition-colors;
}

.path-card {
  @apply bg-gray-50 dark:bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-200 dark:border-gray-700 space-y-4;
}

.path-icon {
  @apply w-12 h-12 rounded-full flex items-center justify-center;
}
</style>
=======
<script setup lang="ts">
import { ref } from 'vue';
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// 学习资源分类
const categories = [
  { id: 'beginner', name: '入门教程', icon: 'material-symbols:school', color: '#4CAF50' },
  { id: 'advanced', name: '进阶学习', icon: 'material-symbols:rocket-launch', color: '#2196F3' },
  { id: 'project', name: '实战项目', icon: 'material-symbols:build', color: '#FF9800' },
  { id: 'algorithm', name: '算法练习', icon: 'material-symbols:calculate', color: '#9C27B0' },
];

// 热门教程
const popularCourses = [
  { 
    id: 1, 
    title: 'JavaScript 入门指南', 
    description: '从零开始学习 JavaScript 编程语言，掌握基本语法和核心概念。', 
    category: 'beginner', 
    level: '入门', 
    duration: '12 小时', 
    author: 'Let Coding',
    language: 'JavaScript'
  },
  { 
    id: 2, 
    title: 'Python 数据分析实战', 
    description: '学习使用 Python 进行数据分析和可视化，掌握 pandas、numpy 和 matplotlib 等库。', 
    category: 'advanced', 
    level: '进阶', 
    duration: '15 小时', 
    author: 'Let Coding',
    language: 'Python'
  },
  { 
    id: 3, 
    title: 'Web 开发实战：Todo 应用', 
    description: '使用 HTML、CSS 和 JavaScript 构建一个完整的 Todo 应用，学习前后端开发。', 
    category: 'project', 
    level: '入门', 
    duration: '8 小时', 
    author: 'Let Coding',
    language: 'JavaScript'
  },
  { 
    id: 4, 
    title: '算法基础：排序与搜索', 
    description: '学习常见的排序和搜索算法，掌握算法分析和优化方法。', 
    category: 'algorithm', 
    level: '入门', 
    duration: '10 小时', 
    author: 'Let Coding',
    language: 'Python'
  },
];

// 当前选中的分类
const selectedCategory = ref('all');

// 过滤后的教程
const filteredCourses = ref([...popularCourses]);

// 按分类过滤教程
const filterByCategory = (categoryId: string) => {
  selectedCategory.value = categoryId;
  if (categoryId === 'all') {
    filteredCourses.value = [...popularCourses];
  } else {
    filteredCourses.value = popularCourses.filter(course => course.category === categoryId);
  }
};

// 开始学习
const startLearning = (courseId: number) => {
  // 这里需要跳转到具体的课程页面
  console.log('开始学习课程:', courseId);
  // 暂时使用 alert
  alert(`开始学习课程 ${courseId}，功能开发中...`);
};
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <!-- 页面标题栏 -->
    <div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-16 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <button 
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" 
            @click="router.back()"
          >
            <Icon icon="material-symbols:arrow-back" class="w-5 h-5" />
          </button>
          <h1 class="text-2xl font-bold">学习资源</h1>
        </div>
      </div>
    </div>
    
    <!-- 学习资源主体 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <!-- 分类筛选 -->
      <div class="mb-8">
        <div class="flex flex-wrap items-center gap-3">
          <button 
            class="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors" 
            :class="selectedCategory === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'"
            @click="filterByCategory('all')"
          >
            <Icon icon="material-symbols:category" class="w-4 h-4" />
            全部
          </button>
          
          <button 
            v-for="category in categories" 
            :key="category.id"
            class="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors" 
            :class="selectedCategory === category.id ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'"
            @click="filterByCategory(category.id)"
          >
            <Icon :icon="category.icon" class="w-4 h-4" :style="{ color: selectedCategory === category.id ? 'white' : category.color }" />
            {{ category.name }}
          </button>
        </div>
      </div>
      
      <!-- 热门教程 -->
      <div class="mb-12">
        <h2 class="text-2xl font-bold mb-6">热门教程</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div 
            v-for="course in filteredCourses" 
            :key="course.id"
            class="bg-white dark:bg-gray-800 rounded-xl shadow-lg hover:shadow-xl transition-shadow border border-gray-200 dark:border-gray-700 overflow-hidden hover:translate-y-[-4px] transition-transform"
          >
            <div class="p-6 space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <span class="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                  {{ course.language }}
                </span>
                <span class="px-3 py-1 text-xs font-medium rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                  {{ course.level }}
                </span>
              </div>
              
              <h3 class="text-xl font-semibold line-clamp-2">{{ course.title }}</h3>
              <p class="text-gray-600 dark:text-gray-300 text-sm line-clamp-3">{{ course.description }}</p>
              
              <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mt-2">
                <div class="flex items-center gap-1">
                  <Icon icon="material-symbols:person" class="w-4 h-4" />
                  {{ course.author }}
                </div>
                <div class="flex items-center gap-1">
                  <Icon icon="material-symbols:schedule" class="w-4 h-4" />
                  {{ course.duration }}
                </div>
              </div>
              
              <button 
                class="w-full mt-4 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                @click="course.title === 'JavaScript 入门指南' ? window.open('https://plan.xauat.site/software/web-basic/javascript-basics.html', '_blank', 'noopener noreferrer') : startLearning(course.id)"
              >
                开始学习
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 学习路径 -->
      <div>
        <h2 class="text-2xl font-bold mb-6">学习路径</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-900 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                <Icon icon="material-symbols:school" class="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 class="text-xl font-semibold">Web 开发路径</h3>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-4">
              学习 Web 开发的完整路径，从 HTML、CSS 和 JavaScript 基础开始，到前端框架和后端开发。
            </p>
            <ul class="space-y-2 mb-6">
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                HTML & CSS 基础
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                JavaScript 核心
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                前端框架（Vue/React）
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                后端开发（Node.js/Python）
              </li>
            </ul>
            <button 
              class="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              查看完整路径
            </button>
          </div>
          
          <div class="bg-gradient-to-br from-green-50 to-teal-50 dark:from-gray-800 dark:to-gray-900 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                <Icon icon="material-symbols:code" class="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 class="text-xl font-semibold">数据科学路径</h3>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-4">
              学习数据科学和机器学习的完整路径，从 Python 基础开始，到数据分析、可视化和机器学习算法。
            </p>
            <ul class="space-y-2 mb-6">
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                Python 编程基础
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                数据分析库（pandas）
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                数据可视化（matplotlib）
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                机器学习算法
              </li>
            </ul>
            <button 
              class="w-full px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors"
            >
              查看完整路径
            </button>
          </div>
          
          <div class="bg-gradient-to-br from-orange-50 to-amber-50 dark:from-gray-800 dark:to-gray-900 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center">
                <Icon icon="material-symbols:calculate" class="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <h3 class="text-xl font-semibold">算法与编程路径</h3>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-4">
              学习算法和编程基础的完整路径，从数据结构开始，到算法设计和优化方法。
            </p>
            <ul class="space-y-2 mb-6">
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                数据结构基础
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                排序与搜索算法
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                动态规划
              </li>
              <li class="flex items-center gap-2 text-sm">
                <Icon icon="material-symbols:check-circle" class="w-4 h-4 text-green-500" />
                算法优化
              </li>
            </ul>
            <button 
              class="w-full px-4 py-2 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors"
            >
              查看完整路径
            </button>
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
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
