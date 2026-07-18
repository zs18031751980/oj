<script setup lang="ts">
import { computed, markRaw, onMounted, onUnmounted, ref } from "vue";
import { Icon } from "@iconify/vue";
import { useRouter } from "vue-router";

const router = useRouter();
const terminalRef = ref<HTMLElement | null>(null);
const terminalStyle = ref<Record<string, string>>({});
const currentLanguage = ref("cpp");
let perspectiveFrame = 0;

const languages = markRaw([
  {
    name: "JavaScript",
    value: "javascript",
    icon: "vscode-icons:file-type-js-official",
    color: "#f7df1e",
  },
  {
    name: "Python",
    value: "python",
    icon: "vscode-icons:file-type-python",
    color: "#3776ab",
  },
  {
    name: "Java",
    value: "java",
    icon: "vscode-icons:file-type-java",
    color: "#ed8b00",
  },
  {
    name: "C++",
    value: "cpp",
    icon: "vscode-icons:file-type-cpp",
    color: "#00599c",
  },
  {
    name: "Go",
    value: "go",
    icon: "vscode-icons:file-type-go",
    color: "#00add8",
  },
  {
    name: "Rust",
    value: "rust",
    icon: "vscode-icons:file-type-rust",
    color: "#dea584",
  },
  {
    name: "Swift",
    value: "swift",
    icon: "vscode-icons:file-type-swift",
    color: "#fa7343",
  },
  {
    name: "Kotlin",
    value: "kotlin",
    icon: "vscode-icons:file-type-kotlin",
    color: "#7f52ff",
  },
]);

const codeSamples: Record<string, string> = {
  cpp: `<span class="code-directive">#include</span> <span class="code-muted">&lt;iostream&gt;</span>\n\n<span class="code-type">int</span> <span class="code-function">main</span>() {\n  <span class="code-object">std::cout</span> <span class="code-muted">&lt;&lt;</span> <span class="code-string">"Hello, Let Coding!"</span> <span class="code-muted">&lt;&lt;</span> <span class="code-string">'\\n'</span>;\n  <span class="code-keyword">return</span> <span class="code-number">0</span>;\n}`,
  python: `<span class="code-keyword">print</span>(<span class="code-string">"Hello, Let Coding!"</span>)`,
  javascript: `<span class="code-object">console</span>.<span class="code-function">log</span>(<span class="code-string">"Hello, Let Coding!"</span>);`,
  java: `<span class="code-keyword">public</span> <span class="code-type">class</span> <span class="code-function">Main</span> {\n  <span class="code-keyword">public</span> <span class="code-type">static void</span> <span class="code-function">main</span>(<span class="code-object">String</span>[] args) {\n    <span class="code-object">System.out</span>.<span class="code-function">println</span>(<span class="code-string">"Hello, Let Coding!"</span>);\n  }\n}`,
  go: `<span class="code-keyword">package</span> <span class="code-function">main</span>\n<span class="code-keyword">import</span> <span class="code-string">"fmt"</span>\n\n<span class="code-type">func</span> <span class="code-function">main</span>() {\n  <span class="code-object">fmt</span>.<span class="code-function">Println</span>(<span class="code-string">"Hello, Let Coding!"</span>)\n}`,
  rust: `<span class="code-type">fn</span> <span class="code-function">main</span>() {\n  <span class="code-object">println!</span>(<span class="code-string">"Hello, Let Coding!"</span>);\n}`,
  swift: `<span class="code-keyword">print</span>(<span class="code-string">"Hello, Let Coding!"</span>)`,
  kotlin: `<span class="code-type">fun</span> <span class="code-function">main</span>() {\n  <span class="code-object">println</span>(<span class="code-string">"Hello, Let Coding!"</span>)\n}`,
};

const extMap: Record<string, string> = {
  cpp: "cpp",
  python: "py",
  javascript: "js",
  java: "java",
  go: "go",
  rust: "rs",
  swift: "swift",
  kotlin: "kt",
};

const currentCode = computed(
  () => codeSamples[currentLanguage.value] || codeSamples.cpp,
);
const currentFileExt = computed(
  () => extMap[currentLanguage.value] || extMap.cpp,
);

