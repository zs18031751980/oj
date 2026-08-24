<script setup lang="ts">
import { computed, markRaw, onMounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';
import MarkdownComponent from '../components/MarkdownComponent.vue';

interface ChapterItem {
  id: string;
  title: string;
  label: string;
  summary: string;
  markdownFile: string;
}

interface LearnResource {
  id: string;
  title: string;
  markdownFile?: string;
  description?: string;
  chapters?: ChapterItem[];
}

interface ResourceItem extends LearnResource {
  duration: string;
  author: string;
  language: string;
}

interface LearningPath extends LearnResource {
  accent: string;
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

const route = useRoute();
const router = useRouter();

const learningPaths: LearningPath[] = markRaw([
  { id: 'web-path', title: 'Web 开发路径', accent: 'from-blue-500 to-sky-500', markdownFile: 'Web 开发路径.md' },
  { id: 'data-path', title: '数据科学路径', accent: 'from-emerald-500 to-lime-500', markdownFile: '数据科学路径.md' },
  { id: 'algorithm-path', title: '算法与竞赛路径', accent: 'from-amber-500 to-orange-500', markdownFile: '算法与竞赛路径.md' },
]);

const cLanguageChapters: ChapterItem[] = markRaw([
  { id: 'chapter-01', label: 'CHAPTER 01', title: '第一章：程序设计和 C 语言', summary: '认识程序、编译过程、C 程序结构与开发环境。', markdownFile: 'c-language/chapters/01-introduction.md' },
  { id: 'chapter-02', label: 'CHAPTER 02', title: '第二章：算法', summary: '理解算法特性、三种基本程序结构和流程图。', markdownFile: 'c-language/chapters/02-algorithms.md' },
  { id: 'chapter-03', label: 'CHAPTER 03', title: '第三章：顺序程序设计', summary: '掌握数据类型、变量、运算符以及标准输入输出。', markdownFile: 'c-language/chapters/03-sequential-programming.md' },
  { id: 'chapter-04', label: 'CHAPTER 04', title: '第四章：选择结构程序设计', summary: '使用 if、switch 和逻辑运算处理分支判断。', markdownFile: 'c-language/chapters/04-selection-structure.md' },
  { id: 'chapter-05', label: 'CHAPTER 05', title: '第五章：循环结构程序设计', summary: '学习 for、while、循环控制与常见算法模式。', markdownFile: 'c-language/chapters/05-loop-structure.md' },
  { id: 'chapter-06', label: 'CHAPTER 06', title: '第六章：利用数组处理批量数据', summary: '处理一维数组、二维数组、字符串与排序问题。', markdownFile: 'c-language/chapters/06-arrays.md' },
  { id: 'chapter-07', label: 'CHAPTER 07', title: '第七章：用函数实现模块化设计', summary: '理解函数调用、参数传递、递归与变量作用域。', markdownFile: 'c-language/chapters/07-functions.md' },
  { id: 'chapter-08', label: 'CHAPTER 08', title: '第八章：善于利用指针', summary: '建立地址与指针概念，学习数组指针和动态内存。', markdownFile: 'c-language/chapters/08-pointers.md' },
  { id: 'chapter-09', label: 'CHAPTER 09', title: '第九章：用户自己建立数据类型', summary: '使用结构体、共用体、枚举、typedef 和链表。', markdownFile: 'c-language/chapters/09-custom-data-types.md' },
  { id: 'chapter-10', label: 'CHAPTER 10', title: '第十章：对文件的输入输出', summary: '掌握文件打开、读写、关闭和定位等常用操作。', markdownFile: 'c-language/chapters/10-file-io.md' },
  { id: 'cpp-extension', label: 'EXTENSION', title: 'C++ 拓展：知识点详解', summary: '从 C 过渡到 C++，了解面向对象、STL 与泛型。', markdownFile: 'c-language/chapters/11-cpp-extension.md' },
]);

const courses: ResourceItem[] = markRaw([
  { id: 'c-language-guide', title: 'C 语言知识点总结', description: '适合零基础学习 C 语言、按章节系统梳理语法与核心概念，并继续了解 C++ 基础知识的同学。', duration: '', author: '陈智祥 ZnS', language: 'C', chapters: cLanguageChapters },
  { id: 'js-guide', title: 'JavaScript 入门指南', duration: '', author: '', language: 'JavaScript', markdownFile: 'JavaScript 入门指南.md' },
  { id: 'python-data', title: 'Python 数据分析实战', duration: '', author: '', language: 'Python', markdownFile: 'Python 数据分析实战.md' },
  { id: 'todo-project', title: 'Web 项目练习：Todo 应用', duration: '', author: '', language: 'JavaScript', markdownFile: 'Web 项目练习：Todo 应用.md' },
  { id: 'algorithm-basic', title: '算法', duration: '', author: '', language: 'C++', markdownFile: '算法.md' },
  { id: 'vue-components', title: 'Vue 组件化开发', duration: '', author: '', language: 'Vue', markdownFile: 'Vue 组件化开发.md' },
  { id: 'oj-strategy', title: 'Agent 开发', duration: '', author: '', language: '通用', markdownFile: 'agent开发.md' },
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

const CARD_INFO_CACHE_KEY = 'learn_card_info_cache_v1';

function readCardInfoCache(): Record<string, CardInfo> {
  try {
    const raw = localStorage.getItem(CARD_INFO_CACHE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

function writeCardInfoCache(map: Record<string, CardInfo>) {
  try {
    localStorage.setItem(CARD_INFO_CACHE_KEY, JSON.stringify(map));
  } catch {
    // ignore
  }
}

async function loadCardData() {
  const cache = readCardInfoCache();
  const results = await Promise.all(
    allResources.map(async (resource) => {
      if (resource.description) {
        return { id: resource.id, description: resource.description, points: [] };
      }

      if (!resource.markdownFile) {
        return { id: resource.id, description: '', points: [] };
      }

      const cached = cache[resource.id];
      if (cached && typeof cached.description === 'string') {
        return { id: resource.id, description: cached.description, points: cached.points || [] };
      }

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
  writeCardInfoCache(map);
}

const filteredCourses = computed(() => courses);

const currentDocId = computed(() => {
  const raw = route.query.doc;
  return Array.isArray(raw) ? raw[0] || '' : String(raw || '');
});

const currentChapterId = computed(() => {
  const raw = route.query.chapter;
  return Array.isArray(raw) ? raw[0] || '' : String(raw || '');
});

const isDetailMode = computed(() => Boolean(currentDocId.value));
const currentResource = computed(() => (
  currentDocId.value ? findResourceById(currentDocId.value) : undefined
));
const currentChapter = computed(() => (
  currentResource.value?.chapters?.find((chapter) => chapter.id === currentChapterId.value)
));
const isChapterDirectory = computed(() => Boolean(
  currentResource.value?.chapters?.length && !currentChapterId.value
));
const currentChapterIndex = computed(() => (
  currentResource.value?.chapters && currentChapter.value
    ? currentResource.value.chapters.findIndex((chapter) => chapter.id === currentChapter.value?.id)
    : -1
));
const previousChapter = computed(() => (
  currentChapterIndex.value > 0
    ? currentResource.value?.chapters?.[currentChapterIndex.value - 1]
    : undefined
));
const nextChapter = computed(() => (
  currentChapterIndex.value >= 0
    ? currentResource.value?.chapters?.[currentChapterIndex.value + 1]
    : undefined
));

const currentMarkdownFile = computed(() => currentChapter.value?.markdownFile || currentResource.value?.markdownFile || '');

const findResourceById = (id: string) => allResources.find((item) => item.id === id || item.title === id);

const getLearnFileUrl = (markdownFile: string) => (
  `/learn/${markdownFile.split('/').map((segment) => encodeURIComponent(segment)).join('/')}`
);

const openResource = async (resource: LearnResource) => {
  await router.push({ path: '/learn', query: { doc: resource.id } });
};

const openChapter = async (chapter: ChapterItem) => {
  await router.push({ path: '/learn', query: { doc: currentDocId.value, chapter: chapter.id } });
};

const goBackFromDetail = async () => {
  if (currentChapter.value) {
    await router.push({ path: '/learn', query: { doc: currentDocId.value } });
    return;
  }

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

const loadMarkdown = async (resourceId: string, chapterId: string = '') => {
  const resource = findResourceById(resourceId);
  if (!resource) {
    selectedResource.value = undefined;
    docError.value = '未找到对应的学习资料。';
    return;
  }

  if (resource.chapters?.length && !chapterId) {
    selectedTitle.value = resource.title;
    selectedResource.value = undefined;
    docError.value = '';
    isLoadingDoc.value = false;
    return;
  }

  const chapter = chapterId
    ? resource.chapters?.find((item) => item.id === chapterId)
    : undefined;

  if (chapterId && !chapter) {
    selectedResource.value = undefined;
    docError.value = '未找到对应的课程章节。';
    return;
  }

  const markdownFile = chapter?.markdownFile || resource.markdownFile;

  if (!markdownFile) {
    selectedResource.value = undefined;
    docError.value = '未找到对应的学习资料文件。';
    isLoadingDoc.value = false;
    return;
  }

  isLoadingDoc.value = true;
  docError.value = '';
  selectedTitle.value = chapter?.title || resource.title;

  try {
    const response = await fetch(getLearnFileUrl(markdownFile));
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

const searchQuery = ref('');
const activeCategory = ref('全部');

const categories = ['全部', 'C', 'JavaScript', 'Python', 'C++', 'Vue', '通用'];
const categoryCount = computed(() => {
  const map: Record<string, number> = {};
  for (const cat of categories) {
    if (cat === '全部') {
      map[cat] = allResources.length;
    } else {
      map[cat] = allResources.filter(r => 'language' in r && (r as ResourceItem).language === cat).length;
    }
  }
  return map;
});

const displayedCourses = computed(() => {
  let list = filteredCourses.value;
  if (activeCategory.value !== '全部') {
    list = list.filter(r => r.language === activeCategory.value);
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    list = list.filter(r => r.title.toLowerCase().includes(q) || (cardInfoMap.value[r.id]?.description || '').toLowerCase().includes(q));
  }
  return list;
});

const displayedPaths = computed(() => {
  if (activeCategory.value !== '全部') return [];
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    return learningPaths.filter(p => p.title.toLowerCase().includes(q) || (cardInfoMap.value[p.id]?.description || '').toLowerCase().includes(q));
  }
  return learningPaths;
});

const getLanguageColor = (lang: string) => {
  const map: Record<string, string> = {
    C: 'bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400',
    JavaScript: 'bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400',
    Python: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400',
    'C++': 'bg-violet-50 text-violet-600 dark:bg-violet-950/40 dark:text-violet-400',
    Vue: 'bg-teal-50 text-teal-600 dark:bg-teal-950/40 dark:text-teal-400',
    '通用': 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
  };
  return map[lang] || map['通用'];
};

onMounted(async () => {
  if (currentDocId.value) {
    await loadMarkdown(currentDocId.value, currentChapterId.value);
  }
  await loadCardData();
});

watch(
  () => [currentDocId.value, currentChapterId.value] as const,
  async ([resourceId, chapterId]) => {
    if (!resourceId) {
      selectedTitle.value = '';
      selectedResource.value = undefined;
      docError.value = '';
      return;
    }

    await loadMarkdown(resourceId, chapterId);
  },
);
</script>

<template>
  <div class="learn-page min-h-screen bg-[#F6F8FC] dark:bg-[#0F172A]">

    <!-- ===== 列表页 ===== -->
    <template v-if="!isDetailMode">
      <div class="app-container-with-sidebar py-6">

        <!-- 左侧导航 -->
        <aside class="app-sidebar-col">
          <div class="learn-sidebar">
            <!-- 顶部入口 -->
            <div class="sidebar-section">
              <div class="sidebar-section-title">学习资源</div>
            </div>

            <!-- 个人区域 -->
            <div class="sidebar-section">
              <button class="sidebar-item" @click="router.push('/learn')">
                <Icon icon="material-symbols:recommend" class="h-4 w-4 text-blue-500" />
                <span>精选推荐</span>
              </button>
              <button class="sidebar-item" @click="router.push('/learn')">
                <Icon icon="material-symbols:library-books" class="h-4 w-4 text-emerald-500" />
                <span>全部资源</span>
                <span class="sidebar-count">{{ allResources.length }}</span>
              </button>
              <button class="sidebar-item">
                <Icon icon="material-symbols:favorite" class="h-4 w-4 text-rose-500" />
                <span>我的收藏</span>
              </button>
              <button class="sidebar-item">
                <Icon icon="material-symbols:history" class="h-4 w-4 text-amber-500" />
                <span>最近浏览</span>
              </button>
              <button class="sidebar-item">
                <Icon icon="material-symbols:play-circle" class="h-4 w-4 text-violet-500" />
                <span>继续学习</span>
              </button>
            </div>

            <!-- 分类区域 -->
            <div class="sidebar-section">
              <div class="sidebar-section-title mt-2">资源分类</div>
              <button
                v-for="cat in categories"
                :key="cat"
                class="sidebar-item"
                :class="{ active: activeCategory === cat }"
                @click="activeCategory = cat"
              >
                <Icon :icon="cat === '全部' ? 'material-symbols:grid-view' : 'material-symbols:folder'" class="h-4 w-4" />
                <span>{{ cat === '全部' ? '全部资源' : cat }}</span>
                <span class="sidebar-count">{{ categoryCount[cat] || 0 }}</span>
              </button>
            </div>
          </div>
        </aside>

        <!-- 右侧主内容 -->
        <section class="min-w-0 flex-1">

          <!-- 标题区 -->
          <div class="mb-5 flex items-start justify-between gap-4">
            <div>
              <h1 class="text-[28px] font-black text-[#1E293B] dark:text-[#E5E7EB]">学习资源</h1>
              <p class="mt-1 text-sm text-[#64748B] dark:text-[#94A3B8]">路径、资料、练习连成一条线</p>
            </div>
            <div class="learn-stats-card">
              <span class="text-2xl font-black text-[#2563EB]">{{ allResources.length }}</span>
              <span class="text-xs text-[#64748B] dark:text-[#94A3B8]">个学习资源</span>
            </div>
          </div>

          <!-- 搜索栏 -->
          <div class="mb-5 flex items-center gap-3">
            <div class="learn-search">
              <Icon icon="material-symbols:search" class="h-5 w-5 text-[#94A3B8]" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索学习资源..."
                class="learn-search-input"
              />
            </div>
            <button class="ui-btn ui-btn-ghost ui-btn-sm" @click="router.push('/playground')">
              <Icon icon="material-symbols:code" class="h-4 w-4" />
              去编辑器练习
            </button>
          </div>

          <!-- 分类横向导航 -->
          <div class="mb-6 flex gap-2 overflow-x-auto pb-1">
            <button
              v-for="cat in categories"
              :key="cat"
              class="learn-cat-chip"
              :class="{ active: activeCategory === cat }"
              @click="activeCategory = cat"
            >
              {{ cat === '全部' ? '全部' : cat }}
              <span class="learn-cat-count">{{ categoryCount[cat] || 0 }}</span>
            </button>
          </div>

          <!-- 精选学习路径 -->
          <div v-if="displayedPaths.length" class="mb-8">
            <div class="mb-4 flex items-center gap-2">
              <Icon icon="material-symbols:route" class="h-5 w-5 text-[#2563EB]" />
              <h2 class="text-lg font-black text-[#1E293B] dark:text-[#E5E7EB]">学习路径</h2>
              <span class="ui-badge ui-badge-blue text-[10px]">推荐</span>
            </div>
            <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              <article
                v-for="(path, idx) in displayedPaths"
                :key="path.id"
                class="learn-path-card"
              >
                <div class="learn-path-cover" :class="['bg-gradient-to-br', path.accent]">
                  <span class="learn-path-badge">PATH {{ String(idx + 1).padStart(2, '0') }}</span>
                </div>
                <div class="learn-path-body">
                  <h3 class="text-base font-black text-[#1E293B] dark:text-[#E5E7EB]">{{ path.title }}</h3>
                  <p class="mt-2 line-clamp-2 text-sm text-[#64748B] dark:text-[#94A3B8]">
                    {{ cardInfoMap[path.id]?.description || '暂无简介' }}
                  </p>
                  <button class="learn-path-btn" @click="openResource(path)">
                    <Icon icon="material-symbols:open-in-new" class="h-3.5 w-3.5" />
                    查看路径
                  </button>
                </div>
              </article>
            </div>
          </div>

          <!-- 全部资源网格 -->
          <div>
            <div class="mb-4 flex items-center gap-2">
              <Icon icon="material-symbols:library-books" class="h-5 w-5 text-[#2563EB]" />
              <h2 class="text-lg font-black text-[#1E293B] dark:text-[#E5E7EB]">全部资源</h2>
              <span class="text-sm text-[#94A3B8]">（{{ displayedCourses.length }}）</span>
            </div>
            <div v-if="displayedCourses.length" class="learn-grid">
              <article
                v-for="(course, index) in displayedCourses"
                :key="course.id"
                class="learn-resource-card"
                @click="openResource(course)"
              >
                <div class="learn-card-top">
                  <span class="learn-card-index">{{ String(index + 1).padStart(2, '0') }}</span>
                  <span class="learn-card-lang" :class="getLanguageColor(course.language)">{{ course.language }}</span>
                </div>
                <h3 class="learn-card-title">{{ course.title }}</h3>
                <p class="learn-card-desc">
                  {{ cardInfoMap[course.id]?.description || '暂无简介' }}
                </p>
                <div class="learn-card-footer">
                  <span v-if="course.chapters" class="learn-card-meta">
                    <Icon icon="material-symbols:menu-book" class="h-3.5 w-3.5" />
                    {{ course.chapters.length }} 章节
                  </span>
                  <span class="learn-card-meta">
                    <Icon icon="material-symbols:arrow-forward" class="h-3.5 w-3.5" />
                  </span>
                </div>
              </article>
            </div>
            <div v-else class="ui-empty mt-4">
              <Icon icon="material-symbols:search-off" class="mb-2 h-10 w-10 text-[#CBD5E1] dark:text-[#475569]" />
              <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">没有找到匹配的资源</p>
              <p class="text-sm text-[#94A3B8]">试试其他关键词或分类</p>
            </div>
          </div>
        </section>
      </div>
    </template>

    <!-- ===== 详情页 ===== -->
    <template v-else>
      <div class="app-container py-6 lg:py-10">

        <!-- 工具栏 -->
        <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
          <button class="learn-back-btn" @click="goBackFromDetail">
            <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4" />
            {{ currentChapter ? '返回课程目录' : '返回学习资源' }}
          </button>

          <div class="flex items-center gap-3">
            <button
              v-if="!isChapterDirectory"
              class="learn-back-btn"
              :disabled="isLoadingDoc || !selectedResource"
              @click="downloadCurrentMarkdown"
            >
              <Icon icon="material-symbols:download-rounded" class="h-4 w-4" />
              导出 Markdown
            </button>
            <button class="ui-btn-primary-sm" @click="router.push('/playground')">
              <Icon icon="material-symbols:code" class="h-4 w-4" />
              去编辑器练习
            </button>
          </div>
        </div>

        <!-- 章节目录模式 -->
        <div v-if="isChapterDirectory" class="learn-chapter-directory">
          <header class="mb-8">
            <p class="chapter-kicker">C LANGUAGE · {{ currentResource?.chapters?.length }} CHAPTERS</p>
            <h1 class="text-[28px] font-black text-[#1E293B] dark:text-[#E5E7EB]">C 语言知识点总结</h1>
            <p class="mt-2 text-sm text-[#64748B] dark:text-[#94A3B8]">按章节逐步学习 C 语言核心知识，每章内容在独立页面中阅读。</p>
          </header>

          <div class="chapter-grid">
            <button
              v-for="chapter in currentResource?.chapters"
              :key="chapter.id"
              class="chapter-card"
              @click="openChapter(chapter)"
            >
              <span class="chapter-label">{{ chapter.label }}</span>
              <h2>{{ chapter.title }}</h2>
              <p>{{ chapter.summary }}</p>
              <span class="chapter-open-icon">
                <Icon icon="material-symbols:arrow-forward-rounded" class="h-5 w-5" />
              </span>
            </button>
          </div>
        </div>

        <!-- Markdown 内容模式 -->
        <template v-else>
          <div class="learn-document">
            <div v-if="isLoadingDoc" class="flex min-h-[320px] items-center justify-center p-8 text-[#94A3B8]">
              正在加载资料内容...
            </div>
            <div v-else-if="docError" class="flex min-h-[320px] items-center justify-center p-8 text-center text-rose-500">
              {{ docError }}
            </div>
            <MarkdownComponent v-else :content="selectedResource" :show-nav="true" :show-heading-links="true" />
          </div>

          <!-- 章节导航 -->
          <nav v-if="currentChapter" class="chapter-pagination" aria-label="章节导航">
            <button
              class="chapter-nav-btn"
              :disabled="!previousChapter"
              @click="previousChapter && openChapter(previousChapter)"
            >
              <Icon icon="material-symbols:arrow-back-rounded" class="h-5 w-5" />
              <span>{{ previousChapter?.title || '已经是第一章' }}</span>
            </button>

            <button class="chapter-directory-btn" title="返回课程目录" @click="goBackFromDetail">
              <Icon icon="material-symbols:format-list-bulleted-rounded" class="h-5 w-5" />
              <span>课程目录</span>
            </button>

            <button
              class="chapter-nav-btn chapter-nav-next"
              :disabled="!nextChapter"
              @click="nextChapter && openChapter(nextChapter)"
            >
              <span>{{ nextChapter?.title || '已经是最后一章' }}</span>
              <Icon icon="material-symbols:arrow-forward-rounded" class="h-5 w-5" />
            </button>
          </nav>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

/* ===== 左侧导航 ===== */
.learn-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.sidebar-section + .sidebar-section {
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid #E2E8F0;
}
:global(html.dark) .sidebar-section + .sidebar-section {
  border-color: #1E293B;
}
.sidebar-section-title {
  padding: 0 0.75rem;
  margin-bottom: 0.375rem;
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #94A3B8;
}
.sidebar-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  width: 100%;
  padding: 0.55rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: #475569;
  text-align: left;
  transition: all 0.15s;
}
.sidebar-item:hover {
  background: #F1F5F9;
  color: #1E293B;
}
.sidebar-item.active {
  background: #EFF6FF;
  color: #2563EB;
  font-weight: 700;
}
:global(html.dark) .sidebar-item {
  color: #94A3B8;
}
:global(html.dark) .sidebar-item:hover {
  background: #1E293B;
  color: #E5E7EB;
}
:global(html.dark) .sidebar-item.active {
  background: #172554;
  color: #60A5FA;
}
.sidebar-count {
  margin-left: auto;
  font-size: 0.7rem;
  font-weight: 700;
  color: #94A3B8;
}

/* ===== 标题区 ===== */
.learn-stats-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 120px;
  padding: 0.75rem 1.25rem;
  border-radius: 0.75rem;
  border: 1px solid #E2E8F0;
  background: white;
}
:global(html.dark) .learn-stats-card {
  border-color: #1E293B;
  background: #111827;
}

/* ===== 搜索栏 ===== */
.learn-search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  max-width: 680px;
  height: 48px;
  padding: 0 1rem;
  border-radius: 0.75rem;
  border: 1px solid #E2E8F0;
  background: white;
  transition: border-color 0.15s;
}
.learn-search:focus-within {
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
:global(html.dark) .learn-search {
  border-color: #1E293B;
  background: #0F172A;
}
.learn-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.875rem;
  color: #1E293B;
}
:global(html.dark) .learn-search-input {
  color: #E5E7EB;
}

/* ===== 分类横向导航 ===== */
.learn-cat-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  height: 40px;
  padding: 0 1rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
  white-space: nowrap;
  color: #64748B;
  border: 1px solid #E2E8F0;
  background: white;
  transition: all 0.15s;
}
.learn-cat-chip:hover {
  border-color: #2563EB;
  color: #2563EB;
}
.learn-cat-chip.active {
  background: #2563EB;
  color: white;
  border-color: #2563EB;
}
:global(html.dark) .learn-cat-chip {
  border-color: #1E293B;
  background: #0F172A;
  color: #94A3B8;
}
:global(html.dark) .learn-cat-chip:hover {
  border-color: #3B82F6;
  color: #60A5FA;
}
:global(html.dark) .learn-cat-chip.active {
  background: #2563EB;
  color: white;
  border-color: #2563EB;
}
.learn-cat-count {
  font-size: 0.7rem;
  opacity: 0.7;
}

/* ===== 学习路径卡片 ===== */
.learn-path-card {
  display: flex;
  flex-direction: column;
  border-radius: 1rem;
  border: 1px solid #E2E8F0;
  background: white;
  overflow: hidden;
  transition: all 0.2s;
}
.learn-path-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: #93C5FD;
}
:global(html.dark) .learn-path-card {
  border-color: #1E293B;
  background: #111827;
}
:global(html.dark) .learn-path-card:hover {
  border-color: #3B82F6;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.learn-path-cover {
  height: 72px;
  padding: 0.75rem;
}
.learn-path-badge {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.65rem;
  font-weight: 800;
  color: white;
  letter-spacing: 0.1em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}
.learn-path-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 1rem;
}
.learn-path-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  align-self: flex-start;
  margin-top: auto;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: #2563EB;
  background: #EFF6FF;
  transition: all 0.15s;
}
.learn-path-btn:hover {
  background: #DBEAFE;
}
:global(html.dark) .learn-path-btn {
  color: #60A5FA;
  background: #172554;
}
:global(html.dark) .learn-path-btn:hover {
  background: #1E3A8A;
}

/* ===== 资源网格 ===== */
.learn-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1.25rem;
}
@media (max-width: 1280px) {
  .learn-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 1024px) {
  .learn-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 768px) {
  .learn-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== 资源卡片 ===== */
.learn-resource-card {
  display: flex;
  flex-direction: column;
  padding: 1.25rem;
  border-radius: 1rem;
  border: 1px solid #E2E8F0;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 200px;
}
.learn-resource-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: #93C5FD;
}
:global(html.dark) .learn-resource-card {
  border-color: #1E293B;
  background: #111827;
}
:global(html.dark) .learn-resource-card:hover {
  border-color: #3B82F6;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.learn-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.learn-card-index {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.7rem;
  font-weight: 800;
  color: #94A3B8;
}
.learn-card-lang {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
}
.learn-card-title {
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.3;
  color: #1E293B;
}
:global(html.dark) .learn-card-title {
  color: #E5E7EB;
}
.learn-card-desc {
  margin-top: 0.5rem;
  flex: 1;
  font-size: 0.8rem;
  line-height: 1.6;
  color: #64748B;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
:global(html.dark) .learn-card-desc {
  color: #94A3B8;
}
.learn-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #F1F5F9;
}
:global(html.dark) .learn-card-footer {
  border-color: #1E293B;
}
.learn-card-meta {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #94A3B8;
}

/* ===== 详情页 ===== */
.learn-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: #475569;
  border: 1px solid #E2E8F0;
  background: white;
  transition: all 0.15s;
}
.learn-back-btn:hover {
  border-color: #2563EB;
  color: #2563EB;
}
.learn-back-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
:global(html.dark) .learn-back-btn {
  border-color: #1E293B;
  background: #0F172A;
  color: #94A3B8;
}
.ui-btn-primary-sm {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  height: 2rem;
  padding: 0 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: white;
  background: #2563EB;
  transition: background 0.15s;
}
.ui-btn-primary-sm:hover {
  background: #1D4ED8;
}

/* ===== 章节目录 ===== */
.learn-chapter-directory {
  max-width: 800px;
}
.chapter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}
.chapter-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 1.25rem 3.5rem 1.25rem 1.25rem;
  min-height: 8rem;
  border-radius: 0.75rem;
  border: 1px solid #E2E8F0;
  background: white;
  text-align: left;
  color: inherit;
  cursor: pointer;
  transition: all 0.2s;
}
.chapter-card:hover {
  border-color: #93C5FD;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
}
:global(html.dark) .chapter-card {
  border-color: #1E293B;
  background: #111827;
}
:global(html.dark) .chapter-card:hover {
  border-color: #3B82F6;
}
.chapter-card::before {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  border-radius: 3px 0 0 3px;
  content: "";
  background: #2563EB;
  transform: scaleY(0.3);
  transform-origin: top;
  transition: transform 0.2s;
}
.chapter-card:hover::before {
  transform: scaleY(1);
}
.chapter-label {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.65rem;
  font-weight: 800;
  color: #2563EB;
}
.chapter-card h2 {
  margin-top: 0.5rem;
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.4;
  color: #1E293B;
}
:global(html.dark) .chapter-card h2 {
  color: #E5E7EB;
}
.chapter-card p {
  margin-top: 0.375rem;
  font-size: 0.8rem;
  line-height: 1.6;
  color: #64748B;
}
:global(html.dark) .chapter-card p {
  color: #94A3B8;
}
.chapter-open-icon {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  color: #2563EB;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
}
:global(html.dark) .chapter-open-icon {
  color: #60A5FA;
  background: #172554;
  border-color: #1E3A8A;
}

/* ===== Markdown 文档 ===== */
.learn-document {
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid #E2E8F0;
  background: white;
}
:global(html.dark) .learn-document {
  border-color: #1E293B;
  background: #111827;
}

/* ===== 章节导航 ===== */
.chapter-pagination {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 0.75rem;
  margin-top: 1.25rem;
}
.chapter-nav-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
  min-height: 3.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid #E2E8F0;
  background: white;
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
  transition: all 0.15s;
}
.chapter-nav-btn span {
  min-width: 0;
  overflow-wrap: anywhere;
}
.chapter-nav-btn:hover:not(:disabled) {
  border-color: #93C5FD;
  background: #EFF6FF;
}
.chapter-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.chapter-nav-next {
  justify-content: flex-end;
  text-align: right;
}
.chapter-directory-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid #E2E8F0;
  background: white;
  font-size: 0.8rem;
  font-weight: 700;
  color: #2563EB;
  transition: all 0.15s;
}
.chapter-directory-btn:hover {
  border-color: #93C5FD;
  background: #EFF6FF;
}
:global(html.dark) .chapter-nav-btn,
:global(html.dark) .chapter-directory-btn {
  border-color: #1E293B;
  background: #0F172A;
  color: #94A3B8;
}
:global(html.dark) .chapter-nav-btn:hover:not(:disabled),
:global(html.dark) .chapter-directory-btn:hover {
  border-color: #3B82F6;
  background: #172554;
}

/* ===== 移动端适配 ===== */
@media (max-width: 640px) {
  .chapter-grid {
    grid-template-columns: 1fr;
  }
  .chapter-pagination {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .chapter-directory-btn {
    grid-column: 1 / -1;
    grid-row: 1;
  }
}
</style>
