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
  // 计算机基础 - 操作系统
  { id: 'os-process-thread', title: '进程和线程的区别', duration: '', author: '', language: '通用', markdownFile: 'cs/os/进程和线程的区别.md' },
  { id: 'os-ipc', title: '进程间通信方式', duration: '', author: '', language: '通用', markdownFile: 'cs/os/进程间通信方式.md' },
  { id: 'os-scheduling', title: '进程调度算法', duration: '', author: '', language: '通用', markdownFile: 'cs/os/进程调度算法.md' },
  { id: 'os-user-kernel', title: '用户态和内核态', duration: '', author: '', language: '通用', markdownFile: 'cs/os/用户态和内核态.md' },
  { id: 'os-virtual-memory', title: '虚拟内存', duration: '', author: '', language: '通用', markdownFile: 'cs/os/虚拟内存.md' },
  { id: 'os-page-replace', title: '页面置换算法', duration: '', author: '', language: '通用', markdownFile: 'cs/os/页面置换算法.md' },
  { id: 'os-deadlock', title: '死锁', duration: '', author: '', language: '通用', markdownFile: 'cs/os/死锁.md' },
  { id: 'os-locks', title: '典型的锁', duration: '', author: '', language: '通用', markdownFile: 'cs/os/典型的锁.md' },
  { id: 'os-io-model', title: 'IO 模型', duration: '', author: '', language: '通用', markdownFile: 'cs/os/IO模型.md' },
  { id: 'os-epoll', title: 'epoll vs select vs poll', duration: '', author: '', language: '通用', markdownFile: 'cs/os/epoll-select-poll区别.md' },
  // 计算机基础 - 数据库
  { id: 'db-transaction', title: '事务四大特性', duration: '', author: '', language: '通用', markdownFile: 'cs/database/事务四大特性.md' },
  { id: 'db-sql-exec', title: 'SQL 查询执行流程', duration: '', author: '', language: '通用', markdownFile: 'cs/database/SQL查询执行流程.md' },
  { id: 'db-mvcc', title: 'MVCC 机制', duration: '', author: '', language: '通用', markdownFile: 'cs/database/MVCC机制.md' },
  { id: 'db-btree', title: 'MySQL 索引 B+ 树', duration: '', author: '', language: '通用', markdownFile: 'cs/database/MySQL索引B+树.md' },
  { id: 'db-index-types', title: '索引种类', duration: '', author: '', language: '通用', markdownFile: 'cs/database/索引种类.md' },
  { id: 'redis-data', title: 'Redis 数据结构', duration: '', author: '', language: '通用', markdownFile: 'cs/database/Redis数据结构.md' },
  { id: 'redis-persist', title: 'Redis 持久化', duration: '', author: '', language: '通用', markdownFile: 'cs/database/Redis持久化.md' },
  { id: 'redis-cache', title: 'Redis 缓存问题', duration: '', author: '', language: '通用', markdownFile: 'cs/database/Redis缓存问题.md' },
  { id: 'redis-lock', title: 'Redis 分布式锁', duration: '', author: '', language: '通用', markdownFile: 'cs/database/Redis分布式锁.md' },
  // 计算机基础 - 网络
  { id: 'net-tcp-udp', title: 'TCP 与 UDP 区别', duration: '', author: '', language: '通用', markdownFile: 'cs/network/TCP与UDP区别.md' },
  { id: 'net-3way', title: 'TCP 三次握手', duration: '', author: '', language: '通用', markdownFile: 'cs/network/TCP三次握手.md' },
  { id: 'net-4way', title: 'TCP 四次挥手', duration: '', author: '', language: '通用', markdownFile: 'cs/network/TCP四次挥手.md' },
  { id: 'net-http-code', title: 'HTTP 状态码', duration: '', author: '', language: '通用', markdownFile: 'cs/network/HTTP状态码.md' },
  { id: 'net-https', title: 'HTTPS 原理', duration: '', author: '', language: '通用', markdownFile: 'cs/network/HTTPS原理.md' },
  { id: 'net-url', title: '从输入 URL 到页面展示', duration: '', author: '', language: '通用', markdownFile: 'cs/network/从输入URL到页面展示.md' },
  // 计算机基础 - 组成原理
  { id: 'arch-von', title: '冯诺依曼与哈佛体系结构', duration: '', author: '', language: '通用', markdownFile: 'cs/arch/冯诺依曼与哈佛体系结构.md' },
  { id: 'arch-cpu-gpu', title: 'CPU 与 GPU 区别', duration: '', author: '', language: '通用', markdownFile: 'cs/arch/CPU与GPU区别.md' },
  // C++
  { id: 'cpp-3principles', title: 'C++ 三大特性：封装、继承、多态', duration: '', author: '', language: 'C++', markdownFile: 'cpp/C++三大特性.md' },
  { id: 'cpp-ptr-ref', title: '指针与引用的区别', duration: '', author: '', language: 'C++', markdownFile: 'cpp/指针与引用.md' },
  { id: 'cpp-static-const', title: 'static 与 const 的区别', duration: '', author: '', language: 'C++', markdownFile: 'cpp/static与const.md' },
  { id: 'cpp-virtual', title: '虚函数的实现机制', duration: '', author: '', language: 'C++', markdownFile: 'cpp/虚函数机制.md' },
  { id: 'cpp-deep-copy', title: '深拷贝与浅拷贝', duration: '', author: '', language: 'C++', markdownFile: 'cpp/深拷贝与浅拷贝.md' },
  { id: 'cpp-heap-stack', title: '堆与栈的区别', duration: '', author: '', language: 'C++', markdownFile: 'cpp/堆与栈.md' },
  { id: 'cpp-new-malloc', title: 'new 和 malloc 的区别', duration: '', author: '', language: 'C++', markdownFile: 'cpp/new与malloc.md' },
  { id: 'cpp-smart-ptr', title: '智能指针的区别与选型', duration: '', author: '', language: 'C++', markdownFile: 'cpp/智能指针.md' },
  { id: 'cpp-vector', title: 'vector 底层原理和扩容', duration: '', author: '', language: 'C++', markdownFile: 'cpp/vector底层原理.md' },
  { id: 'cpp-map', title: 'map 与 unordered_map 区别', duration: '', author: '', language: 'C++', markdownFile: 'cpp/map与unordered_map.md' },
  { id: 'cpp-lambda', title: 'Lambda 表达式', duration: '', author: '', language: 'C++', markdownFile: 'cpp/Lambda表达式.md' },
  { id: 'cpp-move', title: '移动语义', duration: '', author: '', language: 'C++', markdownFile: 'cpp/移动语义.md' },
  { id: 'cpp-io-multiplex', title: 'select / poll / epoll 区别', duration: '', author: '', language: 'C++', markdownFile: 'cpp/select-poll-epoll.md' },
  // Java
  { id: 'java-oop', title: '面向对象三大特性', duration: '', author: '', language: 'Java', markdownFile: 'java/面向对象三大特性.md' },
  { id: 'java-hashmap', title: 'HashMap 实现原理', duration: '', author: '', language: 'Java', markdownFile: 'java/HashMap原理.md' },
  { id: 'java-arraylist', title: 'ArrayList 与 LinkedList 区别', duration: '', author: '', language: 'Java', markdownFile: 'java/ArrayList与LinkedList.md' },
  { id: 'java-jvm-mem', title: 'JVM 内存结构', duration: '', author: '', language: 'Java', markdownFile: 'java/JVM内存结构.md' },
  { id: 'java-gc', title: '垃圾回收', duration: '', author: '', language: 'Java', markdownFile: 'java/垃圾回收.md' },
  { id: 'java-deadlock', title: '死锁', duration: '', author: '', language: 'Java', markdownFile: 'java/死锁.md' },
  { id: 'java-threadpool', title: '线程池', duration: '', author: '', language: 'Java', markdownFile: 'java/线程池.md' },
  { id: 'java-spring-ioc', title: 'Spring IOC', duration: '', author: '', language: 'Java', markdownFile: 'java/Spring-IOC.md' },
  { id: 'java-spring-aop', title: 'Spring AOP', duration: '', author: '', language: 'Java', markdownFile: 'java/Spring-AOP.md' },
  // Go
  { id: 'go-interface', title: 'Go 接口', duration: '', author: '', language: 'Go', markdownFile: 'go/Go接口.md' },
  { id: 'go-goroutine', title: 'Goroutine', duration: '', author: '', language: 'Go', markdownFile: 'go/Goroutine.md' },
  { id: 'go-channel', title: 'channel 区别', duration: '', author: '', language: 'Go', markdownFile: 'go/channel区别.md' },
  { id: 'go-gmp', title: 'GMP 调度模型', duration: '', author: '', language: 'Go', markdownFile: 'go/GMP调度模型.md' },
  { id: 'go-mem', title: 'Go 内存管理', duration: '', author: '', language: 'Go', markdownFile: 'go/Go内存管理.md' },
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
