<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
// 按需引入 Monaco（性能优化）：只加载编辑器核心 + 本项目用到的 c/cpp/python/java
// 语法高亮，不再引入完整的 monaco-editor（含 typescript/json/css/html 语言服务，
// 体积约 3.7MB）。这些语言服务本题库用不到，统一走基础 editor.worker。
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
import "monaco-editor/esm/vs/editor/editor.all";
import "monaco-editor/esm/vs/basic-languages/cpp/cpp.contribution";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";
import "monaco-editor/esm/vs/basic-languages/java/java.contribution";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    language: string;
    isDark: boolean;
    height?: string | number;
  }>(),
  {
    height: "100%",
  },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
  (e: "ready", editor: monaco.editor.IStandaloneCodeEditor): void;
}>();

const containerRef = ref<HTMLElement | null>(null);
let editor: monaco.editor.IStandaloneCodeEditor | null = null;
let preventUpdate = false;

const setupMonacoEnvironment = () => {
  if (typeof window !== "undefined" && !("MonacoEnvironment" in window)) {
    (window as any).MonacoEnvironment = {
      // 只使用基础编辑器 worker（c/cpp/python/java 无需独立语言服务 worker）
      getWorker() {
        return new EditorWorker();
      },
    };
  }
};

const initEditor = () => {
  if (!containerRef.value || editor) return;

  setupMonacoEnvironment();

  editor = monaco.editor.create(containerRef.value, {
    value: props.modelValue,
    language: props.language,
    theme: props.isDark ? "vs-dark" : "vs",
    fontSize: 14,
    fontFamily:
      '"Cascadia Code", "Fira Code", "JetBrains Mono", Consolas, monospace',
    fontLigatures: true,
    lineHeight: 1.75,
    lineNumbersMinChars: 3,
    tabSize: 2,
    insertSpaces: true,
    wordWrap: "on",
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    automaticLayout: true,
    suggestOnTriggerCharacters: true,
    quickSuggestions: true,
    tabCompletion: "on",
    bracketPairColorization: { enabled: true },
    matchBrackets: "always",
    autoClosingBrackets: "always",
    autoClosingQuotes: "always",
    autoIndent: "full",
    formatOnPaste: true,
    renderLineHighlight: "line",
    renderWhitespace: "selection",
    cursorStyle: "line",
    cursorWidth: 2,
    cursorBlinking: "smooth",
    selectionHighlight: true,
    occurrencesHighlight: "singleFile",
    overviewRulerBorder: false,
    smoothScrolling: true,
    padding: { top: 20, bottom: 20 },
  });

  editor.onDidChangeModelContent(() => {
    if (preventUpdate) return;
    const value = editor!.getValue();
    emit("update:modelValue", value);
  });

  emit("ready", editor);
};

watch(
  () => props.modelValue,
  (newVal) => {
    if (!editor || preventUpdate) return;
    const current = editor.getValue();
    if (newVal !== current) {
      preventUpdate = true;
      editor.setValue(newVal);
      queueMicrotask(() => {
        preventUpdate = false;
      });
    }
  },
);

watch(
  () => props.language,
  (lang) => {
    if (!editor) return;
    const model = editor.getModel();
    if (model) {
      monaco.editor.setModelLanguage(model, lang);
    }
  },
);

watch(
  () => props.isDark,
  (dark) => {
    if (editor) {
      monaco.editor.setTheme(dark ? "vs-dark" : "vs");
    }
  },
);

onMounted(() => {
  initEditor();
});

onUnmounted(() => {
  if (editor) {
    editor.dispose();
    editor = null;
  }
});
</script>

<template>
  <div
    ref="containerRef"
    class="monaco-editor-container"
    :style="{ height: typeof height === 'number' ? `${height}px` : height }"
  ></div>
</template>

<style scoped>
.monaco-editor-container {
  width: 100%;
  min-height: 200px;
  overflow: hidden;
}
</style>
