<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import FolderNode from './FolderNode.vue';

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

interface HeadingItem {
  level: number;
  text: string;
  id: string;
}

const props = defineProps<{
  tree: TreeNode[];
  currentPath?: string;
  headings?: HeadingItem[];
  searchQuery?: string;
}>();

const emit = defineEmits<{
  (e: 'select', path: string): void;
  (e: 'rescan'): void;
}>();

/** ====== 状态 ====== */
const activeTab = ref<'files' | 'headings'>('files');
const localSearch = ref('');
const effectiveSearch = computed(() => props.searchQuery || localSearch.value);
const expandedPaths = ref<Set<string>>(new Set());
const STORAGE_KEY = 'learn_sidebar_expanded';

/** ====== 递归：搜索过滤 ====== */
function filterTree(nodes: TreeNode[], q: string): TreeNode[] {
  if (!q) return nodes;
  const lower = q.toLowerCase();
  const result: TreeNode[] = [];
  for (const node of nodes) {
    if (node.type === 'folder') {
      const filtered = filterTree(node.children || [], q);
      if (filtered.length > 0 || node.name.toLowerCase().includes(lower)) {
        result.push({ ...node, children: filtered });
      }
    } else if (node.name.toLowerCase().includes(lower)) {
      result.push(node);
    }
  }
  return result;
}

const displayTree = computed(() => filterTree(props.tree, effectiveSearch.value));

/** ====== 自动展开当前路径的所有父级 ====== */
function expandAncestors(path: string) {
  const parts = path.split('/');
  const next = new Set(expandedPaths.value);
  let accumulated = '';
  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i] || '';
    accumulated = accumulated ? accumulated + '/' + part : part;
    next.add(accumulated);
  }
  expandedPaths.value = next;
}

onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) expandedPaths.value = new Set(JSON.parse(saved));
  } catch { /* ignore */ }
  if (props.currentPath) expandAncestors(props.currentPath);
});

watch(() => props.currentPath, (p) => {
  if (p) {
    expandAncestors(p);
    nextTick(() => {
      const el = document.querySelector('.tree-node-active');
      if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    });
  }
});

watch(expandedPaths, (val) => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify([...val])); } catch { /* ignore */ }
}, { deep: true });

function toggleExpand(path: string) {
  const next = new Set(expandedPaths.value);
  if (next.has(path)) next.delete(path); else next.add(path);
  expandedPaths.value = next;
}

function handleSelect(path: string) {
  emit('select', path);
}
</script>