const selectLanguage = (lang: { value: string }) => {
  currentLanguage.value = lang.value;
};

const features = markRaw([
  {
    icon: "material-symbols:flash-on",
    title: "打开即写",
    description: "进入页面就能练代码，适合课堂演示、算法练习和快速验证想法。",
  },
  {
    icon: "material-symbols:terminal",
    title: "输出即时可见",
    description: "运行结果和报错集中展示，调试时不用反复切换窗口。",
  },
  {
    icon: "material-symbols:school",
    title: "学习资源联动",
    description: "从学习路径、推荐课程到编辑器练习，一条链路直接贯通。",
  },
  {
    icon: "material-symbols:quiz",
    title: "题库实战",
    description: "联系算法与数据结构题目，在线提交即时评测，持续挑战提升。",
  },
]);

const handlePointerMove = (event: PointerEvent) => {
  if (
    window.innerWidth < 1024 ||
    window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
    window.matchMedia("(hover: none), (pointer: coarse)").matches ||
    (navigator.hardwareConcurrency > 0 && navigator.hardwareConcurrency <= 4)
  )
    return;
  const element = terminalRef.value;
  if (!element) return;
  if (perspectiveFrame) cancelAnimationFrame(perspectiveFrame);
  perspectiveFrame = requestAnimationFrame(() => {
    const bounds = element.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width;
    const y = (event.clientY - bounds.top) / bounds.height;
    terminalStyle.value = {
      "--rotate-x": `${(0.5 - y) * 1.4}deg`,
      "--rotate-y": `${(x - 0.5) * 1.8}deg`,
    };
    perspectiveFrame = 0;
  });
};

const resetPerspective = () => {
  terminalStyle.value = {};
};

onMounted(() => {
  terminalRef.value?.addEventListener("pointermove", handlePointerMove);
  terminalRef.value?.addEventListener("pointerleave", resetPerspective);
});

onUnmounted(() => {
  if (perspectiveFrame) cancelAnimationFrame(perspectiveFrame);
  terminalRef.value?.removeEventListener("pointermove", handlePointerMove);
  terminalRef.value?.removeEventListener("pointerleave", resetPerspective);
});
</script>

