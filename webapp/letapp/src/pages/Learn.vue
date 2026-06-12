<script setup lang="ts">
import { computed, ref } from 'vue';
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const categories = [
  { id: 'all', name: '全部', icon: 'material-symbols:category', accent: 'from-slate-200 to-slate-100 dark:from-slate-700 dark:to-slate-800' },
  { id: 'beginner', name: '入门教程', icon: 'material-symbols:school', accent: 'from-emerald-200 to-lime-100 dark:from-emerald-950 dark:to-lime-950' },
  { id: 'advanced', name: '进阶专题', icon: 'material-symbols:rocket-launch', accent: 'from-cyan-200 to-sky-100 dark:from-cyan-950 dark:to-sky-950' },
  { id: 'project', name: '实战项目', icon: 'material-symbols:build', accent: 'from-amber-200 to-orange-100 dark:from-amber-950 dark:to-orange-950' },
  { id: 'algorithm', name: '算法训练', icon: 'material-symbols:calculate', accent: 'from-fuchsia-200 to-violet-100 dark:from-fuchsia-950 dark:to-violet-950' },
];

const courses = [
  {
    id: 1,
    title: 'JavaScript 入门指南',
    description: '从变量、函数和 DOM 基础开始，适合第一次正式接触前端编程的同学。',
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
    description: '围绕数据清洗、可视化和简单分析案例，建立完整的 Python 数据处理思路。',
    category: 'advanced',
    level: '进阶',
    duration: '15 小时',
    author: 'Let Coding',
    language: 'Python',
  },
  {
    id: 3,
    title: 'Web 项目练习：Todo 应用',
    description: '从布局、交互到数据存储，一步步完成一个完整的小型前端项目。',
    category: 'project',
    level: '入门',
    duration: '8 小时',
    author: 'Let Coding',
    language: 'JavaScript',
  },
  {
    id: 4,
    title: '算法基础：排序与搜索',
    description: '理解常见排序与搜索算法，建立时间复杂度和调试思维。',
    category: 'algorithm',
    level: '入门',
    duration: '10 小时',
    author: 'Let Coding',
    language: 'Python',
  },
  {
    id: 5,
    title: 'Vue 组件化开发',
    description: '学习如何拆分页面、设计组件边界，并逐步建立中型项目结构。',
    category: 'advanced',
    level: '进阶',
    duration: '11 小时',
    author: 'Let Coding',
    language: 'Vue',
  },
  {
    id: 6,
    title: 'OJ 刷题策略：从输入输出到调试',
    description: '围绕在线评测常见问题，提升题目阅读、边界处理和错误定位效率。',
    category: 'algorithm',
    level: '进阶',
    duration: '6 小时',
    author: 'Let Coding',
    language: '通用',
  },
];

const learningPaths = [
  {
    title: 'Web 开发路径',
    description: '从 HTML、CSS、JavaScript 开始，逐步进阶到 Vue、接口联调和项目交付。',
    accent: 'from-cyan-500 to-sky-500',
    points: ['HTML 与 CSS 基础', 'JavaScript 核心语法', 'Vue 组件开发', '接口联调与部署'],
  },
  {
    title: '数据科学路径',
    description: '围绕 Python 和常用数据处理工具，打通分析、可视化和基础建模思路。',
    accent: 'from-emerald-500 to-lime-500',
    points: ['Python 编程基础', 'pandas 与 numpy', '数据可视化', '模型与实验记录'],
  },
  {
    title: '算法与竞赛路径',
    description: '适合准备笔试、面试和 OJ 刷题训练，强调解题思路与复杂度意识。',
    accent: 'from-amber-500 to-orange-500',
    points: ['数据结构基础', '搜索与排序', '动态规划专题', '题解复盘与优化'],
  },
];

const selectedCategory = ref('all');

const filteredCourses = computed(() => (
  selectedCategory.value === 'all'
    ? courses
    : courses.filter((course) => course.category === selectedCategory.value)
));

const startLearning = (course: typeof courses[number]) => {
  if (course.url) {
    globalThis.open(course.url, '_blank', 'noopener,noreferrer');
    return;
  }

  router.push('/playground');
};
</script>

