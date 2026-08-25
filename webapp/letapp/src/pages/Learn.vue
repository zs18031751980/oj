<script setup lang="ts">
import { computed, defineAsyncComponent, markRaw, onMounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';

const MarkdownComponent = defineAsyncComponent(
  () => import('../components/MarkdownComponent.vue'),
);

import {
  listLearnFavorites, addLearnFavorite, removeLearnFavorite,
  listLearnHistory, recordLearnHistory,
} from '../services/api';

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
  // 编程笔记
  { id: 'programming-notes', title: '编程笔记', duration: '', author: '', language: '通用', markdownFile: '编程笔记/README.md', chapters: [
    { id: 'programming-notes-interview', label: '大厂面经', title: '大厂面经', summary: '各大厂面试经验总结', markdownFile: '编程笔记/大厂面经/README.md' },
    { id: 'programming-notes-ai', label: '大模型', title: '大模型', summary: '大模型相关知识', markdownFile: '编程笔记/大模型/README.md' },
    { id: 'programming-notes-cpp', label: 'C++', title: 'C++', summary: 'C++ 编程笔记', markdownFile: '编程笔记/C++/README.md' },
    { id: 'programming-notes-go', label: 'Go', title: 'Go', summary: 'Go 编程笔记', markdownFile: '编程笔记/Go/README.md' },
    { id: 'programming-notes-java', label: 'Java', title: 'Java', summary: 'Java 编程笔记', markdownFile: '编程笔记/Java/README.md' },
  ] },
  // 计算机基础
  { id: 'cs-fundamentals', title: '计算机基础', duration: '', author: '', language: '通用', markdownFile: '计算机基础/README.md', chapters: [
    { id: 'cs-os', label: '操作系统', title: '操作系统', summary: '操作系统核心概念', markdownFile: '计算机基础/操作系统/内存管理/内存连续分配管理方式有什么？.md' },
    { id: 'cs-arch', label: '计算机组成原理', title: '计算机组成原理', summary: '计算机组成原理', markdownFile: '计算机基础/计算机组成原理/README.md' },
    { id: 'cs-db', label: '数据库', title: '数据库', summary: '数据库相关知识', markdownFile: '计算机基础/数据库/README.md' },
    { id: 'cs-network', label: '网络', title: '网络', summary: '计算机网络', markdownFile: '计算机基础/网络/README.md' },
  ] },
  // 开发资料
  { id: 'dev-materials', title: '开发资料', duration: '', author: '', language: '通用', markdownFile: '开发资料/README.md', chapters: [
    { id: 'dev-os', label: '操作系统', title: '操作系统', summary: '操作系统学习资料', markdownFile: '开发资料/操作系统.md' },
    { id: 'dev-testing', label: '测试-Docker-缓存-系统设计-源码阅读学习资料', title: '测试-Docker-缓存-系统设计-源码阅读学习资料', summary: '测试、Docker、缓存、系统设计、源码阅读', markdownFile: '开发资料/测试-Docker-缓存-系统设计-源码阅读学习资料.md' },
    { id: 'dev-backend', label: '后端开发学习资料', title: '后端开发学习资料', summary: '后端开发学习资料', markdownFile: '开发资料/后端开发学习资料.md' },
    { id: 'dev-network', label: '网络', title: '网络', summary: '网络学习资料', markdownFile: '开发资料/网络.md' },
    { id: 'dev-path', label: '学习路径', title: '学习路径', summary: '学习路径', markdownFile: '开发资料/学习路径.md' },
    { id: 'dev-frontend', label: 'HTML-CSS-JS学习资料', title: 'HTML-CSS-JS学习资料', summary: '前端学习资料', markdownFile: '开发资料/HTML-CSS-JS学习资料.md' },
    { id: 'dev-oj', label: 'oj项目', title: 'oj项目', summary: 'oj项目相关资料', markdownFile: '开发资料/oj项目.md' },
  ] },
  // 指令
  { id: 'commands', title: '指令', duration: '', author: '', language: '通用', markdownFile: '指令/README.md', chapters: [
    { id: 'cmd-gitee', label: 'gitee终端指令', title: 'gitee终端指令', summary: 'gitee终端指令', markdownFile: '指令/gitee终端指令.md' },
    { id: 'cmd-latex', label: 'latex式子', title: 'latex式子', summary: 'latex式子', markdownFile: '指令/latex式子.md' },
    { id: 'cmd-linux', label: 'Linux终端指令汇总', title: 'Linux终端指令汇总', summary: 'Linux终端指令汇总', markdownFile: '指令/Linux终端指令汇总.md' },
    { id: 'cmd-redis', label: 'redis常用指令', title: 'redis常用指令', summary: 'redis常用指令', markdownFile: '指令/redis常用指令.md' },
    { id: 'cmd-sql', label: 'sql增删改查', title: 'sql增删改查', summary: 'sql增删改查', markdownFile: '指令/sql增删改查.md' },
  ] },
  // C++库资料
  { id: 'cpp-libraries', title: 'C++库资料', duration: '', author: '', language: 'C++', markdownFile: 'C++库资料/00_总览_目录.md', chapters: [
    { id: 'cpp-lib-eigen', label: 'Eigen', title: 'Eigen', summary: 'Eigen库', markdownFile: 'C++库资料/01_Eigen.md' },
    { id: 'cpp-lib-armadillo', label: 'Armadillo/Blaze', title: 'Armadillo/Blaze', summary: 'Armadillo和Blaze库', markdownFile: 'C++库资料/02_Armadillo_Blaze.md' },
    { id: 'cpp-lib-boost', label: 'Boost', title: 'Boost', summary: 'Boost库', markdownFile: 'C++库资料/03_Boost.md' },
    { id: 'cpp-lib-network', label: '网络通信', title: '网络通信', summary: '网络通信库', markdownFile: 'C++库资料/04_网络通信.md' },
    { id: 'cpp-lib-json', label: 'JSON 序列化', title: 'JSON 序列化', summary: 'JSON序列化库', markdownFile: 'C++库资料/05_JSON_序列化.md' },
    { id: 'cpp-lib-opencv', label: 'OpenCV 图像', title: 'OpenCV 图像', summary: 'OpenCV图像处理', markdownFile: 'C++库资料/06_OpenCV_图像.md' },
    { id: 'cpp-lib-gui', label: 'GUI', title: 'GUI', summary: 'GUI库', markdownFile: 'C++库资料/07_GUI.md' },
    { id: 'cpp-lib-concurrency', label: '并发多线程', title: '并发多线程', summary: '并发多线程库', markdownFile: 'C++库资料/08_并发多线程.md' },
    { id: 'cpp-lib-deeplearning', label: '深度学习', title: '深度学习', summary: '深度学习库', markdownFile: 'C++库资料/09_深度学习.md' },
    { id: 'cpp-lib-game', label: '游戏开发', title: '游戏开发', summary: '游戏开发库', markdownFile: 'C++库资料/10_游戏开发.md' },
    { id: 'cpp-lib-cmake', label: '编译选项与CMake', title: '编译选项与CMake', summary: '编译选项与CMake', markdownFile: 'C++库资料/11_编译选项与CMake.md' },
  ] },
]);

