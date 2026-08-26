<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';
import { API_BASE_URL } from '../services/api';

const MarkdownComponent = defineAsyncComponent(
  () => import('../components/MarkdownComponent.vue'),
);
const LearnSidebar = defineAsyncComponent(
  () => import('../components/LearnSidebar.vue'),
);
const FolderPreview = defineAsyncComponent(
  () => import('../components/FolderPreview.vue'),
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

/** ====== 路由 ====== */
const route = useRoute();
const router = useRouter();

/** ====== 状态 ====== */
const treeData = ref<TreeNode | null>(null);
const currentFile = ref<MarkdownData | null>(null);
const isLoadingTree = ref(false);
const isLoadingDoc = ref(false);
const error = ref('');
const searchQuery = ref('');
const mdHeadings = ref<HeadingItem[]>([]);
const mdContainer = ref<HTMLElement | null>(null);

/** ====== 安全解析 JSON 响应（检测后端返回 HTML 错误页） ====== */
async function parseJsonSafe(res: Response): Promise<any> {
  const text = await res.text();
  const trimmed = text.trim();
  // 如果响应以 < 开头，说明是 HTML 页面（通常是 404/500 错误页），不是 JSON
  if (trimmed.startsWith('<')) {
    throw new Error('后端返回了非 JSON 响应（可能是服务未启动或接口不存在）');
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    throw new Error('响应解析失败');
  }
}

/** ====== 加载目录树 ====== */
async function loadTree() {
  isLoadingTree.value = true;
  error.value = '';
  try {
    const res = await fetch(`${API_BASE_URL}/learn-resources/tree`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await parseJsonSafe(res);
    treeData.value = json.data || null;
  } catch (e: any) {
    error.value = `目录加载失败: ${e.message}`;
  } finally {
    isLoadingTree.value = false;
  }
}

/** ====== 加载 Markdown 文件 ====== */
async function loadFile(filePath: string) {
  isLoadingDoc.value = true;
  error.value = '';
  try {
    const res = await fetch(`${API_BASE_URL}/learn-resources/file/${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await parseJsonSafe(res);
    currentFile.value = json.data;
    // 更新路由
    router.replace({ query: { path: filePath } });
  } catch (e: any) {
    error.value = `文件加载失败: ${e.message}`;
  } finally {
    isLoadingDoc.value = false;
  }
}

/** ====== 重新扫描 ====== */
async function rescanTree() {
  isLoadingTree.value = true;
  try {
    const res = await fetch(`${API_BASE_URL}/learn-resources/rescan`, { method: 'POST' });
    if (res.ok) await loadTree();
  } catch { /* ignore */ }
}

const currentBaseDir = computed(() => {
  const file = currentFile.value?.path;
  if (!file) return '';
  const parts = file.split('/');
  parts.pop();
  return parts.join('/');
});

const handleMdNavigate = async (filePath: string) => {
  isLoadingDoc.value = true;
  error.value = '';
  try {
    const res = await fetch(`${API_BASE_URL}/learn-resources/file/${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    currentFile.value = json.data;
    router.replace({ query: { path: filePath } });
  } catch (e: any) {
    error.value = `加载资料失败：${e.message}`;
  } finally {
    isLoadingDoc.value = false;
  }
};

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

// 监听 Markdown 内容变化，更新标题
watch(() => currentFile.value?.content, (content) => {
  if (content) {
    mdHeadings.value = parseHeadings(content);
    nextTick(() => addHeadingIds());
  }
}, { immediate: true });

/** ====== 为标题添加 ID 用于锚点跳转 ====== */
function addHeadingIds() {
  if (!mdContainer.value) return;
  const headings = mdContainer.value.querySelectorAll('h1, h2, h3');
  headings.forEach((el) => {
    const text = el.textContent?.trim() || '';
    const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
    el.id = id;
  });
}

/** ====== 侧边栏选择 ====== */
function handleSidebarSelect(pathOrId: string) {
  // 如果是标题 ID（不含 /），滚动到对应标题
  if (!pathOrId.includes('/')) {
    const el = document.getElementById(pathOrId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  // 否则加载文件
  loadFile(pathOrId);
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

/** ====== 统计文件数量 ====== */
function countFiles(node: TreeNode): number {
  if (node.type === 'file') return 1;
  if (!node.children) return 0;
  return node.children.reduce((sum, c) => sum + countFiles(c), 0);
}

const totalFiles = computed(() => treeData.value ? countFiles(treeData.value) : 0);

/** ====== 滚动时高亮标题 ====== */
let scrollHandler: (() => void) | null = null;

function setupScrollListener() {
  const container = document.querySelector('.learn-detail-main');
  if (!container) return;
  scrollHandler = () => {
    const headings = mdContainer.value?.querySelectorAll('h1, h2, h3');
    if (!headings || headings.length === 0) return;
    let activeId = '';
    headings.forEach((el) => {
      const rect = el.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      if (rect.top <= containerRect.top + 100) {
        activeId = el.id;
      }
    });
    // 更新当前高亮标题（通过 CSS）
    headings.forEach((el) => {
      el.classList.toggle('heading-active', el.id === activeId);
    });
  };
  container.addEventListener('scroll', scrollHandler, { passive: true });
}

onMounted(async () => {
  await loadTree();
  // 如果 URL 有 path 参数，自动打开
  const queryPath = route.query.path as string;
  if (queryPath) {
    await loadFile(queryPath);
  }
  nextTick(() => setupScrollListener());
});

onUnmounted(() => {
  const container = document.querySelector('.learn-detail-main');
  if (container && scrollHandler) {
    container.removeEventListener('scroll', scrollHandler);
  }
});
</script>

<template>
  <div class="min-h-screen bg-[#f6f8fc] dark:bg-[#0f172a]">

    <!-- ===== 列表模式（首页） ===== -->
    <div v-if="!currentFile" class="learn-layout">

      <!-- 左侧树形导航 -->
      <aside v-if="treeData" class="learn-sidebar-wrap">
        <Suspense>
          <LearnSidebar
            :tree="treeData.children || []"
            :current-path="''"
            :headings="mdHeadings"
            :search-query="searchQuery"
            @select="handleSidebarSelect"
            @rescan="rescanTree"
          />
        </Suspense>
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
            <span class="text-2xl font-black text-[#2563EB]">{{ totalFiles }}</span>
            <span class="text-xs text-[#64748B] dark:text-[#94A3B8]">篇文档</span>
          </div>
        </div>

        <!-- 搜索栏 -->
        <div class="mb-5 flex items-center gap-3">
          <div class="learn-search">
            <Icon icon="material-symbols:search" class="h-5 w-5 text-[#94A3B8]" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索学习资料..."
              class="learn-search-input"
            />
          </div>
          <button class="ui-btn ui-btn-ghost ui-btn-sm" @click="router.push('/playground')">
            <Icon icon="material-symbols:code" class="h-4 w-4" />
            去编辑器练习
          </button>
        </div>

        <!-- 加载中 -->
        <div v-if="isLoadingTree" class="learn-loading">
          <Icon icon="svg-spinners:90-ring-with-bg" class="h-10 w-10 text-[#2563EB]" />
          <p class="mt-3 text-sm text-[#64748B]">正在扫描学习资料目录...</p>
        </div>

        <!-- 错误 -->
        <div v-else-if="error && !treeData" class="learn-error">
          <Icon icon="material-symbols:error-outline" class="h-10 w-10 text-[#EF4444]" />
          <p class="mt-2 text-sm text-[#EF4444]">{{ error }}</p>
          <button class="ui-btn ui-btn-primary mt-3" @click="loadTree">重试</button>
        </div>

        <!-- 目录预览（首页卡片） -->
        <div v-else-if="treeData">
          <div class="mb-4 flex items-center gap-2">
            <Icon icon="material-symbols:folder" class="h-5 w-5 text-[#2563EB]" />
            <h2 class="text-lg font-black text-[#1E293B] dark:text-[#E5E7EB]">目录结构</h2>
          </div>
          <FolderPreview
            v-for="node in treeData.children || []"
            :key="node.id"
            :node="node"
            @open="loadFile"
          />
        </div>
      </section>
    </div>

    <!-- ===== 详情页模式 ===== -->
    <div v-else class="learn-detail-layout">

      <!-- 左侧树形导航 -->
      <aside v-if="treeData" class="learn-sidebar-wrap">
        <Suspense>
          <LearnSidebar
            :tree="treeData.children || []"
            :current-path="currentFile ? currentFile.path : ''"
            :headings="mdHeadings"
            :search-query="searchQuery"
            @select="handleSidebarSelect"
            @rescan="rescanTree"
          />
        </Suspense>
      </aside>

      <!-- 右侧内容 -->
      <div class="learn-detail-main">

        <!-- 工具栏 -->
        <div class="learn-toolbar">
          <button class="learn-back-btn" @click="currentFile = null; router.replace({ query: {} })">
            <Icon icon="material-symbols:arrow-back-rounded" class="h-4 w-4" />
            返回目录
          </button>

          <div class="flex items-center gap-2">
            <span v-if="currentFile.path" class="text-xs text-[#94A3B8]">{{ currentFile.path }}</span>
            <button class="learn-toolbar-btn" title="导出 Markdown" @click="downloadCurrentMarkdown">
              <Icon icon="material-symbols:download-rounded" class="h-4 w-4" />
            </button>
            <button class="learn-toolbar-btn" title="去编辑器练习" @click="router.push('/playground')">
              <Icon icon="material-symbols:code" class="h-4 w-4" />
            </button>
          </div>
        </div>

        <!-- 加载中 -->
        <div v-if="isLoadingDoc" class="learn-doc-loading">
          <Icon icon="svg-spinners:90-ring-with-bg" class="h-8 w-8 text-[#2563EB]" />
          <p class="mt-2 text-sm text-[#64748B]">加载文档中...</p>
        </div>

        <!-- Markdown 内容 -->
        <article v-else-if="currentFile" ref="mdContainer" class="learn-doc-container">
          <h1 class="learn-doc-title">{{ currentFile.title }}</h1>
          <div class="learn-doc-meta">
            <span>{{ currentFile.path }}</span>
          </div>
          <Suspense>
            <MarkdownComponent :source="currentFile.content" :show-nav="false" :base-dir="currentBaseDir" @navigate="handleMdNavigate" />
          </Suspense>
        </article>

        <!-- 错误 -->
        <div v-else-if="error" class="learn-error">
          <Icon icon="material-symbols:error-outline" class="h-10 w-10 text-[#EF4444]" />
          <p class="mt-2 text-sm text-[#EF4444]">{{ error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ===== 列表页布局 ===== */
.learn-layout {
  display: flex;
  gap: 0;
  min-height: 100vh;
}
.learn-sidebar-wrap {
  width: 280px;
  min-width: 280px;
  flex-shrink: 0;
}

/* ===== 详情页布局 ===== */
.learn-detail-layout {
  display: flex;
  min-height: 100vh;
}
.learn-detail-main {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow-y: auto;
  height: 100vh;
  padding: 24px 32px;
}

/* ===== 统计卡片 ===== */
.learn-stats-card {
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 16px;
}
:global(html.dark) .learn-stats-card {
  background: #1e293b;
  border-color: #334155;
}

/* ===== 搜索 ===== */
.learn-search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0 12px;
  flex: 1;
  max-width: 400px;
}
:global(html.dark) .learn-search {
  background: #1e293b;
  border-color: #334155;
}
.learn-search-input {
  width: 100%;
  padding: 10px 0;
  border: none;
  outline: none;
  font-size: 14px;
  background: transparent;
  color: #1e293b;
}
.learn-search-input::placeholder {
  color: #94a3b8;
}
:global(html.dark) .learn-search-input {
  color: #e2e8f0;
}

/* ===== 加载/错误 ===== */
.learn-loading, .learn-error, .learn-doc-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 0;
}

/* ===== 工具栏 ===== */
.learn-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}
:global(html.dark) .learn-toolbar {
  border-bottom-color: #1e293b;
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
.learn-back-btn:hover {
  background: #e2e8f0;
}
:global(html.dark) .learn-back-btn {
  background: #1e293b;
  color: #cbd5e1;
}
:global(html.dark) .learn-back-btn:hover {
  background: #334155;
}
.learn-toolbar-btn {
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
.learn-toolbar-btn:hover {
  background: #e2e8f0;
  color: #2563eb;
}
:global(html.dark) .learn-toolbar-btn {
  background: #1e293b;
  color: #94a3b8;
}
:global(html.dark) .learn-toolbar-btn:hover {
  background: #334155;
  color: #60a5fa;
}

/* ===== 文档内容 ===== */
.learn-doc-container {
  max-width: 860px;
  margin: 0 auto;
}
.learn-doc-title {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 8px;
}
:global(html.dark) .learn-doc-title {
  color: #e5e7eb;
}
.learn-doc-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 24px;
}

/* ===== 文件夹预览卡片 ===== */
.preview-folder {
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: white;
  overflow: hidden;
}
:global(html.dark) .preview-folder {
  border-color: #1e293b;
  background: #1e293b;
}
.preview-folder-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
:global(html.dark) .preview-folder-header {
  background: #0f172a;
  border-bottom-color: #1e293b;
}
.preview-folder-icon {
  width: 20px;
  height: 20px;
  color: #f59e0b;
  flex-shrink: 0;
}
.preview-folder-name {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  flex: 1;
}
:global(html.dark) .preview-folder-name {
  color: #e2e8f0;
}
.preview-folder-count {
  font-size: 12px;
  color: #94a3b8;
}
.preview-folder-children {
  padding: 8px 16px;
}
.preview-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s;
}
.preview-file:hover {
  background: #eff6ff;
}
:global(html.dark) .preview-file:hover {
  background: #172554;
}
.preview-file-icon {
  width: 16px;
  height: 16px;
  color: #2563eb;
  flex-shrink: 0;
}
:global(html.dark) .preview-file-icon {
  color: #60a5fa;
}
.preview-file-name {
  font-size: 13px;
  color: #475569;
}
:global(html.dark) .preview-file-name {
  color: #cbd5e1;
}

/* ===== 移动端适配 ===== */
@media (max-width: 768px) {
  .learn-layout, .learn-detail-layout {
    flex-direction: column;
  }
  .learn-sidebar-wrap {
    width: 100%;
    min-width: 100%;
    height: auto;
    max-height: 50vh;
  }
  .learn-detail-main {
    padding: 16px;
  }
}
</style>