<template>
  <main class="home-shell">
    <section class="hero-section">
      <div class="hero-grid" aria-hidden="true"></div>
      <div class="hero-layout">
        <div class="hero-copy">
          <span class="hero-label intro intro-label">
            <span class="status-dot"></span>
            Let Coding Online Judge
          </span>

          <h1 class="hero-title">
            <span class="title-line intro intro-title-one">让写代码</span>
            <span
              class="title-line title-accent intro intro-title-two"
              data-text="更直接、更顺手"
              >更直接、更顺手</span
            >
          </h1>

          <div class="hero-actions intro intro-actions">
            <button
              class="hero-button hero-primary"
              @click="router.push('/playground')"
            >
              <Icon icon="material-symbols:play-arrow" />
              <span>进入在线编辑器</span>
            </button>
            <button
              class="hero-button hero-secondary"
              @click="router.push('/learn')"
            >
              <Icon icon="material-symbols:school" />
              <span>查看学习资源</span>
            </button>
          </div>
        </div>

        <div
          ref="terminalRef"
          class="terminal-stage intro intro-terminal"
          :style="terminalStyle"
        >
          <div class="terminal-frame">
            <div class="terminal-toolbar">
              <div class="window-controls" aria-hidden="true">
                <span></span><span></span><span></span>
              </div>
              <div class="file-path">playground/main.{{ currentFileExt }}</div>
              <Icon
                icon="material-symbols:terminal-rounded"
                class="toolbar-icon"
              />
            </div>

            <div class="terminal-workspace">
              <section class="code-panel">
                <div class="panel-heading">
                  <span><Icon icon="material-symbols:code" />Sample Code</span>
                </div>
                <div class="editor-body">
                  <div class="line-numbers" aria-hidden="true">
                    <span v-for="line in 7" :key="line">{{ line }}</span>
                  </div>
                  <pre><code v-html="currentCode"></code></pre>
                  <div class="typing-mask" aria-hidden="true"></div>
                </div>
              </section>

              <aside class="terminal-side">
                <section class="result-panel">
                  <div class="panel-heading">
                    <span>运行结果</span>
                  </div>
                  <div class="judge-timeline">
                    <div class="judge-status status-compiling">
                      <span></span>Compiling
                    </div>
                    <div class="judge-status status-running">
                      <span></span>Running
                    </div>
                    <div class="judge-status status-accepted">
                      <Icon
                        icon="material-symbols:check-circle-rounded"
                      />Accepted
                    </div>
                  </div>
                  <div class="preview-output">Hello, Let Coding!</div>
                </section>

                <section class="language-panel">
                  <div class="panel-heading">
                    <span>支持语言</span>
                  </div>
                  <div class="language-grid">
                    <button
                      v-for="(language, index) in languages"
                      :key="language.value"
                      type="button"
                      class="language-button"
                      :class="{ active: currentLanguage === language.value }"
                      :style="{
                        '--language-color': language.color,
                        '--language-delay': `${2.35 + index * 0.08}s`,
                      }"
                      :aria-label="language.name"
                      @click="selectLanguage(language)"
                    >
                      <Icon :icon="language.icon" />
                    </button>
                  </div>
                </section>
              </aside>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section v-once class="feature-section">
      <div class="feature-grid">
        <article
          v-for="feature in features"
          :key="feature.title"
          class="feature-card"
        >
          <div class="feature-icon"><Icon :icon="feature.icon" /></div>
          <h2>{{ feature.title }}</h2>
          <p>{{ feature.description }}</p>
        </article>
      </div>
    </section>

    <section v-once class="cta-section">
      <div class="cta-panel">
        <div class="cta-copy">
          <p>Ready To Start</p>
          <h2>点击右侧按钮，开始代码编写！</h2>
          <span>学习资源目前正在补充中……</span>
        </div>
        <div class="hero-actions">
          <button
            class="hero-button hero-primary"
            @click="router.push('/playground')"
          >
            <span>现在开始写代码</span>
          </button>
          <button
            class="hero-button hero-secondary"
            @click="router.push('/learn')"
          >
            <span>查看学习资源</span>
          </button>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.home-shell {
  overflow: hidden;
  background: #eef2f5;
  color: #111827;
}
.hero-section {
  position: relative;
  min-height: calc(100svh - var(--header-h, 5rem));
  border-bottom: 1px solid #cbd5e1;
  background: #f3f6f8;
}
.hero-grid {
  position: absolute;
  inset: 0;
  opacity: 0.65;
  background-image:
    linear-gradient(rgba(71, 85, 105, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(71, 85, 105, 0.08) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: linear-gradient(to bottom, #000 0%, transparent 92%);
}
.hero-layout {
  position: relative;
  z-index: 1;
  display: grid;
  width: min(100% - 2rem, 82rem);
  min-height: calc(100svh - var(--header-h, 5rem));
  margin: auto;
  align-items: center;
  gap: clamp(2rem, 5vw, 5rem);
  padding: 3.5rem 0;
}
.hero-copy {
  min-width: 0;
}
.hero-label {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  border: 1px solid #aebac5;
  background: rgba(248, 250, 252, 0.82);
  padding: 0.55rem 0.8rem;
  color: #0e7490;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}
.status-dot {
  width: 0.45rem;
  height: 0.45rem;
  background: #06b6d4;
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.12);
}
.hero-title {
  margin: 1.5rem 0 0;
  font-size: clamp(2.8rem, 7vw, 6.4rem);
  font-weight: 900;
  line-height: 0.98;
  letter-spacing: 0;
}
.title-line {
  display: block;
}
.title-accent {
  position: relative;
  width: fit-content;
  margin-top: 0.25rem;
  color: #0891b2;
}
.title-accent::after {
  content: attr(data-text);
  position: absolute;
  inset: 0;
  color: #f0c75e;
  clip-path: inset(0 100% 0 0);
  pointer-events: none;
  animation: decode-flash 0.52s steps(8, end) 1.05s 1 both;
}
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 2rem;
}
.hero-button {
  position: relative;
  isolation: isolate;
  display: inline-flex;
  min-height: 3rem;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  overflow: hidden;
  border: 1px solid #9aa9b6;
  padding: 0.75rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 800;
  transition:
    color 0.25s ease,
    border-color 0.25s ease,
    transform 0.25s ease;
}
.hero-button::before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: 0;
  transform: scaleX(0);
  transform-origin: left;
  background: #22d3ee;
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.hero-button:hover::before {
  transform: scaleX(1);
}
.hero-button:hover {
  border-color: #22d3ee;
  color: #082f49;
}
.hero-button svg {
  width: 1.2rem;
  height: 1.2rem;
  transition: transform 0.25s ease;
}
.hero-button:hover svg {
  transform: translateX(4px);
}
.hero-primary {
  border-color: #0891b2;
  background: #0e7490;
  color: white;
}
.hero-secondary {
  background: rgba(248, 250, 252, 0.8);
  color: #334155;
}
.terminal-stage {
  position: relative;
  min-width: 0;
  perspective: 1200px;
  transform-style: preserve-3d;
}
.terminal-frame {
  position: relative;
  overflow: hidden;
  border: 1px solid #8393a1;
  background: #111820;
  box-shadow: 12px 14px 0 rgba(15, 23, 42, 0.07);
  transform: rotateX(var(--rotate-x, 0)) rotateY(var(--rotate-y, 0));
  transition: transform 0.18s ease-out;
}
.terminal-frame::before {
  content: "";
  position: absolute;
  z-index: 4;
  inset: 0;
  border: 1px solid rgba(103, 232, 249, 0.2);
  pointer-events: none;
}
.terminal-toolbar {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  min-height: 3.1rem;
  border-bottom: 1px solid #34414c;
  background: #1b252e;
  padding: 0 1rem;
}
.window-controls {
  display: flex;
  gap: 0.45rem;
}
.window-controls span {
  width: 0.55rem;
  height: 0.55rem;
  border: 1px solid #61717f;
  background: #26343f;
}
.window-controls span:nth-child(2) {
  border-color: #b78b2e;
  background: #d3a63f;
}
.file-path {
  max-width: 13rem;
  overflow: hidden;
  color: #aab8c4;
  font: 500 0.7rem/1.2 monospace;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.toolbar-icon {
  justify-self: end;
  color: #67e8f9;
}
.terminal-workspace {
  display: grid;
  min-height: 28.5rem;
  grid-template-columns: minmax(0, 1.45fr) minmax(12.5rem, 0.75fr);
}
.code-panel {
  min-width: 0;
  border-right: 1px solid #34414c;
  background: #0b1117;
}
.terminal-side {
  display: grid;
  grid-template-rows: 1fr auto;
  min-width: 0;
}
.panel-heading {
  display: flex;
  min-height: 2.6rem;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #2d3943;
  padding: 0 0.9rem;
  color: #8193a0;
  font: 700 0.65rem/1 monospace;
  text-transform: uppercase;
}
.panel-heading span {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.panel-heading svg {
  width: 1rem;
  height: 1rem;
  color: #22d3ee;
}
.editor-body {
  position: relative;
  display: grid;
  grid-template-columns: 2.4rem minmax(0, 1fr);
  height: calc(100% - 2.6rem);
  overflow: hidden;
  padding: 1.2rem 0.6rem 1rem 0;
}
.line-numbers {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #40505d;
  font: 0.75rem/1.72rem monospace;
  user-select: none;
}
.editor-body pre {
  margin: 0;
  overflow: auto hidden;
  color: #c5d1d9;
  font:
    0.78rem/1.72rem "Cascadia Code",
    Consolas,
    monospace;
  scrollbar-width: none;
}
.editor-body code {
  white-space: pre;
}
.typing-mask {
  position: absolute;
  z-index: 2;
  inset: 0 0 0 2.4rem;
  background: #0b1117;
  transform-origin: right;
  animation: reveal-code 1s steps(24, end) 1.05s 1 both;
}
.typing-mask::after {
  content: "";
  position: absolute;
  left: 0;
  top: 1.2rem;
  width: 1px;
  height: 1.1rem;
  background: #67e8f9;
  animation: caret-blink 0.45s step-end 1.05s 3;
}
:deep(.code-directive),
:deep(.code-type) {
  color: #67e8f9;
}
:deep(.code-muted) {
  color: #71808d;
}
:deep(.code-function),
:deep(.code-number) {
  color: #f0c75e;
}
:deep(.code-object) {
  color: #9fb7c8;
}
:deep(.code-string) {
  color: #7dd3a8;
}
:deep(.code-keyword) {
  color: #f09da8;
}
.result-panel {
  background: #131c24;
}
.judge-timeline {
  padding: 1rem;
}
.judge-status {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-height: 2.1rem;
  border-left: 1px solid #34414c;
  padding-left: 0.8rem;
  color: #687986;
  font: 700 0.7rem/1 monospace;
  opacity: 0;
  transform: translateY(5px);
  animation: status-in 0.28s ease forwards;
}
.judge-status span {
  width: 0.4rem;
  height: 0.4rem;
  margin-left: -0.99rem;
  border: 1px solid #526571;
  background: #17222b;
}
.status-compiling {
  animation-delay: 1.8s;
}
.status-running {
  animation-delay: 2.05s;
}
.status-accepted {
  color: #8ce8ae;
  animation-delay: 2.3s;
}
.status-accepted svg {
  width: 0.85rem;
  height: 0.85rem;
  margin-left: -0.22rem;
}
.preview-output {
  margin: 0 1rem 1rem;
  border: 1px solid #2d3b46;
  background: #0b1117;
  padding: 0.8rem;
  color: #8ce8ae;
  font: 0.72rem/1.4 monospace;
  opacity: 0;
  animation: status-in 0.3s ease 2.42s forwards;
}
.language-panel {
  border-top: 1px solid #34414c;
  background: #101820;
}
.language-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: #2d3943;
}
.language-button {
  display: grid;
  aspect-ratio: 1;
  min-width: 0;
  place-items: center;
  border: 0;
  background: #151f27;
  filter: grayscale(1);
  opacity: 0.42;
  transition:
    background 0.2s ease,
    filter 0.2s ease,
    opacity 0.2s ease;
  animation: language-on 0.28s ease var(--language-delay) forwards;
}
.language-button:hover,
.language-button.active {
  background: #1e2b35;
  filter: grayscale(0);
  opacity: 1;
}
.language-button.active {
  box-shadow: inset 0 -2px var(--language-color);
}
.language-button svg {
  width: 1.45rem;
  height: 1.45rem;
}
.intro {
  opacity: 0;
  transform: translateY(12px);
  animation: intro-in 0.55s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}
.intro-label {
  animation-delay: 0.2s;
}
.intro-title-one {
  animation-delay: 0.35s;
}
.intro-title-two {
  animation-delay: 0.46s;
}
.intro-actions {
  animation-delay: 0.6s;
}
.intro-terminal {
  animation-delay: 0.7s;
}
.feature-section,
.cta-section {
  width: min(100% - 2rem, 82rem);
  margin: auto;
}
.feature-section {
  padding: 4rem 0 2rem;
}
.feature-grid {
  display: grid;
  gap: 1px;
  border: 1px solid #c3cdd5;
  background: #c3cdd5;
}
.feature-card {
  position: relative;
  min-width: 0;
  background: #f8fafc;
  padding: 1.5rem;
  transition: background 0.25s ease;
}
.feature-card:hover {
  background: #eefbfc;
}
.feature-icon {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  place-items: center;
  border: 1px solid #9fb0bd;
  color: #0e7490;
}
.feature-icon svg {
  width: 1.25rem;
  height: 1.25rem;
}
.feature-card h2 {
  margin: 1.2rem 0 0.55rem;
  font-size: 1rem;
}
.feature-card p {
  margin: 0;
  color: #5b6873;
  font-size: 0.8rem;
  line-height: 1.75;
}
.cta-section {
  padding: 2rem 0 5rem;
}
.cta-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  border-block: 1px solid #b9c5ce;
  padding: 2rem 0;
}
.cta-copy p {
  margin: 0;
  color: #0e7490;
  font: 800 0.68rem/1 monospace;
  text-transform: uppercase;
}
.cta-copy h2 {
  margin: 0.6rem 0;
  font-size: clamp(1.45rem, 3vw, 2.25rem);
}
.cta-copy span {
  color: #667580;
  font-size: 0.85rem;
}
.cta-panel .hero-actions {
  flex-shrink: 0;
  margin-top: 0;
}
.dark .home-shell {
  background: #070c11;
  color: #e6edf2;
}
.dark .hero-section {
  border-color: #26343e;
  background: #080e13;
}
.dark .hero-grid {
  opacity: 0.5;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.07) 1px, transparent 1px);
}
.dark .hero-label {
  border-color: #344550;
  background: rgba(11, 18, 24, 0.8);
  color: #67e8f9;
}
.dark .hero-secondary {
  border-color: #45545f;
  background: rgba(15, 23, 31, 0.8);
  color: #d2dce3;
}
.dark .feature-grid {
  border-color: #293741;
  background: #293741;
}
.dark .feature-card {
  background: #0e161c;
}
.dark .feature-card:hover {
  background: #111f26;
}
.dark .feature-card p,
.dark .cta-copy span {
  color: #98a8b4;
}
.dark .feature-icon {
  border-color: #3b505c;
  color: #67e8f9;
}
.dark .cta-panel {
  border-color: #34434e;
}
@media (min-width: 1024px) {
  .hero-layout {
    grid-template-columns: minmax(22rem, 0.82fr) minmax(31rem, 1.18fr);
  }
  .feature-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
@media (max-width: 1023px) {
  .hero-layout {
    align-content: center;
    padding-block: 4.5rem;
  }
  .terminal-stage {
    width: min(100%, 44rem);
  }
  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 640px) {
  .hero-layout {
    width: min(100% - 1.25rem, 82rem);
    gap: 2.75rem;
    padding-block: 3rem;
  }
  .hero-title {
    font-size: clamp(2.55rem, 13.5vw, 4rem);
  }
  .hero-actions {
    display: grid;
    grid-template-columns: 1fr;
  }
  .hero-button {
    width: 100%;
  }
  .terminal-workspace {
    min-height: 0;
    grid-template-columns: 1fr;
  }
  .code-panel {
    min-height: 18rem;
    border-right: 0;
    border-bottom: 1px solid #34414c;
  }
  .terminal-side {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
  }
  .editor-body pre {
    font-size: 0.69rem;
    line-height: 1.55rem;
  }
  .line-numbers {
    line-height: 1.55rem;
  }
  .result-panel {
    min-height: 13.5rem;
  }
  .file-path {
    max-width: 10rem;
  }
  .terminal-frame {
    box-shadow: 8px 10px 0 rgba(15, 23, 42, 0.1);
  }
  .feature-section,
  .cta-section {
    width: min(100% - 1.25rem, 82rem);
  }
  .feature-grid {
    grid-template-columns: 1fr;
  }
  .cta-panel {
    align-items: stretch;
    flex-direction: column;
  }
  .cta-panel .hero-actions {
    width: 100%;
  }
  .hero-coordinate {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .intro,
  .title-accent::after,
  .typing-mask,
  .typing-mask::after,
  .judge-status,
  .preview-output,
  .language-button {
    animation: none !important;
    opacity: 1;
    transform: none;
    clip-path: inset(0 100% 0 0);
  }
  .typing-mask {
    display: none;
  }
  .terminal-frame,
  .hero-button,
  .hero-button::before,
  .hero-button svg,
  .language-button {
    transition-duration: 0.01ms !important;
  }
}
@media (hover: none), (pointer: coarse) {
  .terminal-frame {
    transform: none !important;
    transition: none;
  }
}
@keyframes intro-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes decode-flash {
  0% {
    clip-path: inset(0 100% 0 0);
  }
  48% {
    clip-path: inset(0 0 0 0);
  }
  100% {
    clip-path: inset(0 0 0 100%);
  }
}
@keyframes reveal-code {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(100%);
  }
}
@keyframes caret-blink {
  50% {
    opacity: 0;
  }
}
@keyframes status-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes language-on {
  to {
    filter: grayscale(0);
    opacity: 0.88;
  }
}
</style>