const selectedTitle = ref('');
const selectedResource = ref<MarkdownContent | undefined>();
const isLoadingDoc = ref(false);
const docError = ref('');

const allResources = [...courses];

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

const favoriteIds = ref<Set<string>>(new Set());
const recentHistory = ref<{ resource_id: string; browsed_at: string | null }[]>([]);

async function loadFavorites() {
  try {
    const res = await listLearnFavorites();
    if (res?.data) {
      favoriteIds.value = new Set(res.data.map(f => f.resource_id));
    }
  } catch { /* 未登录或出错 */ }
}

async function toggleFavorite(resourceId: string, e: MouseEvent) {
  e.stopPropagation();
  const wasFavorited = favoriteIds.value.has(resourceId);
  // 乐观更新
  const next = new Set(favoriteIds.value);
  if (wasFavorited) next.delete(resourceId); else next.add(resourceId);
  favoriteIds.value = next;

  try {
    if (wasFavorited) {
      await removeLearnFavorite(resourceId);
    } else {
      await addLearnFavorite(resourceId);
    }
  } catch {
    // 回滚
    favoriteIds.value = new Set(wasFavorited ? [...next, resourceId] : [...next].filter(id => id !== resourceId));
  }
}

async function loadHistory() {
  try {
    const res = await listLearnHistory();
    if (res?.data) {
      recentHistory.value = res.data;
    }
  } catch { /* 未登录或出错 */ }
}

