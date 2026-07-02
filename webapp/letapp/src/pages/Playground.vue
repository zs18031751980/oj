<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, onUnmounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute, useRouter } from 'vue-router';
import { apiRequest } from '../services/api';
import { useAuthStore } from '../stores/auth';
import { useThemeStore } from '../stores/theme';

const MonacoEditor = defineAsyncComponent(() => import('../components/MonacoEditor.vue'));

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
const themeStore = useThemeStore();

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

${'import "fmt"'}

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

const defaultLanguage = languages.find((lang) => lang.value === 'cpp')!;
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
const languageCodeMap = ref<Record<string, string>>({});
const stdin = ref<string>('');
const output = ref<string>('');
const executionStatus = ref<string>('');
const expectedOutput = ref<string>('');
const testVerdict = ref<'pass' | 'failed' | null>(null);
const outputKind = ref<'info' | 'error'>('info');
const isExecuting = ref(false);
const exportFileName = ref<string>(fallbackFileNames[defaultLanguage.value] ?? 'code');
const bottomPanelsCollapsed = ref(false);
const outputPosition = ref<'bottom' | 'side'>('bottom');
const viewportWidth = ref(typeof window === 'undefined' ? 1440 : window.innerWidth);
const isFullscreen = ref(false);
const isFullscreenMenuOpen = ref(false);
const editorPanelRef = ref<HTMLElement | null>(null);
const fullscreenExitArmed = ref(false);

const isTouchFullscreenQuirkDevice = () => {
  if (typeof navigator === 'undefined') {
    return false;
  }

  const userAgent = navigator.userAgent;
  return /iPhone|iPod/.test(userAgent);
};

const syncPageScrollLock = (locked: boolean) => {
  if (typeof document === 'undefined') {
    return;
  }

  document.documentElement.style.overflow = locked ? 'hidden' : '';
  document.body.style.overflow = locked ? 'hidden' : '';
};

const preventFullscreenExitSwipe = (e: TouchEvent) => {
  const target = e.target as HTMLElement | null;
  if (!target) return;
  const scrollable = target.closest('textarea, pre, .monaco-editor, .output-box');
  if (scrollable) return;
  e.preventDefault();
};

const toggleFullscreen = async () => {
  if (isFullscreen.value) {
    fullscreenExitArmed.value = true;

    const activeEl = document.fullscreenElement || (document as any).webkitFullscreenElement;
    if (activeEl && !isTouchFullscreenQuirkDevice()) {
      try {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        } else if ((document as any).webkitExitFullscreen) {
          (document as any).webkitExitFullscreen();
        }
        return;
      } catch {
        // fall through to local state reset
      }
    }

    isFullscreen.value = false;
    isFullscreenMenuOpen.value = false;
    return;
  }

  isFullscreen.value = true;
  fullscreenExitArmed.value = false;

  if (isTouchFullscreenQuirkDevice()) {
    return;
  }

  const docEl = document.documentElement as any;
  const requestFS = docEl.requestFullscreen || docEl.webkitRequestFullscreen || docEl.mozRequestFullScreen;

  if (requestFS) {
    try {
      await requestFS.call(docEl);
      return;
    } catch {
      // fall back to in-app fullscreen mode
    }
  }
};

const handleFullscreenChange = () => {
  if (isTouchFullscreenQuirkDevice()) {
    return;
  }

  const active = !!(document.fullscreenElement || (document as any).webkitFullscreenElement);

  isFullscreen.value = active;
  if (!active) {
    isFullscreenMenuOpen.value = false;
  }

  fullscreenExitArmed.value = false;
};

const currentLanguageInfo = computed<LanguageOption>(() => (
  languages.find((lang) => lang.value === selectedLanguage.value) ?? defaultLanguage
));

const exportExtension = computed(() => extensionMap[selectedLanguage.value] ?? 'txt');

