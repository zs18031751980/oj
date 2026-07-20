<script setup lang="ts">
import { computed, markRaw, onMounted, ref, watch } from 'vue';
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

const learningPaths: LearningPath[] = markRaw([
  { id: 'web-path', title: 'Web 开发路径', accent: 'from-cyan-500 to-sky-500', markdownFile: 'Web 开发路径.md' },
  { id: 'data-path', title: '数据科学路径', accent: 'from-emerald-500 to-lime-500', markdownFile: '数据科学路径.md' },
  { id: 'algorithm-path', title: '算法与竞赛路径', accent: 'from-amber-500 to-orange-500', markdownFile: '算法与竞赛路径.md' },
]);

const courses: ResourceItem[] = markRaw([
  { id: 'js-guide', title: 'JavaScript 入门指南', duration: '', author: '', language: 'JavaScript', markdownFile: 'JavaScript 入门指南.md' },
  { id: 'python-data', title: 'Python 数据分析实战', duration: '', author: '', language: 'Python', markdownFile: 'Python 数据分析实战.md' },
  { id: 'todo-project', title: 'Web 项目练习：Todo 应用', duration: '', author: '', language: 'JavaScript', markdownFile: 'Web 项目练习：Todo 应用.md' },
  { id: 'algorithm-basic', title: '算法', duration: '', author: '', language: 'C++', markdownFile: '算法.md' },
  { id: 'vue-components', title: 'Vue 组件化开发', duration: '', author: '', language: 'Vue', markdownFile: 'Vue 组件化开发.md' },
  { id: 'oj-strategy', title: 'agent开发', duration: '', author: '', language: '通用', markdownFile: 'agent开发.md' },
]);

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