async function trackBrowse(resourceId: string) {
  try {
    await recordLearnHistory(resourceId);
    await loadHistory();
  } catch { /* 静默 */ }
}

const isHistoryMode = ref(false);

const searchQuery = ref('');

const activeCategory = ref('全部');

const categories = ['全部', 'C', 'JavaScript', 'Python', 'C++', 'Java', 'Go', 'Vue', '通用'];
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

  // 搜索时跨模式搜索所有资源
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase().replace(/\s+/g, '');
    list = allResources.filter(r => {
      const title = r.title.toLowerCase().replace(/\s+/g, '');
      const lang = 'language' in r ? (r as ResourceItem).language.toLowerCase().replace(/\s+/g, '') : '';
      const desc = (cardInfoMap.value[r.id]?.description || '').toLowerCase().replace(/\s+/g, '');
      return title.includes(q) || lang.includes(q) || desc.includes(q);
    });
  } else if (isFavoritesMode.value) {
    list = list.filter(r => favoriteIds.value.has(r.id));
  } else if (isHistoryMode.value) {
    const historyIds = recentHistory.value.map(h => h.resource_id);
    list = list.filter(r => historyIds.includes(r.id));
    list.sort((a, b) => historyIds.indexOf(a.id) - historyIds.indexOf(b.id));
  } else if (activeCategory.value !== '全部') {
    list = list.filter(r => r.language === activeCategory.value);
  }

  return list;
});

