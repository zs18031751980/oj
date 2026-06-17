<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';
import MarkdownComponent from '../components/MarkdownComponent.vue';

interface ResourceItem {
  id: string;
  title: string;
  duration: string;
  author: string;
  language: string;
  markdownFile: string;
}

interface LearningPath {
  id: string;
  title: string;
  accent: string;
  markdownFile: string;
}

interface CardInfo {
  description: string;
  points: string[];
}

interface MarkdownContent {
  title?: string;
  date?: string;
  watch?: number;
  content: string;
}

type LearnResource = { id: string; title: string; markdownFile: string };

const route = useRoute();
const router = useRouter();

const learningPaths: LearningPath[] = [
  { id: 'web-path', title: 'Web 开发路径', accent: 'from-cyan-500 to-sky-500', markdownFile: 'Web 开发路径.md' },
  { id: 'data-path', title: '数据科学路径', accent: 'from-emerald-500 to-lime-500', markdownFile: '数据科学路径.md' },
  { id: 'algorithm-path', title: '算法与竞赛路径', accent: 'from-amber-500 to-orange-500', markdownFile: '算法与竞赛路径.md' },
];

const courses: ResourceItem[] = [
  { id: 'js-guide', title: 'JavaScript 入门指南', duration: '', author: '', language: 'JavaScript', markdownFile: 'JavaScript 入门指南.md' },
  { id: 'python-data', title: 'Python 数据分析实战', duration: '', author: '', language: 'Python', markdownFile: 'Python 数据分析实战.md' },
  { id: 'todo-project', title: 'Web 项目练习：Todo 应用', duration: '', author: '', language: 'JavaScript', markdownFile: 'Web 项目练习：Todo 应用.md' },
  { id: 'algorithm-basic', title: '算法', duration: '', author: '', language: 'C++', markdownFile: '算法.md' },
  { id: 'vue-components', title: 'Vue 组件化开发', duration: '', author: '', language: 'Vue', markdownFile: 'Vue 组件化开发.md' },
  { id: 'oj-strategy', title: 'agent开发', duration: '', author: '', language: '通用', markdownFile: 'agent开发.md' },
];

const selectedTitle = ref('');
const selectedResource = ref<MarkdownContent | undefined>();
const isLoadingDoc = ref(false);
const docError = ref('');

const allResources = [...learningPaths, ...courses];

const cardInfoMap = ref<Record<string, CardInfo>>({});

