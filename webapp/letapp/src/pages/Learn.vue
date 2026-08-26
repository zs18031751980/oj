<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';
import { sortNodesFoldersFirst } from '../utils/treeSort';
import type { RecentItem } from '../components/RecentPanel.vue';

const MarkdownComponent = defineAsyncComponent(
  () => import('../components/MarkdownComponent.vue'),
);
const LearnSidebar = defineAsyncComponent(
  () => import('../components/LearnSidebar.vue'),
);
const RecentPanel = defineAsyncComponent(
  () => import('../components/RecentPanel.vue'),
);

/** ====== 数据类型 ====== */
interface TreeNode {
  id: string;
  name: string;
  type: 'folder' | 'file';
  path: string;
  children?: TreeNode[];
  size?: number;
  mtime?: number;
}

interface MarkdownData {
  content: string;
  title: string;
  path: string;
  mtime: number;
}

interface HeadingItem {
  level: number;
  text: string;
  id: string;
}

interface BreadcrumbItem {
  name: string;
  path: string;
}

/** ====== 路由 ====== */
const route = useRoute();
const router = useRouter();

/** ====== 状态 ====== */
const treeData = ref<TreeNode | null>(null);
const currentFile = ref<MarkdownData | null>(null);
const isLoadingTree = ref(false);
const isLoadingDoc = ref(false);
const error = ref('');
const mdHeadings = ref<HeadingItem[]>([]);
const mdContainer = ref<HTMLElement | null>(null);

/** 当前在中间区域浏览的文件夹路径（'' = 根目录） */
const browsePath = ref('');
const middleSearch = ref('');
const expandedGroups = ref<Set<string>>(new Set());
const recentList = ref<RecentItem[]>([]);
const mobileSidebarOpen = ref(false);

const RECENT_KEY = 'learn_recent_v1';

/** ====== 路径工具：学习资料以同源静态文件方式提供（public/learn） ====== */
function encodePath(p: string): string {
  return p.split('/').map((s) => encodeURIComponent(s)).join('/');
}

const learnBase = '/learn-dist';

const PREFIX_RE = /^\d+[-_.\s]+/;
function cleanName(name: string): string {
  return name.replace(PREFIX_RE, '').replace(/\.md$/, '');
}
function cleanPath(path: string): string {
  return path.split('/').filter(Boolean).map(cleanName).join(' / ');
}