const isFavoritesMode = ref(false);


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
  await Promise.all([loadFavorites(), loadHistory()]);
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
    trackBrowse(resourceId);
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
                <Icon icon="material-symbols:library-books" class="h-4 w-4 text-emerald-500" />
                <span>全部资源</span>
                <span class="sidebar-count">{{ allResources.length }}</span>
              </button>
              <button class="sidebar-item" :class="{ active: isFavoritesMode }" @click="isFavoritesMode = !isFavoritesMode; activeCategory = '全部'; isHistoryMode = false">
                <Icon icon="material-symbols:favorite" class="h-4 w-4 text-rose-500" />
                <span>我的收藏</span>
                <span class="sidebar-count">{{ favoriteIds.size }}</span>
              </button>
              <button class="sidebar-item" :class="{ active: isHistoryMode }" @click="isHistoryMode = !isHistoryMode; activeCategory = '全部'; isFavoritesMode = false">
                <Icon icon="material-symbols:history" class="h-4 w-4 text-amber-500" />
                <span>最近浏览</span>
                <span class="sidebar-count">{{ recentHistory.length }}</span>
              </button>
            </div>

            <!-- 分类区域 -->
            <div class="sidebar-section">
              <div class="sidebar-section-title mt-2">资源分类</div>
              <button
                v-for="cat in categories"
                :key="cat"
                class="sidebar-item"
                :class="{ active: activeCategory === cat && !isFavoritesMode && !isHistoryMode }"
                @click="activeCategory = cat; isFavoritesMode = false; isHistoryMode = false"
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
              :class="{ active: activeCategory === cat && !isFavoritesMode && !isHistoryMode }"
              @click="activeCategory = cat; isFavoritesMode = false; isHistoryMode = false"
            >
              {{ cat === '全部' ? '全部' : cat }}
              <span class="learn-cat-count">{{ categoryCount[cat] || 0 }}</span>
            </button>
          </div>

          <!-- 全部资源网格 -->
          <div>
            <div class="mb-4 flex items-center gap-2">
              <Icon icon="material-symbols:library-books" class="h-5 w-5 text-[#2563EB]" />
              <h2 class="text-lg font-black text-[#1E293B] dark:text-[#E5E7EB]">
                {{ searchQuery.trim() ? '搜索结果' : isFavoritesMode ? '我的收藏' : isHistoryMode ? '最近浏览' : '全部资源' }}
              </h2>
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
                  <div class="flex items-center gap-2">
                    <span class="learn-card-lang" :class="getLanguageColor(course.language)">{{ course.language }}</span>
                    <button
                      class="learn-fav-btn"
                      :class="{ active: favoriteIds.has(course.id) }"
                      :title="favoriteIds.has(course.id) ? '取消收藏' : '收藏'"
                      @click="toggleFavorite(course.id, $event)"
                    >
                      <Icon :icon="favoriteIds.has(course.id) ? 'material-symbols:bookmark' : 'material-symbols:bookmark_border'" class="h-4 w-4" />
                    </button>
                  </div>
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
              <p class="font-bold text-[#1E293B] dark:text-[#E5E7EB]">{{ searchQuery.trim() ? '没有找到匹配的资源' : isFavoritesMode ? '还没有收藏任何资源' : isHistoryMode ? '还没有浏览记录' : '没有找到匹配的资源' }}</p>
              <p class="text-sm text-[#94A3B8]">{{ searchQuery.trim() ? '试试其他关键词或分类' : isFavoritesMode ? '点击资源卡片右上角的书签图标即可收藏' : isHistoryMode ? '打开任意资源后会自动记录' : '试试其他关键词或分类' }}</p>
            </div>
          </div>
        </section>
      </div>
    </template>

    <!-- ===== 详情页 ===== -->
    <template v-else>
      <div class="learn-detail-container py-6 lg:py-8">

        <!-- 工具栏 -->
        <div class="learn-toolbar">
          <button class="learn-back-btn" @click="goBackFromDetail">
            <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4" />
            {{ currentChapter ? '返回课程目录' : '返回学习资源' }}
          </button>

          <div class="flex items-center gap-2">
            <button
              v-if="!isChapterDirectory"
              class="learn-toolbar-btn"
              :disabled="isLoadingDoc || !selectedResource"
              @click="downloadCurrentMarkdown"
              title="导出 Markdown"
            >
              <Icon icon="material-symbols:download-rounded" class="h-4 w-4" />
            </button>
            <button class="learn-toolbar-btn" title="去编辑器练习" @click="router.push('/playground')">
              <Icon icon="material-symbols:code" class="h-4 w-4" />
            </button>
          </div>
        </div>

        <!-- 章节目录模式 -->
        <div v-if="isChapterDirectory" class="learn-chapter-directory">
          <header class="chapter-directory-header">
            <p class="chapter-kicker">{{ currentResource?.title }} · {{ currentResource?.chapters?.length }} 章节</p>
            <h1 class="chapter-directory-title">{{ currentResource?.title }}</h1>
            <p class="chapter-directory-desc">按章节逐步学习核心知识，每章内容在独立页面中阅读。</p>
          </header>

          <div class="chapter-grid">
            <button
              v-for="(chapter, idx) in currentResource?.chapters"
              :key="chapter.id"
              class="chapter-card"
              @click="openChapter(chapter)"
            >
              <div class="chapter-card-top">
                <span class="chapter-index">{{ String(idx + 1).padStart(2, '0') }}</span>
                <span class="chapter-open-icon">
                  <Icon icon="material-symbols:arrow-forward-rounded" class="h-4 w-4" />
                </span>
              </div>
              <h2 class="chapter-card-title">{{ chapter.title }}</h2>
              <p class="chapter-card-summary">{{ chapter.summary }}</p>
            </button>
          </div>
        </div>

        <!-- Markdown 内容模式 -->
        <template v-else>
          <!-- 章节标题区 -->
          <div v-if="currentChapter" class="learn-chapter-header">
            <p class="chapter-kicker">{{ currentResource?.title }}</p>
            <h1 class="chapter-main-title">{{ currentChapter.title }}</h1>
            <div class="chapter-info-row">
              <span class="chapter-info-item">
                <Icon icon="material-symbols:menu-book" class="h-3.5 w-3.5" />
                第 {{ (currentChapterIndex ?? 0) + 1 }} / {{ currentResource?.chapters?.length }} 章
              </span>
              <span v-if="currentChapter.summary" class="chapter-info-item">
                <Icon icon="material-symbols:info-outline" class="h-3.5 w-3.5" />
                {{ currentChapter.summary }}
              </span>
            </div>
          </div>

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
              class="chapter-nav-btn chapter-nav-prev"
              :disabled="!previousChapter"
              @click="previousChapter && openChapter(previousChapter)"
            >
              <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4 shrink-0" />
              <div class="chapter-nav-text">
                <span class="chapter-nav-label">上一章</span>
                <span class="chapter-nav-title">{{ previousChapter?.title || '已经是第一章' }}</span>
              </div>
            </button>

            <button class="chapter-directory-btn" title="返回课程目录" @click="goBackFromDetail">
              <Icon icon="material-symbols:format-list-bulleted-rounded" class="h-4 w-4" />
              <span>目录</span>
            </button>

            <button
              class="chapter-nav-btn chapter-nav-next"
              :disabled="!nextChapter"
              @click="nextChapter && openChapter(nextChapter)"
            >
              <div class="chapter-nav-text chapter-nav-text-right">
                <span class="chapter-nav-label">下一章</span>
                <span class="chapter-nav-title">{{ nextChapter?.title || '已经是最后一章' }}</span>
              </div>
              <Icon icon="material-symbols:arrow-forward-rounded" class="h-4 w-4 shrink-0" />
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