const bottomPanelSpacer = computed(() => {
  if (bottomPanelsCollapsed.value) {
    return '5.5rem';
  }

  if (viewportWidth.value < 768) {
    return '39rem';
  }

  if (viewportWidth.value < 900) {
    return '38rem';
  }

  return '23rem';
});

const floatingButtonBottom = computed(() => {
  if (bottomPanelsCollapsed.value) {
    return '1.25rem';
  }

  if (viewportWidth.value < 768) {
    return '28rem';
  }

  if (viewportWidth.value < 900) {
    return '26rem';
  }

  return '11rem';
});

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
  executionStatus.value = '';
  outputKind.value = 'info';
  testVerdict.value = null;
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

    const stderrText = (result.stderr || '').trim();
    const stdoutText = (result.stdout || '').trim();
    const messageText = (result.message || '').trim();

    if (stderrText) {
      output.value = stderrText;
      outputKind.value = 'error';
      executionStatus.value = '编译错误';
    } else {
      output.value = stdoutText || messageText;
      outputKind.value = 'info';
      executionStatus.value = output.value ? '执行成功' : '程序已运行，但没有产生输出。';
    }

    if (expectedOutput.value.trim()) {
      const compareText = stdoutText || messageText;
      testVerdict.value = compareText.trim() === expectedOutput.value.trim() ? 'pass' : 'failed';
    }
  } catch (error) {
    outputKind.value = 'error';
    output.value = `执行错误: ${error instanceof Error ? error.message : '未知错误'}`;
  } finally {
    isExecuting.value = false;
  }
};

const handleMonacoReady = (editor: { addAction: (action: { id: string; label: string; keybindings: number[]; run: () => void }) => void }) => {
  editor.addAction({
    id: 'run-code',
    label: 'Run Code',
    keybindings: [2048 | 3],
    run: () => {
      if (!isExecuting.value) {
        void runCode();
      }
    },
  });
};

const handleStdinKeydown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault();
    if (!isExecuting.value) {
      void runCode();
    }
    return;
  }

  if (event.key === 'Tab') {
    event.preventDefault();
    const target = event.target as HTMLTextAreaElement;
    const start = target.selectionStart;
    const end = target.selectionEnd;
    target.value = `${target.value.slice(0, start)}  ${target.value.slice(end)}`;
    target.selectionStart = target.selectionEnd = start + 2;
  }
};

const handleGlobalShortcut = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && isFullscreen.value) {
    event.preventDefault();
    void toggleFullscreen();
    return;
  }

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
  languageCodeMap.value[selectedLanguage.value] = code.value;
  selectedLanguage.value = language;
  isLanguageMenuOpen.value = false;
  code.value = languageCodeMap.value[language] ?? getLanguagePreset(language);
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
  delete languageCodeMap.value[selectedLanguage.value];
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
        languageCodeMap.value[detectedLanguage] = code.value;
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
  } else {
    const savedLanguage = localStorage.getItem('playground_language');
    if (savedLanguage && languages.some((lang) => lang.value === savedLanguage)) {
      selectedLanguage.value = savedLanguage;
      previousLanguage.value = savedLanguage;
      code.value = getLanguagePreset(savedLanguage) || code.value;
    }
  }

  updateExportFileName(selectedLanguage.value);
  updateViewportWidth();

  window.addEventListener('keydown', handleGlobalShortcut);
  window.addEventListener('resize', updateViewportWidth);
  window.addEventListener('click', closeLanguageMenuOnOutsideClick);
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
});

onUnmounted(() => {
  syncPageScrollLock(false);
  window.removeEventListener('keydown', handleGlobalShortcut);
  window.removeEventListener('resize', updateViewportWidth);
  window.removeEventListener('click', closeLanguageMenuOnOutsideClick);
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.removeEventListener('touchmove', preventFullscreenExitSwipe);
});

watch(selectedLanguage, (lang) => {
  localStorage.setItem('playground_language', lang);
});

