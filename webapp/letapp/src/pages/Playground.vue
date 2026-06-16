<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';
import Prism from 'prismjs';
import { apiRequest } from '../services/api';
import { useAuthStore } from '../stores/auth';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-kotlin';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-swift';

interface ExecutionResponse {
  stdout?: string;
  stderr?: string;
  message?: string;
}

interface LanguageOption {
  name: string;
  value: string;
  prism: string;
  icon: string;
  color: string;
}

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const highlightedCodeRef = ref<HTMLElement | null>(null);
const languageMenuRef = ref<HTMLElement | null>(null);

const languagePresets: Record<string, string> = {
  javascript: `function greet(name) {
  return \`Hello, \${name}!\`;
}

const message = greet('Let Coding');
console.log(message);`,
  python: `def greet(name):
    return f"Hello, {name}!"

message = greet("Let Coding")
print(message)`,
  java: `public class Main {
  public static void main(String[] args) {
    System.out.println("Hello, Let Coding!");
  }
}`,
  cpp: `#include <iostream>

int main() {
  std::cout << "Hello, Let Coding!" << std::endl;
  return 0;
}`,
  go: `package main

import "fmt"

func main() {
  fmt.Println("Hello, Let Coding!")
}`,
  rust: `fn main() {
    println!("Hello, Let Coding!");
}`,
  swift: `import Foundation

print("Hello, Let Coding!")`,
  kotlin: `fun main() {
    println("Hello, Let Coding!")
}`,
};

const languages: LanguageOption[] = [
  { name: 'JavaScript', value: 'javascript', prism: 'javascript', icon: 'vscode-icons:file-type-js-official', color: '#f7df1e' },
  { name: 'Python', value: 'python', prism: 'python', icon: 'vscode-icons:file-type-python', color: '#3776ab' },
  { name: 'Java', value: 'java', prism: 'java', icon: 'vscode-icons:file-type-java', color: '#ed8b00' },
  { name: 'C++', value: 'cpp', prism: 'cpp', icon: 'vscode-icons:file-type-cpp', color: '#00599c' },
  { name: 'Go', value: 'go', prism: 'go', icon: 'vscode-icons:file-type-go', color: '#00add8' },
  { name: 'Rust', value: 'rust', prism: 'rust', icon: 'vscode-icons:file-type-rust', color: '#dea584' },
  { name: 'Swift', value: 'swift', prism: 'swift', icon: 'vscode-icons:file-type-swift', color: '#fa7343' },
  { name: 'Kotlin', value: 'kotlin', prism: 'kotlin', icon: 'vscode-icons:file-type-kotlin', color: '#7f52ff' },
];

const defaultLanguage = languages[0]!;
const fallbackFileNames: Record<string, string> = {
  javascript: 'script',
  python: 'script',
  java: 'Main',
  cpp: 'main',
  go: 'main',
  rust: 'main',
  swift: 'main',
  kotlin: 'Main',
};

const extensionMap: Record<string, string> = {
  javascript: 'js',
  python: 'py',
  java: 'java',
  cpp: 'cpp',
  go: 'go',
  rust: 'rs',
  swift: 'swift',
  kotlin: 'kt',
};

const getLanguagePreset = (language: string) => languagePresets[language] ?? '';

const sanitizeFileName = (value: string) => (
  value
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, '')
    .trim()
);

const selectedLanguage = ref<string>(defaultLanguage.value);
const previousLanguage = ref<string>(defaultLanguage.value);
const isLanguageMenuOpen = ref(false);
const code = ref<string>(getLanguagePreset(defaultLanguage.value));
const stdin = ref<string>('');
const output = ref<string>('');
const outputKind = ref<'info' | 'error'>('info');
const isExecuting = ref(false);
const exportFileName = ref<string>(fallbackFileNames[defaultLanguage.value] ?? 'code');
const bottomPanelsCollapsed = ref(false);
const outputPosition = ref<'bottom' | 'side'>('bottom');
const viewportWidth = ref(typeof window === 'undefined' ? 1440 : window.innerWidth);