const openResource = async (resource: LearnResource) => {
  await router.push({ path: '/learn', query: { doc: resource.id } });
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
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.24),_transparent_34%),radial-gradient(circle_at_85%_18%,_rgba(250,204,21,0.18),_transparent_22%),linear-gradient(180deg,_#ecfeff_0%,_#f8fafc_52%,_#f8fafc_100%)] text-slate-950 dark:bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_32%),radial-gradient(circle_at_85%_18%,_rgba(250,204,21,0.08),_transparent_22%),linear-gradient(180deg,_#020617_0%,_#020617_100%)] dark:text-slate-50">
    <template v-if="!isDetailMode">
      <section v-once class="learn-hero border-b border-slate-200/60 bg-white/60 backdrop-blur-2xl dark:border-slate-800/50 dark:bg-slate-950/50">
        <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="max-w-3xl">
              <p class="learn-eyebrow text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Learning Hub</p>
              <h1 class="mt-3 text-4xl font-black tracking-tight sm:text-5xl">路径、资料、练习连成一条线。</h1>
            </div>

            <button class="learn-primary-button inline-flex w-fit self-center items-center gap-2 rounded-full bg-slate-950 px-6 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300" @click="router.push('/playground')">
              <Icon icon="material-symbols:code" class="h-5 w-5" />
              去编辑器练习
            </button>
          </div>
        </div>
      </section>

      <section class="learn-path-section mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div class="paths-panel rounded-[2rem] border border-slate-200 bg-white/85 p-8 shadow-xl shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-800/85 dark:shadow-black/20 lg:p-10">
          <div class="section-heading mb-8">
            <h2 class="text-2xl font-black tracking-tight">学习路径建议</h2>
            <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
              如果还没确定从哪里开始，可以先按下面的路径走。
            </p>
          </div>

          <div class="path-grid grid gap-6 lg:grid-cols-3">
            <article
              v-for="path in learningPaths"
              :key="path.title"
              class="path-card"
            >
              <div class="path-card-topline">
                <span class="path-index">PATH</span>
                <span class="path-status">START HERE</span>
              </div>
              <h3 class="mt-0 text-2xl font-black tracking-tight">{{ path.title }}</h3>
              <p class="mt-5 text-sm leading-7 text-slate-600 dark:text-slate-300">
                {{ cardInfoMap[path.id]?.description || '' }}
              </p>
              <button
                class="mt-auto inline-flex self-start items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300"
                @click="openResource(path)"
              >
                <Icon icon="material-symbols:open-in-new" class="h-4 w-4" />
                查看路径
              </button>
            </article>
          </div>
        </div>
      </section>

      <section class="courses-section mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8 lg:pb-24">
        <div class="section-heading mb-6 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-black tracking-tight">推荐课程</h2>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">当前共展示 {{ filteredCourses.length }} 个学习项。</p>
          </div>
        </div>

        <div class="course-grid grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          <article v-for="(course, index) in filteredCourses" :key="course.id" class="course-card">
            <div class="course-card-topline flex items-center gap-2">
              <span class="course-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <span class="pill cyan">{{ course.language }}</span>
            </div>
            <h3 class="mt-5 text-2xl font-black tracking-tight">{{ course.title }}</h3>
            <p class="mt-5 mb-5 text-sm leading-7 text-slate-600 dark:text-slate-300">
              {{ cardInfoMap[course.id]?.description || '' }}
            </p>
            <button
              class="mt-auto inline-flex self-start items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white transition hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300"
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
      <section class="learn-detail mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <div class="detail-toolbar mb-6 flex flex-wrap items-center justify-between gap-4">
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

        <div class="detail-document overflow-hidden rounded-[2rem] border border-slate-200 bg-white/85 shadow-xl shadow-slate-200/60 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-800/85 dark:shadow-black/20">
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

    <div v-if="isDetailMode" class="border-t border-slate-200/60 bg-white/60 backdrop-blur-2xl dark:border-slate-800/50 dark:bg-slate-950/50">
    </div><template v-if="!isDetailMode">
      <footer class="border-t border-slate-200/60 bg-white/60 backdrop-blur-2xl dark:border-slate-800/50 dark:bg-slate-950/50">
        <div class="mx-auto max-w-7xl px-4 py-6 text-center text-sm text-slate-400 dark:text-slate-500">
          Let Coding — Learn
        </div>
      </footer>
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

.min-h-screen {
  --learn-border: #c7d2da;
  --learn-muted: #60717d;
  --learn-accent: #0e7490;
  background: #e8ecef !important;
}

.learn-hero {
  position: relative;
  overflow: hidden;
  background: #f1f4f6 !important;
}

.learn-hero::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: "";
  opacity: 0.42;
  background-image:
    linear-gradient(rgba(14, 116, 144, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14, 116, 144, 0.08) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: linear-gradient(90deg, #000, transparent 78%);
}

.learn-hero > div {
  position: relative;
  z-index: 1;
}

.learn-eyebrow {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 0.28em;
}

.learn-hero-title {
  max-width: 48rem;
  font-size: clamp(2.25rem, 5vw, 4.5rem) !important;
  line-height: 1.05;
}

.learn-primary-button {
  box-shadow: 0 12px 24px rgba(8, 145, 178, 0.22);
}

.learn-path-section,
.courses-section {
  padding-top: 3.5rem !important;
}

.paths-panel {
  border-radius: 0.75rem !important;
  border-color: var(--learn-border) !important;
  background: #f7f9fa !important;
  box-shadow: 0 20px 50px rgba(51, 65, 85, 0.1) !important;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
}

.section-heading > div:first-child {
  position: relative;
  padding-left: 1rem;
}

.section-heading > div:first-child::before {
  position: absolute;
  top: 0.25rem;
  bottom: 0.25rem;
  left: 0;
  width: 3px;
  content: "";
  background: #06b6d4;
}

.path-card,
.course-card {
  position: relative;
  overflow: hidden;
  border-radius: 0.75rem !important;
  border-color: var(--learn-border) !important;
  transition:
    transform 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.path-card {
  min-height: 19rem !important;
  background: #eef3f6 !important;
  padding: 1.5rem !important;
}

.course-card {
  min-height: 18rem !important;
  background: #f7f9fa !important;
  padding: 1.5rem !important;
}

.path-card::before,
.course-card::before {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  content: "";
  background: #22d3ee;
  transform: scaleX(0.22);
  transform-origin: left;
  transition: transform 0.25s ease;
}

.path-card:nth-child(2)::before {
  background: #34d399;
}

.path-card:nth-child(3)::before {
  background: #f59e0b;
}

.path-card:hover,
.course-card:hover {
  transform: translateY(-4px);
  border-color: #67e8f9 !important;
  box-shadow: 0 18px 35px rgba(51, 65, 85, 0.14) !important;
}

.path-card:hover::before,
.course-card:hover::before {
  transform: scaleX(1);
}

.path-card-topline,
.course-card-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.path-index,
.course-index,
.path-status {
  color: #0e7490;
  font: 800 0.68rem/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.path-status {
  color: #7a8b96;
  font-size: 0.6rem;
}

.course-index {
  color: #7a8b96;
}

.path-card h3,
.course-card h3 {
  line-height: 1.2;
}

.path-card p,
.course-card p {
  color: var(--learn-muted) !important;
}

.pill.cyan {
  border: 1px solid #9bd9e7;
  background: #e4f8fb !important;
  color: #0e7490 !important;
}

.learn-detail {
  min-height: calc(100vh - var(--header-h, 5rem));
}

.detail-toolbar {
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--learn-border);
}

.detail-document {
  border-radius: 0.75rem !important;
  border-color: var(--learn-border) !important;
  background: #f7f9fa !important;
  box-shadow: 0 20px 50px rgba(51, 65, 85, 0.1) !important;
}

html.dark .min-h-screen {
  --learn-border: #35414a;
  --learn-muted: #9aa9b3;
  --learn-accent: #67e8f9;
  background: #101418 !important;
}

html.dark .learn-hero {
  background: #151b20 !important;
}

html.dark .learn-hero::after {
  opacity: 0.3;
  background-image:
    linear-gradient(rgba(103, 232, 249, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(103, 232, 249, 0.08) 1px, transparent 1px);
}

html.dark .paths-panel {
  border-color: #35414a !important;
  background: #151b20 !important;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.22) !important;
}

html.dark .path-card {
  border-color: #35414a !important;
  background: #0f161c !important;
}

html.dark .course-card {
  border-color: #35414a !important;
  background: #151b20 !important;
  box-shadow: none !important;
}

html.dark .path-card:hover,
html.dark .course-card:hover {
  border-color: #0891b2 !important;
  box-shadow: 0 18px 35px rgba(0, 0, 0, 0.28) !important;
}

html.dark .pill.cyan {
  border-color: #155e75;
  background: #083344 !important;
  color: #67e8f9 !important;
}

html.dark .detail-toolbar {
  border-color: #35414a;
}

html.dark .detail-document {
  border-color: #35414a !important;
  background: #151b20 !important;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.22) !important;
}

@media (max-width: 640px) {
  .learn-hero-title {
    font-size: clamp(2.2rem, 12vw, 3.4rem) !important;
  }

  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .paths-panel {
    padding: 1.25rem !important;
  }

  .path-card,
  .course-card {
    min-height: 16rem !important;
  }
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
