<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';

interface TreeNode {
  id: string;
  title: string;
  markdownFile?: string;
  children?: TreeNode[];
}

const props = defineProps<{
  tree: TreeNode[];
  currentId?: string;
  currentChapterId?: string;
  headings?: { level: number; text: string; id: string }[];
}>();

const emit = defineEmits<{
  (e: 'select', node: TreeNode): void;
}>();

const activeTab = ref<'files' | 'headings'>('files');
const searchQuery = ref('');
const expandedIds = ref<Set<string>>(new Set());

const toggleExpand = (id: string) => {
  const next = new Set(expandedIds.value);
  if (next.has(id)) next.delete(id); else next.add(id);
  expandedIds.value = next;
};

const matchesSearch = (node: TreeNode, q: string): boolean => {
  if (!q) return true;
  const lower = q.toLowerCase();
  if (node.title.toLowerCase().includes(lower)) return true;
  return node.children?.some(c => matchesSearch(c, q)) ?? false;
};

const filteredTree = computed(() => {
  const q = searchQuery.value.trim();
  if (!q) return props.tree;
  return props.tree.filter(n => matchesSearch(n, q));
});

const autoExpandForCurrent = () => {
  if (!props.currentId) return;
  const findPath = (nodes: TreeNode[], target: string, path: string[] = []): string[] | null => {
    for (const n of nodes) {
      if (n.id === target) return [...path, n.id];
      if (n.children) {
        const found = findPath(n.children, target, [...path, n.id]);
        if (found) return found;
      }
    }
    return null;
  };
  const path = findPath(props.tree, props.currentId);
  if (path) {
    const next = new Set(expandedIds.value);
    path.forEach(id => next.add(id));
    expandedIds.value = next;
  }
};

watch(() => props.currentId, () => {
  nextTick(autoExpandForCurrent);
}, { immediate: true });

watch(searchQuery, (q) => {
  if (q.trim()) {
    const all = new Set<string>();
    const collect = (nodes: TreeNode[]) => {
      for (const n of nodes) {
        if (n.children?.length) { all.add(n.id); collect(n.children); }
      }
    };
    collect(props.tree);
    expandedIds.value = all;
  }
});

const currentHeadingId = ref('');
const headingObserver = ref<{ disconnect: () => void } | null>(null);

const setupHeadingObserver = () => {
  headingObserver.value?.disconnect();
  nextTick(() => {
    const container = document.querySelector('.learn-document');
    if (!container) return;
    const headings = container.querySelectorAll('h1[id], h2[id], h3[id]');
    if (!headings.length) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            currentHeadingId.value = e.target.id;
            break;
          }
        }
      },
      { rootMargin: '-80px 0px -60% 0px', threshold: 0 }
    );
    headings.forEach(h => observer.observe(h));
    headingObserver.value = observer;
  });
};

watch(() => props.headings, () => {
  if (activeTab.value === 'headings') setupHeadingObserver();
}, { immediate: true });

watch(activeTab, (tab) => {
  if (tab === 'headings') setupHeadingObserver();
  else headingObserver.value?.disconnect();
});

const scrollToFile = (node: TreeNode) => {
  emit('select', node);
};

