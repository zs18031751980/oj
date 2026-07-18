<script setup lang="ts">
import {
  computed,
  defineAsyncComponent,
  markRaw,
  onMounted,
  onUnmounted,
  ref,
  watch,
} from "vue";
import { Icon } from "@iconify/vue";
import { useRoute, useRouter } from "vue-router";
import { apiRequest } from "../services/api";
import { useAuthStore } from "../stores/auth";
import { useThemeStore } from "../stores/theme";

const MonacoEditor = defineAsyncComponent(
  () => import("../components/MonacoEditor.vue"),
);

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

const languagePresets: Record<string, string> = markRaw({
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
  `,
});

const languages: LanguageOption[] = markRaw([
  {
    name: "JavaScript",
    value: "javascript",
    prism: "javascript",
    icon: "vscode-icons:file-type-js-official",
    color: "#f7df1e",
  },
  {
    name: "Python",
    value: "python",
    prism: "python",
    icon: "vscode-icons:file-type-python",
    color: "#3776ab",
  },
  {
    name: "Java",
    value: "java",
    prism: "java",
    icon: "vscode-icons:file-type-java",
    color: "#ed8b00",
  },
  {
    name: "C++",
    value: "cpp",
    prism: "cpp",
    icon: "vscode-icons:file-type-cpp",
    color: "#00599c",
  },
  {
    name: "Go",
    value: "go",
    prism: "go",
    icon: "vscode-icons:file-type-go",
    color: "#00add8",
  },
  {
    name: "Rust",
    value: "rust",
    prism: "rust",
    icon: "vscode-icons:file-type-rust",
    color: "#dea584",
  },
  {
    name: "Swift",
    value: "swift",
    prism: "swift",
    icon: "vscode-icons:file-type-swift",
    color: "#fa7343",
  },
  {
    name: "Kotlin",
    value: "kotlin",
    prism: "kotlin",
    icon: "vscode-icons:file-type-kotlin",
    color: "#7f52ff",
  },
]);

const defaultLanguage = languages.find((lang) => lang.value === "cpp")!;
const fallbackFileNames: Record<string, string> = markRaw({
  javascript: "script",
  python: "script",
  java: "Main",
  cpp: "main",
  go: "main",
  rust: "main",
  swift: "main",
  kotlin: "Main",
});

const extensionMap: Record<string, string> = markRaw({
  javascript: "js",
  python: "py",
  java: "java",
  cpp: "cpp",
  go: "go",
  rust: "rs",
  swift: "swift",
  kotlin: "kt",
});

const getLanguagePreset = (language: string) => languagePresets[language] ?? "";

const sanitizeFileName = (value: string) =>
  value.replace(/[<>:"/\\|?*\u0000-\u001f]/g, "").trim();

const selectedLanguage = ref<string>(defaultLanguage.value);
const previousLanguage = ref<string>(defaultLanguage.value);
const isLanguageMenuOpen = ref(false);
const code = ref<string>(getLanguagePreset(defaultLanguage.value));
const languageCodeMap = ref<Record<string, string>>({});
const stdin = ref<string>("");
const output = ref<string>("");
const executionStatus = ref<string>("");
const expectedOutput = ref<string>("");
const testVerdict = ref<"pass" | "failed" | null>(null);
const outputKind = ref<"info" | "error">("info");
const isExecuting = ref(false);
const exportFileName = ref<string>(
  fallbackFileNames[defaultLanguage.value] ?? "code",
);
const activePanelTab = ref<"stdin" | "expected" | "output">("stdin");
const workspaceRef = ref<HTMLElement | null>(null);
const editorPanePercent = ref(68);
const isResizing = ref(false);

const isFullscreen = ref(false);
const isFullscreenMenuOpen = ref(false);
const editorPanelRef = ref<HTMLElement | null>(null);
const fullscreenExitArmed = ref(false);

const isTouchFullscreenQuirkDevice = () => {
  if (typeof navigator === "undefined") {
    return false;
  }

  const userAgent = navigator.userAgent;
  return /iPhone|iPod/.test(userAgent);
};

const syncPageScrollLock = (locked: boolean) => {
  if (typeof document === "undefined") {
    return;
  }

  document.documentElement.style.overflow = locked ? "hidden" : "";
  document.body.style.overflow = locked ? "hidden" : "";
};

const preventFullscreenExitSwipe = (e: TouchEvent) => {
  const target = e.target as HTMLElement | null;
  if (!target) return;
  const scrollable = target.closest(
    "textarea, pre, .monaco-editor, .output-box",
  );
  if (scrollable) return;
  e.preventDefault();
};

const toggleFullscreen = async () => {
  if (isFullscreen.value) {
    fullscreenExitArmed.value = true;

    const activeEl =
      document.fullscreenElement || (document as any).webkitFullscreenElement;
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
  const requestFS =
    docEl.requestFullscreen ||
    docEl.webkitRequestFullscreen ||
    docEl.mozRequestFullScreen;

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

  const active = !!(
    document.fullscreenElement || (document as any).webkitFullscreenElement
  );

  isFullscreen.value = active;
  if (!active) {
    isFullscreenMenuOpen.value = false;
  }

  fullscreenExitArmed.value = false;
};

const currentLanguageInfo = computed<LanguageOption>(
  () =>
    languages.find((lang) => lang.value === selectedLanguage.value) ??
    defaultLanguage,
);

const executionVisualState = computed<"idle" | "running" | "success" | "error">(
  () => {
    if (isExecuting.value) return "running";
    if (outputKind.value === "error" && output.value) return "error";
    if (executionStatus.value || output.value) return "success";
    return "idle";
  },
);

const exportExtension = computed(
  () => extensionMap[selectedLanguage.value] ?? "txt",
);

const runCode = async () => {
  activePanelTab.value = "output";
  const source = code.value;
  if (!source.trim()) {
    outputKind.value = "error";
    output.value = "代码不能为空。";
    return;
  }

  isExecuting.value = true;
  output.value = "";
  executionStatus.value = "";
  outputKind.value = "info";
  testVerdict.value = null;

  try {
    const endpoint = authStore.isAuthenticated
      ? "/code/run"
      : "/code/run/public";
    const result = await apiRequest<ExecutionResponse>(endpoint, {
      method: "POST",
      skipAuth: !authStore.isAuthenticated,
      body: JSON.stringify({
        code: source,
        language: selectedLanguage.value,
        stdin: stdin.value,
      }),
    });

    const stderrText = (result.stderr || "").trim();
    const stdoutText = (result.stdout || "").trim();
    const messageText = (result.message || "").trim();

    if (stderrText) {
      output.value = stderrText;
      outputKind.value = "error";
      executionStatus.value = "编译错误";
    } else {
      output.value = stdoutText || messageText;
      outputKind.value = "info";
      executionStatus.value = output.value
        ? "执行成功"
        : "程序已运行，但没有产生输出。";
    }

    if (expectedOutput.value.trim()) {
      const compareText = stdoutText || messageText;
      testVerdict.value =
        compareText.trim() === expectedOutput.value.trim() ? "pass" : "failed";
    }
  } catch (error) {
    outputKind.value = "error";
    output.value = `执行错误: ${error instanceof Error ? error.message : "未知错误"}`;
  } finally {
    isExecuting.value = false;
  }
};

const handleMonacoReady = (editor: {
  addAction: (action: {
    id: string;
    label: string;
    keybindings: number[];
    run: () => void;
  }) => void;
}) => {
  editor.addAction({
    id: "run-code",
    label: "Run Code",
    keybindings: [2048 | 3],
    run: () => {
      if (!isExecuting.value) {
        void runCode();
      }
    },
  });
};

const handleStdinKeydown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    if (!isExecuting.value) {
      void runCode();
    }
    return;
  }

  if (event.key === "Tab") {
    event.preventDefault();
    const target = event.target as HTMLTextAreaElement;
    const start = target.selectionStart;
    const end = target.selectionEnd;
    target.value = `${target.value.slice(0, start)}  ${target.value.slice(end)}`;
    target.selectionStart = target.selectionEnd = start + 2;
  }
};

const handleGlobalShortcut = (event: KeyboardEvent) => {
  if (event.key === "Escape" && isFullscreen.value) {
    event.preventDefault();
    void toggleFullscreen();
    return;
  }

  if (
    (event.ctrlKey || event.metaKey) &&
    event.key === "Enter" &&
    !isExecuting.value
  ) {
    const target = event.target as HTMLElement | null;
    const isEditable =
      target?.tagName === "TEXTAREA" || target?.tagName === "INPUT";
    if (isEditable) {
      return;
    }

    event.preventDefault();
    void runCode();
  }
};

const closeLanguageMenuOnOutsideClick = (event: MouseEvent) => {
  const target = event.target as Node | null;
  if (
    languageMenuRef.value &&
    target &&
    !languageMenuRef.value.contains(target)
  ) {
    isLanguageMenuOpen.value = false;
  }
};

const updateExportFileName = (language: string) => {
  const fallback = fallbackFileNames[language] ?? "code";
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
  const baseName =
    sanitizeFileName(exportFileName.value) ||
    fallbackFileNames[selectedLanguage.value] ||
    "code";
  exportFileName.value = baseName;

  const blob = new Blob([code.value], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
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
  stdin.value = "";
  output.value = "";
  outputKind.value = "info";
};

const importCode = () => {
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = ".js,.py,.java,.cpp,.go,.rs,.swift,.kt,.txt";

  fileInput.onchange = (event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (readerEvent) => {
      code.value = String(readerEvent.target?.result || "");

      const ext = file.name.split(".").pop()?.toLowerCase() || "";
      const extToLanguage: Record<string, string> = {
        js: "javascript",
        py: "python",
        java: "java",
        cpp: "cpp",
        go: "go",
        rs: "rust",
        swift: "swift",
        kt: "kotlin",
      };

      const detectedLanguage = extToLanguage[ext];
      if (detectedLanguage) {
        languageCodeMap.value[detectedLanguage] = code.value;
        selectedLanguage.value = detectedLanguage;
        previousLanguage.value = detectedLanguage;
      }

      const importedName = file.name.replace(/\.[^.]+$/, "");
      const sanitizedImportedName = sanitizeFileName(importedName);
      exportFileName.value =
        sanitizedImportedName ||
        fallbackFileNames[selectedLanguage.value] ||
        "code";
    };

    reader.readAsText(file);
  };

  fileInput.click();
};

const updateEditorPaneWidth = (clientX: number) => {
  const workspace = workspaceRef.value;
  if (!workspace || window.innerWidth < 1024) return;
  const bounds = workspace.getBoundingClientRect();
  const nextPercent = ((clientX - bounds.left) / bounds.width) * 100;
  editorPanePercent.value = Math.min(78, Math.max(45, nextPercent));
};

const handleResizeMove = (event: PointerEvent) => {
  if (!isResizing.value) return;
  updateEditorPaneWidth(event.clientX);
};

const stopResizing = () => {
  isResizing.value = false;
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
  window.removeEventListener("pointermove", handleResizeMove);
  window.removeEventListener("pointerup", stopResizing);
};

const startResizing = (event: PointerEvent) => {
  if (window.innerWidth < 1024) return;
  event.preventDefault();
  isResizing.value = true;
  document.body.style.cursor = "col-resize";
  document.body.style.userSelect = "none";
  window.addEventListener("pointermove", handleResizeMove);
  window.addEventListener("pointerup", stopResizing);
};

const handleSplitterKeydown = (event: KeyboardEvent) => {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  event.preventDefault();
  const direction = event.key === "ArrowLeft" ? -2 : 2;
  editorPanePercent.value = Math.min(
    78,
    Math.max(45, editorPanePercent.value + direction),
  );
};

onMounted(() => {
  const languageParam = route.query.language as string | undefined;
  if (languageParam && languages.some((lang) => lang.value === languageParam)) {
    selectedLanguage.value = languageParam;
    previousLanguage.value = languageParam;
    code.value = getLanguagePreset(languageParam) || code.value;
  } else {
    const savedLanguage = localStorage.getItem("playground_language");
    if (
      savedLanguage &&
      languages.some((lang) => lang.value === savedLanguage)
    ) {
      selectedLanguage.value = savedLanguage;
      previousLanguage.value = savedLanguage;
      code.value = getLanguagePreset(savedLanguage) || code.value;
    }
  }

  updateExportFileName(selectedLanguage.value);

  window.addEventListener("keydown", handleGlobalShortcut);
  window.addEventListener("click", closeLanguageMenuOnOutsideClick);
  document.addEventListener("fullscreenchange", handleFullscreenChange);
  document.addEventListener("webkitfullscreenchange", handleFullscreenChange);
});

onUnmounted(() => {
  stopResizing();
  syncPageScrollLock(false);
  window.removeEventListener("keydown", handleGlobalShortcut);
  window.removeEventListener("click", closeLanguageMenuOnOutsideClick);
  document.removeEventListener("fullscreenchange", handleFullscreenChange);
  document.removeEventListener(
    "webkitfullscreenchange",
    handleFullscreenChange,
  );
  document.removeEventListener("touchmove", preventFullscreenExitSwipe);
});

watch(selectedLanguage, (lang) => {
  localStorage.setItem("playground_language", lang);
});

watch(isFullscreen, (active) => {
  syncPageScrollLock(active);
  if (!active) {
    isFullscreenMenuOpen.value = false;
    document.removeEventListener("touchmove", preventFullscreenExitSwipe);
  } else {
    document.addEventListener("touchmove", preventFullscreenExitSwipe, {
      passive: false,
    });
  }
});
</script>

<template>
  <div class="ide-page">
    <section
      ref="editorPanelRef"
      class="ide-workbench"
      :class="{ 'ide-fullscreen': isFullscreen }"
    >
      <header class="ide-topbar">
        <div class="ide-title-group">
          <button
            class="ide-icon-button"
            title="返回"
            aria-label="返回"
            @click="router.back()"
          >
            <Icon icon="material-symbols:arrow-back" />
          </button>
          <div class="ide-title-copy">
            <h1>在线代码编辑器</h1>
            <p>Ctrl + Enter 运行</p>
          </div>
        </div>

        <div class="ide-toolbar">
          <div ref="languageMenuRef" class="ide-language-control">
            <button
              class="ide-language-button"
              :title="currentLanguageInfo.name"
              :aria-expanded="isLanguageMenuOpen"
              @click="isLanguageMenuOpen = !isLanguageMenuOpen"
            >
              <Icon
                :icon="currentLanguageInfo.icon"
                :style="{ color: currentLanguageInfo.color }"
              />
              <span>{{ currentLanguageInfo.name }}</span>
              <Icon
                icon="material-symbols:arrow-drop-down"
                class="language-chevron"
                :class="{ 'rotate-180': isLanguageMenuOpen }"
              />
            </button>
            <div v-if="isLanguageMenuOpen" class="ide-language-menu">
              <button
                v-for="lang in languages"
                :key="lang.value"
                type="button"
                class="ide-language-option"
                @click="updateLanguage(lang.value)"
              >
                <Icon :icon="lang.icon" :style="{ color: lang.color }" />
                <span>{{ lang.name }}</span>
                <span
                  v-if="selectedLanguage === lang.value"
                  class="language-current-dot"
                ></span>
              </button>
            </div>
          </div>

          <div class="ide-tool-group">
            <button
              v-if="isFullscreen"
              class="ide-icon-button"
              title="菜单"
              aria-label="菜单"
              @click="isFullscreenMenuOpen = !isFullscreenMenuOpen"
            >
              <Icon icon="material-symbols:menu" />
            </button>
            <button
              class="ide-icon-button"
              title="导入"
              aria-label="导入"
              @click="importCode"
            >
              <Icon icon="material-symbols:upload" />
            </button>
            <button
              class="ide-icon-button"
              title="导出"
              aria-label="导出"
              @click="saveCode"
            >
              <Icon icon="material-symbols:download" />
            </button>
            <button
              class="ide-icon-button"
              title="重置"
              aria-label="重置"
              @click="resetCode"
            >
              <Icon icon="material-symbols:refresh" />
            </button>
            <button
              class="ide-icon-button"
              :title="isFullscreen ? '退出全屏' : '全屏'"
              :aria-label="isFullscreen ? '退出全屏' : '全屏'"
              @click="toggleFullscreen"
            >
              <Icon
                :icon="
                  isFullscreen
                    ? 'material-symbols:fullscreen-exit'
                    : 'material-symbols:fullscreen'
                "
              />
            </button>
          </div>

          <button
            class="ide-run-button"
            :disabled="isExecuting"
            @click="runCode"
          >
            <Icon
              :icon="
                isExecuting
                  ? 'material-symbols:hourglass-top'
                  : 'material-symbols:play-arrow'
              "
              :class="{ 'animate-spin': isExecuting }"
            />
            {{ isExecuting ? "运行中..." : "运行代码" }}
          </button>
        </div>
      </header>

      <div v-if="isFullscreen && isFullscreenMenuOpen" class="fullscreen-menu">
        <div class="fullscreen-menu-section">
          <div class="fullscreen-menu-label">切换语言</div>
          <button
            v-for="lang in languages"
            :key="lang.value"
            type="button"
            class="fullscreen-menu-item"
            @click="
              updateLanguage(lang.value);
              isFullscreenMenuOpen = false;
            "
          >
            <Icon
              :icon="lang.icon"
              class="h-4 w-4 shrink-0"
              :style="{ color: lang.color }"
            />
            <span>{{ lang.name }}</span>
            <span
              v-if="selectedLanguage === lang.value"
              class="ml-auto h-2 w-2 rounded-full bg-cyan-400"
            ></span>
          </button>
        </div>
        <div class="fullscreen-menu-divider"></div>
        <button
          class="fullscreen-menu-item"
          @click="
            importCode();
            isFullscreenMenuOpen = false;
          "
        >
          <Icon icon="material-symbols:upload" class="h-4 w-4" /> 导入
        </button>
        <button
          class="fullscreen-menu-item"
          @click="
            saveCode();
            isFullscreenMenuOpen = false;
          "
        >
          <Icon icon="material-symbols:download" class="h-4 w-4" /> 导出
        </button>
      </div>
      <div class="ide-filebar">
        <div class="ide-file-tab">
          <Icon icon="material-symbols:code" />
          <span class="file-section-title">代码编辑区</span>
          <label class="file-name-control">
            <span>导出文件名</span>
            <input
              v-model="exportFileName"
              type="text"
              :placeholder="fallbackFileNames[selectedLanguage] || 'code'"
            />
            <span>.{{ exportExtension }}</span>
          </label>
        </div>
        <div class="file-save-preview">
          <span>保存为</span>
          <span
            >{{
              sanitizeFileName(exportFileName) ||
              fallbackFileNames[selectedLanguage] ||
              "code"
            }}.{{ exportExtension }}</span
          >
        </div>
      </div>

      <div
        ref="workspaceRef"
        class="ide-workspace"
        :class="{ 'is-resizing': isResizing }"
        :style="{ '--editor-pane-percent': `${editorPanePercent}%` }"
      >
        <div class="ide-editor-pane">
          <MonacoEditor
            v-model="code"
            :language="selectedLanguage"
            :is-dark="themeStore.isDark"
            @ready="handleMonacoReady"
          />
        </div>

        <div
          class="ide-splitter"
          role="separator"
          tabindex="0"
          aria-orientation="vertical"
          aria-label="调整编辑器宽度"
          aria-valuemin="45"
          aria-valuemax="78"
          :aria-valuenow="Math.round(editorPanePercent)"
          @pointerdown="startResizing"
          @keydown="handleSplitterKeydown"
        >
          <span></span>
        </div>

        <aside class="ide-utility-pane">
          <div class="ide-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              :aria-selected="activePanelTab === 'stdin'"
              :class="{ active: activePanelTab === 'stdin' }"
              @click="activePanelTab = 'stdin'"
            >
              <Icon icon="material-symbols:input" />
              <span>输入数据</span>
            </button>
            <button
              type="button"
              role="tab"
              :aria-selected="activePanelTab === 'expected'"
              :class="{ active: activePanelTab === 'expected' }"
              @click="activePanelTab = 'expected'"
            >
              <Icon icon="material-symbols:fact-check-outline" />
              <span>预期结果</span>
            </button>
            <button
              type="button"
              role="tab"
              :aria-selected="activePanelTab === 'output'"
              :class="{ active: activePanelTab === 'output' }"
              @click="activePanelTab = 'output'"
            >
              <span class="execution-dot" :class="executionVisualState"></span>
              <Icon
                :icon="
                  outputKind === 'error'
                    ? 'material-symbols:error'
                    : 'material-symbols:output'
                "
              />
              <span>输出</span>
            </button>
          </div>

          <div class="ide-tab-content">
            <section
              v-show="activePanelTab === 'stdin'"
              role="tabpanel"
              class="ide-tab-panel"
            >
              <textarea
                v-model="stdin"
                class="ide-textarea"
                placeholder="如果程序需要输入，可以在这里填写测试数据。"
                @keydown="handleStdinKeydown"
              ></textarea>
            </section>

            <section
              v-show="activePanelTab === 'expected'"
              role="tabpanel"
              class="ide-tab-panel"
            >
              <textarea
                v-model="expectedOutput"
                class="ide-textarea"
                placeholder="预期结果（选填）：填写后自动对比实际输出"
              ></textarea>
            </section>

            <section
              v-show="activePanelTab === 'output'"
              role="tabpanel"
              class="ide-tab-panel"
            >
              <div
                class="ide-output"
                :class="{
                  'has-output': output,
                  'is-error': outputKind === 'error',
                }"
              >
                <pre v-if="output">{{ output }}</pre>
                <div v-else class="placeholder-copy">
                  运行结果和报错都会显示在这里。
                </div>
              </div>
              <div v-if="executionStatus" class="ide-output-status">
                <span
                  :class="
                    outputKind === 'error'
                      ? 'text-rose-500'
                      : 'text-emerald-600'
                  "
                  >{{ executionStatus }}</span
                >
                <span
                  v-if="testVerdict"
                  class="test-badge"
                  :class="testVerdict"
                  >{{ testVerdict === "pass" ? "✓ PASS" : "✗ FAILED" }}</span
                >
              </div>
            </section>
          </div>
        </aside>
      </div>
    </section>
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
  font-family:
    ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  font-size: 14px;
  line-height: 1.6;
  overflow: auto;
  background: linear-gradient(
    to bottom,
    #f1f5f9 95%,
    #e2e8f0 95%,
    #e2e8f0 100%
  );
  color: #1e293b;
}
.dark .output-box {
  background: linear-gradient(
    to bottom,
    #020617 95%,
    #0f172a 95%,
    #0f172a 100%
  );
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

<style scoped>
.ide-page {
  height: calc(100dvh - var(--header-h, 5rem));
  min-height: 0;
  overflow: hidden;
  padding: 0.75rem;
  background: #e8ecef;
  color: #17212b;
}

.ide-workbench {
  display: flex;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #b9c3ca;
  border-radius: 0.5rem;
  background: #f7f9fa;
}

.ide-topbar {
  position: relative;
  z-index: 30;
  display: flex;
  min-height: 3.5rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  border-bottom: 1px solid #c6cfd5;
  background: #eef2f4;
  padding: 0.45rem 0.6rem;
}

.ide-title-group,
.ide-toolbar,
.ide-tool-group {
  display: flex;
  min-width: 0;
  align-items: center;
}

.ide-title-group {
  gap: 0.55rem;
}

.ide-title-copy {
  min-width: 0;
}

.ide-title-copy h1 {
  margin: 0;
  overflow: hidden;
  font-size: 0.9rem;
  font-weight: 800;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ide-title-copy p {
  margin: 0.15rem 0 0;
  color: #687985;
  font:
    500 0.65rem/1.2 ui-monospace,
    SFMono-Regular,
    Menlo,
    Consolas,
    monospace;
}

.ide-toolbar {
  justify-content: flex-end;
  gap: 0.4rem;
}

.ide-tool-group {
  gap: 0.2rem;
}

.ide-icon-button {
  display: grid;
  width: 2.1rem;
  height: 2.1rem;
  flex: 0 0 2.1rem;
  place-items: center;
  border: 1px solid transparent;
  border-radius: 0.375rem;
  color: #4b5d69;
  background: transparent;
  transition:
    border-color 0.16s ease,
    background 0.16s ease,
    color 0.16s ease;
}

.ide-icon-button:hover {
  border-color: #aebbc4;
  background: #f8fafb;
  color: #087c93;
}

.ide-icon-button svg,
.ide-language-button svg,
.ide-run-button svg {
  width: 1.05rem;
  height: 1.05rem;
}

.ide-language-control {
  position: relative;
  flex-shrink: 0;
}

.ide-language-button {
  display: flex;
  width: 8.8rem;
  height: 2.1rem;
  min-width: 0;
  align-items: center;
  gap: 0.45rem;
  border: 1px solid #b8c4cc;
  border-radius: 0.375rem;
  background: #f8fafb;
  padding: 0 0.55rem;
  color: #283944;
  font-size: 0.75rem;
  font-weight: 700;
}

.ide-language-button > span {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.language-chevron {
  flex-shrink: 0;
  transition: transform 0.16s ease;
}

.ide-language-menu {
  position: absolute;
  z-index: 60;
  top: calc(100% + 0.35rem);
  right: 0;
  width: 13rem;
  border: 1px solid #aebbc4;
  border-radius: 0.5rem;
  background: #f8fafb;
  padding: 0.3rem;
  box-shadow: 0 14px 28px rgba(31, 41, 55, 0.16);
}

.ide-language-option {
  display: flex;
  width: 100%;
  min-height: 2.25rem;
  align-items: center;
  gap: 0.55rem;
  border-radius: 0.3rem;
  padding: 0.35rem 0.55rem;
  color: #31434f;
  font-size: 0.75rem;
  font-weight: 700;
  text-align: left;
}

.ide-language-option:hover {
  background: #e7edf1;
}

.ide-language-option svg {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.language-current-dot {
  width: 0.4rem;
  height: 0.4rem;
  margin-left: auto;
  border-radius: 50%;
  background: #0891b2;
}

.ide-run-button {
  display: inline-flex;
  min-width: 7.3rem;
  height: 2.1rem;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  border: 1px solid #0e7490;
  border-radius: 0.375rem;
  background: #0e7490;
  padding: 0 0.8rem;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 800;
  transition:
    background 0.16s ease,
    border-color 0.16s ease;
}

.ide-run-button:hover:not(:disabled) {
  border-color: #0891b2;
  background: #0891b2;
}

.ide-run-button:disabled {
  cursor: wait;
  opacity: 0.68;
}

.ide-filebar {
  display: flex;
  min-height: 2.65rem;
  flex-shrink: 0;
  align-items: stretch;
  justify-content: space-between;
  border-bottom: 1px solid #bcc7ce;
  background: #dde4e8;
}

.ide-file-tab {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 0.5rem;
  border-right: 1px solid #b5c0c8;
  border-top: 2px solid #0891b2;
  background: #f7f9fa;
  padding: 0 0.7rem;
}

.ide-file-tab > svg {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: #087c93;
}

.file-section-title {
  flex-shrink: 0;
  font-size: 0.72rem;
  font-weight: 800;
}

.file-name-control {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 0.2rem;
  color: #697a86;
  font-size: 0.65rem;
}

.file-name-control input {
  width: 7rem;
  min-width: 3rem;
  border: 0;
  border-bottom: 1px solid transparent;
  background: transparent;
  padding: 0.2rem 0.1rem;
  color: #23343f;
  font:
    600 0.72rem/1.2 ui-monospace,
    SFMono-Regular,
    Menlo,
    Consolas,
    monospace;
  outline: none;
}

.file-name-control input:focus {
  border-bottom-color: #0891b2;
}

.file-save-preview {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 0.4rem;
  padding: 0 0.75rem;
  color: #6c7c87;
  font-size: 0.65rem;
}

.file-save-preview span:last-child {
  overflow: hidden;
  color: #324550;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ide-workspace {
  display: grid;
  min-width: 0;
  min-height: 0;
  flex: 1;
  grid-template-columns:
    minmax(0, calc(var(--editor-pane-percent) - 3px))
    6px minmax(0, 1fr);
  overflow: hidden;
  background: #f4f6f7;
}

.ide-editor-pane,
.ide-utility-pane,
.ide-tab-content,
.ide-tab-panel {
  min-width: 0;
  min-height: 0;
}

.ide-editor-pane {
  overflow: hidden;
  border-right: 1px solid #aebac2;
}

.ide-splitter {
  position: relative;
  z-index: 3;
  display: grid;
  cursor: col-resize;
  place-items: center;
  background: #d8e0e4;
  touch-action: none;
}

.ide-splitter::before {
  content: "";
  position: absolute;
  inset: 0 -3px;
}

.ide-splitter span {
  width: 1px;
  height: 2.25rem;
  background: #7e909c;
  transition:
    width 0.16s ease,
    background 0.16s ease;
}

.ide-splitter:hover span,
.ide-splitter:focus-visible span,
.ide-workspace.is-resizing .ide-splitter span {
  width: 2px;
  background: #0891b2;
}

.ide-utility-pane {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f7f9fa;
}

.ide-tabs {
  display: grid;
  min-height: 2.65rem;
  flex-shrink: 0;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-bottom: 1px solid #bec8cf;
  background: #e8edef;
}

.ide-tabs button {
  position: relative;
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  border-right: 1px solid #c5cdd3;
  color: #60717d;
  font-size: 0.7rem;
  font-weight: 700;
}

.ide-tabs button:last-child {
  border-right: 0;
}

.ide-tabs button::after {
  content: "";
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 2px;
  background: #0891b2;
  transform: scaleX(0);
  transition: transform 0.16s ease;
}

.ide-tabs button.active {
  background: #f7f9fa;
  color: #17212b;
}

.ide-tabs button.active::after {
  transform: scaleX(1);
}

.ide-tabs svg {
  width: 0.95rem;
  height: 0.95rem;
  flex-shrink: 0;
}

.execution-dot {
  width: 0.4rem;
  height: 0.4rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: #94a3b8;
}

.execution-dot.running {
  background: #d4a72c;
  animation: execution-pulse 0.9s ease-in-out infinite alternate;
}

.execution-dot.success {
  background: #16a34a;
}

.execution-dot.error {
  background: #dc2626;
}

.ide-tab-content {
  position: relative;
  flex: 1;
  overflow: hidden;
}

.ide-tab-panel {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  overflow: hidden;
}

.ide-textarea {
  width: 100%;
  height: 100%;
  min-height: 0;
  resize: none;
  border: 0;
  background: #f7f9fa;
  padding: 1rem;
  color: #1f303b;
  font:
    0.78rem/1.6 ui-monospace,
    SFMono-Regular,
    Menlo,
    Consolas,
    monospace;
  outline: none;
  tab-size: 2;
}

.ide-textarea::placeholder {
  color: #85949e;
}

.ide-textarea:focus {
  box-shadow: inset 2px 0 #0891b2;
}

.ide-output {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #f7f9fa;
  padding: 1rem;
  color: #15803d;
  font:
    0.78rem/1.6 ui-monospace,
    SFMono-Regular,
    Menlo,
    Consolas,
    monospace;
}

.ide-output pre {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.ide-output.is-error {
  color: #be123c;
}

.placeholder-copy {
  color: #778792;
  font-size: 0.75rem;
  font-style: italic;
}

.ide-output-status {
  display: flex;
  min-height: 2.5rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  border-top: 1px solid #c3ccd2;
  background: #edf1f3;
  padding: 0.45rem 0.75rem;
  font-size: 0.72rem;
  font-weight: 700;
}

.test-badge {
  border-radius: 0.25rem;
}

.ide-fullscreen {
  position: fixed;
  z-index: 9999;
  inset: 0;
  width: 100vw;
  height: 100dvh;
  border: 0;
  border-radius: 0;
}

.ide-fullscreen .fullscreen-menu {
  position: absolute;
  z-index: 70;
  top: 3.5rem;
  right: 0.6rem;
  width: 15rem;
  max-height: calc(100dvh - 4.5rem);
  overflow: auto;
  border: 1px solid #aebbc4;
  border-radius: 0.5rem;
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.2);
}

html.dark .ide-page {
  background: #101418;
  color: #e4e9ed;
}

html.dark .ide-workbench,
html.dark .ide-utility-pane,
html.dark .ide-tab-panel,
html.dark .ide-textarea,
html.dark .ide-output {
  border-color: #36414a;
  background: #151b20;
  color: #dce4e9;
}

html.dark .ide-topbar {
  border-color: #35414a;
  background: #1b2228;
}

html.dark .ide-title-copy p,
html.dark .file-name-control,
html.dark .file-save-preview,
html.dark .placeholder-copy {
  color: #8e9ca6;
}

html.dark .ide-icon-button {
  color: #b5c0c8;
}

html.dark .ide-icon-button:hover {
  border-color: #4a5964;
  background: #242d34;
  color: #67e8f9;
}

html.dark .ide-language-button,
html.dark .ide-language-menu {
  border-color: #45525c;
  background: #20282e;
  color: #dbe3e8;
}

html.dark .ide-language-option {
  color: #d0d9df;
}

html.dark .ide-language-option:hover {
  background: #2b353d;
}

html.dark .ide-filebar,
html.dark .ide-tabs {
  border-color: #39454e;
  background: #1d252b;
}

html.dark .ide-file-tab,
html.dark .ide-tabs button.active {
  border-color: #45515a;
  background: #151b20;
}

html.dark .file-name-control input,
html.dark .file-save-preview span:last-child {
  color: #dce4e9;
}

html.dark .ide-workspace {
  background: #12171b;
}

html.dark .ide-editor-pane {
  border-color: #3b4750;
}

html.dark .ide-splitter {
  background: #283137;
}

html.dark .ide-tabs button {
  border-color: #38444d;
  color: #96a5af;
}

html.dark .ide-tabs button.active {
  color: #f3f7f9;
}

html.dark .ide-textarea::placeholder {
  color: #65747e;
}

html.dark .ide-output {
  color: #86efac;
}

html.dark .ide-output.is-error {
  color: #fda4af;
}

html.dark .ide-output-status {
  border-color: #3c4851;
  background: #1b2329;
}

@media (max-width: 1023px) {
  .ide-page {
    padding: 0;
  }

  .ide-workbench {
    border-inline: 0;
    border-bottom: 0;
    border-radius: 0;
  }

  .ide-topbar {
    flex-wrap: wrap;
  }

  .ide-title-group {
    flex: 1 1 auto;
  }

  .ide-toolbar {
    flex: 1 1 auto;
  }

  .ide-workspace {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: minmax(0, 1.15fr) minmax(12rem, 0.85fr);
  }

  .ide-splitter {
    display: none;
  }

  .ide-editor-pane {
    border-right: 0;
    border-bottom: 1px solid #aebac2;
  }
}

@media (max-width: 640px) {
  .ide-topbar {
    gap: 0.4rem;
    padding: 0.4rem;
  }

  .ide-title-group {
    flex-basis: 100%;
  }

  .ide-toolbar {
    width: 100%;
    flex-wrap: nowrap;
    gap: 0.2rem;
  }

  .ide-language-button {
    width: 5.9rem;
    padding-inline: 0.35rem;
  }

  .ide-tool-group {
    gap: 0;
  }

  .ide-icon-button {
    width: 1.9rem;
    height: 1.9rem;
    flex-basis: 1.9rem;
  }

  .ide-run-button {
    min-width: 5.7rem;
    height: 1.9rem;
    padding-inline: 0.35rem;
  }

  .ide-filebar {
    min-height: 4.6rem;
    flex-wrap: wrap;
  }

  .ide-file-tab,
  .file-save-preview {
    width: 100%;
    min-height: 2.3rem;
  }

  .file-save-preview {
    border-top: 1px solid #c3ccd2;
  }

  .file-section-title {
    display: none;
  }

  .file-name-control {
    flex: 1;
  }

  .file-name-control input {
    width: 100%;
  }

  .ide-tabs button {
    gap: 0.2rem;
    font-size: 0.64rem;
  }

  .ide-tabs svg {
    width: 0.8rem;
    height: 0.8rem;
  }

  .execution-dot {
    width: 0.32rem;
    height: 0.32rem;
  }

  .ide-textarea,
  .ide-output {
    padding: 0.75rem;
    font-size: 0.72rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ide-icon-button,
  .ide-run-button,
  .language-chevron,
  .ide-splitter span,
  .ide-tabs button::after {
    transition-duration: 0.01ms !important;
  }

  .execution-dot.running {
    animation: none;
  }
}

@keyframes execution-pulse {
  to {
    opacity: 0.45;
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