function parseCardInfo(markdown: string): CardInfo {
  const lines = markdown.split('\n');
  let description = '';
  const points: string[] = [];
  let heading = '';

  const descHeadings = ['路径说明', '课程目标', '项目目标', '适合谁'];

  for (const raw of lines) {
    const line = raw.trim();

    if (line.startsWith('## ')) {
      heading = line.slice(2).trim();
      continue;
    }

    if (!description && descHeadings.some(h => heading.includes(h)) && line && !line.startsWith('#')) {
      description = line.replace(/^[-*]\s*/, '');
    }

    if (line.startsWith('### ')) {
      const point = line.replace(/^###\s*\d*\.?\s*/, '').trim();
      if (point) {
        points.push(point);
      }
    }
  }

  return { description, points };
}

async function loadCardData() {
  const results = await Promise.all(
    allResources.map(async (resource) => {
      try {
        const res = await fetch(`/learn/${encodeURIComponent(resource.markdownFile)}`);
        const markdown = await res.text();
        return { id: resource.id, ...parseCardInfo(markdown) };
      } catch {
        return { id: resource.id, description: '', points: [] };
      }
    })
  );
  const map: Record<string, CardInfo> = {};
  for (const r of results) {
    map[r.id] = { description: r.description, points: r.points };
  }
  cardInfoMap.value = map;
}

const filteredCourses = computed(() => courses);

const currentDocId = computed(() => {
  const raw = route.query.doc;
  return Array.isArray(raw) ? raw[0] || '' : String(raw || '');
});

const isDetailMode = computed(() => Boolean(currentDocId.value));
const currentResource = computed(() => (
  currentDocId.value ? findResourceById(currentDocId.value) : undefined
));

const currentMarkdownFile = computed(() => currentResource.value?.markdownFile || '');

const findResourceById = (id: string) => allResources.find((item) => item.id === id || item.title === id);

const getResourceLink = (resource: LearnResource) => {
  const resolved = router.resolve({ path: '/learn', query: { doc: resource.id } });
  return resolved.href;
};

const openResource = (resource: LearnResource) => {
  const url = getResourceLink(resource);
  window.open(url, '_blank', 'noopener,noreferrer');
};

const goBackToList = async () => {
  await router.push('/learn');
};

const downloadCurrentMarkdown = () => {
  const content = selectedResource.value?.content;
  const markdownFile = currentMarkdownFile.value;

  if (!markdownFile || !content) {
    return;
  }

  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = markdownFile;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(objectUrl);
};

const loadMarkdown = async (resourceId: string) => {
  const resource = findResourceById(resourceId);
  if (!resource) {
    selectedResource.value = undefined;
    docError.value = '未找到对应的学习资料。';
    return;
  }

  isLoadingDoc.value = true;
  docError.value = '';
  selectedTitle.value = resource.title;

  try {
    const response = await fetch(`/learn/${encodeURIComponent(resource.markdownFile)}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const markdown = await response.text();
    selectedResource.value = {
      content: markdown,
    };
  } catch (error) {
    selectedResource.value = undefined;
    docError.value = `加载资料失败：${error instanceof Error ? error.message : '未知错误'}`;
  } finally {
    isLoadingDoc.value = false;
  }
};

onMounted(async () => {
  if (currentDocId.value) {
    await loadMarkdown(currentDocId.value);
  }
  await loadCardData();
});

watch(
  () => currentDocId.value,
  async (resourceId) => {
    if (!resourceId) {
      selectedTitle.value = '';
      selectedResource.value = undefined;
      docError.value = '';
      return;
    }

    await loadMarkdown(resourceId);
  },
);
</script>

<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,_#f8fafc_0%,_#f8fafc_100%)] text-slate-950 dark:bg-[linear-gradient(180deg,_#020617_0%,_#020617_100%)] dark:text-slate-50">
    <template v-if="!isDetailMode">
      <section class="border-b border-slate-200/80 bg-white/80 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/80">
        <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="max-w-3xl">
              <p class="text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Learning Hub</p>
              <h1 class="mt-3 text-4xl font-black tracking-tight sm:text-5xl">把路径、资料和练习入口连成一条线。</h1>
            </div>

            <button class="inline-flex w-fit self-center items-center gap-2 rounded-full bg-slate-950 px-6 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300" @click="router.push('/playground')">
              <Icon icon="material-symbols:code" class="h-5 w-5" />
              先去写点代码
            </button>
          </div>
        </div>
      </section>

      <section class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div class="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20 lg:p-10">
          <div class="mb-8">
            <h2 class="text-2xl font-black tracking-tight">学习路径建议</h2>
            <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
              如果你还没确定从哪里开始，可以先按下面的路径走。
            </p>
          </div>

          <div class="grid gap-6 lg:grid-cols-3">
            <article
              v-for="path in learningPaths"
              :key="path.title"
              class="path-card"
            >
              <h3 class="mt-0 text-2xl font-black tracking-tight">{{ path.title }}</h3>
              <p class="mt-5 text-sm leading-7 text-slate-600 dark:text-slate-300">
                {{ cardInfoMap[path.id]?.description || '' }}
              </p>
              <button
                class="mt-auto pt-2 inline-flex self-start items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300"
                @click="openResource(path)"
              >
                <Icon icon="material-symbols:open-in-new" class="h-4 w-4" />
                查看路径
              </button>
            </article>
          </div>
        </div>
      </section>

      <section class="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8 lg:pb-24">
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
            </div>
            <h3 class="mt-5 text-2xl font-black tracking-tight">{{ course.title }}</h3>
            <p class="mt-5 text-sm leading-7 text-slate-600 dark:text-slate-300">
              {{ cardInfoMap[course.id]?.description || '' }}
            </p>
            <button
              class="mt-auto pt-2 inline-flex items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300"
              @click="openResource(course)"
            >
              <Icon icon="material-symbols:arrow-forward" class="h-4 w-4" />
              查看课程
            </button>
          </article>
        </div>
      </section>
    </template>

    <template v-else>
      <section class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
          <button
            class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            @click="goBackToList"
          >
            <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4" />
            返回学习资源
          </button>

          <button
            class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isLoadingDoc || !selectedResource"
            @click="downloadCurrentMarkdown"
          >
            <Icon icon="material-symbols:download-rounded" class="h-4 w-4" />
            导出 Markdown
          </button>

          <button
            class="inline-flex items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300"
            @click="router.push('/playground')"
          >
            <Icon icon="material-symbols:code" class="h-4 w-4" />
            去编辑器练习
          </button>
        </div>

        <div class="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-xl shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20">
          <div v-if="isLoadingDoc" class="flex min-h-[320px] items-center justify-center p-8 text-slate-500 dark:text-slate-400">
            正在加载资料内容...
          </div>
          <div v-else-if="docError" class="flex min-h-[320px] items-center justify-center p-8 text-center text-rose-500">
            {{ docError }}
          </div>
          <MarkdownComponent v-else :content="selectedResource" :show-nav="false" :show-heading-links="false" />
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.course-card {
  @apply flex min-h-[20rem] flex-col rounded-[1.75rem] border border-slate-200 bg-white p-8 shadow-lg shadow-slate-200/60 transition hover:-translate-y-1 hover:shadow-xl;
}

.path-card {
  @apply flex min-h-[20rem] flex-col rounded-[1.75rem] border border-slate-200 bg-slate-50 p-8 transition hover:-translate-y-1 hover:border-cyan-300 hover:shadow-lg;
}

.pill {
  @apply inline-flex rounded-full px-3 py-1 text-xs font-black;
}

.pill.cyan {
  @apply bg-cyan-100 text-cyan-700;
}

.pill.slate {
  @apply bg-slate-100 text-slate-600;
}
</style>

<style>
html.dark .course-card {
  border-color: #1e293b !important;
  background-color: #0f172a !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2) !important;
}

html.dark .path-card {
  border-color: #1e293b !important;
  background-color: #020617 !important;
}

html.dark .path-card:hover {
  border-color: #155e75 !important;
}

html.dark .pill.cyan {
  background-color: #083344 !important;
  color: #67e8f9 !important;
}

html.dark .pill.slate {
  background-color: #1e293b !important;
  color: #cbd5e1 !important;
}

html:not(.dark) .path-card {
  background-color: #f8fafc !important;
  border-color: #e2e8f0 !important;
  color: #0f172a !important;
}

html:not(.dark) .course-card {
  background-color: #ffffff !important;
  border-color: #e2e8f0 !important;
  color: #0f172a !important;
}

html:not(.dark) .path-card p,
html:not(.dark) .course-card p {
  color: #475569 !important;
}

html:not(.dark) .path-card li,
html:not(.dark) .course-card .mt-6 {
  color: #334155 !important;
}

html:not(.dark) .path-card button,
html:not(.dark) .course-card button {
  background-color: #0ea5e9 !important;
  color: #ffffff !important;
}

html:not(.dark) .course-card button,
html:not(.dark) .course-card button * {
  color: #ffffff !important;
}

html.dark .path-card button,
html.dark .course-card button {
  background-color: #0ea5e9 !important;
  color: #ffffff !important;
}
</style>