<template>
  <div class="learn-sidebar">
    <!-- 搜索框 -->
    <div class="sidebar-search">
      <Icon icon="material-symbols:search" class="search-icon" />
      <input
        v-model="localSearch"
        type="text"
        placeholder="搜索资料…"
        class="search-input"
      />
      <button v-if="localSearch" class="search-clear" @click="localSearch = ''">
        <Icon icon="material-symbols:close" class="h-3 w-3" />
      </button>
    </div>

    <!-- Tab 切换 -->
    <div class="sidebar-tabs">
      <button :class="['tab-btn', activeTab === 'files' && 'tab-active']" @click="activeTab = 'files'">
        资料目录
      </button>
      <button :class="['tab-btn', activeTab === 'headings' && 'tab-active']" @click="activeTab = 'headings'">
        本文目录
      </button>
      <button v-if="activeTab === 'files'" class="tab-rescan" title="重新扫描" @click="emit('rescan')">
        <Icon icon="material-symbols:refresh" class="h-4 w-4" />
      </button>
    </div>

    <!-- 文件树 -->
    <div v-show="activeTab === 'files'" class="tree-content">
      <div v-if="displayTree.length === 0" class="tree-empty">
        <Icon icon="material-symbols:folder-off" class="empty-icon" />
        <p class="empty-text">{{ effectiveSearch ? '无匹配结果' : '暂无学习资料' }}</p>
      </div>
      <template v-else>
        <FolderNode
          v-for="node in displayTree"
          :key="node.id"
          :node="node"
          :current-path="currentPath || ''"
          :expanded-paths="expandedPaths"
          :depth="0"
          @toggle="toggleExpand"
          @select="handleSelect"
        />
      </template>
    </div>

    <!-- 本文目录 -->
    <div v-show="activeTab === 'headings'" class="tree-content">
      <div v-if="!headings || headings.length === 0" class="tree-empty">
        <Icon icon="material-symbols:text-snippet" class="empty-icon" />
        <p class="empty-text">无标题结构</p>
      </div>
      <div v-else>
        <button
          v-for="(h, i) in headings"
          :key="i"
          :class="['heading-item', `heading-level-${h.level}`]"
          @click="emit('select', h.id)"
        >
          <span class="heading-text">{{ h.text }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.learn-sidebar {
  width: 280px;
  min-width: 280px;
  height: 100vh;
  position: sticky;
  top: 76px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  z-index: 20;
  overflow: hidden;
}
:global(html.dark) .learn-sidebar {
  background: #111827;
  border-right-color: #1e293b;
}

.sidebar-search {
  padding: 12px;
  border-bottom: 1px solid #e2e8f0;
  position: relative;
}
:global(html.dark) .sidebar-search { border-bottom-color: #1e293b; }
.search-icon {
  position: absolute; left: 20px; top: 50%; transform: translateY(-50%);
  color: #94a3b8; width: 16px; height: 16px;
}
.search-input {
  width: 100%; padding: 7px 32px 7px 32px;
  border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px;
  outline: none; background: #f8fafc; color: #1e293b; transition: border-color 0.2s;
}
.search-input:focus { border-color: #3b82f6; }
.search-input::placeholder { color: #94a3b8; }
:global(html.dark) .search-input {
  background: #1e293b; border-color: #334155; color: #e2e8f0;
}
.search-clear {
  position: absolute; right: 20px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; color: #94a3b8; padding: 2px;
}
.search-clear:hover { color: #64748b; }

.sidebar-tabs {
  display: flex; align-items: center; padding: 8px 12px; gap: 4px;
  border-bottom: 1px solid #e2e8f0;
}
:global(html.dark) .sidebar-tabs { border-bottom-color: #1e293b; }
.tab-btn {
  flex: 1; padding: 6px 0; border: none; background: none;
  font-size: 12px; font-weight: 600; color: #64748b; cursor: pointer;
  border-radius: 4px; transition: all 0.15s;
}
.tab-btn:hover { background: #f1f5f9; color: #475569; }
.tab-active { color: #2563eb; background: #eff6ff; }
:global(html.dark) .tab-btn:hover { background: #1e293b; }
:global(html.dark) .tab-active { color: #60a5fa; background: #172554; }
.tab-rescan {
  background: none; border: none; cursor: pointer; color: #64748b;
  padding: 4px; border-radius: 4px; transition: all 0.2s; margin-left: 4px;
}
.tab-rescan:hover { color: #2563eb; background: #eff6ff; }
:global(html.dark) .tab-rescan:hover { color: #60a5fa; background: #172554; }

.tree-content {
  flex: 1; overflow-y: auto; padding: 8px 0;
}
.tree-content::-webkit-scrollbar { width: 4px; }
.tree-content::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }
:global(html.dark) .tree-content::-webkit-scrollbar-thumb { background: #334155; }

.tree-empty { padding: 32px 16px; text-align: center; }
.empty-icon { width: 32px; height: 32px; color: #cbd5e1; margin-bottom: 8px; }
:global(html.dark) .empty-icon { color: #475569; }
.empty-text { font-size: 12px; color: #94a3b8; margin: 0; }

.heading-item {
  display: block; width: 100%; text-align: left; border: none; background: none;
  cursor: pointer; font-size: 13px; color: #475569; padding: 5px 12px;
  transition: background 0.12s, color 0.12s; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; font-family: inherit;
}
.heading-item:hover { background: #f1f5f9; color: #2563eb; }
:global(html.dark) .heading-item { color: #cbd5e1; }
:global(html.dark) .heading-item:hover { background: #1e293b; color: #60a5fa; }
.heading-level-1 { padding-left: 12px; font-weight: 600; }
.heading-level-2 { padding-left: 24px; }
.heading-level-3 { padding-left: 36px; font-size: 12px; }
</style>