/* ===== 收藏按钮 ===== */
.learn-fav-btn {
  display: grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.5rem;
  color: #94A3B8;
  background: transparent;
  transition: all 0.15s;
}
.learn-fav-btn:hover {
  background: #FEF2F2;
  color: #F43F5E;
}
.learn-fav-btn.active {
  color: #F43F5E;
}
.learn-fav-btn.active:hover {
  background: #FEF2F2;
}
:global(html.dark) .learn-fav-btn:hover {
  background: #4C1D2566;
  color: #FB7185;
}
:global(html.dark) .learn-fav-btn.active {
  color: #FB7185;
}

/* ===== 详情页容器 ===== */
.learn-detail-container {
  max-width: 1320px;
  margin: 0 auto;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
}

/* ===== 工具栏 ===== */
.learn-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.learn-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  border: 1px solid #E2E8F0;
  background: white;
  transition: all 0.15s;
}
.learn-back-btn:hover {
  border-color: #2563EB;
  color: #2563EB;
  background: #EFF6FF;
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
:global(html.dark) .learn-back-btn:hover {
  border-color: #3B82F6;
  color: #60A5FA;
  background: #172554;
}

.learn-toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  color: #64748B;
  border: 1px solid #E2E8F0;
  background: white;
  transition: all 0.15s;
}
.learn-toolbar-btn:hover {
  border-color: #2563EB;
  color: #2563EB;
  background: #EFF6FF;
}
.learn-toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
:global(html.dark) .learn-toolbar-btn {
  border-color: #1E293B;
  background: #0F172A;
  color: #94A3B8;
}
:global(html.dark) .learn-toolbar-btn:hover {
  border-color: #3B82F6;
  color: #60A5FA;
  background: #172554;
}

/* ===== 章节标题区 ===== */
.learn-chapter-header {
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid #F1F5F9;
}
:global(html.dark) .learn-chapter-header {
  border-color: #1E293B;
}

.chapter-kicker {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #2563EB;
  margin-bottom: 10px;
}
:global(html.dark) .chapter-kicker {
  color: #60A5FA;
}

.chapter-main-title {
  font-size: 34px;
  font-weight: 700;
  line-height: 1.3;
  color: #0F172A;
  letter-spacing: -0.02em;
}
:global(html.dark) .chapter-main-title {
  color: #F1F5F9;
}

.chapter-info-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-top: 14px;
}

.chapter-info-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #94A3B8;
}

/* ===== 章节目录模式 ===== */
.learn-chapter-directory {
  max-width: 900px;
  margin: 0 auto;
}

.chapter-directory-header {
  margin-bottom: 36px;
}

