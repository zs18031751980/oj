<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'

defineProps<{
  stdin: string
  expectedOutput: string
  output: string
  status: string
  verdict: 'pass' | 'fail' | null
  isRunning: boolean
}>()

const emit = defineEmits<{
  'update:stdin': [value: string]
  'update:expectedOutput': [value: string]
  'run': []
}>()

const collapsed = ref(false)
const panelHeight = ref(300)
const dragging = ref(false)

const onDragStart = (e: MouseEvent) => {
  dragging.value = true
  const startY = e.clientY
  const startHeight = panelHeight.value
  const onMouseMove = (ev: MouseEvent) => {
    const delta = startY - ev.clientY
    panelHeight.value = Math.max(180, Math.min(700, startHeight + delta))
  }
  const onMouseUp = () => {
    dragging.value = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
</script>

<template>
  <div class="self-test-panel" :class="{ 'panel-collapsed': collapsed }">
    <div
      class="drag-handle"
      :class="{ 'drag-active': dragging }"
      @mousedown.prevent="onDragStart"
    >
      <Icon icon="material-symbols:drag-indicator" class="drag-icon" />
    </div>

    <div class="panel-header">
      <div class="flex items-center gap-2">
        <Icon icon="material-symbols:test-tube" class="h-4 w-4 text-cyan-500" />
        <span class="text-xs font-bold text-slate-600 dark:text-slate-400">自测运行</span>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="run-btn"
          :disabled="isRunning"
          @click="emit('run')"
        >
          <Icon
            :icon="isRunning ? 'material-symbols:hourglass-top' : 'material-symbols:play-arrow'"
            class="h-3.5 w-3.5"
            :class="{ 'animate-spin': isRunning }"
          />
          {{ isRunning ? '运行中...' : '运行' }}
        </button>
        <button
          class="collapse-btn"
          :title="collapsed ? '展开' : '收起'"
          @click="collapsed = !collapsed"
        >
          <Icon
            :icon="collapsed ? 'material-symbols:unfold-less-rounded' : 'material-symbols:unfold-more-rounded'"
            class="h-4 w-4"
          />
        </button>
      </div>
    </div>

    <div v-show="!collapsed" class="panel-body" :style="{ height: panelHeight + 'px' }">
      <div class="body-scroll">
        <textarea
          :value="stdin"
          class="panel-textarea"
          placeholder="如果代码需要输入，可以在这里填写测试数据。"
          rows="3"
          @input="emit('update:stdin', ($event.target as HTMLTextAreaElement).value)"
        ></textarea>
        <textarea
          :value="expectedOutput"
          class="panel-textarea"
          placeholder="预期结果（选填）：填写后自动对比实际输出。"
          rows="2"
          @input="emit('update:expectedOutput', ($event.target as HTMLTextAreaElement).value)"
        ></textarea>
        <div v-if="output" class="result-section">
          <div class="result-header">
            <span>输出</span>
            <span
              v-if="verdict"
              class="result-badge"
              :class="verdict === 'pass' ? 'badge-pass' : 'badge-fail'"
            >{{ verdict === 'pass' ? 'PASS' : 'FAILED' }}</span>
          </div>
          <div class="result-body-wrap">
            <pre
              class="result-body"
              :class="{ 'result-error': verdict === 'fail' }"
            >{{ output }}</pre>
            <div v-if="status" class="result-footer">
              <span :class="verdict === 'pass' ? 'text-emerald-500' : 'text-rose-500'">{{ status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.self-test-panel {
  border-top: 1px solid #e2e8f0;
  background: #fff;
  position: relative;
}
:global(.dark) .self-test-panel {
  border-color: #1e293b;
  background: #0f172a;
}

.panel-collapsed .panel-body {
  display: none;
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 14px;
  cursor: ns-resize;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  user-select: none;
}
:global(.dark) .drag-handle {
  background: #1e293b;
  border-color: #334155;
}
.drag-handle:hover,
.drag-active {
  background: #e2e8f0;
}
:global(.dark) .drag-handle:hover,
:global(.dark) .drag-active {
  background: #334155;
}

.drag-icon {
  font-size: 14px;
  color: #94a3b8;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 1.25rem;
}

.run-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  border-radius: 0.5rem;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #059669;
  background: #ecfdf5;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.run-btn:hover:not(:disabled) {
  background: #d1fae5;
}
.run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
:global(.dark) .run-btn {
  color: #34d399;
  background: rgba(52, 211, 153, 0.15);
}
:global(.dark) .run-btn:hover:not(:disabled) {
  background: rgba(52, 211, 153, 0.25);
}

.collapse-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  padding: 0.25rem;
  color: #94a3b8;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.collapse-btn:hover {
  background: #f1f5f9;
}
:global(.dark) .collapse-btn:hover {
  background: #1e293b;
}

.panel-body {
  overflow: hidden;
  transition: height 0.1s ease;
}

.body-scroll {
  height: 100%;
  overflow-y: auto;
  padding: 0 1.25rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.panel-textarea {
  display: block;
  width: 100%;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  padding: 0.625rem;
  font-size: 0.75rem;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  color: #1e293b;
  outline: none;
  transition: border-color 0.15s;
  resize: vertical;
}
.panel-textarea:focus {
  border-color: #22d3ee;
}
:global(.dark) .panel-textarea {
  border-color: #334155;
  background: rgba(30, 41, 59, 0.5);
  color: #f1f5f9;
}
:global(.dark) .panel-textarea:focus {
  border-color: #22d3ee;
}

.result-section {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  overflow: hidden;
}
:global(.dark) .result-section {
  border-color: #1e293b;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  font-weight: 800;
  color: #1e293b;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}
:global(.dark) .result-header {
  color: #f8fafc;
  background: #0f172a;
  border-color: #1e293b;
}

.result-body-wrap {
  overflow: hidden;
}

.result-body {
  min-height: 48px;
  padding: 12px 18px;
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
  background: linear-gradient(to bottom, #f1f5f9 95%, #e2e8f0 95%, #e2e8f0 100%);
  color: #1e293b;
}
:global(.dark) .result-body {
  background: linear-gradient(to bottom, #020617 95%, #0f172a 95%, #0f172a 100%);
  color: #6ee7b7;
}

.result-error {
  color: #dc2626;
}
:global(.dark) .result-error {
  color: #fca5a5;
}

.result-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0.35rem 0.75rem;
  font-size: 0.7rem;
  font-weight: 600;
  background: #e2e8f0;
  border-top: 1px dashed #94a3b8;
}
:global(.dark) .result-footer {
  background: #0f172a;
  border-color: #475569;
}

.result-badge {
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.05em;
  padding: 1px 8px;
  border-radius: 999px;
}
.badge-pass {
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
}
.badge-fail {
  color: #ef4444;
  background: rgba(68, 68, 239, 0.15);
}
</style>
