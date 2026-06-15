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

const languagePresets: Record<string, string> = {
  javascript: `function greet(name) {
  return \`Hello, ${name}!\`;
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
const stdout = ref<string>('');
const stderr = ref<string>('');
const isExecuting = ref(false);
const exportFileName = ref<string>(fallbackFileNames[defaultLanguage.value] ?? 'code');

const currentLanguageInfo = computed<LanguageOption>(() => (
  languages.find((lang) => lang.value === selectedLanguage.value) ?? defaultLanguage
));

const exportExtension = computed(() => extensionMap[selectedLanguage.value] ?? 'txt');
const lineCount = computed(() => code.value.split('\n').length);

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
    stderr.value = '代码不能为空。\n';
    return;
  }

  isExecuting.value = true;
  stdout.value = '';
  stderr.value = '';

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

    stdout.value = result.stdout || result.message || '';
    stderr.value = result.stderr || '';
  } catch (error) {
    stderr.value = `执行错误: ${error instanceof Error ? error.message : '未知错误'}\n`;
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

  const currentCode = code.value;
  if (currentCode.trim() === '' || currentCode === getLanguagePreset(previousLanguage.value)) {
    code.value = getLanguagePreset(language);
  }

  updateExportFileName(language);
};

onMounted(() => {
  const languageParam = route.query.language as string;
  if (languageParam && languages.some((lang) => lang.value === languageParam)) {
    selectedLanguage.value = languageParam;
    previousLanguage.value = languageParam;
    code.value = getLanguagePreset(languageParam) || code.value;
  }

  updateExportFileName(selectedLanguage.value);
  window.addEventListener('keydown', handleGlobalShortcut);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalShortcut);
});

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
  stdout.value = '';
  stderr.value = '';
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
</script>

<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,_#ecfeff_0%,_#f8fafc_32%,_#f8fafc_100%)] text-slate-950 dark:bg-[linear-gradient(180deg,_#020617_0%,_#020617_100%)] dark:text-slate-50">
    <div class="sticky top-0 z-30 border-b border-slate-200/80 bg-white/75 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/75">
      <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-5 sm:px-6 lg:px-8">
        <div class="flex items-center gap-4">
          <button class="glass-icon-button" @click="router.back()">
            <Icon icon="material-symbols:arrow-back" class="h-5 w-5" />
          </button>
          <div>
            <h1 class="text-2xl font-black tracking-tight">在线代码编辑器</h1>
            <p class="text-sm text-slate-500 dark:text-slate-400">支持多语言运行、标准输入和结果回显。</p>
          </div>
        </div>

        <div class="toolbar-cluster">
          <div class="relative">
            <button class="toolbar-button min-w-[160px] justify-between" :title="currentLanguageInfo.name" @click="isLanguageMenuOpen = !isLanguageMenuOpen">
              <span class="flex items-center gap-2">
                <Icon :icon="currentLanguageInfo.icon" class="h-4 w-4" :style="{ color: currentLanguageInfo.color }" />
                <span>{{ currentLanguageInfo.name }}</span>
              </span>
              <Icon icon="material-symbols:arrow-drop-down" class="h-5 w-5 transition-transform" :class="{ 'rotate-180': isLanguageMenuOpen }" />
            </button>

            <div v-if="isLanguageMenuOpen" class="absolute right-0 top-full z-50 mt-2 w-60 rounded-3xl border border-slate-200 bg-white p-2 shadow-2xl shadow-slate-200/80 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/40">
              <button
                v-for="lang in languages"
                :key="lang.value"
                type="button"
                class="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-sm font-bold transition hover:bg-slate-100 dark:hover:bg-slate-800"
                @click="updateLanguage(lang.value)"
              >
                <Icon :icon="lang.icon" class="h-4 w-4" :style="{ color: lang.color }" />
                <span>{{ lang.name }}</span>
                <span v-if="selectedLanguage === lang.value" class="ml-auto h-2.5 w-2.5 rounded-full bg-cyan-400"></span>
              </button>
            </div>
          </div>

          <button class="toolbar-button" @click="importCode">
            <Icon icon="material-symbols:upload" class="h-4 w-4" />
            导入
          </button>
          <button class="toolbar-button" @click="saveCode">
            <Icon icon="material-symbols:download" class="h-4 w-4" />
            导出
          </button>
          <button class="toolbar-button" @click="resetCode">
            <Icon icon="material-symbols:refresh" class="h-4 w-4" />
            重置
          </button>
          <button class="run-button" :disabled="isExecuting" @click="runCode">
            <Icon :icon="isExecuting ? 'material-symbols:hourglass-top' : 'material-symbols:play-arrow'" class="h-4 w-4" :class="{ 'animate-spin': isExecuting }" />
            {{ isExecuting ? '执行中...' : '运行代码' }}
          </button>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div class="grid items-start gap-8 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
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
              保存为
              <span class="export-file-chip">{{ sanitizeFileName(exportFileName) || fallbackFileNames[selectedLanguage] || 'code' }}.{{ exportExtension }}</span>
            </div>
          </div>

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
        </section>

        <div class="side-panel-stack">
          <section class="surface-panel">
            <div class="panel-header">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:input" class="h-5 w-5 text-amber-500" />
                <span>标准输入</span>
              </div>
              <div class="text-xs text-slate-500 dark:text-slate-400">Tab 会插入两个空格</div>
            </div>
            <textarea
              v-model="stdin"
              class="plain-textarea h-48"
              placeholder="需要的话，可以在这里输入测试数据。"
              @keydown="handleStdinKeydown"
            ></textarea>
          </section>

          <section class="surface-panel">
            <div class="panel-header">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:output" class="h-5 w-5 text-emerald-500" />
                <span>标准输出</span>
              </div>
            </div>
            <div class="output-box">
              <pre v-if="stdout" class="text-emerald-400">{{ stdout }}</pre>
              <div v-else class="placeholder-copy">运行结果会显示在这里。</div>
            </div>
          </section>

          <section class="surface-panel">
            <div class="panel-header">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:error" class="h-5 w-5 text-rose-500" />
                <span>错误输出</span>
              </div>
            </div>
            <div class="output-box">
              <pre v-if="stderr" class="text-rose-400">{{ stderr }}</pre>
              <div v-else class="placeholder-copy">如果程序报错，这里会展示详细信息。</div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
@import 'prismjs/themes/prism-tomorrow.min.css';
</style>

<style scoped>
@reference 'tailwindcss';

.glass-icon-button {
  @apply grid h-11 w-11 place-items-center rounded-2xl border border-slate-200 bg-white/90 text-slate-700 shadow-sm transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800;
}

.toolbar-cluster {
  @apply flex flex-wrap items-center gap-3 xl:gap-4;
}

.toolbar-button {
  @apply inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800;
}

.run-button {
  @apply inline-flex items-center gap-2 rounded-2xl bg-cyan-400 px-5 py-2.5 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:-translate-y-0.5 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70;
  margin-left: 0.4rem;
}

.editor-panel {
  @apply overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-xl shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20;
}

.surface-panel {
  @apply overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-lg shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/15;
}

.side-panel-stack {
  @apply grid min-w-0 gap-6;
}

.panel-header {
  @apply flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-4 text-sm font-black text-slate-800 dark:border-slate-800 dark:text-slate-100;
}

.editor-toolbar {
  @apply grid gap-4 border-b border-slate-200 bg-slate-50 px-5 py-4 dark:border-slate-800 dark:bg-slate-950/60;
  grid-template-columns: minmax(0, 1fr);
}

.export-name-field {
  @apply flex min-w-0 flex-col gap-2 text-xs font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400;
}

.export-name-input {
  @apply w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold normal-case tracking-normal text-slate-900 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:ring-cyan-900;
}

.export-hint {
  @apply flex flex-wrap items-center gap-2 text-sm text-slate-500 dark:text-slate-400;
}

.export-file-chip {
  @apply inline-flex max-w-full items-center rounded-full bg-slate-900 px-3 py-1 font-mono text-xs text-cyan-200 dark:bg-slate-800;
  overflow-wrap: anywhere;
}

.editor-shell {
  @apply relative h-[560px] overflow-hidden bg-slate-950;
}

.editor-highlight,
.editor-input {
  @apply absolute inset-0 m-0 h-full w-full overflow-auto whitespace-pre-wrap break-normal p-5 font-mono text-sm leading-7;
  tab-size: 2;
}

.editor-highlight {
  @apply pointer-events-none bg-transparent text-slate-100;
}

.editor-highlight :deep(code) {
  @apply block min-h-full font-mono text-sm leading-7;
  white-space: inherit;
  tab-size: 2;
}

.editor-input {
  @apply resize-none border-none bg-transparent text-transparent caret-white outline-none;
}

.editor-input::selection {
  background: rgba(34, 211, 238, 0.28);
}

.plain-textarea {
  @apply w-full resize-none border-none bg-slate-50 p-5 font-mono text-sm text-slate-800 outline-none focus:ring-0 dark:bg-slate-950 dark:text-slate-100;
  tab-size: 2;
}

.output-box {
  @apply min-h-[180px] bg-slate-950 p-5 font-mono text-sm text-slate-100;
}

.placeholder-copy {
  @apply text-sm italic text-slate-500;
}

@media (min-width: 900px) {
  .editor-toolbar {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: end;
  }
}
</style>
