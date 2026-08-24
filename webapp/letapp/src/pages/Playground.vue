<script setup lang="ts">
import {
  computed, defineAsyncComponent, markRaw, onMounted, onUnmounted, ref, watch,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiRequest, getContestProblem, type ContestProblemData } from "../services/api";
import { useAuthStore } from "../stores/auth";
import { useThemeStore } from "../stores/theme";

const MarkdownComponent = defineAsyncComponent(
  () => import("../components/MarkdownComponent.vue"),
);

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

interface ProblemOption {
  id: number;
  title: string;
  difficulty: string;
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
  { name: "JavaScript", value: "javascript", prism: "javascript", icon: "vscode-icons:file-type-js-official", color: "#f7df1e" },
  { name: "Python", value: "python", prism: "python", icon: "vscode-icons:file-type-python", color: "#3776ab" },
  { name: "Java", value: "java", prism: "java", icon: "vscode-icons:file-type-java", color: "#ed8b00" },
  { name: "C++", value: "cpp", prism: "cpp", icon: "vscode-icons:file-type-cpp", color: "#00599c" },
  { name: "Go", value: "go", prism: "go", icon: "vscode-icons:file-type-go", color: "#00add8" },
  { name: "Rust", value: "rust", prism: "rust", icon: "vscode-icons:file-type-rust", color: "#dea584" },
]);

const defaultLanguage = languages.find((lang) => lang.value === "cpp")!;
const extensionMap: Record<string, string> = markRaw({
  javascript: "js", python: "py", java: "java", cpp: "cpp", go: "go", rust: "rs",
});

const getLanguagePreset = (language: string) => languagePresets[language] ?? "";
const selectedLanguage = ref<string>(defaultLanguage.value);
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

// Contest problem state
const contestProblem = ref<ContestProblemData | null>(null);
const contestId = ref<number | null>(null);
const problemId = ref<number | null>(null);

// Problem selector
const showProblemSelector = ref(false);
const problemList = ref<ProblemOption[]>([]);
const problemListLoading = ref(false);

// Panel state
const activeLeftTab = ref<"problem" | "submissions" | "hints">("problem");
const activeBottomTab = ref<"testcase" | "result" | "submit">("testcase");
const isFullscreen = ref(false);

function toggleFullscreen() {
  if (isFullscreen.value) {
    isFullscreen.value = false;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    }
  } else {
    isFullscreen.value = true;
    document.documentElement.requestFullscreen().catch(() => {});
  }
}
const onFullscreenChange = () => {
  if (!document.fullscreenElement) {
    isFullscreen.value = false;
  }
};
const showLeftPanel = ref(true);
const bottomPanelHeight = ref(240);
const isDraggingBottom = ref(false);
const editorPercent = ref(66);
const isDraggingEditor = ref(false);

// Auto-save state
const saveStatus = ref<"saved" | "saving" | "error">("saved");

const currentLanguageInfo = computed<LanguageOption>(
  () => languages.find((lang) => lang.value === selectedLanguage.value) ?? defaultLanguage,
);

const executionVisualState = computed<"idle" | "running" | "success" | "error">(() => {
  if (isExecuting.value) return "running";
  if (outputKind.value === "error" && output.value) return "error";
  if (executionStatus.value || output.value) return "success";
  return "idle";
});

const exportExtension = computed(() => extensionMap[selectedLanguage.value] ?? "txt");

const runCode = async () => {
  activeBottomTab.value = "result";
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
    const endpoint = authStore.isAuthenticated ? "/code/run" : "/code/run/public";
    const result = await apiRequest<ExecutionResponse>(endpoint, {
      method: "POST",
      skipAuth: !authStore.isAuthenticated,
      body: JSON.stringify({ code: source, language: selectedLanguage.value, stdin: stdin.value }),
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
      executionStatus.value = output.value ? "执行成功" : "程序已运行，但没有产生输出。";
    }
    if (expectedOutput.value.trim()) {
      const compareText = stdoutText || messageText;
      testVerdict.value = compareText.trim() === expectedOutput.value.trim() ? "pass" : "failed";
    }
  } catch (error) {
    outputKind.value = "error";
    output.value = `执行错误: ${error instanceof Error ? error.message : "未知错误"}`;
  } finally {
    isExecuting.value = false;
  }
};

const updateLanguage = (language: string) => {
  languageCodeMap.value[selectedLanguage.value] = code.value;
  selectedLanguage.value = language;
  isLanguageMenuOpen.value = false;
  code.value = languageCodeMap.value[language] ?? getLanguagePreset(language);
};

