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

const props = defineProps<{
  node: TreeNode;
}>();

const emit = defineEmits<{
  (e: 'open', path: string): void;
}>();

const PREFIX_RE = /^\d+[-_.\s]+/;
function displayName(name: string): string {
  return name.replace(PREFIX_RE, '');
}

function countFiles(node: TreeNode): number {
  if (node.type === 'file') return 1;
  if (!node.children) return 0;
  return node.children.reduce((sum, c) => sum + countFiles(c), 0);
}

const isFile = computed(() => props.node.type === 'file');
const fileCount = computed(() => countFiles(props.node));
const cleanName = computed(() => displayName(props.node.name));
const sortedChildren = computed(() => {
  if (!props.node.children) return [];
  return [...props.node.children].sort((a, b) => {
    if (a.type === 'folder' && b.type !== 'folder') return -1;
    if (a.type !== 'folder' && b.type === 'folder') return 1;
    return a.name.localeCompare(b.name, 'zh-CN');
  });
});

function handleClick() {
  if (isFile.value) {
    emit('open', props.node.path);
  }
}
</script>

<template>
  <div v-if="isFile" class="preview-file" @click="handleClick">
    <Icon icon="material-symbols:description" class="preview-file-icon" />
    <span class="preview-file-name">{{ cleanName }}</span>
  </div>
  <div v-else class="preview-folder">
    <div class="preview-folder-header">
      <Icon icon="material-symbols:folder" class="preview-folder-icon" />
      <span class="preview-folder-name">{{ cleanName }}</span>
      <span class="preview-folder-count">{{ fileCount }} 篇</span>
    </div>
    <div class="preview-folder-children">
      <FolderPreview
        v-for="child in sortedChildren"
        :key="child.id"
        :node="child"
        @open="(p: string) => emit('open', p)"
      />
    </div>
  </div>
</template>

<style scoped>
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
</style>
