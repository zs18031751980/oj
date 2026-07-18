<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import * as monaco from "monaco-editor";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import TsWorker from "monaco-editor/esm/vs/language/typescript/ts.worker?worker";
import JsonWorker from "monaco-editor/esm/vs/language/json/json.worker?worker";
import CssWorker from "monaco-editor/esm/vs/language/css/css.worker?worker";
import HtmlWorker from "monaco-editor/esm/vs/language/html/html.worker?worker";

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
      getWorker(_: string, label: string) {
        switch (label) {
          case "json":
            return new JsonWorker();
          case "css":
          case "scss":
          case "less":
            return new CssWorker();
          case "html":
          case "handlebars":
          case "razor":
            return new HtmlWorker();
          case "typescript":
          case "javascript":
            return new TsWorker();
          default:
            return new EditorWorker();
        }
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