<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,_#f8fafc_0%,_#f8fafc_100%)] text-slate-950 dark:bg-[linear-gradient(180deg,_#020617_0%,_#020617_100%)] dark:text-slate-50">
    <section class="border-b border-slate-200/80 bg-white/80 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/80">
      <div class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div class="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div class="max-w-3xl">
            <p class="text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Learning Hub</p>
            <h1 class="mt-3 text-4xl font-black tracking-tight sm:text-5xl">把课程入口、练习路径和项目练手放在一起。</h1>
            <p class="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
              这里整理了适合 Let Coding 用户的学习资源。你可以按阶段筛选，也可以直接从一条完整路径开始。
            </p>
          </div>

          <button class="inline-flex w-fit items-center gap-2 rounded-full bg-slate-950 px-6 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300" @click="router.push('/playground')">
            <Icon icon="material-symbols:code" class="h-5 w-5" />
            先去写点代码
          </button>
        </div>

        <div class="mt-8 flex flex-wrap gap-3">
          <button
            v-for="category in categories"
            :key="category.id"
            class="category-chip"
            :class="selectedCategory === category.id ? 'category-chip-active' : 'category-chip-idle'"
            @click="selectedCategory = category.id"
          >
            <span class="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br" :class="category.accent">
              <Icon :icon="category.icon" class="h-5 w-5 text-slate-900 dark:text-white" />
            </span>
            {{ category.name }}
          </button>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black tracking-tight">推荐课程</h2>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">当前共展示 {{ filteredCourses.length }} 个学习项。</p>
        </div>
      </div>

      <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        <article v-for="course in filteredCourses" :key="course.id" class="course-card">
          <div class="flex items-center gap-2">
            <span class="pill cyan">{{ course.language }}</span>
            <span class="pill slate">{{ course.level }}</span>
          </div>
          <h3 class="mt-5 text-2xl font-black tracking-tight">{{ course.title }}</h3>
          <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
            {{ course.description }}
          </p>
          <div class="mt-6 flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
            <span class="inline-flex items-center gap-1">
              <Icon icon="material-symbols:person" class="h-4 w-4" />
              {{ course.author }}
            </span>
            <span class="inline-flex items-center gap-1">
              <Icon icon="material-symbols:schedule" class="h-4 w-4" />
              {{ course.duration }}
            </span>
          </div>
          <button class="mt-6 inline-flex items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300" @click="startLearning(course)">
            <Icon icon="material-symbols:arrow-forward" class="h-4 w-4" />
            开始学习
          </button>
        </article>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8 lg:pb-24">
      <div class="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20 lg:p-10">
        <div class="mb-8">
          <h2 class="text-2xl font-black tracking-tight">学习路径建议</h2>
          <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
            如果你不知道从哪里开始，可以先按下面的路径走，边学边在编辑器里验证。
          </p>
        </div>

        <div class="grid gap-6 lg:grid-cols-3">
          <article v-for="path in learningPaths" :key="path.title" class="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-6 dark:border-slate-800 dark:bg-slate-950">
            <div class="inline-flex rounded-full bg-gradient-to-r px-4 py-2 text-xs font-black uppercase tracking-[0.22em] text-white" :class="path.accent">
              Path
            </div>
            <h3 class="mt-5 text-2xl font-black tracking-tight">{{ path.title }}</h3>
            <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
              {{ path.description }}
            </p>
            <ul class="mt-6 space-y-3">
              <li v-for="point in path.points" :key="point" class="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-200">
                <Icon icon="material-symbols:check-circle" class="mt-0.5 h-5 w-5 text-cyan-500" />
                <span>{{ point }}</span>
              </li>
            </ul>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.category-chip {
  @apply inline-flex items-center gap-3 rounded-full border px-4 py-2.5 text-sm font-black transition;
}

.category-chip-idle {
  @apply border-slate-200 bg-white text-slate-700 hover:-translate-y-0.5 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800;
}

.category-chip-active {
  @apply border-cyan-300 bg-cyan-50 text-cyan-700 shadow-lg shadow-cyan-100 dark:border-cyan-900 dark:bg-cyan-950/50 dark:text-cyan-300 dark:shadow-black/0;
}

.course-card {
  @apply rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60 transition hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20;
}

.pill {
  @apply inline-flex rounded-full px-3 py-1 text-xs font-black;
}

.pill.cyan {
  @apply bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300;
}

.pill.slate {
  @apply bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300;
}
</style>