const currentLanguageInfo = computed<LanguageOption>(() => (
  languages.find((lang) => lang.value === selectedLanguage.value) ?? defaultLanguage
));

const exportExtension = computed(() => extensionMap[selectedLanguage.value] ?? 'txt');
const lineCount = computed(() => code.value.split('\n').length);

const bottomPanelSpacer = computed(() => {
  if (bottomPanelsCollapsed.value) {
    return '5.5rem';
  }

  if (viewportWidth.value < 768) {
    return '39rem';
  }

  if (viewportWidth.value < 900) {
    return '30rem';
  }

  return '23rem';
});

const floatingButtonBottom = computed(() => {
  if (bottomPanelsCollapsed.value) {
    return '1.25rem';
  }

  if (viewportWidth.value < 768) {
    return '40rem';
  }

  if (viewportWidth.value < 900) {
    return '31rem';
  }

  return '24rem';
});

const highlightedCode = computed(() => {
  const language = currentLanguageInfo.value.prism;
  const grammar = Prism.languages[language];
  const source = code.value;
  const normalizedSource = source.length > 0 ? source : ' ';
  return grammar ? Prism.highlight(normalizedSource, grammar, language) : Prism.util.encode(normalizedSource);
});

const syncEditorScrollFromTextarea = (target: HTMLTextAreaElement) => {
  if (!highlightedCodeRef.value) {
    return;
  }

  highlightedCodeRef.value.scrollTop = target.scrollTop;
  highlightedCodeRef.value.scrollLeft = target.scrollLeft;
};

const syncEditorScroll = (event: Event) => {
  syncEditorScrollFromTextarea(event.target as HTMLTextAreaElement);
};

const updateTextareaValue = (
  target: HTMLTextAreaElement,
  targetRef: { value: string },
  replacement: string,
) => {
  const start = target.selectionStart;
  const end = target.selectionEnd;
  const value = targetRef.value;
  targetRef.value = `${value.slice(0, start)}${replacement}${value.slice(end)}`;

  requestAnimationFrame(() => {
    const nextPosition = start + replacement.length;
    target.selectionStart = nextPosition;
    target.selectionEnd = nextPosition;
    target.focus();
    syncEditorScrollFromTextarea(target);
  });
};

const handleTabInsertion = (event: KeyboardEvent, targetRef: { value: string }) => {
  if (event.key !== 'Tab') {
    return;
  }

  const target = event.target as HTMLTextAreaElement | null;
  if (!target) {
    return;
  }

  event.preventDefault();
  updateTextareaValue(target, targetRef, '  ');
};

const runCode = async () => {
  const source = code.value;
  if (!source.trim()) {
    outputKind.value = 'error';
    output.value = '代码不能为空。';
    bottomPanelsCollapsed.value = false;
    return;
  }

  isExecuting.value = true;
  output.value = '';
  outputKind.value = 'info';
  bottomPanelsCollapsed.value = false;

  try {
    const endpoint = authStore.isAuthenticated ? '/code/run' : '/code/run/public';
    const result = await apiRequest<ExecutionResponse>(endpoint, {
      method: 'POST',
      skipAuth: !authStore.isAuthenticated,
      body: JSON.stringify({
        code: source,
        language: selectedLanguage.value,
        stdin: stdin.value,
      }),
    });

    const text = [result.stdout, result.message, result.stderr].filter(Boolean).join('\n').trim();
    output.value = text || '程序已运行，但没有产生输出。';
    outputKind.value = result.stderr ? 'error' : 'info';
  } catch (error) {
    outputKind.value = 'error';
    output.value = `执行错误: ${error instanceof Error ? error.message : '未知错误'}`;
  } finally {
    isExecuting.value = false;
  }
};

const handleEditorKeydown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault();
    if (!isExecuting.value) {
      void runCode();
    }
    return;
  }

  handleTabInsertion(event, code);
};

const handleStdinKeydown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault();
    if (!isExecuting.value) {
      void runCode();
    }
    return;
  }

  handleTabInsertion(event, stdin);
};

