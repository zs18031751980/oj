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
    panelHeight.value = Math.max(220, startHeight + delta)
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
          {{ isRunning ? '运行中...' : '运行代码' }}
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
        <section class="surface-panel">
          <div class="collapse-header">
            <div class="flex items-center gap-2">
              <Icon icon="material-symbols:input" class="h-5 w-5 text-amber-500" />
              <span>输入数据</span>
            </div>
          </div>
          <div class="collapse-body">
            <textarea
              :value="stdin"
              class="plain-textarea panel-textarea"
              placeholder="如果代码需要输入，可以在这里填写测试数据。"
              @input="emit('update:stdin', ($event.target as HTMLTextAreaElement).value)"
            ></textarea>
            <textarea
              :value="expectedOutput"
              class="plain-textarea panel-textarea"
              placeholder="预期结果（选填）：填写后自动对比实际输出"
              style="margin-top: 8px;"
              @input="emit('update:expectedOutput', ($event.target as HTMLTextAreaElement).value)"
            ></textarea>
          </div>
        </section>

        <section class="surface-panel">
          <div class="collapse-header">
            <div class="flex items-center gap-2">
              <Icon icon="material-symbols:output" class="h-5 w-5 text-emerald-500" />
              <span>输出</span>
            </div>
            <span
              v-if="verdict"
              class="test-badge"
              :class="verdict === 'pass' ? 'pass' : 'failed'"
            >{{ verdict === 'pass' ? '✓ PASS' : '✗ FAILED' }}</span>
          </div>
          <div class="collapse-body output-body">
            <div v-if="output" class="output-box" :class="{ 'has-output': output }">
              <pre :class="verdict === 'fail' ? 'text-rose-300' : 'text-emerald-300'">{{ output }}</pre>
            </div>
            <div v-else class="output-box">
              <div class="placeholder-copy">运行结果和报错都会显示在这里。</div>
            </div>
            <div v-if="status" class="output-status">
              <div class="status-divider"></div>
              <div class="status-content">
                <span class="status-text" :class="verdict === 'pass' ? 'text-emerald-400' : 'text-rose-400'">{{ status }}</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.self-test-panel {
  background: #fff;
  position: relative;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.08);
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
.drag-handle:hover,
.drag-active {
  background: #e2e8f0;
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
  padding: 0.375rem 0.875rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #fff;
  background: #14b8a6;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
  min-width: 8rem;
  justify-content: center;
}
.run-btn:hover:not(:disabled) {
  background: #0d9488;
}
.run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.panel-body {
  overflow: hidden;
  transition: height 0.1s ease;
}

.body-scroll {
  height: 100%;
  overflow-y: auto;
  padding: 0 1.25rem 0.75rem;
  display: flex;
  gap: 0.75rem;
}

.surface-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.collapse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #1e293b;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.collapse-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.output-body {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.plain-textarea {
  width: 100%;
  resize: none;
  border: none;
  padding: 0.75rem;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 0.8rem;
  outline: none;
  transition: background-color 0.3s, color 0.3s;
  background-color: #ffffff;
  color: #1e293b;
  tab-size: 2;
}

.panel-textarea {
  height: 100%;
  min-height: 60px;
}

.output-box {
  flex: 1;
  min-height: 60px;
  padding: 0.75rem;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
  background: linear-gradient(to bottom, #f1f5f9 95%, #e2e8f0 95%, #e2e8f0 100%);
  color: #1e293b;
}

.output-box.has-output {
  min-height: 40px;
}

.placeholder-copy {
  color: #94a3b8;
  font-size: 13px;
}

.output-status {
  flex-shrink: 0;
  padding: 6px 12px;
  background: #e2e8f0;
}

.status-divider {
  height: 1px;
  border-top: 1px dashed #94a3b8;
  margin-bottom: 6px;
}

.status-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-text {
  font-size: 12px;
  font-weight: 600;
}

.test-badge {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.05em;
  padding: 2px 10px;
  border-radius: 999px;
}
.test-badge.pass {
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
}
.test-badge.failed {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}
</style>

<style>
html.dark .self-test-panel {
  background: #0f172a !important;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.3) !important;
}
html.dark .drag-handle {
  background: #1e293b !important;
  border-color: #334155 !important;
}
html.dark .drag-handle:hover,
html.dark .drag-active {
  background: #334155 !important;
}
html.dark .run-btn {
  background: #0d9488 !important;
}
html.dark .run-btn:hover:not(:disabled) {
  background: #14b8a6 !important;
}
html.dark .collapse-btn:hover {
  background: #1e293b !important;
}
html.dark .plain-textarea {
  background-color: #1e293b !important;
  color: #e2e8f0 !important;
}
html.dark .surface-panel {
  border-color: #334155 !important;
}
html.dark .collapse-header {
  color: #f8fafc !important;
  background: #1e293b !important;
  border-color: #334155 !important;
}
html.dark .output-box {
  background: linear-gradient(to bottom, #020617 95%, #0f172a 95%, #0f172a 100%) !important;
  color: #6ee7b7 !important;
}
html.dark .output-status {
  background: #0f172a !important;
}
html.dark .status-divider {
  border-color: #475569 !important;
}
html.dark .placeholder-copy {
  color: #64748b !important;
}
</style>
