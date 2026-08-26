<script setup lang="ts">
import { computed } from 'vue';
import { Icon } from '@iconify/vue';

interface TreeNode {
  id: string;
  name: string;
  type: 'folder' | 'file';
  path: string;
  children?: TreeNode[];
}

const props = withDefaults(defineProps<{
  node: TreeNode;
  currentPath?: string;
  expandedPaths: Set<string>;
  depth?: number;
}>(), {
  currentPath: '',
  depth: 0,
});

const emit = defineEmits<{
  (e: 'toggle', path: string): void;
  (e: 'select', path: string): void;
}>();

const PREFIX_RE = /^\d+[-_.\s]+/;
function displayName(name: string): string {
  return name.replace(PREFIX_RE, '');
}

const isFolder = computed(() => props.node.type === 'folder');
const isExpanded = computed(() => props.expandedPaths.has(props.node.path));
const isActive = computed(() => !isFolder.value && props.currentPath === props.node.path);
const paddingLeft = computed(() => `${12 + props.depth * 16}px`);

const childNodes = computed(() => {
  if (!props.node.children) return [];
  return [...props.node.children].sort((a, b) => {
    if (a.type === 'folder' && b.type !== 'folder') return -1;
    if (a.type !== 'folder' && b.type === 'folder') return 1;
    return a.name.localeCompare(b.name, 'zh-CN');
  });
});

const cleanName = computed(() => displayName(props.node.name));

function handleClick() {
  if (isFolder.value) {
    emit('toggle', props.node.path);
  } else {
    emit('select', props.node.path);
  }
}
</script>

<template>
  <div>
    <button
      :class="[
        'fn-node',
        isFolder ? 'fn-folder' : 'fn-file',
        isActive && 'fn-active',
      ]"
      :style="{ paddingLeft }"
      @click="handleClick"
    >
      <template v-if="isFolder">
        <Icon
          icon="material-symbols:chevron-right-rounded"
          :class="['fn-arrow', isExpanded && 'fn-arrow-open']"
        />
        <Icon :icon="isExpanded ? 'material-symbols:folder-open' : 'material-symbols:folder'" class="fn-icon fn-icon-folder" />
      </template>
      <template v-else>
        <Icon icon="material-symbols:description" class="fn-icon fn-icon-file" />
      </template>
      <span class="fn-name">{{ cleanName }}</span>
      <span v-if="isFolder && node.children?.length" class="fn-count">
        {{ node.children.length }}
      </span>
    </button>

    <div v-if="isFolder && isExpanded" class="fn-children">
      <FolderNode
        v-for="child in childNodes"
        :key="child.id"
        :node="child"
        :current-path="currentPath"
        :expanded-paths="expandedPaths"
        :depth="depth + 1"
        @toggle="(p: string) => emit('toggle', p)"
        @select="(p: string) => emit('select', p)"
      />
    </div>
  </div>
</template>

<style scoped>
.fn-node {
  display: flex;
  align-items: center;
  width: 100%;
  text-align: left;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
  color: #475569;
  padding: 6px 12px;
  transition: background 0.12s, color 0.12s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: inherit;
  line-height: 1.4;
}
.fn-node:hover {
  background: #f1f5f9;
}
:global(html.dark) .fn-node {
  color: #cbd5e1;
}
:global(html.dark) .fn-node:hover {
  background: #1e293b;
}

.fn-active {
  background: #eff6ff !important;
  color: #2563eb !important;
  font-weight: 600;
  box-shadow: inset 3px 0 0 #2563eb;
}
:global(html.dark) .fn-active {
  background: #172554 !important;
  color: #60a5fa !important;
  box-shadow: inset 3px 0 0 #60a5fa;
}

.fn-arrow {
  width: 14px;
  height: 14px;
  margin-right: 2px;
  flex-shrink: 0;
  color: #94a3b8;
  transition: transform 0.15s;
}
.fn-arrow-open {
  transform: rotate(90deg);
}
.fn-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  flex-shrink: 0;
}
.fn-icon-folder {
  color: #f59e0b;
}
.fn-icon-file {
  color: #94a3b8;
}
.fn-active .fn-icon-file {
  color: #2563eb;
}
:global(html.dark) .fn-active .fn-icon-file {
  color: #60a5fa;
}

.fn-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fn-count {
  font-size: 11px;
  color: #94a3b8;
  margin-left: 4px;
  flex-shrink: 0;
}

.fn-children {
  /* 子节点自然缩进，由 depth 控制 */
}
</style>