/** 提取 Markdown 标题（首个 # 标题） */
function extractTitle(content: string, fallback: string): string {
  const m = content.match(/^#\s+(.+)$/m);
  if (m && m[1]) return m[1].trim();
  return fallback.split('/').pop()?.replace(/\.md$/, '') || fallback;
}

/** ====== 树查找 / 面包屑 ====== */
function getNodeByPath(path: string): TreeNode | null {
  if (!treeData.value) return null;
  if (!path) return treeData.value;
  const parts = path.split('/').filter(Boolean);
  let node: TreeNode | null = treeData.value;
  let acc = '';
  for (const part of parts) {
    if (!node || !node.children) return null;
    acc = acc ? acc + '/' + part : part;
    node = node.children.find((c) => c.path === acc) || null;
    if (!node) return null;
  }
  return node;
}

function buildBreadcrumb(path: string): BreadcrumbItem[] {
  if (!treeData.value || !path) return [];
  const parts = path.split('/').filter(Boolean);
  const crumbs: BreadcrumbItem[] = [];
  let node: TreeNode | null = treeData.value;
  let acc = '';
  for (const part of parts) {
    if (!node || !node.children) break;
    acc = acc ? acc + '/' + part : part;
    node = node.children.find((c) => c.path === acc) || null;
    if (!node) break;
    crumbs.push({ name: node.name, path: acc });
  }
  return crumbs;
}

/** ====== 加载目录树（静态 manifest） ====== */
async function loadTree() {
  isLoadingTree.value = true;
  error.value = '';
  try {
    const res = await fetch(`${learnBase}/tree.json`, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    treeData.value = json || null;
  } catch (e: any) {
    error.value = `目录加载失败: ${e.message}`;
  } finally {
    isLoadingTree.value = false;
  }
}

/** ====== 加载 Markdown 文件（静态文件） ====== */
async function fetchMarkdown(filePath: string): Promise<MarkdownData> {
  const res = await fetch(`${learnBase}/${encodePath(filePath)}`, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const text = await res.text();
  return {
    content: text,
    title: extractTitle(text, filePath),
    path: filePath,
    mtime: 0,
  };
}

async function loadFile(filePath: string) {
  isLoadingDoc.value = true;
  error.value = '';
  try {
    currentFile.value = await fetchMarkdown(filePath);
    router.replace({ query: { path: filePath } });
    pushRecent(currentFile.value);
  } catch (e: any) {
    error.value = `文件加载失败: ${e.message}`;
  } finally {
    isLoadingDoc.value = false;
  }
}

/** 打开中间区域的资料 */
function openFile(filePath: string) {
  loadFile(filePath);
  mobileSidebarOpen.value = false;
}

/** ====== 重新扫描（重新拉取 manifest） ====== */
async function rescanTree() {
  isLoadingTree.value = true;
  try {
    const res = await fetch(`${learnBase}/tree.json?t=${Date.now()}`);
    if (res.ok) treeData.value = await res.json();
  } catch { /* ignore */ }
  finally {
    isLoadingTree.value = false;
  }
}

/** ====== 导航：文件夹浏览 ====== */
function navigateToFolder(path: string) {
  browsePath.value = path;
  middleSearch.value = '';
  mobileSidebarOpen.value = false;
  // 默认展开当前目录下所有文件夹分组
  const node = getNodeByPath(path);
  if (node?.children) {
    const next = new Set(expandedGroups.value);
    for (const c of node.children) {
      if (c.type === 'folder') next.add(c.path);
    }
    expandedGroups.value = next;
  }
}

/** 关闭详情回到浏览 */
function backToBrowse() {
  currentFile.value = null;
  router.replace({ query: {} });
}

const currentLocation = computed(() => (currentFile.value ? currentFile.value.path : browsePath.value));

/** ====== 侧边栏事件 ====== */
function handleSidebarSelect(path: string) {
  loadFile(path);
}
function handleSidebarHeading(id: string) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function handleSidebarBrowse(path: string) {
  navigateToFolder(path);
}
function handleMdNavigate(filePath: string) {
  isLoadingDoc.value = true;
  error.value = '';
  fetchMarkdown(filePath)
    .then((data) => {
      currentFile.value = data;
      router.replace({ query: { path: filePath } });
      pushRecent(data);
    })
    .catch((e: any) => { error.value = `加载资料失败：${e.message}`; })
    .finally(() => { isLoadingDoc.value = false; });
}

/** ====== 解析 Markdown 标题 ====== */
function parseHeadings(markdown: string) {
  const headings: HeadingItem[] = [];
  const lines = markdown.split('\n');
  for (const raw of lines) {
    const match = raw.match(/^(#{1,3})\s+(.+)/);
    if (match) {
      const level = match[1]?.length ?? 1;
      const text = (match[2] || '').replace(/[*_`~\[\]]/g, '').trim();
      const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
      headings.push({ level, text, id });
    }
  }
  return headings;
}

watch(() => currentFile.value?.content, (content) => {
  if (content) {
    mdHeadings.value = parseHeadings(content);
    nextTick(() => addHeadingIds());
  }
}, { immediate: true });

function addHeadingIds() {
  if (!mdContainer.value) return;
  const headings = mdContainer.value.querySelectorAll('h1, h2, h3');
  headings.forEach((el) => {
    const text = el.textContent?.trim() || '';
    const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
    el.id = id;
  });
}

/** ====== 导出 Markdown ====== */
function downloadCurrentMarkdown() {
  if (!currentFile.value) return;
  const blob = new Blob([currentFile.value.content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentFile.value.title || 'document'}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

/** ====== 统计 ====== */
function countFiles(node: TreeNode | null): number {
  if (!node) return 0;
  if (node.type === 'file') return 1;
  if (!node.children) return 0;
  return node.children.reduce((sum, c) => sum + countFiles(c), 0);
}
const totalFiles = computed(() => countFiles(treeData.value));
const totalCategories = computed(() => {
  if (!treeData.value?.children) return 0;
  return treeData.value.children.filter((c) => c.type === 'folder').length;
});

/** ====== 中间区域内容 ====== */
const currentBrowseNode = computed(() => getNodeByPath(browsePath.value));
const breadcrumb = computed(() => buildBreadcrumb(browsePath.value));

const sortedChildren = computed(() => {
  const node = currentBrowseNode.value;
  if (!node?.children) return [];
  return sortNodesFoldersFirst(node.children);
});

const folderChildren = computed(() => sortedChildren.value.filter((c) => c.type === 'folder'));
const fileChildren = computed(() => sortedChildren.value.filter((c) => c.type === 'file'));

const filteredFolders = computed(() => {
  const q = middleSearch.value.trim().toLowerCase();
  if (!q) return folderChildren.value;
  return folderChildren.value.filter((c) => cleanName(c.name).toLowerCase().includes(q));
});
const filteredFiles = computed(() => {
  const q = middleSearch.value.trim().toLowerCase();
  if (!q) return fileChildren.value;
  return fileChildren.value.filter((c) => cleanName(c.name).toLowerCase().includes(q));
});

const currentFolderFileCount = computed(() => countFiles(currentBrowseNode.value));

function childrenOf(node: TreeNode): TreeNode[] {
  if (!node.children) return [];
  return sortNodesFoldersFirst(node.children);
}
function folderFiles(node: TreeNode): TreeNode[] {
  return childrenOf(node).filter((c) => c.type === 'file');
}
function folderSubFolders(node: TreeNode): TreeNode[] {
  return childrenOf(node).filter((c) => c.type === 'folder');
}
function isGroupExpanded(path: string): boolean {
  return expandedGroups.value.has(path);
}
function toggleGroup(path: string) {
  const next = new Set(expandedGroups.value);
  if (next.has(path)) next.delete(path); else next.add(path);
  expandedGroups.value = next;
}

/** ====== 文件图标 / 类型标签 ====== */
function iconFor(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'].includes(ext)) return 'material-symbols:image';
  if (ext === 'pdf') return 'material-symbols:picture-as-pdf';
  if (['js', 'ts', 'py', 'c', 'cpp', 'h', 'java', 'go', 'rs', 'json', 'html', 'css'].includes(ext)) return 'material-symbols:code';
  return 'material-symbols:description';
}
function colorFor(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'].includes(ext)) return '#10b981';
  if (ext === 'pdf') return '#ef4444';
  if (['js', 'ts', 'py', 'c', 'cpp', 'h', 'java', 'go', 'rs', 'json', 'html', 'css'].includes(ext)) return '#8b5cf6';
  return '#2563eb';
}
function typeLabel(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  if (ext === 'md') return 'Markdown';
  if (ext === 'pdf') return 'PDF';
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'].includes(ext)) return '图片';
  if (['js', 'ts', 'py', 'c', 'cpp', 'h', 'java', 'go', 'rs', 'json', 'html', 'css'].includes(ext)) return '代码';
  return '文档';
}
import { formatDate } from '../utils/time';

function timeAgo(ts: number): string {
  if (!ts) return '未知时间';
  const diff = Date.now() - ts * 1000;
  const day = 86400000;
  if (diff < day) return '今天';
  if (diff < 2 * day) return '昨天';
  if (diff < 7 * day) return `${Math.floor(diff / day)} 天前`;
  return formatDate(ts * 1000, { month: 'short', day: 'numeric' });
}

/** ====== 最近浏览（localStorage） ====== */
function loadRecent() {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    if (raw) recentList.value = JSON.parse(raw);
  } catch { /* ignore */ }
}
function saveRecent() {
  try { localStorage.setItem(RECENT_KEY, JSON.stringify(recentList.value)); } catch { /* ignore */ }
}
function pushRecent(file: MarkdownData) {
  const parent = file.path.split('/').slice(0, -1).join('/');
  const item: RecentItem = {
    path: file.path,
    title: file.title,
    dir: cleanPath(parent),
    mtime: file.mtime || Math.floor(Date.now() / 1000),
    visitedAt: Date.now(),
  };
  const next = recentList.value.filter((r) => r.path !== file.path);
  next.unshift(item);
  recentList.value = next.slice(0, 6);
  saveRecent();
}
function clearRecent() {
  recentList.value = [];
  saveRecent();
}
const continueItem = computed(() => recentList.value[0] || null);

/** ====== 详情页面包屑 ====== */
const fileBreadcrumb = computed<BreadcrumbItem[]>(() => {
  if (!currentFile.value) return [];
  const parent = currentFile.value.path.split('/').slice(0, -1).join('/');
  return buildBreadcrumb(parent);
});

/** ====== 响应式 ====== */
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440);
const showRecent = computed(() => windowWidth.value >= 1280);
function onResize() {
  windowWidth.value = window.innerWidth;
  if (windowWidth.value >= 768) mobileSidebarOpen.value = false;
}
function toggleMobileSidebar() {
  mobileSidebarOpen.value = !mobileSidebarOpen.value;
}

/** ====== 滚动时高亮标题 ====== */
let scrollHandler: (() => void) | null = null;
function teardownScrollListener() {
  const container = document.querySelector('.learn-detail-main');
  if (container && scrollHandler) container.removeEventListener('scroll', scrollHandler);
  scrollHandler = null;
}
function setupScrollListener() {
  teardownScrollListener();
  const container = document.querySelector('.learn-detail-main');
  if (!container) return;
  scrollHandler = () => {
    const headings = mdContainer.value?.querySelectorAll('h1, h2, h3');
    if (!headings || headings.length === 0) return;
    let activeId = '';
    headings.forEach((el) => {
      const rect = el.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      if (rect.top <= containerRect.top + 100) activeId = el.id;
    });
    headings.forEach((el) => el.classList.toggle('heading-active', el.id === activeId));
  };
  container.addEventListener('scroll', scrollHandler, { passive: true });
}
watch(currentFile, (f) => {
  if (f) nextTick(setupScrollListener);
  else teardownScrollListener();
});

onMounted(async () => {
  window.addEventListener('resize', onResize);
  loadRecent();
  await loadTree();
  const queryPath = route.query.path as string;
  if (queryPath) await loadFile(queryPath);
  else navigateToFolder('');
  nextTick(() => setupScrollListener());
});

onUnmounted(() => {
  window.removeEventListener('resize', onResize);
  const container = document.querySelector('.learn-detail-main');
  if (container && scrollHandler) container.removeEventListener('scroll', scrollHandler);
});
</script>

<template>
  <div class="learn-shell">

    <!-- 移动端遮罩 -->
    <div v-if="mobileSidebarOpen" class="sidebar-overlay" @click="mobileSidebarOpen = false" />

    <!-- ===== 页面标题区 ===== -->
    <header class="learn-header">
      <div class="learn-header-left">
        <button v-if="windowWidth < 768" class="header-menu-btn" @click="toggleMobileSidebar">
          <Icon icon="material-symbols:menu" class="h-5 w-5" />
        </button>
        <div>
          <h1 class="learn-title">学习资源</h1>
          <p class="learn-subtitle">路径、资料、练习连成一条线</p>
        </div>
      </div>
      <div class="learn-stats">
        <span class="learn-stats-num">{{ totalFiles }}</span>
        <span class="learn-stats-unit">篇资料</span>
        <span class="learn-stats-divider">·</span>
        <span class="learn-stats-num">{{ totalCategories }}</span>
        <span class="learn-stats-unit">个分类</span>
      </div>
    </header>

    <!-- ===== 主体三栏 ===== -->
    <div class="learn-body">

      <!-- 左侧资源目录 -->
      <aside
        v-if="treeData"
        class="learn-sidebar-col"
        :class="{ 'is-open': mobileSidebarOpen }"
      >
        <Suspense>
          <LearnSidebar
            :tree="treeData.children || []"
            :current-path="currentLocation"
            :headings="mdHeadings"
            @select="handleSidebarSelect"
            @heading="handleSidebarHeading"
            @browse="handleSidebarBrowse"
            @rescan="rescanTree"
          />
        </Suspense>
      </aside>

      <!-- 中间主内容 -->
      <main class="learn-main-col">

        <!-- 加载中 -->
        <div v-if="isLoadingTree" class="learn-state">
          <Icon icon="svg-spinners:90-ring-with-bg" class="h-10 w-10 text-[#2563EB]" />
          <p class="mt-3 text-sm text-[#64748B]">正在扫描学习资料目录...</p>
        </div>

        <!-- 错误 -->
        <div v-else-if="error && !treeData" class="learn-state">
          <Icon icon="material-symbols:error-outline" class="h-10 w-10 text-[#EF4444]" />
          <p class="mt-2 text-sm text-[#EF4444]">{{ error }}</p>
          <button class="ui-btn ui-btn-primary mt-3" @click="loadTree">重试</button>
        </div>

        <!-- ===== 浏览模式 ===== -->
        <template v-else-if="treeData && !currentFile">

          <!-- 继续学习 -->
          <div v-if="continueItem" class="continue-banner" @click="openFile(continueItem.path)">
            <div class="continue-icon">
              <Icon icon="material-symbols:play-circle" class="h-6 w-6" />
            </div>
            <div class="continue-body">
              <span class="continue-label">继续学习</span>
              <span class="continue-title">{{ continueItem.title }}</span>
              <span class="continue-meta">{{ continueItem.dir }}</span>
            </div>
            <Icon icon="material-symbols:chevron-right" class="continue-arrow" />
          </div>

          <!-- 面包屑 -->
          <nav class="learn-breadcrumb">
            <button class="crumb-root" @click="navigateToFolder('')">学习资源</button>
            <template v-for="(c, i) in breadcrumb" :key="c.path">
              <Icon icon="material-symbols:chevron-right" class="crumb-sep" />
              <button
                :class="['crumb', i === breadcrumb.length - 1 && 'crumb-current']"
                @click="navigateToFolder(c.path)"
              >{{ c.name }}</button>
            </template>
          </nav>

          <!-- 工具栏 -->
          <div class="main-toolbar">
            <div class="toolbar-left">
              <Icon icon="material-symbols:folder" class="toolbar-folder-icon" />
              <h2 class="toolbar-title">目录结构</h2>
              <span class="toolbar-count">{{ currentFolderFileCount }} 个文件</span>
            </div>
            <div class="toolbar-search">
              <Icon icon="material-symbols:search" class="toolbar-search-icon" />
              <input
                v-model="middleSearch"
                type="text"
                placeholder="搜索当前目录中的资料"
                class="toolbar-search-input"
              />
            </div>
            <button class="ui-btn ui-btn-ghost ui-btn-sm toolbar-action" @click="router.push('/playground')">
              <Icon icon="material-symbols:code" class="h-4 w-4" />
              去编辑器练习
            </button>
          </div>

          <!-- 目录内容 -->
          <div class="dir-content">
            <!-- 文件夹分组 -->
            <div v-for="folder in filteredFolders" :key="folder.path" class="dir-group">
              <div class="dir-group-header" @click="navigateToFolder(folder.path)">
                <button
                  class="dir-group-toggle"
                  :class="{ 'is-open': isGroupExpanded(folder.path) }"
                  @click.stop="toggleGroup(folder.path)"
                >
                  <Icon icon="material-symbols:chevron-right" class="dir-group-chevron" />
                </button>
                <Icon icon="material-symbols:folder" class="dir-group-icon" />
                <span class="dir-group-name">{{ cleanName(folder.name) }}</span>
                <span class="dir-group-count">{{ countFiles(folder) }}</span>
                <Icon icon="material-symbols:chevron-right" class="dir-group-enter" />
              </div>

              <transition name="group-expand">
                <div v-if="isGroupExpanded(folder.path)" class="dir-group-body">
                  <button
                    v-for="f in folderFiles(folder)"
                    :key="f.path"
                    class="file-row"
                    @click="openFile(f.path)"
                  >
                    <Icon :icon="iconFor(f.name)" class="file-icon" :style="{ color: colorFor(f.name) }" />
                    <span class="file-name" :title="cleanName(f.name)">{{ cleanName(f.name) }}</span>
                    <span class="file-meta">{{ timeAgo(f.mtime || 0) }} · {{ typeLabel(f.name) }}</span>
                    <Icon icon="material-symbols:chevron-right" class="file-enter" />
                  </button>
                  <button
                    v-for="sub in folderSubFolders(folder)"
                    :key="sub.path"
                    class="file-row file-row-folder"
                    @click="navigateToFolder(sub.path)"
                  >
                    <Icon icon="material-symbols:folder" class="file-icon" style="color: #f59e0b" />
                    <span class="file-name" :title="cleanName(sub.name)">{{ cleanName(sub.name) }}</span>
                    <span class="file-meta">{{ countFiles(sub) }} 篇</span>
                    <Icon icon="material-symbols:chevron-right" class="file-enter" />
                  </button>
                </div>
              </transition>
            </div>

            <!-- 零散文件 -->
            <div v-if="filteredFiles.length" class="dir-files">
              <button
                v-for="f in filteredFiles"
                :key="f.path"
                class="file-row"
                @click="openFile(f.path)"
              >
                <Icon :icon="iconFor(f.name)" class="file-icon" :style="{ color: colorFor(f.name) }" />
                <span class="file-name" :title="cleanName(f.name)">{{ cleanName(f.name) }}</span>
                <span class="file-meta">{{ timeAgo(f.mtime || 0) }} · {{ typeLabel(f.name) }}</span>
                <Icon icon="material-symbols:chevron-right" class="file-enter" />
              </button>
            </div>

            <!-- 空状态 -->
            <div v-if="!filteredFolders.length && !filteredFiles.length" class="dir-empty">
              <Icon icon="material-symbols:folder-open" class="dir-empty-icon" />
              <p>该目录下暂无资料</p>
            </div>
          </div>
        </template>

        <!-- ===== 详情模式 ===== -->
        <template v-else-if="currentFile">
          <div class="learn-detail-main">
            <!-- 面包屑 -->
            <nav class="learn-breadcrumb">
              <button class="crumb-root" @click="backToBrowse">学习资源</button>
              <template v-for="c in fileBreadcrumb" :key="c.path">
                <Icon icon="material-symbols:chevron-right" class="crumb-sep" />
                <button class="crumb" @click="navigateToFolder(c.path)">{{ c.name }}</button>
              </template>
              <Icon icon="material-symbols:chevron-right" class="crumb-sep" />
              <span class="crumb crumb-current">{{ currentFile.title }}</span>
            </nav>

            <!-- 工具栏 -->
            <div class="main-toolbar">
              <button class="learn-back-btn" @click="backToBrowse">
                <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4" />
                返回目录
              </button>
              <div class="toolbar-right">
                <span class="detail-path">{{ currentFile.path }}</span>
                <button class="toolbar-icon-btn" title="导出 Markdown" @click="downloadCurrentMarkdown">
                  <Icon icon="material-symbols:download-rounded" class="h-4 w-4" />
                </button>
                <button class="toolbar-icon-btn" title="去编辑器练习" @click="router.push('/playground')">
                  <Icon icon="material-symbols:code" class="h-4 w-4" />
                </button>
              </div>
            </div>

            <!-- 加载中 -->
            <div v-if="isLoadingDoc" class="learn-state">
              <Icon icon="svg-spinners:90-ring-with-bg" class="h-8 w-8 text-[#2563EB]" />
              <p class="mt-2 text-sm text-[#64748B]">加载文档中...</p>
            </div>

            <!-- Markdown 内容 -->
            <article v-else ref="mdContainer" class="learn-doc-container">
              <h1 class="learn-doc-title">{{ currentFile.title }}</h1>
              <div class="learn-doc-meta">{{ currentFile.path }}</div>
              <Suspense>
                <MarkdownComponent
                  :source="currentFile.content"
                  :show-nav="false"
                  :base-dir="currentFile.path.split('/').slice(0, -1).join('/')"
                  @navigate="handleMdNavigate"
                />
              </Suspense>
            </article>
          </div>
        </template>
      </main>

      <!-- 右侧最近浏览 -->
      <aside v-if="showRecent && treeData" class="learn-recent-col">
        <RecentPanel
          :items="recentList"
          @open="openFile"
          @clear="clearRecent"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.learn-shell {
  min-height: 100vh;
  background: #f6f8fc;
}
:global(html.dark) .learn-shell { background: #0f172a; }

/* ===== 页面标题区 ===== */
.learn-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 24px 20px;
  min-height: 92px;
}
.learn-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.learn-title {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
  color: #1e293b;
  margin: 0;
}
:global(html.dark) .learn-title { color: #e5e7eb; }
.learn-subtitle {
  margin: 2px 0 0;
  font-size: 13px;
  color: #94a3b8;
}
.header-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  color: #475569;
  cursor: pointer;
}
:global(html.dark) .header-menu-btn { background: #1e293b; border-color: #334155; color: #cbd5e1; }

.learn-stats {
  display: flex;
  align-items: baseline;
  gap: 5px;
  white-space: nowrap;
}
.learn-stats-num {
  font-size: 22px;
  font-weight: 700;
  color: #2563eb;
  line-height: 1;
}
:global(html.dark) .learn-stats-num { color: #60a5fa; }
.learn-stats-unit {
  font-size: 13px;
  color: #64748b;
}
.learn-stats-divider {
  font-size: 13px;
  color: #cbd5e1;
  margin: 0 2px;
}

/* ===== 主体 ===== */
.learn-body {
  display: flex;
  align-items: flex-start;
  gap: 0;
  padding: 0 24px 40px;
}
.learn-sidebar-col {
  width: 280px;
  min-width: 280px;
  flex-shrink: 0;
  position: sticky;
  top: 76px;
  align-self: stretch;
  height: calc(100vh - 76px);
}
.learn-main-col {
  flex: 1;
  min-width: 0;
  padding: 0 24px;
  max-width: 920px;
}
.learn-recent-col {
  width: 280px;
  min-width: 280px;
  flex-shrink: 0;
  position: sticky;
  top: 104px;
  height: calc(100vh - 124px);
  border-left: 1px solid #e2e8f0;
  padding-left: 20px;
}
:global(html.dark) .learn-recent-col { border-left-color: #1e293b; }

/* ===== 状态 ===== */
.learn-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 0;
}

/* ===== 继续学习 ===== */
.continue-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 18px;
  background: linear-gradient(90deg, #eff6ff, #f5f3ff);
  border: 1px solid #dbeafe;
  border-radius: 12px;
  cursor: pointer;
  transition: box-shadow 0.15s, transform 0.15s;
}
.continue-banner:hover {
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.14);
  transform: translateY(-1px);
}
:global(html.dark) .continue-banner { background: #172554; border-color: #1e3a8a; }
.continue-icon { color: #2563eb; display: flex; }
:global(html.dark) .continue-icon { color: #60a5fa; }
.continue-body {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
  min-width: 0;
}
.continue-label {
  font-size: 11px;
  font-weight: 600;
  color: #2563eb;
  letter-spacing: 0.04em;
}
:global(html.dark) .continue-label { color: #60a5fa; }
.continue-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:global(html.dark) .continue-title { color: #e5e7eb; }
.continue-meta {
  font-size: 12px;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.continue-arrow { color: #2563eb; width: 20px; height: 20px; flex-shrink: 0; }
:global(html.dark) .continue-arrow { color: #60a5fa; }

/* ===== 面包屑 ===== */
.learn-breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px;
  margin-bottom: 12px;
  font-size: 13px;
}
.crumb-root, .crumb {
  border: none;
  background: none;
  cursor: pointer;
  color: #94a3b8;
  font-size: 13px;
  padding: 2px 4px;
  border-radius: 5px;
  transition: color 0.13s, background 0.13s;
  font-family: inherit;
}
.crumb-root:hover, .crumb:hover { color: #2563eb; background: #eff6ff; }
.crumb-current {
  color: #1e293b;
  font-weight: 600;
  cursor: default;
}
.crumb-current:hover { background: none; color: #1e293b; }
:global(html.dark) .crumb-current { color: #e5e7eb; }
.crumb-sep {
  width: 16px;
  height: 16px;
  color: #cbd5e1;
  flex-shrink: 0;
}
:global(html.dark) .crumb-sep { color: #475569; }

/* ===== 工具栏 ===== */
.main-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  margin-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}
:global(html.dark) .main-toolbar { border-bottom-color: #1e293b; }
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.toolbar-folder-icon { width: 20px; height: 20px; color: #2563eb; }
:global(html.dark) .toolbar-folder-icon { color: #60a5fa; }
.toolbar-title {
  font-size: 19px;
  font-weight: 650;
  color: #1e293b;
  margin: 0;
}
:global(html.dark) .toolbar-title { color: #e5e7eb; }
.toolbar-count {
  font-size: 12px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 10px;
}
:global(html.dark) .toolbar-count { background: #1e293b; color: #94a3b8; }
.toolbar-search {
  position: relative;
  flex: 1;
  max-width: 380px;
  margin-left: auto;
}
.toolbar-search-icon {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  color: #94a3b8; width: 16px; height: 16px;
}
.toolbar-search-input {
  width: 100%;
  height: 38px;
  padding: 0 12px 0 36px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  background: #fff;
  color: #1e293b;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.toolbar-search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}
.toolbar-search-input::placeholder { color: #94a3b8; }
:global(html.dark) .toolbar-search-input { background: #1e293b; border-color: #334155; color: #e2e8f0; }
.toolbar-action { flex-shrink: 0; }
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.detail-path {
  font-size: 12px;
  color: #94a3b8;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.toolbar-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  color: #64748b;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}
.toolbar-icon-btn:hover { background: #e2e8f0; color: #2563eb; }
:global(html.dark) .toolbar-icon-btn { background: #1e293b; color: #94a3b8; }
:global(html.dark) .toolbar-icon-btn:hover { background: #334155; color: #60a5fa; }

/* ===== 目录内容 ===== */
.dir-content { padding-top: 4px; }
.dir-group { margin-bottom: 4px; }
.dir-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 50px;
  padding: 0 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.13s;
}
.dir-group-header:hover { background: #f1f5f9; }
:global(html.dark) .dir-group-header:hover { background: #1e293b; }
.dir-group-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  background: none;
  cursor: pointer;
  color: #94a3b8;
  flex-shrink: 0;
}
.dir-group-chevron {
  width: 18px;
  height: 18px;
  transition: transform 0.16s ease;
}
.dir-group-toggle.is-open .dir-group-chevron { transform: rotate(90deg); }
.dir-group-icon { width: 20px; height: 20px; color: #f59e0b; flex-shrink: 0; }
.dir-group-name {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}
:global(html.dark) .dir-group-name { color: #cbd5e1; }
.dir-group-count {
  font-size: 12px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 2px 9px;
  border-radius: 10px;
  flex-shrink: 0;
}
:global(html.dark) .dir-group-count { background: #1e293b; color: #94a3b8; }
.dir-group-enter {
  width: 18px;
  height: 18px;
  color: #cbd5e1;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.13s;
}
.dir-group-header:hover .dir-group-enter { opacity: 1; }

.dir-group-body {
  padding: 2px 0 6px 30px;
  border-left: 1px solid #eef2f7;
  margin-left: 18px;
}
:global(html.dark) .dir-group-body { border-left-color: #1e293b; }

.dir-files { margin-top: 4px; }

/* 文件行 */
.file-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 44px;
  padding: 6px 10px;
  border: none;
  background: none;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: background 0.13s;
}
.file-row:hover { background: #f1f5f9; }
:global(html.dark) .file-row:hover { background: #1e293b; }
.file-icon { width: 18px; height: 18px; flex-shrink: 0; }
.file-name {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:global(html.dark) .file-name { color: #cbd5e1; }
.file-row:hover .file-name { color: #1e293b; }
:global(html.dark) .file-row:hover .file-name { color: #f1f5f9; }
.file-meta {
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
  white-space: nowrap;
}
.file-enter {
  width: 16px;
  height: 16px;
  color: #2563eb;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.13s;
}
.file-row:hover .file-enter { opacity: 1; }
:global(html.dark) .file-enter { color: #60a5fa; }

/* 空状态 */
.dir-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0;
  color: #94a3b8;
}
.dir-empty-icon { width: 36px; height: 36px; color: #cbd5e1; margin-bottom: 8px; }
:global(html.dark) .dir-empty-icon { color: #475569; }
.dir-empty p { margin: 0; font-size: 13px; }

/* ===== 详情页 ===== */
.learn-detail-main {
  height: calc(100vh - 76px);
  overflow-y: auto;
  padding: 4px 0 40px;
}
.learn-doc-container { max-width: 820px; }
.learn-doc-title {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 8px;
}
:global(html.dark) .learn-doc-title { color: #e5e7eb; }
.learn-doc-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 24px;
}
.learn-back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  background: #f1f5f9;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}
.learn-back-btn:hover { background: #e2e8f0; }
:global(html.dark) .learn-back-btn { background: #1e293b; color: #cbd5e1; }
:global(html.dark) .learn-back-btn:hover { background: #334155; }

/* ===== 分组展开动画 ===== */
.group-expand-enter-active,
.group-expand-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
  overflow: hidden;
}
.group-expand-enter-from,
.group-expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ===== 移动端遮罩 ===== */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: 40;
}

/* ===== 响应式 ===== */
@media (max-width: 1279px) {
  .learn-recent-col { display: none; }
  .learn-main-col { max-width: none; }
}
@media (max-width: 1023px) {
  .learn-sidebar-col {
    width: 240px;
    min-width: 240px;
  }
}
@media (max-width: 767px) {
  .learn-header { padding: 16px 16px 14px; min-height: 72px; }
  .learn-title { font-size: 24px; }
  .learn-body { padding: 0 12px 24px; }
  .learn-main-col { padding: 0; max-width: none; }
  .learn-sidebar-col {
    position: fixed;
    top: 0;
    left: 0;
    width: 280px;
    min-width: 280px;
    height: 100vh;
    z-index: 50;
    background: #fff;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: 2px 0 12px rgba(15, 23, 42, 0.12);
  }
  :global(html.dark) .learn-sidebar-col { background: #111827; }
  .learn-sidebar-col.is-open { transform: translateX(0); }
  .toolbar-search { max-width: none; }
  .detail-path { display: none; }
}
</style>