const scrollToHeading = (id: string) => {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const isFileActive = (node: TreeNode) => {
  if (node.markdownFile && props.currentChapterId) {
    return node.id === props.currentChapterId;
  }
  return node.id === props.currentId;
};

const getFileIcon = (node: TreeNode) => {
  if (node.children?.length) return 'material-symbols:folder';
  return 'material-symbols:description';
};

const getFileIconColor = (node: TreeNode) => {
  if (node.children?.length) return 'text-amber-500';
  return 'text-blue-500';
};

const getHeadingIcon = (level: number) => {
  if (level === 1) return 'material-symbols:title';
  if (level === 2) return 'material-symbols:format-h2';
  return 'material-symbols:format-h3';
};
</script>

<template>
  <aside class="learn-file-sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">导航</h2>
    </div>

    <div class="sidebar-tabs">
      <button
        class="sidebar-tab"
        :class="{ active: activeTab === 'files' }"
        @click="activeTab = 'files'"
      >
        <Icon icon="material-symbols:folder-open" class="tab-icon" />
        资料目录
      </button>
      <button
        class="sidebar-tab"
        :class="{ active: activeTab === 'headings' }"
        :disabled="!headings?.length"
        @click="activeTab = 'headings'"
      >
        <Icon icon="material-symbols:format-list-bulleted" class="tab-icon" />
        本文目录
      </button>
    </div>

    <div v-if="activeTab === 'files'" class="sidebar-search">
      <Icon icon="material-symbols:search" class="search-icon" />
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索资料..."
        class="search-input"
      />
    </div>

    <div class="sidebar-scroll">
      <template v-if="activeTab === 'files'">
        <template v-if="filteredTree.length">
          <div v-for="node in filteredTree" :key="node.id">
            <button
              class="tree-folder"
              :class="{ expanded: expandedIds.has(node.id), active: node.id === currentId }"
              @click="node.children?.length ? toggleExpand(node.id) : scrollToFile(node)"
            >
              <span v-if="node.children?.length" class="expand-arrow">
                <Icon icon="material-symbols:chevron-right" class="arrow-icon" />
              </span>
              <span v-else class="expand-spacer" />
              <Icon :icon="getFileIcon(node)" class="tree-icon" :class="getFileIconColor(node)" />
              <span class="tree-label" :title="node.title">{{ node.title }}</span>
            </button>

            <Transition name="expand">
              <div v-if="node.children?.length && expandedIds.has(node.id)" class="tree-children">
                <button
                  v-for="child in node.children"
                  :key="child.id"
                  class="tree-file"
                  :class="{ active: isFileActive(child) }"
                  @click="scrollToFile(child)"
                >
                  <span class="expand-spacer" />
                  <Icon :icon="getFileIcon(child)" class="tree-icon" :class="getFileIconColor(child)" />
                  <span class="tree-label" :title="child.title">{{ child.title }}</span>
                </button>
              </div>
            </Transition>
          </div>
        </template>
        <div v-else class="sidebar-empty">
          <Icon icon="material-symbols:search-off" class="empty-icon" />
          <span>无匹配结果</span>
        </div>
      </template>

      <template v-else>
        <div v-if="headings?.length" class="heading-list">
          <button
            v-for="h in headings"
            :key="h.id"
            class="heading-item"
            :class="[
              `heading-level-${h.level}`,
              { active: currentHeadingId === h.id }
            ]"
            @click="scrollToHeading(h.id)"
          >
            <Icon :icon="getHeadingIcon(h.level)" class="heading-icon" />
            <span class="heading-text" :title="h.text">{{ h.text }}</span>
          </button>
        </div>
        <div v-else class="sidebar-empty">
          <Icon icon="material-symbols:article" class="empty-icon" />
          <span>暂无标题</span>
        </div>
      </template>
    </div>
  </aside>
</template>

<style scoped>
.learn-file-sidebar {
  position: sticky;
  top: 76px;
  width: 280px;
  min-width: 280px;
  height: calc(100vh - 76px);
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
}
:global(html.dark) .learn-file-sidebar {
  border-color: #1e293b;
  background: #0f172a;
}

.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid #e2e8f0;
}
:global(html.dark) .sidebar-header {
  border-color: #1e293b;
}
.sidebar-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}
:global(html.dark) .sidebar-title {
  color: #f1f5f9;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
}
:global(html.dark) .sidebar-tabs {
  border-color: #1e293b;
}
.sidebar-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 40px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
}
.sidebar-tab:hover:not(:disabled) {
  color: #334155;
  background: #f1f5f9;
}
.sidebar-tab.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}
.sidebar-tab:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
:global(html.dark) .sidebar-tab {
  color: #94a3b8;
}
:global(html.dark) .sidebar-tab:hover:not(:disabled) {
  color: #e2e8f0;
  background: #1e293b;
}
:global(html.dark) .sidebar-tab.active {
  color: #60a5fa;
  border-bottom-color: #2563eb;
}
.tab-icon {
  width: 14px;
  height: 14px;
}