const handleGlobalShortcut = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter' && !isExecuting.value) {
    const target = event.target as HTMLElement | null;
    const isEditable = target?.tagName === 'TEXTAREA' || target?.tagName === 'INPUT';
    if (isEditable) {
      return;
    }

    event.preventDefault();
    void runCode();
  }
};

const updateViewportWidth = () => {
  viewportWidth.value = window.innerWidth;
};

const closeLanguageMenuOnOutsideClick = (event: MouseEvent) => {
  const target = event.target as Node | null;
  if (languageMenuRef.value && target && !languageMenuRef.value.contains(target)) {
    isLanguageMenuOpen.value = false;
  }
};

const updateExportFileName = (language: string) => {
  const fallback = fallbackFileNames[language] ?? 'code';
  if (!sanitizeFileName(exportFileName.value)) {
    exportFileName.value = fallback;
  }
};

const updateLanguage = (language: string) => {
  previousLanguage.value = selectedLanguage.value;
  selectedLanguage.value = language;
  isLanguageMenuOpen.value = false;
  code.value = getLanguagePreset(language);
  updateExportFileName(language);
};

const saveCode = () => {
  const baseName = sanitizeFileName(exportFileName.value) || fallbackFileNames[selectedLanguage.value] || 'code';
  exportFileName.value = baseName;

  const blob = new Blob([code.value], { type: 'text/plain;charset=utf-8' });
  const link = document.createElement('a');
  const objectUrl = URL.createObjectURL(blob);
  link.href = objectUrl;
  link.download = `${baseName}.${exportExtension.value}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(objectUrl);
};

const resetCode = () => {
  code.value = getLanguagePreset(selectedLanguage.value);
  stdin.value = '';
  output.value = '';
  outputKind.value = 'info';
};

const importCode = () => {
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.js,.py,.java,.cpp,.go,.rs,.swift,.kt,.txt';

  fileInput.onchange = (event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (readerEvent) => {
      code.value = String(readerEvent.target?.result || '');

      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      const extToLanguage: Record<string, string> = {
        js: 'javascript',
        py: 'python',
        java: 'java',
        cpp: 'cpp',
        go: 'go',
        rs: 'rust',
        swift: 'swift',
        kt: 'kotlin',
      };

      const detectedLanguage = extToLanguage[ext];
      if (detectedLanguage) {
        selectedLanguage.value = detectedLanguage;
        previousLanguage.value = detectedLanguage;
      }

      const importedName = file.name.replace(/\.[^.]+$/, '');
      const sanitizedImportedName = sanitizeFileName(importedName);
      exportFileName.value = sanitizedImportedName || fallbackFileNames[selectedLanguage.value] || 'code';
    };

    reader.readAsText(file);
  };

  fileInput.click();
};

onMounted(() => {
  const languageParam = route.query.language as string | undefined;
  if (languageParam && languages.some((lang) => lang.value === languageParam)) {
    selectedLanguage.value = languageParam;
    previousLanguage.value = languageParam;
    code.value = getLanguagePreset(languageParam) || code.value;
  }

  updateExportFileName(selectedLanguage.value);
  updateViewportWidth();

  window.addEventListener('keydown', handleGlobalShortcut);
  window.addEventListener('resize', updateViewportWidth);
  window.addEventListener('click', closeLanguageMenuOnOutsideClick);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalShortcut);
  window.removeEventListener('resize', updateViewportWidth);
  window.removeEventListener('click', closeLanguageMenuOnOutsideClick);
});
</script>

<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,_#ecfeff_0%,_#f8fafc_32%,_#f8fafc_100%)] text-slate-950 dark:bg-[linear-gradient(180deg,_#020617_0%,_#020617_100%)] dark:text-slate-50">
    <div class="sticky top-0 z-30 border-b border-slate-200/80 bg-white/75 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/75">
      <div class="playground-container mx-auto flex flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div class="flex min-w-0 flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div class="flex min-w-0 items-start gap-4">
            <button class="glass-icon-button shrink-0" @click="router.back()">
              <Icon icon="material-symbols:arrow-back" class="h-5 w-5" />
            </button>
            <div class="min-w-0">
              <h1 class="truncate text-2xl font-black tracking-tight">在线代码编辑器</h1>
              <p class="text-sm text-slate-500 dark:text-slate-400">支持多语言运行、标准输入，以及统一输出结果显示。</p>
            </div>
          </div>

          <div class="toolbar-cluster">
            <div ref="languageMenuRef" class="relative w-full sm:w-auto">
              <button class="toolbar-button w-full min-w-0 justify-between sm:min-w-[170px]" :title="currentLanguageInfo.name" @click="isLanguageMenuOpen = !isLanguageMenuOpen">
                <span class="flex min-w-0 items-center gap-2">
                  <Icon :icon="currentLanguageInfo.icon" class="h-4 w-4 shrink-0" :style="{ color: currentLanguageInfo.color }" />
                  <span class="truncate">{{ currentLanguageInfo.name }}</span>
                </span>
                <Icon icon="material-symbols:arrow-drop-down" class="h-5 w-5 shrink-0 transition-transform" :class="{ 'rotate-180': isLanguageMenuOpen }" />
              </button>

              <div v-if="isLanguageMenuOpen" class="absolute right-0 top-full z-50 mt-2 w-full min-w-[15rem] rounded-3xl border border-slate-200 bg-white p-2 shadow-2xl shadow-slate-200/80 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/40 sm:w-60">
                <button
                  v-for="lang in languages"
                  :key="lang.value"
                  type="button"
                  class="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-sm font-bold transition hover:bg-slate-100 dark:hover:bg-slate-800"
                  @click="updateLanguage(lang.value)"
                >
                  <Icon :icon="lang.icon" class="h-4 w-4 shrink-0" :style="{ color: lang.color }" />
                  <span>{{ lang.name }}</span>
                  <span v-if="selectedLanguage === lang.value" class="ml-auto h-2.5 w-2.5 rounded-full bg-cyan-400"></span>
                </button>
              </div>
            </div>

            <button class="toolbar-button flex-1 sm:flex-none" @click="importCode">
              <Icon icon="material-symbols:upload" class="h-4 w-4" />
              导入
            </button>
            <button class="toolbar-button flex-1 sm:flex-none" @click="saveCode">
              <Icon icon="material-symbols:download" class="h-4 w-4" />
              导出
            </button>
            <button class="toolbar-button flex-1 sm:flex-none" @click="resetCode">
              <Icon icon="material-symbols:refresh" class="h-4 w-4" />
              重置
            </button>
            <button class="toolbar-button flex-1 sm:flex-none" :title="outputPosition === 'bottom' ? '切换为右边显示' : '切换为底部显示'" @click="outputPosition = outputPosition === 'bottom' ? 'side' : 'bottom'">
              <Icon :icon="outputPosition === 'bottom' ? 'material-symbols:side-navigation' : 'material-symbols:bottom-panel'" class="h-4 w-4" />
              {{ outputPosition === 'bottom' ? '右边' : '底部' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="playground-container mx-auto px-4 py-6 sm:px-6 lg:px-8" :style="{ paddingBottom: outputPosition === 'bottom' ? bottomPanelSpacer : '5.5rem' }">
      <div class="playground-stack" :class="{ 'playground-side-mode': outputPosition === 'side' }">
        <section class="editor-panel">
          <div class="panel-header">
            <div class="flex items-center gap-2">
              <Icon icon="material-symbols:code" class="h-5 w-5 text-cyan-500" />
              <span>代码编辑区</span>
            </div>
            <div class="text-sm text-slate-500 dark:text-slate-400">{{ lineCount }} 行</div>
          </div>

          <div class="editor-toolbar">
            <label class="export-name-field">
              <span>导出文件名</span>
              <input
                v-model="exportFileName"
                type="text"
                class="export-name-input"
                :placeholder="fallbackFileNames[selectedLanguage] || 'code'"
              />
            </label>
            <div class="export-hint">
              <span>保存为</span>
              <span class="export-file-chip">{{ sanitizeFileName(exportFileName) || fallbackFileNames[selectedLanguage] || 'code' }}.{{ exportExtension }}</span>
            </div>
          </div>

          <div class="editor-body">
            <div class="editor-shell">
              <pre ref="highlightedCodeRef" :class="`editor-highlight language-${currentLanguageInfo.prism}`"><code v-html="highlightedCode"></code></pre>
              <textarea
                v-model="code"
                spellcheck="false"
                class="editor-input"
                placeholder="在这里输入你的代码..."
                @scroll="syncEditorScroll"
                @keydown="handleEditorKeydown"
              ></textarea>
            </div>

            <aside v-if="outputPosition === 'side'" class="side-io-panel">
              <section class="surface-panel side-io-section">
                <div class="collapse-header input-header">
                  <div class="flex items-center gap-2">
                    <Icon icon="material-symbols:input" class="h-5 w-5 text-amber-500" />
                    <span>输入数据</span>
                  </div>
                  <button class="run-button editor-run-button" :disabled="isExecuting" @click="runCode">
                    <Icon :icon="isExecuting ? 'material-symbols:hourglass-top' : 'material-symbols:play-arrow'" class="h-4 w-4" :class="{ 'animate-spin': isExecuting }" />
                    {{ isExecuting ? '运行中...' : '运行代码' }}
                  </button>
                </div>
                <div class="collapse-body">
                  <textarea
                    v-model="stdin"
                    class="plain-textarea panel-textarea"
                    placeholder="如果程序需要输入，可以在这里填写测试数据。"
                    @keydown="handleStdinKeydown"
                  ></textarea>
                </div>
              </section>

              <section class="surface-panel side-io-section">
                <div class="collapse-header">
                  <div class="flex items-center gap-2">
                    <Icon :icon="outputKind === 'error' ? 'material-symbols:error' : 'material-symbols:output'" class="h-5 w-5" :class="outputKind === 'error' ? 'text-rose-500' : 'text-emerald-500'" />
                    <span>输出</span>
                  </div>
                </div>
                <div class="collapse-body">
                  <div class="output-box">
                    <pre
                      v-if="output"
                      :class="outputKind === 'error' ? 'text-rose-500 dark:text-rose-300' : 'text-emerald-600 dark:text-emerald-300'"
                    >{{ output }}</pre>
                    <div v-else class="placeholder-copy">运行结果和报错都会显示在这里。</div>
                  </div>
                </div>
              </section>
            </aside>
          </div>
        </section>
      </div>
    </div>

    <div v-if="outputPosition === 'bottom'" v-show="!bottomPanelsCollapsed" class="fixed-panels-shell">
      <div class="playground-container fixed-panels-inner">
        <div class="bottom-panels">
          <section class="surface-panel">
            <div class="collapse-header input-header">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:input" class="h-5 w-5 text-amber-500" />
                <span>输入数据</span>
              </div>
              <button class="run-button editor-run-button" :disabled="isExecuting" @click="runCode">
                <Icon :icon="isExecuting ? 'material-symbols:hourglass-top' : 'material-symbols:play-arrow'" class="h-4 w-4" :class="{ 'animate-spin': isExecuting }" />
                {{ isExecuting ? '运行中...' : '运行代码' }}
              </button>
            </div>
            <div class="collapse-body">
              <textarea
                v-model="stdin"
                class="plain-textarea panel-textarea"
                placeholder="如果程序需要输入，可以在这里填写测试数据。"
                @keydown="handleStdinKeydown"
              ></textarea>
            </div>
          </section>

          <section class="surface-panel">
            <div class="collapse-header">
              <div class="flex items-center gap-2">
                <Icon :icon="outputKind === 'error' ? 'material-symbols:error' : 'material-symbols:output'" class="h-5 w-5" :class="outputKind === 'error' ? 'text-rose-500' : 'text-emerald-500'" />
                <span>输出</span>
              </div>
            </div>
            <div class="collapse-body">
              <div class="output-box">
                <pre
                  v-if="output"
                  :class="outputKind === 'error' ? 'text-rose-500 dark:text-rose-300' : 'text-emerald-600 dark:text-emerald-300'"
                >{{ output }}</pre>
                <div v-else class="placeholder-copy">运行结果和报错都会显示在这里。</div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>

    <div v-if="outputPosition === 'bottom'" class="floating-button-group" :style="{ bottom: floatingButtonBottom }">
      <button
        class="floating-collapse-button"
        type="button"
        @click="bottomPanelsCollapsed = !bottomPanelsCollapsed"
      >
        <Icon :icon="bottomPanelsCollapsed ? 'material-symbols:unfold-less-rounded' : 'material-symbols:unfold-more-rounded'" class="h-5 w-5" />
        <span>{{ bottomPanelsCollapsed ? '展开' : '收起' }}</span>
      </button>
    </div>
  </div>
</template>

<style>
@import 'prismjs/themes/prism-tomorrow.min.css';
</style>

<style scoped>
@reference 'tailwindcss';

.glass-icon-button {
  @apply grid h-11 w-11 place-items-center rounded-2xl border border-slate-200 bg-white/90 text-slate-700 shadow-sm transition hover:bg-slate-100;
}

.playground-container {
  max-width: 90rem;
}

.playground-stack {
  @apply flex flex-col gap-6;
}

.toolbar-cluster {
  @apply flex w-full flex-wrap items-stretch gap-3 xl:w-auto xl:justify-end;
}

.toolbar-button {
  @apply inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-100;
}

.run-button {
  @apply inline-flex min-h-11 items-center gap-2 rounded-2xl bg-cyan-400 px-5 py-2.5 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:-translate-y-0.5 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70;
}

.editor-panel {
  @apply overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-xl shadow-slate-200/60;
}

.surface-panel {
  @apply overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-lg shadow-slate-200/50;
}

.fixed-panels-shell {
  @apply pointer-events-none fixed right-0 bottom-0 z-40;
  left: var(--app-content-left, 0px);
}

.fixed-panels-inner {
  @apply mx-auto w-full px-4 pb-4 sm:px-6 lg:px-8;
  pointer-events: auto;
}

.bottom-panels {
  @apply grid gap-4;
}

.panel-header {
  @apply flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-4 text-sm font-black text-slate-800;
}

.collapse-header {
  @apply flex w-full items-center justify-between gap-4 border-b border-slate-200 px-5 py-4 text-left text-sm font-black text-slate-800;
}

.input-header {
  @apply gap-3;
}

.collapse-body {
  @apply overflow-hidden;
}

.editor-toolbar {
  @apply grid gap-4 border-b border-slate-200 bg-slate-50 px-5 py-4;
  grid-template-columns: minmax(0, 1fr);
}

.export-name-field {
  @apply flex min-w-0 flex-col gap-2 text-xs font-bold uppercase tracking-[0.2em] text-slate-500;
}

.export-name-input {
  @apply w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold normal-case tracking-normal text-slate-900 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-200;
}

.export-hint {
  @apply flex flex-wrap items-center gap-2 text-sm text-slate-500;
}

.export-file-chip {
  @apply inline-flex max-w-full items-center rounded-full bg-slate-900 px-3 py-1 font-mono text-xs text-cyan-200;
  overflow-wrap: anywhere;
}

.editor-shell {
  @apply relative h-[620px] overflow-hidden bg-white transition-colors duration-300;
}

.editor-run-button {
  @apply min-w-[10.75rem] justify-center;
}

.editor-highlight,
.editor-input {
  @apply absolute inset-0 m-0 h-full w-full overflow-auto whitespace-pre-wrap break-normal p-5 font-mono text-sm leading-7;
  tab-size: 2;
}

.editor-highlight {
  @apply pointer-events-none text-slate-900 transition-colors duration-300;
}

.editor-highlight[class*='language-'] {
  background: transparent !important;
}

.editor-highlight :deep(code),
.editor-highlight :deep([class*='language-']),
.editor-highlight :deep(.token) {
  background: transparent !important;
  text-shadow: none !important;
}

.editor-highlight :deep(code) {
  @apply block min-h-full font-mono text-sm leading-7;
  white-space: inherit;
  tab-size: 2;
}

.editor-input {
  @apply resize-none border-none bg-transparent text-transparent caret-slate-950 outline-none transition-colors duration-300;
}

.editor-input::selection {
  background: rgba(8, 145, 178, 0.22);
}

:global(.dark) .editor-input::selection {
  background: rgba(34, 211, 238, 0.28);
}

.plain-textarea {
  @apply w-full resize-none border-none bg-white p-5 font-mono text-sm text-slate-800 outline-none transition-colors duration-300 placeholder:text-slate-400 focus:ring-0;
  tab-size: 2;
}

.panel-textarea {
  height: 220px;
}

.output-box {
  @apply min-h-[220px] bg-white p-5 font-mono text-sm text-slate-900 transition-colors duration-300;
  max-height: 220px;
  overflow: auto;
}

.floating-collapse-button {
  @apply inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-3 text-sm font-black text-white shadow-2xl shadow-slate-900/25 transition hover:-translate-y-0.5 hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:shadow-cyan-950/30 dark:hover:bg-cyan-300;
}

.placeholder-copy {
  @apply text-sm italic text-slate-500;
}

.floating-button-group {
  position: fixed;
  right: 5rem;
  z-index: 50;
  display: flex;
  gap: 0.5rem;
}

@media (max-width: 767px) {
  .playground-container {
    max-width: 100%;
  }

  .glass-icon-button {
    @apply h-10 w-10 rounded-xl;
  }

  .toolbar-button,
  .run-button {
    @apply min-h-10 rounded-xl px-3 py-2 text-sm;
  }

  .editor-panel,
  .surface-panel {
    border-radius: 1.35rem;
  }

  .panel-header,
  .collapse-header {
    @apply px-4 py-3 text-[13px];
  }

  .editor-toolbar {
    @apply px-4 py-3;
  }

  .editor-shell {
    height: 380px;
  }

  .editor-highlight,
  .editor-input,
  .plain-textarea,
  .output-box {
    @apply p-4 text-[13px] leading-6;
  }

  .panel-textarea,
  .output-box {
    height: 160px;
    max-height: 160px;
  }

  .fixed-panels-inner {
    @apply px-4 pb-4;
  }

.playground-side-mode .editor-body {
  display: flex;
  flex-direction: row;
  gap: 1rem;
}

.playground-side-mode .editor-shell {
  flex: 1;
}

.side-io-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 24rem;
  flex-shrink: 0;
}

.side-io-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.side-io-section .collapse-body {
  flex: 1;
  overflow: hidden;
}

.side-io-section .panel-textarea,
.side-io-section .output-box {
  height: 100%;
  max-height: none;
}

@media (max-width: 1023px) {
  .playground-side-mode .editor-panel {
    flex-direction: column;
  }

  .side-io-panel {
    width: 100%;
  }
}

.floating-button-group {
    right: 4rem;
  }

  .floating-collapse-button {
    @apply px-3.5 py-2.5 text-[13px];
  }
}

@media (min-width: 768px) and (max-width: 1366px) {
  .playground-container {
    max-width: 76rem;
  }

  .toolbar-cluster {
    gap: 0.65rem;
  }

  .toolbar-button,
  .run-button {
    @apply min-h-10 px-4 py-2 text-sm;
  }

  .panel-header,
  .collapse-header {
    @apply px-4 py-3.5;
  }

  .editor-toolbar {
    @apply px-4 py-3.5;
  }

  .editor-shell {
    height: 500px;
  }

  .panel-textarea,
  .output-box {
    height: 180px;
    max-height: 180px;
  }
}

@media (min-width: 1367px) and (max-width: 1440px) {
  .playground-container {
    max-width: 84rem;
  }

  .editor-shell {
    height: 560px;
  }
}

@media (min-width: 1441px) and (max-width: 1920px) {
  .playground-container {
    max-width: 96rem;
  }

  .editor-shell {
    height: 640px;
  }
}

@media (min-width: 1921px) {
  .playground-container {
    max-width: 108rem;
  }

  .editor-shell {
    height: 720px;
  }
}

@media (min-width: 900px) {
  .editor-toolbar {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: end;
  }

  .bottom-panels {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>

<style>
html.dark .glass-icon-button,
html.dark .toolbar-button {
  border-color: #1e293b !important;
  background-color: #0f172a !important;
  color: #e2e8f0 !important;
}

html.dark .glass-icon-button:hover,
html.dark .toolbar-button:hover {
  background-color: #1e293b !important;
}

html.dark .editor-panel,
html.dark .surface-panel {
  border-color: #1e293b !important;
  background-color: #0f172a !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2) !important;
}

html.dark .panel-header,
html.dark .collapse-header {
  border-color: #1e293b !important;
  color: #f8fafc !important;
}

html.dark .editor-toolbar {
  border-color: #1e293b !important;
  background-color: #0f172a !important;
}

html.dark .export-name-field,
html.dark .export-hint,
html.dark .placeholder-copy {
  color: #94a3b8 !important;
}

html.dark .export-name-input {
  border-color: #334155 !important;
  background-color: #020617 !important;
  color: #f8fafc !important;
  caret-color: #ffffff !important;
}

html.dark .export-name-input::placeholder {
  color: #475569 !important;
}

html.dark .export-file-chip {
  background-color: #1e293b !important;
  color: #a5f3fc !important;
}

html.dark .editor-shell,
html.dark .plain-textarea,
html.dark .output-box {
  background-color: #020617 !important;
  color: #f8fafc !important;
}

html.dark .editor-highlight {
  color: #f8fafc !important;
}

html.dark .editor-input,
html.dark .plain-textarea {
  caret-color: #ffffff !important;
}

html:not(.dark) .editor-panel,
html:not(.dark) .surface-panel,
html:not(.dark) .editor-shell,
html:not(.dark) .editor-shell::before,
html:not(.dark) .plain-textarea,
html:not(.dark) .output-box {
  background-color: #ffffff !important;
  color: #0f172a !important;
}

html:not(.dark) .panel-header,
html:not(.dark) .collapse-header {
  background-color: #ffffff !important;
  color: #0f172a !important;
}

html:not(.dark) .editor-toolbar {
  background-color: #f8fafc !important;
}

html:not(.dark) .export-name-input {
  background-color: #ffffff !important;
  border-color: #cbd5e1 !important;
  color: #0f172a !important;
}

html:not(.dark) .export-name-field,
html:not(.dark) .export-hint,
html:not(.dark) .placeholder-copy {
  color: #475569 !important;
}

html:not(.dark) .export-file-chip {
  background-color: #e2e8f0 !important;
  color: #0f172a !important;
}

html:not(.dark) .editor-input,
html:not(.dark) .plain-textarea {
  caret-color: #0f172a !important;
}

html:not(.dark) .output-box pre {
  color: inherit !important;
}

html:not(.dark) pre.editor-highlight[class*='language-'],
html:not(.dark) pre.editor-highlight[class*='language-'] code,
html:not(.dark) pre.editor-highlight[class*='language-'] .token {
  background: #ffffff !important;
  color: #0f172a !important;
}

html:not(.dark) pre.editor-highlight[class*='language-'] .token.comment,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.prolog,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.doctype,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.cdata {
  color: #64748b !important;
}

html:not(.dark) pre.editor-highlight[class*='language-'] .token.punctuation,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.operator {
  color: #334155 !important;
}

html:not(.dark) pre.editor-highlight[class*='language-'] .token.keyword,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.selector,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.atrule {
  color: #7c3aed !important;
}

html:not(.dark) pre.editor-highlight[class*='language-'] .token.string,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.attr-value,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.char,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.inserted {
  color: #059669 !important;
}

html:not(.dark) pre.editor-highlight[class*='language-'] .token.function,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.class-name {
  color: #2563eb !important;
}

html:not(.dark) pre.editor-highlight[class*='language-'] .token.number,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.boolean,
html:not(.dark) pre.editor-highlight[class*='language-'] .token.constant {
  color: #ea580c !important;
}
</style>