watch(isFullscreen, (active) => {
  syncPageScrollLock(active);
  if (!active) {
    isFullscreenMenuOpen.value = false;
    document.removeEventListener('touchmove', preventFullscreenExitSwipe);
  } else {
    document.addEventListener('touchmove', preventFullscreenExitSwipe, { passive: false });
  }
});
</script>

<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,_#ecfeff_0%,_#f8fafc_32%,_#f8fafc_100%)] text-slate-950 dark:bg-[linear-gradient(180deg,_#020617_0%,_#020617_100%)] dark:text-slate-50">
    <div class="sticky top-0 z-30 border-b border-slate-200/80 bg-white/75 backdrop-blur-2xl dark:border-slate-800 dark:bg-slate-950/75">
      <div class="playground-container mx-auto flex flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div class="flex min-w-0 flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div class="flex min-w-0 items-start gap-4">
            <button class="glass-icon-button shrink-0" @click="router.back()">
              <Icon icon="material-symbols:arrow-back" class="h-5 w-5" />
            </button>
            <div class="min-w-0">
              <h1 class="truncate text-2xl font-black tracking-tight">在线代码编辑器</h1>
              <p class="text-sm text-slate-500 dark:text-slate-400">Ctrl + Enter 运行</p>
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
              <Icon :icon="outputPosition === 'bottom' ? 'material-symbols:vertical-split' : 'material-symbols:horizontal-split'" class="h-4 w-4" />
              {{ outputPosition === 'bottom' ? '右边' : '底部' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="playground-container mx-auto px-4 py-6 sm:px-6 lg:px-8" :style="{ paddingBottom: outputPosition === 'bottom' ? bottomPanelSpacer : '5.5rem' }">
      <div class="playground-stack" :class="{ 'playground-side-mode': outputPosition === 'side' }">
        <section
          ref="editorPanelRef"
          class="editor-panel"
          :class="{
            'fullscreen-mode': isFullscreen,
            'fullscreen-side-mode': isFullscreen && outputPosition === 'side',
            'fullscreen-bottom-mode': isFullscreen && outputPosition === 'bottom',
          }"
        >
          <div class="panel-header">
            <div class="flex items-center gap-2">
              <Icon icon="material-symbols:code" class="h-5 w-5 text-cyan-500" />
              <span>代码编辑区</span>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="isFullscreen"
                class="fullscreen-icon-btn"
                :title="outputPosition === 'bottom' ? '切换为右边显示' : '切换为底部显示'"
                @click="outputPosition = outputPosition === 'bottom' ? 'side' : 'bottom'"
              >
                <Icon :icon="outputPosition === 'bottom' ? 'material-symbols:vertical-split' : 'material-symbols:horizontal-split'" class="h-5 w-5" />
              </button>
              <button v-if="isFullscreen" class="fullscreen-icon-btn" title="菜单" @click="isFullscreenMenuOpen = !isFullscreenMenuOpen">
                <Icon icon="material-symbols:menu" class="h-5 w-5" />
              </button>
              <button class="fullscreen-icon-btn" :title="isFullscreen ? '退出全屏' : '全屏'" @click="toggleFullscreen">
                <Icon :icon="isFullscreen ? 'material-symbols:fullscreen-exit' : 'material-symbols:fullscreen'" class="h-5 w-5" />
              </button>
            </div>
          </div>

          <div v-if="isFullscreen && isFullscreenMenuOpen" class="fullscreen-menu">
            <div class="fullscreen-menu-section">
              <div class="fullscreen-menu-label">切换语言</div>
              <button
                v-for="lang in languages"
                :key="lang.value"
                type="button"
                class="fullscreen-menu-item"
                @click="updateLanguage(lang.value); isFullscreenMenuOpen = false"
              >
                <Icon :icon="lang.icon" class="h-4 w-4 shrink-0" :style="{ color: lang.color }" />
                <span>{{ lang.name }}</span>
                <span v-if="selectedLanguage === lang.value" class="ml-auto h-2 w-2 rounded-full bg-cyan-400"></span>
              </button>
            </div>
            <div class="fullscreen-menu-divider"></div>
            <button class="fullscreen-menu-item" @click="importCode(); isFullscreenMenuOpen = false">
              <Icon icon="material-symbols:upload" class="h-4 w-4" /> 导入
            </button>
            <button class="fullscreen-menu-item" @click="saveCode(); isFullscreenMenuOpen = false">
              <Icon icon="material-symbols:download" class="h-4 w-4" /> 导出
            </button>
          </div>

          <div v-show="!isFullscreen" class="editor-toolbar">
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
              <MonacoEditor
                v-model="code"
                :language="selectedLanguage"
                :is-dark="themeStore.isDark"
                @ready="handleMonacoReady"
              />
            </div>

            <aside
              v-if="outputPosition === 'side'"
              class="side-io-panel"
              :class="{ 'fullscreen-side-io-panel': isFullscreen }"
            >
              <section class="surface-panel side-io-section">
                <div class="collapse-header">
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
                  <textarea
                    v-model="expectedOutput"
                    class="plain-textarea panel-textarea"
                    placeholder="预期结果（选填）：填写后自动对比实际输出"
                    style="margin-top: 8px;"
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
                <div class="collapse-body output-body">
                  <div class="output-box" :class="{ 'has-output': output, 'is-error': outputKind === 'error' }">
                    <pre v-if="output" :class="outputKind === 'error' ? 'text-rose-300' : 'text-emerald-300'">{{ output }}</pre>
                    <div v-else class="placeholder-copy">运行结果和报错都会显示在这里。</div>
                  </div>
                  <div v-if="executionStatus" class="output-status">
                    <div class="status-divider"></div>
                    <div class="status-content">
                      <span class="status-text" :class="outputKind === 'error' ? 'text-rose-400' : 'text-emerald-400'">{{ executionStatus }}</span>
                      <span v-if="testVerdict" class="test-badge" :class="testVerdict">{{ testVerdict === 'pass' ? '✓ PASS' : '✗ FAILED' }}</span>
                    </div>
                  </div>
                </div>
              </section>
            </aside>
          </div>

          <template v-if="isFullscreen && outputPosition === 'bottom'">
            <div v-if="!bottomPanelsCollapsed" class="fullscreen-panels">
              <section class="surface-panel fullscreen-panel-item">
                <div class="collapse-header">
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
                  <textarea
                    v-model="expectedOutput"
                    class="plain-textarea panel-textarea"
                    placeholder="预期结果（选填）：填写后自动对比实际输出"
                    style="margin-top: 8px;"
                  ></textarea>
                </div>
              </section>
              <section class="surface-panel fullscreen-panel-item">
                <div class="collapse-header">
                  <div class="flex items-center gap-2">
                    <Icon :icon="outputKind === 'error' ? 'material-symbols:error' : 'material-symbols:output'" class="h-5 w-5" :class="outputKind === 'error' ? 'text-rose-500' : 'text-emerald-500'" />
                    <span>输出</span>
                  </div>
                </div>
                <div class="collapse-body output-body">
                  <div class="output-box" :class="{ 'has-output': output, 'is-error': outputKind === 'error' }">
                    <pre v-if="output" :class="outputKind === 'error' ? 'text-rose-300' : 'text-emerald-300'">{{ output }}</pre>
                    <div v-else class="placeholder-copy">运行结果和报错都会显示在这里。</div>
                  </div>
                  <div v-if="executionStatus" class="output-status">
                    <div class="status-divider"></div>
                    <div class="status-content">
                      <span class="status-text" :class="outputKind === 'error' ? 'text-rose-400' : 'text-emerald-400'">{{ executionStatus }}</span>
                      <span v-if="testVerdict" class="test-badge" :class="testVerdict">{{ testVerdict === 'pass' ? '✓ PASS' : '✗ FAILED' }}</span>
                    </div>
                  </div>
                </div>
              </section>
            </div>
            <div class="fullscreen-bottom-bar">
              <button class="toolbar-button flex-1 sm:flex-none" @click="outputPosition = 'side'">
                <Icon icon="material-symbols:vertical-split" class="h-4 w-4" />
                侧边
              </button>
              <button class="toolbar-button flex-1 sm:flex-none" @click="resetCode">
                <Icon icon="material-symbols:refresh" class="h-4 w-4" />
                重置
              </button>
              <button class="floating-collapse-button" @click="bottomPanelsCollapsed = !bottomPanelsCollapsed">
                <Icon :icon="bottomPanelsCollapsed ? 'material-symbols:unfold-less-rounded' : 'material-symbols:unfold-more-rounded'" class="h-5 w-5" />
                {{ bottomPanelsCollapsed ? '展开' : '收起' }}
              </button>
            </div>
          </template>
          <template v-else-if="isFullscreen">
            <div class="fullscreen-bottom-bar fullscreen-side-bottom-bar">
              <button class="toolbar-button flex-1 sm:flex-none" @click="outputPosition = 'bottom'">
                <Icon icon="material-symbols:horizontal-split" class="h-4 w-4" />
                底部
              </button>
              <button class="toolbar-button flex-1 sm:flex-none" @click="resetCode">
                <Icon icon="material-symbols:refresh" class="h-4 w-4" />
                重置
              </button>
            </div>
          </template>
        </section>
      </div>
    </div>

    <div v-if="!isFullscreen && outputPosition === 'bottom'" v-show="!bottomPanelsCollapsed" class="fixed-panels-shell">
      <div class="playground-container fixed-panels-inner">
        <div class="bottom-panels">
          <section class="surface-panel">
            <div class="collapse-header">
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
              <textarea
                v-model="expectedOutput"
                class="plain-textarea panel-textarea"
                placeholder="预期结果（选填）：填写后自动对比实际输出"
                style="margin-top: 8px;"
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
            <div class="collapse-body output-body">
              <div class="output-box" :class="{ 'has-output': output, 'is-error': outputKind === 'error' }">
                <pre v-if="output" :class="outputKind === 'error' ? 'text-rose-300' : 'text-emerald-300'">{{ output }}</pre>
                <div v-else class="placeholder-copy">运行结果和报错都会显示在这里。</div>
              </div>
              <div v-if="executionStatus" class="output-status">
                <div class="status-divider"></div>
                <div class="status-content">
                  <span class="status-text" :class="outputKind === 'error' ? 'text-rose-400' : 'text-emerald-400'">{{ executionStatus }}</span>
                  <span v-if="testVerdict" class="test-badge" :class="testVerdict">{{ testVerdict === 'pass' ? '✓ PASS' : '✗ FAILED' }}</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>

    <div v-if="!isFullscreen && outputPosition === 'bottom'" class="floating-button-group" :style="{ bottom: floatingButtonBottom }">
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

<style scoped>
@reference 'tailwindcss';

.glass-icon-button {
  @apply grid h-11 w-11 place-items-center rounded-2xl border border-slate-200 bg-white/90 text-slate-700 shadow-sm backdrop-blur-2xl transition hover:bg-slate-100;
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
  @apply inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm backdrop-blur-2xl transition hover:-translate-y-0.5 hover:bg-slate-100;
}

.run-button {
  @apply inline-flex min-h-11 items-center gap-2 rounded-2xl bg-cyan-400 px-5 py-2.5 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:-translate-y-0.5 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70;
}

.editor-panel {
  @apply overflow-hidden rounded-[2rem] border border-slate-200 bg-white/85 shadow-xl shadow-slate-200/60 backdrop-blur-2xl;
}

.surface-panel {
  @apply overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white/85 shadow-lg shadow-slate-200/50 backdrop-blur-2xl;
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

.collapse-body {
  @apply overflow-hidden;
}

.output-body {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.output-box {
  flex: 1;
  min-height: 180px;
  padding: 20px;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 14px;
  line-height: 1.6;
  overflow: auto;
  background: linear-gradient(to bottom, #f1f5f9 95%, #e2e8f0 95%, #e2e8f0 100%);
  color: #1e293b;
}
.dark .output-box {
  background: linear-gradient(to bottom, #020617 95%, #0f172a 95%, #0f172a 100%);
  color: #6ee7b7;
}
.output-box.is-error {
  color: #dc2626;
}
.dark .output-box.is-error {
  color: #fca5a5;
}
.output-box.has-output {
  min-height: 60px;
}

.output-status {
  flex-shrink: 0;
  padding: 8px 16px;
  background: #e2e8f0;
}
.dark .output-status {
  background: #0f172a;
}

.status-divider {
  height: 1px;
  border-top: 1px dashed #94a3b8;
  margin-bottom: 8px;
}
.dark .status-divider {
  border-top-color: #475569;
}

.status-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-text {
  font-size: 13px;
  font-weight: 600;
}

.test-badge {
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.05em;
  padding: 2px 12px;
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
  @apply relative h-[620px] overflow-hidden;
}

.editor-shell :deep(.monaco-editor .margin),
.editor-shell :deep(.monaco-editor .monaco-editor-background) {
  background: transparent !important;
}

.editor-run-button {
  @apply min-w-[10.75rem] justify-center;
}

.plain-textarea {
  @apply w-full resize-none border-none p-5 font-mono text-sm outline-none transition-colors duration-300 placeholder:text-slate-400 focus:ring-0;
  background-color: #ffffff;
  color: #1e293b;
  tab-size: 2;
}
.dark .plain-textarea {
  background-color: #1e293b !important;
  color: #e2e8f0 !important;
}

.panel-textarea {
  height: 330px;
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
  z-index: 9999;
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

  .plain-textarea,
  .output-box {
    @apply p-4 text-[13px] leading-6;
  }

  .panel-textarea {
    height: 240px;
    max-height: 240px;
  }
  .output-body .output-box {
    min-height: 80px;
  }

  .fixed-panels-inner {
    @apply px-4 pb-4;
  }

  .floating-button-group {
    right: 4rem;
  }

  .floating-collapse-button {
    @apply px-3.5 py-2.5 text-[13px];
  }
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

.fullscreen-side-io-panel {
  width: min(28rem, 32vw);
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
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.side-io-section .panel-textarea {
  flex: 1;
  min-height: 0;
  max-height: none;
  height: auto;
}
.side-io-section .output-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.side-io-section .output-body .output-box {
  flex: 1;
  min-height: 0;
}
.side-io-section .output-body .output-status {
  flex-shrink: 0;
}

@media (max-width: 1023px) {
  .playground-side-mode .editor-body {
    flex-direction: column;
  }

  .side-io-panel {
    width: 100%;
  }

  .fullscreen-side-io-panel {
    width: 100%;
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

  .panel-textarea {
    height: 270px;
    max-height: 270px;
  }
  .output-body .output-box {
    min-height: 100px;
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

  .bottom-panels .surface-panel {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }
  .bottom-panels .collapse-body {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .bottom-panels .panel-textarea {
    flex: 1;
    min-height: 0;
    max-height: none;
    height: auto;
  }
  .bottom-panels .output-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    gap: 0;
  }
  .bottom-panels .output-body .output-box {
    flex: 1;
    min-height: 0;
  }
  .bottom-panels .output-body .output-status {
    flex-shrink: 0;
  }
}

@media (min-width: 768px) and (max-width: 1024px) {
  .bottom-panels {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    height: 50vh;
    min-height: 0;
  }

  .bottom-panels .surface-panel {
    display: flex;
    flex-direction: column;
    max-height: 50vh;
    min-height: 0;
  }

  .bottom-panels .collapse-body {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .bottom-panels .panel-textarea {
    flex: 1;
    min-height: 0;
    max-height: none;
    height: auto;
  }
  .bottom-panels .output-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }
  .bottom-panels .output-body .output-box {
    flex: 1;
    min-height: 0;
  }
  .bottom-panels .output-body .output-status {
    flex-shrink: 0;
  }

  .floating-button-group {
    right: 1.5rem;
  }

  .floating-collapse-button {
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
  }
}

/* 鈹€鈹€ Fullscreen Mode 鈹€鈹€ */

.fullscreen-mode {
  position: fixed !important;
  inset: 0 !important;
  z-index: 9999 !important;
  display: flex !important;
  flex-direction: column !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  touch-action: manipulation;
  overscroll-behavior: none;
}

.fullscreen-mode .panel-header {
  flex-shrink: 0;
  border-radius: 0;
}

.fullscreen-mode .editor-body {
  flex: 1 !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
}

.fullscreen-side-mode .editor-body {
  flex-direction: row !important;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
}

.fullscreen-mode .editor-shell {
  flex: 1 !important;
  min-height: 0 !important;
  height: auto !important;
}

.fullscreen-side-mode .editor-shell {
  min-width: 0 !important;
}

.fullscreen-icon-btn {
  @apply grid h-9 w-9 place-items-center rounded-xl border border-slate-200 bg-white/90 text-slate-700 shadow-sm transition hover:bg-slate-100;
}

.fullscreen-menu {
  flex-shrink: 0;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
  padding: 0.75rem;
}

.fullscreen-menu-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.fullscreen-menu-label {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: #94a3b8;
  padding: 0.25rem 0.75rem 0.5rem;
}

.fullscreen-menu-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.75rem;
  border-radius: 1rem;
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 700;
  color: #334155;
  transition: background 0.15s;
}

.fullscreen-menu-item:hover {
  background: #f1f5f9;
}

.fullscreen-menu-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 0.5rem 0.75rem;
}

.fullscreen-panels {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  height: 33.33vh;
  min-height: 0;
  gap: 0.75rem;
  padding: 0.75rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.fullscreen-panels .surface-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.fullscreen-panels .collapse-body {
  flex: 1;
  overflow: hidden;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.fullscreen-panels .panel-textarea {
  flex: 1;
  min-height: 0;
  max-height: none;
  height: auto;
}
.fullscreen-panels .output-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.fullscreen-panels .output-body .output-box {
  flex: 1;
  min-height: 0;
}
.fullscreen-panels .output-body .output-status {
  flex-shrink: 0;
}

.fullscreen-panel-item {
  border-radius: 1.25rem !important;
}

.fullscreen-bottom-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem;
  border-top: 1px solid #e2e8f0;
  background: #fff;
}

.fullscreen-side-bottom-bar {
  justify-content: flex-end;
}

@media (max-width: 1023px) {
  .fullscreen-side-mode .editor-body {
    flex-direction: column !important;
  }
}

/* dark overrides for fullscreen */
html.dark .fullscreen-menu {
  border-color: #1e293b;
  background: #0f172a;
}

html.dark .fullscreen-menu-item {
  color: #e2e8f0;
}

html.dark .fullscreen-menu-item:hover {
  background: #1e293b;
}

html.dark .fullscreen-menu-divider {
  background: #1e293b;
}

html.dark .fullscreen-panels {
  border-color: #1e293b;
  background: #0f172a;
}

html.dark .fullscreen-side-mode .editor-body {
  background: #0f172a;
}

html.dark .fullscreen-bottom-bar {
  border-color: #1e293b;
  background: #0f172a;
}

html.dark .fullscreen-icon-btn {
  border-color: #1e293b;
  background: #0f172a;
  color: #e2e8f0;
}

html.dark .fullscreen-icon-btn:hover {
  background: #1e293b;
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

html.dark .plain-textarea,
html.dark .plain-textarea {
  caret-color: #ffffff !important;
}

html:not(.dark) .editor-panel,
html:not(.dark) .surface-panel,
html:not(.dark) .plain-textarea {
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

html:not(.dark) .plain-textarea {
  caret-color: #0f172a !important;
}




</style>