.chapter-directory-title {
  font-size: 34px;
  font-weight: 700;
  line-height: 1.3;
  color: #0F172A;
  letter-spacing: -0.02em;
}
:global(html.dark) .chapter-directory-title {
  color: #F1F5F9;
}

.chapter-directory-desc {
  margin-top: 10px;
  font-size: 14px;
  color: #64748B;
}
:global(html.dark) .chapter-directory-desc {
  color: #94A3B8;
}

.chapter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.chapter-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  background: white;
  text-align: left;
  color: inherit;
  cursor: pointer;
  transition: all 0.2s;
}

.chapter-card:hover {
  border-color: #93C5FD;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.08);
  transform: translateY(-2px);
}

:global(html.dark) .chapter-card {
  border-color: #1E293B;
  background: #111827;
}
:global(html.dark) .chapter-card:hover {
  border-color: #3B82F6;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
}

.chapter-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.chapter-index {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  font-weight: 800;
  color: #2563EB;
}
:global(html.dark) .chapter-index {
  color: #60A5FA;
}

.chapter-card .chapter-open-icon {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: #2563EB;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  transition: all 0.2s;
}
.chapter-card:hover .chapter-open-icon {
  background: #2563EB;
  color: white;
  border-color: #2563EB;
}
:global(html.dark) .chapter-card .chapter-open-icon {
  color: #60A5FA;
  background: #172554;
  border-color: #1E3A8A;
}
:global(html.dark) .chapter-card:hover .chapter-open-icon {
  background: #3B82F6;
  color: white;
  border-color: #3B82F6;
}

.chapter-card-title {
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
  color: #1E293B;
}
:global(html.dark) .chapter-card-title {
  color: #E5E7EB;
}

.chapter-card-summary {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: #64748B;
}
:global(html.dark) .chapter-card-summary {
  color: #94A3B8;
}

/* ===== Markdown 文档容器 ===== */
.learn-document {
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  background: white;
  overflow: hidden;
}
:global(html.dark) .learn-document {
  border-color: #1E293B;
  background: #111827;
}

/* ===== 章节导航 ===== */
.chapter-pagination {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 12px;
  margin-top: 20px;
}

.chapter-nav-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  min-height: 80px;
  padding: 16px 20px;
  border-radius: 10px;
  border: 1px solid #E2E8F0;
  background: white;
  text-align: left;
  color: inherit;
  transition: all 0.15s;
}

.chapter-nav-btn:hover:not(:disabled) {
  border-color: #93C5FD;
  background: #EFF6FF;
}
.chapter-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

:global(html.dark) .chapter-nav-btn {
  border-color: #1E293B;
  background: #0F172A;
}
:global(html.dark) .chapter-nav-btn:hover:not(:disabled) {
  border-color: #3B82F6;
  background: #172554;
}

.chapter-nav-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.chapter-nav-text-right {
  text-align: right;
}

.chapter-nav-label {
  font-size: 11px;
  font-weight: 600;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chapter-nav-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:global(html.dark) .chapter-nav-title {
  color: #CBD5E1;
}

.chapter-nav-next {
  justify-content: flex-end;
  text-align: right;
}

.chapter-directory-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  background: white;
  font-size: 13px;
  font-weight: 600;
  color: #2563EB;
  transition: all 0.15s;
}
.chapter-directory-btn:hover {
  border-color: #93C5FD;
  background: #EFF6FF;
}
:global(html.dark) .chapter-directory-btn {
  border-color: #1E293B;
  background: #0F172A;
  color: #60A5FA;
}
:global(html.dark) .chapter-directory-btn:hover {
  border-color: #3B82F6;
  background: #172554;
}

/* ===== 移动端适配 ===== */
@media (max-width: 768px) {
  .learn-detail-container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  .chapter-grid {
    grid-template-columns: 1fr;
  }
  .chapter-main-title,
  .chapter-directory-title {
    font-size: 26px;
  }
  .learn-document {
    padding: 20px 16px;
  }
}

@media (max-width: 640px) {
  .chapter-pagination {
    grid-template-columns: 1fr;
  }
  .chapter-nav-btn {
    min-height: auto;
  }
  .chapter-directory-btn {
    order: -1;
    justify-content: center;
    padding: 10px;
  }
}
</style>