.sidebar-search {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 8px 12px;
  height: 34px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background: white;
  transition: border-color 0.15s;
}
.sidebar-search:focus-within {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.08);
}
:global(html.dark) .sidebar-search {
  border-color: #334155;
  background: #1e293b;
}
.search-icon {
  width: 14px;
  height: 14px;
  color: #94a3b8;
  flex-shrink: 0;
}
.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 12px;
  color: #1e293b;
}
:global(html.dark) .search-input {
  color: #e2e8f0;
}

.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}
.sidebar-scroll::-webkit-scrollbar {
  width: 4px;
}
.sidebar-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}
:global(html.dark) .sidebar-scroll::-webkit-scrollbar-thumb {
  background: #334155;
}

/* Tree folder */
.tree-folder {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  height: 42px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  text-align: left;
  cursor: pointer;
  transition: background 0.12s;
}
.tree-folder:hover {
  background: #f1f5f9;
}
.tree-folder.active {
  background: #eff6ff;
  color: #2563eb;
}
:global(html.dark) .tree-folder {
  color: #e2e8f0;
}
:global(html.dark) .tree-folder:hover {
  background: #1e293b;
}
:global(html.dark) .tree-folder.active {
  background: #172554;
  color: #60a5fa;
}

.expand-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}
.tree-folder.expanded .expand-arrow {
  transform: rotate(90deg);
}
.arrow-icon {
  width: 16px;
  height: 16px;
  color: #94a3b8;
}
.expand-spacer {
  width: 16px;
  flex-shrink: 0;
}

.tree-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.tree-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Tree children */
.tree-children {
  overflow: hidden;
}
.tree-file {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  height: 34px;
  padding: 0 12px 0 34px;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  text-align: left;
  cursor: pointer;
  transition: background 0.12s;
  border-left: 3px solid transparent;
}
.tree-file:hover {
  background: #f1f5f9;
}
.tree-file.active {
  background: #eff6ff;
  color: #2563eb;
  border-left-color: #2563eb;
  font-weight: 700;
}
:global(html.dark) .tree-file {
  color: #94a3b8;
}
:global(html.dark) .tree-file:hover {
  background: #1e293b;
}
:global(html.dark) .tree-file.active {
  background: #172554;
  color: #60a5fa;
  border-left-color: #2563eb;
}

/* Expand animation */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  max-height: 500px;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

/* Heading list */
.heading-list {
  padding: 4px 0;
}
.heading-item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  height: 34px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  text-align: left;
  cursor: pointer;
  transition: background 0.12s;
  border-left: 3px solid transparent;
}
.heading-item:hover {
  background: #f1f5f9;
}
.heading-item.active {
  background: #eff6ff;
  color: #2563eb;
  border-left-color: #2563eb;
  font-weight: 700;
}
:global(html.dark) .heading-item {
  color: #94a3b8;
}
:global(html.dark) .heading-item:hover {
  background: #1e293b;
}
:global(html.dark) .heading-item.active {
  background: #172554;
  color: #60a5fa;
  border-left-color: #2563eb;
}

.heading-level-1 { padding-left: 12px; font-weight: 700; font-size: 13px; color: #1e293b; }
.heading-level-2 { padding-left: 24px; }
.heading-level-3 { padding-left: 36px; font-size: 11px; opacity: 0.8; }
:global(html.dark) .heading-level-1 { color: #e2e8f0; }

.heading-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: #94a3b8;
}
.heading-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 32px 16px;
  color: #94a3b8;
  font-size: 12px;
}
.empty-icon {
  width: 24px;
  height: 24px;
  opacity: 0.5;
}
</style>