const resetCode = () => {
  delete languageCodeMap.value[selectedLanguage.value];
  code.value = getLanguagePreset(selectedLanguage.value);
  stdin.value = "";
  output.value = "";
  outputKind.value = "info";
};

// Export code as file
const exportCode = () => {
  const blob = new Blob([code.value], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `main.${exportExtension.value}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// Bottom panel resize
const startDragBottom = (e: PointerEvent) => {
  e.preventDefault();
  isDraggingBottom.value = true;
  const startY = e.clientY;
  const startH = bottomPanelHeight.value;
  const onMove = (ev: PointerEvent) => {
    const delta = startY - ev.clientY;
    bottomPanelHeight.value = Math.min(Math.max(160, startH + delta), window.innerHeight * 0.55);
  };
  const onUp = () => {
    isDraggingBottom.value = false;
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
  };
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
};

// Editor panel resize
const startDragEditor = (e: PointerEvent) => {
  e.preventDefault();
  isDraggingEditor.value = true;
  const startX = e.clientX;
  const workspace = (e.target as HTMLElement).parentElement;
  if (!workspace) return;
  const wWidth = workspace.getBoundingClientRect().width;
  const startPct = editorPercent.value;
  const onMove = (ev: PointerEvent) => {
    const delta = ev.clientX - startX;
    const pct = startPct + (delta / wWidth) * 100;
    editorPercent.value = Math.min(75, Math.max(30, pct));
  };
  const onUp = () => {
    isDraggingEditor.value = false;
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
  };
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
};

const handleGlobalShortcut = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && !isExecuting.value) {
    event.preventDefault();
    void runCode();
  }
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === "Enter" && !isExecuting.value) {
    event.preventDefault();
    void runCode();
  }
};

const closeLanguageMenuOnOutsideClick = (event: MouseEvent) => {
  const target = event.target as Node | null;
  if (languageMenuRef.value && target && !languageMenuRef.value.contains(target)) {
    isLanguageMenuOpen.value = false;
  }
};

const handleMonacoReady = (editor: any) => {
  editor.addAction({
    id: "run-code",
    label: "Run Code",
    keybindings: [2048 | 3],
    run: () => { if (!isExecuting.value) void runCode(); },
  });
};

const loadContestProblem = async () => {
  const cid = route.query.contest ? Number(route.query.contest) : null;
  const pid = route.query.problem ? Number(route.query.problem) : null;
  if (!cid || !pid) return;
  contestId.value = cid;
  problemId.value = pid;
  try {
    const data = await getContestProblem(pid);
    contestProblem.value = data;
  } catch {
    // silently fail
  }
};

// Open problem selector and load problem list
const openProblemSelector = async () => {
  showProblemSelector.value = true;
  if (problemList.value.length > 0) return;
  problemListLoading.value = true;
  try {
    const res = await apiRequest<{ data: any[]; total: number }>("/problems", { skipAuth: true });
    problemList.value = (res.data || []).map((p: any) => ({
      id: p.id,
      title: p.title,
      difficulty: p.difficulty || "简单",
    }));
  } catch {
    problemList.value = [];
  } finally {
    problemListLoading.value = false;
  }
};

const selectProblemFromList = (p: ProblemOption) => {
  problemId.value = p.id;
  // Load as contest problem fallback — for now show basic info
  contestProblem.value = {
    id: p.id,
    contest_id: 0,
    problem_index: `P${p.id}`,
    title: p.title,
    description: "",
    input_desc: "",
    output_desc: "",
    correct_answer: "",
    time_limit: 1000,
    memory_limit: 256,
    difficulty: p.difficulty,
    testcase_count: 0,
  };
  showProblemSelector.value = false;
  activeLeftTab.value = "problem";
};

const closeProblemSelector = () => {
  showProblemSelector.value = false;
};

const difficultyClass = (d: string) =>
  d === "简单" ? "diff-easy" : d === "中等" ? "diff-mid" : "diff-hard";

onMounted(() => {
  const languageParam = route.query.language as string | undefined;
  if (languageParam && languages.some((lang) => lang.value === languageParam)) {
    selectedLanguage.value = languageParam;
    code.value = getLanguagePreset(languageParam) || code.value;
  }
  void loadContestProblem();
  window.addEventListener("keydown", handleGlobalShortcut);
  window.addEventListener("click", closeLanguageMenuOnOutsideClick);
  document.addEventListener("fullscreenchange", onFullscreenChange);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleGlobalShortcut);
  window.removeEventListener("click", closeLanguageMenuOnOutsideClick);
  document.removeEventListener("fullscreenchange", onFullscreenChange);
});

watch(selectedLanguage, (lang) => {
  localStorage.setItem("playground_language", lang);
  saveStatus.value = "saved";
});
</script>

<template>
  <div class="ide-page">
    <section class="ide-workbench" :class="{ 'ide-fullscreen': isFullscreen }">

      <!-- ===== 顶部状态栏 ===== -->
      <header class="ide-topbar">
        <div class="ide-topbar-left">
          <button class="ide-icon-btn" title="返回" @click="router.back()">←</button>
          <template v-if="contestProblem">
            <div class="ide-problem-info">
              <span class="ide-problem-id">{{ contestProblem.problem_index }}</span>
              <span class="ide-problem-name">{{ contestProblem.title }}</span>
            </div>
          </template>
          <template v-else>
            <span class="ide-topbar-title">在线代码编辑器</span>
          </template>
        </div>
        <div class="ide-topbar-center">
          <span class="ide-save-status" :class="saveStatus">
            {{ saveStatus === 'saved' ? '✓ 已保存' : saveStatus === 'saving' ? '⟳ 保存中...' : '✗ 保存失败' }}
          </span>
        </div>
        <div class="ide-topbar-right">
          <button class="ide-icon-btn" :title="showLeftPanel ? '收起题目面板' : '展开题目面板'" @click="showLeftPanel = !showLeftPanel">
            <svg v-if="showLeftPanel" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
          </button>
          <button class="ide-icon-btn" title="全屏" @click="toggleFullscreen">
            <svg v-if="!isFullscreen" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
          </button>
        </div>
      </header>

      <!-- ===== 主工作区 ===== -->
      <div class="ide-workspace">
        <!-- 左侧题目面板 -->
        <div class="ide-left-panel" v-show="showLeftPanel">
          <!-- 无题目时：空状态 + 选择按钮 -->
          <div v-if="!contestProblem" class="ide-empty-state">
            <div class="ide-empty-icon">📝</div>
            <p class="ide-empty-title">尚未选择题目</p>
            <p class="ide-empty-desc">选择一道题目开始编码挑战</p>
            <button class="ide-select-btn" @click="openProblemSelector">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              选择题目
            </button>
          </div>

          <!-- 有题目时：题目内容 -->
          <template v-else>
            <div class="ide-panel-tabs">
              <button :class="{ active: activeLeftTab === 'problem' }" @click="activeLeftTab = 'problem'">📝 题目</button>
              <button :class="{ active: activeLeftTab === 'submissions' }" @click="activeLeftTab = 'submissions'">📊 提交记录</button>
              <button :class="{ active: activeLeftTab === 'hints' }" @click="activeLeftTab = 'hints'">💡 提示</button>
            </div>
            <div class="ide-panel-body">
              <div v-if="activeLeftTab === 'problem'" class="ide-problem-content">
                <div class="ide-problem-header">
                  <h2>{{ contestProblem.title }}</h2>
                  <div class="ide-problem-meta">
                    <span :class="difficultyClass(contestProblem.difficulty)">{{ contestProblem.difficulty }}</span>
                    <span>⏱ {{ contestProblem.time_limit }}ms</span>
                    <span>💾 {{ contestProblem.memory_limit }}MB</span>
                  </div>
                </div>
                <div v-if="contestProblem.description" class="ide-problem-desc">
                  <MarkdownComponent :content="{ content: contestProblem.description }" :show-nav="false" :show-heading-links="false" />
                </div>
                <div v-if="contestProblem.input_desc" class="mt-4">
                  <h3>输入格式</h3>
                  <div class="ide-sample"><pre>{{ contestProblem.input_desc }}</pre></div>
                </div>
                <div v-if="contestProblem.output_desc" class="mt-4">
                  <h3>输出格式</h3>
                  <div class="ide-sample"><pre>{{ contestProblem.output_desc }}</pre></div>
                </div>
                <div class="mt-4">
                  <button class="ide-change-problem-btn" @click="openProblemSelector">更换题目</button>
                </div>
              </div>
              <div v-else-if="activeLeftTab === 'submissions'" class="ide-submissions">
                <p class="ide-empty-hint">暂无提交记录</p>
              </div>
              <div v-else class="ide-hints">
                <div class="ide-hint-card">可以使用哈希表来优化查找过程</div>
                <div class="ide-hint-card">时间复杂度要求 O(n)</div>
              </div>
            </div>
          </template>
        </div>

        <!-- 可拖拽分割线 -->
        <div
          v-show="showLeftPanel && !!contestProblem"
          class="ide-vsplitter"
          :class="{ dragging: isDraggingEditor }"
          @pointerdown="startDragEditor"
        ></div>

        <!-- 右侧编辑器面板 -->
        <div class="ide-right-panel">
          <!-- 编辑器工具栏 -->
          <div class="ide-editor-toolbar">
            <div class="ide-editor-toolbar-left">
              <div ref="languageMenuRef" class="ide-lang-select">
                <button class="ide-lang-btn" @click="isLanguageMenuOpen = !isLanguageMenuOpen">
                  <span>{{ currentLanguageInfo.name }}</span>
                  <span class="ide-chevron" :class="{ open: isLanguageMenuOpen }">▾</span>
                </button>
                <div v-if="isLanguageMenuOpen" class="ide-lang-menu">
                  <button v-for="lang in languages" :key="lang.value" :class="{ selected: selectedLanguage === lang.value }" @click="updateLanguage(lang.value)">
                    {{ lang.name }}
                  </button>
                </div>
              </div>
              <span class="ide-file-name">main.{{ exportExtension }}</span>
            </div>
            <div class="ide-editor-toolbar-right">
              <button class="ide-icon-btn-sm" title="导出代码" @click="exportCode">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              </button>
              <button class="ide-icon-btn-sm" title="重置代码" @click="resetCode">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/></svg>
              </button>
            </div>
          </div>

          <!-- 代码编辑区 -->
          <div class="ide-editor-area">
            <MonacoEditor
              v-model="code"
              :language="selectedLanguage"
              :is-dark="themeStore.isDark"
              @ready="handleMonacoReady"
            />
          </div>

          <!-- 编辑器状态栏 -->
          <div class="ide-editor-statusbar">
            <span>{{ currentLanguageInfo.name }}</span>
            <span>UTF-8</span>
            <span>空格: 2</span>
          </div>
        </div>
      </div>

      <!-- ===== 可拖拽底部分割线 ===== -->
      <div class="ide-hsplitter" :class="{ dragging: isDraggingBottom }" @pointerdown="startDragBottom">
        <span></span>
      </div>

      <!-- ===== 底部结果区 ===== -->
      <div class="ide-bottom-panel" :style="{ height: bottomPanelHeight + 'px' }">
        <div class="ide-bottom-tabs">
          <button :class="{ active: activeBottomTab === 'testcase' }" @click="activeBottomTab = 'testcase'">测试用例</button>
          <button :class="{ active: activeBottomTab === 'result' }" @click="activeBottomTab = 'result'">
            <span class="exec-dot" :class="executionVisualState"></span>
            运行结果
          </button>
          <button :class="{ active: activeBottomTab === 'submit' }" @click="activeBottomTab = 'submit'">提交结果</button>
        </div>
        <div class="ide-bottom-content">
          <!-- 测试用例 Tab -->
          <div v-show="activeBottomTab === 'testcase'" class="ide-testcase-panel">
            <div class="ide-testcase-left">
              <div class="ide-testcase-header">
                <span>自定义输入</span>
                <button class="ide-text-btn" @click="stdin = ''">清空</button>
              </div>
              <textarea v-model="stdin" class="ide-io-textarea" placeholder="在此输入测试数据..."></textarea>
            </div>
            <div class="ide-testcase-right">
              <div class="ide-testcase-header">
                <span>标准输出</span>
                <button class="ide-text-btn" @click="expectedOutput = ''">清空</button>
              </div>
              <textarea v-model="expectedOutput" class="ide-io-textarea" placeholder="预期输出（选填）"></textarea>
            </div>
          </div>

          <!-- 运行结果 Tab -->
          <div v-show="activeBottomTab === 'result'" class="ide-result-panel">
            <div v-if="executionStatus" class="ide-result-status">
              <span :class="outputKind === 'error' ? 'text-red' : 'text-green'">{{ executionStatus }}</span>
              <span v-if="testVerdict" class="ide-verdict" :class="testVerdict">{{ testVerdict === 'pass' ? '✓ PASS' : '✗ FAILED' }}</span>
            </div>
            <div class="ide-result-output" :class="{ error: outputKind === 'error' }">
              <pre v-if="output">{{ output }}</pre>
              <div v-else class="ide-empty-hint">运行代码查看结果 · Ctrl + Enter</div>
            </div>
          </div>

          <!-- 提交结果 Tab -->
          <div v-show="activeBottomTab === 'submit'" class="ide-submit-panel">
            <div class="ide-empty-hint">提交代码后在此查看评测结果</div>
          </div>
        </div>
      </div>

      <!-- ===== 底部固定操作栏 ===== -->
      <footer class="ide-action-bar">
        <div class="ide-action-left">
          <span class="ide-save-status-sm" :class="saveStatus">{{ saveStatus === 'saved' ? '✓ 已保存' : '⟳ 保存中' }}</span>
          <span class="ide-shortcut-hint">Ctrl+Enter 运行</span>
        </div>
        <div class="ide-action-right">
          <button class="ide-btn-run" :disabled="isExecuting" @click="runCode">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            {{ isExecuting ? '运行中...' : '运行代码' }}
          </button>
          <button class="ide-btn-submit" :disabled="isExecuting">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            提交代码
          </button>
        </div>
      </footer>
    </section>

    <!-- ===== 题目选择弹窗 ===== -->
    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="showProblemSelector" class="ide-modal-overlay" @click.self="closeProblemSelector">
          <div class="ide-modal">
            <div class="ide-modal-header">
              <h3>选择题目</h3>
              <button class="ide-modal-close" @click="closeProblemSelector">✕</button>
            </div>
            <div class="ide-modal-body">
              <div v-if="problemListLoading" class="ide-modal-loading">
                <div class="ide-spinner"></div>
                <span>加载题目列表...</span>
              </div>
              <div v-else-if="problemList.length === 0" class="ide-modal-empty">
                <p>暂无可用题目</p>
              </div>
              <div v-else class="ide-problem-list">
                <button
                  v-for="p in problemList"
                  :key="p.id"
                  class="ide-problem-item"
                  @click="selectProblemFromList(p)"
                >
                  <span class="ide-problem-item-id">P{{ p.id }}</span>
                  <span class="ide-problem-item-title">{{ p.title }}</span>
                  <span class="ide-problem-item-diff" :class="difficultyClass(p.difficulty)">{{ p.difficulty }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.ide-page {
  height: calc(100dvh - var(--header-h, 4rem));
  min-height: 0;
  overflow: hidden;
  padding: 8px;
  background: #E8ECF0;
  color: #1E293B;
}
html.dark .ide-page { background: #0B1120; color: #E5E7EB; }

.ide-workbench {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  background: #F8FAFC;
}
html.dark .ide-workbench { border-color: #1E293B; background: #0F172A; }

.ide-fullscreen,
:fullscreen .ide-workbench { position: fixed; z-index: 9999; inset: 0; border: 0; border-radius: 0; }

/* ===== 顶部状态栏 ===== */
.ide-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  flex-shrink: 0;
  border-bottom: 1px solid #E2E8F0;
  background: #F1F5F9;
  padding: 0 12px;
}
html.dark .ide-topbar { border-color: #1E293B; background: #1E293B; }

.ide-topbar-left { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1; }
.ide-topbar-center { display: flex; align-items: center; justify-content: center; }
.ide-topbar-right { display: flex; align-items: center; gap: 4px; }

.ide-topbar-title { font-size: 14px; font-weight: 700; color: #475569; }
html.dark .ide-topbar-title { color: #CBD5E1; }

.ide-problem-info { display: flex; flex-direction: column; min-width: 0; }
.ide-problem-id { font-size: 11px; color: #94A3B8; font-weight: 600; }
.ide-problem-name { font-size: 14px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 280px; }

.ide-save-status { font-size: 12px; font-weight: 600; }
.ide-save-status.saved { color: #6B7280; }
.ide-save-status.saving { color: #3B82F6; }
.ide-save-status.error { color: #EF4444; }

.ide-icon-btn {
  display: grid; place-items: center;
  width: 32px; height: 32px;
  border: none; border-radius: 6px;
  background: transparent; color: #6B7280;
  cursor: pointer; font-size: 16px;
  transition: background 0.15s;
}
.ide-icon-btn:hover { background: #E0E7FF; color: #2563EB; }
html.dark .ide-icon-btn:hover { background: #1E3A5F; }

/* ===== 主工作区 ===== */
.ide-workspace {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 左侧面板 */
.ide-left-panel {
  display: flex;
  flex-direction: column;
  width: 34%;
  min-width: 320px;
  max-width: 48%;
  border-right: 1px solid #E2E8F0;
  background: #FFFFFF;
}
html.dark .ide-left-panel { border-color: #1E293B; background: #111827; }

/* 空状态 */
.ide-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 32px;
  text-align: center;
}
.ide-empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.6; }
.ide-empty-title { font-size: 18px; font-weight: 700; color: #1E293B; margin-bottom: 8px; }
html.dark .ide-empty-title { color: #E5E7EB; }
.ide-empty-desc { font-size: 13px; color: #94A3B8; margin-bottom: 20px; }
.ide-select-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: #2563EB;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.ide-select-btn:hover { background: #1D4ED8; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37,99,235,0.3); }

.ide-panel-tabs {
  display: flex;
  height: 44px;
  flex-shrink: 0;
  border-bottom: 1px solid #E2E8F0;
  background: #F8FAFC;
}
html.dark .ide-panel-tabs { border-color: #1E293B; background: #1F2937; }

.ide-panel-tabs button {
  flex: 1;
  display: flex; align-items: center; justify-content: center; gap: 4px;
  border: none; border-bottom: 2px solid transparent;
  background: transparent;
  color: #6B7280; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.15s;
}
.ide-panel-tabs button.active {
  color: #2563EB; border-bottom-color: #2563EB;
  background: #FFFFFF;
}
html.dark .ide-panel-tabs button.active { background: #111827; }

.ide-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.ide-problem-header { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #F1F5F9; }
.ide-problem-header h2 { font-size: 20px; font-weight: 800; margin: 0 0 8px; }
.ide-problem-meta { display: flex; gap: 12px; font-size: 13px; color: #6B7280; }
.diff-easy { background: #D1FAE5; color: #059669; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }
.diff-mid { background: #FEF3C7; color: #D97706; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }
.diff-hard { background: #FEE2E2; color: #DC2626; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }

.ide-problem-desc { font-size: 14px; line-height: 1.75; color: #374151; }
html.dark .ide-problem-desc { color: #D1D5DB; }
.ide-problem-desc h3 { font-size: 16px; font-weight: 700; margin: 20px 0 8px; color: #1E293B; }
html.dark .ide-problem-desc h3 { color: #F3F4F6; }
.ide-problem-desc code { background: #F1F5F9; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.ide-problem-desc p { margin: 0 0 12px; }

.ide-sample { margin: 8px 0; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden; }
.ide-sample pre {
  margin: 0; padding: 12px 16px;
  background: #F8FAFC; font-family: 'JetBrains Mono', monospace; font-size: 13px;
  overflow-x: auto;
}
html.dark .ide-sample pre { background: #1F2937; color: #E5E7EB; }

.ide-change-problem-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  background: #fff;
  color: #64748B;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.ide-change-problem-btn:hover { border-color: #2563EB; color: #2563EB; background: #EFF6FF; }
html.dark .ide-change-problem-btn { border-color: #374151; background: #1F2937; color: #94A3B8; }
html.dark .ide-change-problem-btn:hover { border-color: #60A5FA; color: #60A5FA; background: #172554; }

.ide-submissions, .ide-hints { padding: 20px; }
.ide-empty-hint { color: #9CA3AF; font-size: 13px; text-align: center; padding: 40px 0; }
.ide-hint-card {
  padding: 10px 14px; margin-bottom: 8px;
  background: #EFF6FF; border-radius: 6px;
  font-size: 13px; color: #1D4ED8; font-weight: 500;
}
html.dark .ide-hint-card { background: #1E3A5F; color: #93C5FD; }

/* 可拖拽垂直分割线 */
.ide-vsplitter {
  width: 6px;
  cursor: col-resize;
  background: #E5E7EB;
  position: relative;
  flex-shrink: 0;
  transition: background 0.15s;
}
.ide-vsplitter:hover, .ide-vsplitter.dragging { background: #2563EB; }
.ide-vsplitter::before {
  content: '';
  position: absolute;
  inset: 0 -3px;
}

/* 右侧编辑器面板 */
.ide-right-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.ide-editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  flex-shrink: 0;
  border-bottom: 1px solid #E2E8F0;
  background: #F9FAFB;
  padding: 0 12px;
}
html.dark .ide-editor-toolbar { border-color: #1E293B; background: #1F2937; }

.ide-editor-toolbar-left { display: flex; align-items: center; gap: 8px; }
.ide-editor-toolbar-right { display: flex; align-items: center; gap: 4px; }

.ide-lang-select { position: relative; }
.ide-lang-btn {
  display: flex; align-items: center; gap: 4px;
  height: 32px; padding: 0 12px;
  border: 1px solid #D1D5DB; border-radius: 6px;
  background: #FFFFFF; color: #374151;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
html.dark .ide-lang-btn { border-color: #374151; background: #1F2937; color: #E5E7EB; }
.ide-chevron { transition: transform 0.15s; }
.ide-chevron.open { transform: rotate(180deg); }

.ide-lang-menu {
  position: absolute; z-index: 50; top: calc(100% + 4px); left: 0;
  min-width: 180px; border: 1px solid #D1D5DB; border-radius: 8px;
  background: #FFFFFF; box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  padding: 4px;
}
html.dark .ide-lang-menu { border-color: #374151; background: #1F2937; }
.ide-lang-menu button {
  display: block; width: 100%; padding: 8px 12px;
  border: none; border-radius: 4px;
  background: transparent; color: #374151;
  font-size: 13px; font-weight: 500; text-align: left; cursor: pointer;
}
.ide-lang-menu button:hover { background: #F3F4F6; }
.ide-lang-menu button.selected { background: #EFF6FF; color: #2563EB; }

.ide-file-name { font-size: 13px; color: #6B7280; font-weight: 500; }

.ide-icon-btn-sm {
  display: grid; place-items: center;
  width: 30px; height: 30px;
  border: none; border-radius: 6px;
  background: transparent; color: #6B7280;
  cursor: pointer;
}
.ide-icon-btn-sm:hover { background: #F3F4F6; color: #2563EB; }
html.dark .ide-icon-btn-sm:hover { background: #1E3A5F; }

.ide-editor-area { flex: 1; min-height: 0; overflow: hidden; }

.ide-editor-statusbar {
  display: flex; align-items: center; gap: 16px;
  height: 26px; flex-shrink: 0;
  border-top: 1px solid #E2E8F0;
  background: #F9FAFB;
  padding: 0 12px;
  font-size: 11px; color: #9CA3AF;
}
html.dark .ide-editor-statusbar { border-color: #1E293B; background: #1F2937; }

/* ===== 底部可拖拽分割线 ===== */
.ide-hsplitter {
  height: 6px;
  cursor: row-resize;
  background: #E5E7EB;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: background 0.15s;
}
.ide-hsplitter:hover, .ide-hsplitter.dragging { background: #2563EB; }
.ide-hsplitter span { width: 24px; height: 2px; background: #9CA3AF; border-radius: 1px; }

/* ===== 底部结果区 ===== */
.ide-bottom-panel {
  display: flex;
  flex-direction: column;
  min-height: 160px;
  border-top: 1px solid #E2E8F0;
  background: #FFFFFF;
}
html.dark .ide-bottom-panel { border-color: #1E293B; background: #111827; }

.ide-bottom-tabs {
  display: flex;
  height: 40px;
  flex-shrink: 0;
  border-bottom: 1px solid #E2E8F0;
  background: #F9FAFB;
}
html.dark .ide-bottom-tabs { border-color: #1E293B; background: #1F2937; }

.ide-bottom-tabs button {
  display: flex; align-items: center; gap: 6px;
  padding: 0 16px;
  border: none; border-bottom: 2px solid transparent;
  background: transparent;
  color: #6B7280; font-size: 13px; font-weight: 600;
  cursor: pointer;
}
.ide-bottom-tabs button.active { color: #2563EB; border-bottom-color: #2563EB; }

.exec-dot { width: 6px; height: 6px; border-radius: 50%; background: #D1D5DB; }
.exec-dot.running { background: #F59E0B; animation: pulse 1s infinite; }
.exec-dot.success { background: #10B981; }
.exec-dot.error { background: #EF4444; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.ide-bottom-content { flex: 1; min-height: 0; overflow: hidden; }

.ide-testcase-panel { display: flex; height: 100%; gap: 16px; padding: 12px; }
.ide-testcase-left, .ide-testcase-right { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.ide-testcase-header {
  display: flex; align-items: center; justify-content: space-between;
  height: 32px; font-size: 12px; font-weight: 600; color: #6B7280;
}
.ide-text-btn {
  border: none; background: transparent; color: #6B7280;
  font-size: 12px; cursor: pointer;
}
.ide-text-btn:hover { color: #2563EB; }

.ide-io-textarea {
  flex: 1; resize: none; border: 1px solid #E5E7EB; border-radius: 6px;
  padding: 12px; font-family: 'JetBrains Mono', monospace; font-size: 13px;
  background: #F8FAFC; color: #1E293B; outline: none;
}
.ide-io-textarea:focus { border-color: #2563EB; }
html.dark .ide-io-textarea { border-color: #374151; background: #1F2937; color: #E5E7EB; }

.ide-result-panel { display: flex; flex-direction: column; height: 100%; }
.ide-result-status {
  display: flex; align-items: center; gap: 12px;
  height: 44px; padding: 0 16px;
  border-bottom: 1px solid #F1F5F9;
  font-size: 14px; font-weight: 700;
}
.text-green { color: #059669; }
.text-red { color: #DC2626; }
.ide-verdict { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.ide-verdict.pass { background: #D1FAE5; color: #059669; }
.ide-verdict.failed { background: #FEE2E2; color: #DC2626; }

.ide-result-output {
  flex: 1; overflow: auto; padding: 12px 16px;
  font-family: 'JetBrains Mono', monospace; font-size: 13px;
  color: #059669;
}
.ide-result-output.error { color: #DC2626; }
.ide-result-output pre { margin: 0; white-space: pre-wrap; }

.ide-submit-panel { display: flex; align-items: center; justify-content: center; height: 100%; }

/* ===== 底部操作栏 ===== */
.ide-action-bar {
  display: flex; align-items: center; justify-content: space-between;
  height: 56px; flex-shrink: 0;
  border-top: 1px solid #E2E8F0;
  background: #FFFFFF;
  padding: 0 16px;
}
html.dark .ide-action-bar { border-color: #1E293B; background: #111827; }

.ide-action-left { display: flex; align-items: center; gap: 12px; }
.ide-action-right { display: flex; align-items: center; gap: 10px; }

.ide-save-status-sm { font-size: 12px; font-weight: 600; color: #6B7280; }
.ide-save-status-sm.saved { color: #059669; }
.ide-shortcut-hint { font-size: 11px; color: #9CA3AF; }

.ide-btn-run {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  height: 40px; padding: 0 20px;
  border: 1px solid #2563EB; border-radius: 8px;
  background: #FFFFFF; color: #2563EB;
  font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all 0.15s;
}
.ide-btn-run:hover:not(:disabled) { background: #EFF6FF; }
.ide-btn-run:disabled { opacity: 0.5; cursor: not-allowed; }

.ide-btn-submit {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  height: 40px; padding: 0 20px;
  border: none; border-radius: 8px;
  background: #2563EB; color: #FFFFFF;
  font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all 0.15s;
}
.ide-btn-submit:hover:not(:disabled) { background: #1D4ED8; }
.ide-btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

/* ===== 题目选择弹窗 ===== */
.ide-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}
.ide-modal {
  width: 90%;
  max-width: 560px;
  max-height: 70vh;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
html.dark .ide-modal { background: #1F2937; }
.ide-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #E2E8F0;
}
html.dark .ide-modal-header { border-color: #374151; }
.ide-modal-header h3 { margin: 0; font-size: 16px; font-weight: 700; }
.ide-modal-close {
  width: 28px; height: 28px;
  display: grid; place-items: center;
  border: none; border-radius: 6px;
  background: transparent; color: #6B7280;
  cursor: pointer; font-size: 14px;
}
.ide-modal-close:hover { background: #F3F4F6; }
.ide-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.ide-modal-loading, .ide-modal-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #94A3B8;
  font-size: 14px;
  gap: 12px;
}
.ide-spinner {
  width: 24px; height: 24px;
  border: 3px solid #E5E7EB;
  border-top-color: #2563EB;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.ide-problem-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ide-problem-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 14px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s;
}
.ide-problem-item:hover {
  background: #EFF6FF;
  border-color: #BFDBFE;
}
html.dark .ide-problem-item:hover { background: #172554; border-color: #1E3A5F; }
.ide-problem-item-id { font-size: 12px; font-weight: 700; color: #94A3B8; min-width: 40px; }
.ide-problem-item-title { flex: 1; font-size: 14px; font-weight: 600; color: #1E293B; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
html.dark .ide-problem-item-title { color: #E5E7EB; }
.ide-problem-item-diff { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; flex-shrink: 0; }

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .ide-left-panel { display: none; }
  .ide-vsplitter { display: none; }
}
@media (max-width: 768px) {
  .ide-topbar { height: 44px; padding: 0 8px; }
  .ide-problem-name { display: none; }
  .ide-action-bar { height: 52px; padding: 0 8px; }
  .ide-btn-run, .ide-btn-submit { height: 36px; font-size: 12px; padding: 0 14px; }
}

/* ===== 弹窗过渡 ===== */
.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
