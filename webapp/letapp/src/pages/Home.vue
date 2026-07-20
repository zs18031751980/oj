<script setup lang="ts">
import { computed, markRaw, onMounted, onUnmounted, ref } from "vue";
import { Icon } from "@iconify/vue";
import { useRouter } from "vue-router";

const router = useRouter();
const terminalRef = ref<HTMLElement | null>(null);
const particleCanvasRef = ref<HTMLCanvasElement | null>(null);
const terminalStyle = ref<Record<string, string>>({});
const currentLanguage = ref("cpp");
let perspectiveFrame = 0;
let particleFrame = 0;
let particleResizeObserver: ResizeObserver | null = null;
let lastParticleAt = 0;

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  size: number;
  color: string;
}

const particles: Particle[] = [];
const particleColors = ["#67e8f9", "#22d3ee", "#f0c75e"];

const isMotionLimited = () =>
  window.innerWidth < 1024 ||
  window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
  window.matchMedia("(hover: none), (pointer: coarse)").matches ||
  (navigator.hardwareConcurrency > 0 && navigator.hardwareConcurrency <= 4);

const resizeParticleCanvas = () => {
  const canvas = particleCanvasRef.value;
  const element = terminalRef.value;
  if (!canvas || !element) return;
  const bounds = element.getBoundingClientRect();
  const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
  canvas.width = Math.max(1, Math.round(bounds.width * ratio));
  canvas.height = Math.max(1, Math.round(bounds.height * ratio));
  canvas.style.width = `${bounds.width}px`;
  canvas.style.height = `${bounds.height}px`;
};

const renderParticles = () => {
  const canvas = particleCanvasRef.value;
  const context = canvas?.getContext("2d");
  if (!canvas || !context) {
    particleFrame = 0;
    return;
  }

  const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, canvas.width / ratio, canvas.height / ratio);

  for (let index = particles.length - 1; index >= 0; index -= 1) {
    const particle = particles[index];
    if (!particle) continue;
    particle.x += particle.vx;
    particle.y += particle.vy;
    particle.vy += 0.012;
    particle.life -= 0.045;

    if (particle.life <= 0) {
      particles.splice(index, 1);
      continue;
    }

    context.globalAlpha = Math.max(0, particle.life * 0.75);
    context.fillStyle = particle.color;
    context.fillRect(particle.x, particle.y, particle.size, particle.size);
  }
  context.globalAlpha = 1;

  if (particles.length) {
    particleFrame = requestAnimationFrame(renderParticles);
  } else {
    particleFrame = 0;
    context.clearRect(0, 0, canvas.width / ratio, canvas.height / ratio);
  }
};

const emitParticles = (event: PointerEvent) => {
  if (isMotionLimited() || event.timeStamp - lastParticleAt < 22) return;
  const element = terminalRef.value;
  if (!element) return;
  const bounds = element.getBoundingClientRect();
  const x = event.clientX - bounds.left;
  const y = event.clientY - bounds.top;
  lastParticleAt = event.timeStamp;

  for (let index = 0; index < 2; index += 1) {
    particles.push({
      x: x + (Math.random() - 0.5) * 8,
      y: y + (Math.random() - 0.5) * 8,
      vx: (Math.random() - 0.5) * 0.9,
      vy: -0.25 - Math.random() * 0.55,
      life: 0.7 + Math.random() * 0.3,
      size: 1.2 + Math.random() * 1.8,
      color:
        particleColors[Math.floor(Math.random() * particleColors.length)] ??
        "#67e8f9",
    });
  }
  if (particles.length > 48) particles.splice(0, particles.length - 48);
  if (!particleFrame) particleFrame = requestAnimationFrame(renderParticles);
};

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

const handlePointerMove = (event: PointerEvent) => {
  emitParticles(event);
  if (isMotionLimited()) return;
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

const handleTerminalClick = (event: MouseEvent) => {
  if ((event.target as HTMLElement).closest("button")) return;
  void router.push("/playground");
};

const handleTerminalKeydown = (event: KeyboardEvent) => {
  if (event.target !== event.currentTarget) return;
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    void router.push("/playground");
  }
};

onMounted(() => {
  resizeParticleCanvas();
  particleResizeObserver = new ResizeObserver(resizeParticleCanvas);
  if (terminalRef.value) particleResizeObserver.observe(terminalRef.value);
  terminalRef.value?.addEventListener("pointermove", handlePointerMove);
  terminalRef.value?.addEventListener("pointerleave", resetPerspective);
});

onUnmounted(() => {
  if (perspectiveFrame) cancelAnimationFrame(perspectiveFrame);
  if (particleFrame) cancelAnimationFrame(particleFrame);
  particleResizeObserver?.disconnect();
  particles.length = 0;
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
              >更直接 更顺手</span
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
          role="link"
          tabindex="0"
          aria-label="进入在线编辑器"
          @click="handleTerminalClick"
          @keydown="handleTerminalKeydown"
        >
          <canvas
            ref="particleCanvasRef"
            class="particle-canvas"
            aria-hidden="true"
          ></canvas>
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
                  <div class="active-line" aria-hidden="true"></div>
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
              </aside>
            </div>

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
                    '--language-delay': `${0.78 + index * 0.04}s`,
                  }"
                  :aria-label="language.name"
                  @click.stop="selectLanguage(language)"
                >
                  <Icon :icon="language.icon" />
                </button>
              </div>
            </section>
          </div>
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
  line-height: 1.08;
  letter-spacing: 0;
}
.title-line {
  display: block;
}
.title-accent {
  position: relative;
  width: fit-content;
  margin-top: 0.4rem;
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
  border-radius: 1.25rem;
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
  isolation: isolate;
  min-width: 0;
  perspective: 1200px;
  transform-style: preserve-3d;
  cursor: pointer;
  outline: none;
}
.terminal-stage::before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: 0;
  border: 1px solid #52616d;
  border-radius: 1.5rem;
  transform: translate(10px, 10px);
  pointer-events: none;
}
.terminal-stage:focus-visible .terminal-frame {
  border-color: #22d3ee;
  box-shadow:
    0 0 0 2px rgba(34, 211, 238, 0.2),
    0 24px 48px rgba(2, 8, 12, 0.28);
}
.particle-canvas {
  position: absolute;
  z-index: 6;
  inset: 0;
  display: block;
  pointer-events: none;
}
.terminal-frame {
  position: relative;
  overflow: hidden;
  border: 1px solid #8393a1;
  border-radius: 1.5rem;
  background: #111820;
  box-shadow: 0 24px 48px rgba(2, 8, 12, 0.24);
  transform: rotateX(var(--rotate-x, 0)) rotateY(var(--rotate-y, 0));
  transition: transform 0.18s ease-out;
}
.terminal-frame::before {
  content: "";
  position: absolute;
  z-index: 4;
  inset: 0;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: inherit;
  pointer-events: none;
}
.terminal-frame::after {
  content: "";
  position: absolute;
  z-index: 5;
  top: 0;
  left: 14%;
  width: 26%;
  height: 2px;
  background: #22d3ee;
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
  min-height: 24.5rem;
  grid-template-columns: minmax(0, 68fr) minmax(11.5rem, 32fr);
}
.code-panel {
  min-width: 0;
  border-right: 1px solid #34414c;
  background: #0b1117;
}
.terminal-side {
  display: block;
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
.active-line {
  position: absolute;
  z-index: 0;
  top: calc(1.2rem + 3 * 1.72rem);
  right: 0;
  left: 2.4rem;
  height: 1.72rem;
  border-left: 2px solid #22d3ee;
  background: rgba(34, 211, 238, 0.065);
  opacity: 0;
  transform: scaleX(0.92);
  transform-origin: left;
  animation: active-line-in 0.22s ease-out 0.95s 1 forwards;
}
.line-numbers,
.editor-body pre {
  position: relative;
  z-index: 1;
}
.typing-mask {
  position: absolute;
  z-index: 2;
  inset: 0 0 0 2.4rem;
  background: #0b1117;
  transform-origin: bottom;
  animation: reveal-code 0.72s steps(7, end) 0.82s 1 both;
}
.typing-mask::after {
  content: "";
  position: absolute;
  left: 0;
  top: 1.2rem;
  width: 1px;
  height: 1.1rem;
  background: #67e8f9;
  animation: caret-blink 0.24s step-end 0.82s 3;
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
  display: flex;
  height: 100%;
  flex-direction: column;
  background: #131c24;
}
.judge-timeline {
  position: relative;
  display: grid;
  gap: 0.15rem;
  padding: 1rem;
}
.judge-timeline::before {
  content: "";
  position: absolute;
  top: 1.55rem;
  bottom: 1.55rem;
  left: 1.19rem;
  width: 1px;
  background: #3c4b56;
}
.judge-status {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-height: 2.1rem;
  padding-left: 0;
  color: #687986;
  font: 700 0.7rem/1 monospace;
  opacity: 0;
  transform: translateY(5px);
  animation: status-in 0.28s ease forwards;
}
.judge-status span {
  width: 0.4rem;
  height: 0.4rem;
  border: 1px solid #526571;
  background: #17222b;
  position: relative;
  z-index: 1;
}
.status-compiling {
  animation-delay: 1.55s;
}
.status-running {
  animation-delay: 1.8s;
}
.status-accepted {
  color: #8ce8ae;
  animation-delay: 2.05s;
}
.status-accepted svg {
  position: relative;
  z-index: 1;
  width: 0.85rem;
  height: 0.85rem;
  background: #131c24;
}
.preview-output {
  margin: auto 1rem 1rem;
  border: 1px solid #2d3b46;
  background: #0b1117;
  padding: 0.8rem;
  color: #8ce8ae;
  font: 0.72rem/1.4 monospace;
  opacity: 0;
  animation: status-in 0.22s ease 2.18s forwards;
}
.language-panel {
  display: grid;
  grid-template-columns: 7.5rem minmax(0, 1fr);
  border-top: 1px solid #34414c;
  background: #101820;
}
.language-panel > .panel-heading {
  min-height: 3.65rem;
  border-right: 1px solid #2d3943;
  border-bottom: 0;
}
.language-grid {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 1px;
  background: #2d3943;
}
.language-button {
  display: grid;
  position: relative;
  min-width: 0;
  min-height: 3.65rem;
  place-items: center;
  border: 0;
  background: #151f27;
  filter: grayscale(1);
  opacity: 0.42;
  transition:
    background 0.2s ease,
    filter 0.2s ease,
    opacity 0.2s ease,
    transform 0.2s ease;
  animation: language-on 0.18s ease var(--language-delay) forwards;
}
.language-button:hover,
.language-button.active {
  background: #1e2b35;
  filter: grayscale(0);
  opacity: 1;
}
.language-button.active {
  transform: translateY(-2px);
  box-shadow: inset 0 -2px #22d3ee;
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
html:not(.dark) .terminal-stage::before {
  border-color: #a7b4be;
}
html:not(.dark) .terminal-frame {
  border-color: #9eacb7;
  background: #eef3f6;
  box-shadow: 0 24px 48px rgba(51, 65, 85, 0.16);
}
html:not(.dark) .terminal-frame::before {
  border-color: rgba(71, 85, 105, 0.16);
}
html:not(.dark) .terminal-toolbar {
  border-color: #bac6cf;
  background: #e3e9ed;
}
html:not(.dark) .window-controls span {
  border-color: #9aa9b4;
  background: #c5d0d7;
}
html:not(.dark) .window-controls span:nth-child(2) {
  border-color: #b78b2e;
  background: #d3a63f;
}
html:not(.dark) .file-path {
  color: #425466;
}
html:not(.dark) .toolbar-icon,
html:not(.dark) .panel-heading svg {
  color: #087c93;
}
html:not(.dark) .code-panel {
  border-color: #bdc8d0;
  background: #f5f7f9;
}
html:not(.dark) .panel-heading {
  border-color: #c4ced5;
  color: #526371;
}
html:not(.dark) .line-numbers {
  color: #8b9aa6;
}
html:not(.dark) .editor-body pre {
  color: #1e293b;
}
html:not(.dark) .active-line {
  border-color: #0891b2;
  background: rgba(8, 145, 178, 0.08);
}
html:not(.dark) .typing-mask {
  background: #f5f7f9;
}
html:not(.dark) .typing-mask::after {
  background: #0891b2;
}
html:not(.dark) .result-panel {
  background: #eaf0f3;
}
html:not(.dark) .judge-timeline::before {
  background: #b6c2ca;
}
html:not(.dark) .judge-status {
  color: #61717d;
}
html:not(.dark) .judge-status span {
  border-color: #93a4af;
  background: #edf2f5;
}
html:not(.dark) .status-accepted {
  color: #15803d;
}
html:not(.dark) .status-accepted svg {
  background: #eaf0f3;
}
html:not(.dark) .preview-output {
  border-color: #bdc8d0;
  background: #f8fafc;
  color: #15803d;
}
html:not(.dark) .language-panel {
  border-color: #b8c4cc;
  background: #e3e9ed;
}
html:not(.dark) .language-panel > .panel-heading {
  border-color: #bdc8d0;
}
html:not(.dark) .language-grid {
  background: #c3cdd4;
}
html:not(.dark) .language-button {
  background: #f1f5f7;
}
html:not(.dark) .language-button:hover,
html:not(.dark) .language-button.active {
  background: #e5f5f7;
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
@media (min-width: 1024px) {
  .hero-layout {
    grid-template-columns: minmax(22rem, 0.82fr) minmax(31rem, 1.18fr);
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
    display: block;
  }
  .editor-body pre {
    font-size: 0.69rem;
    line-height: 1.55rem;
  }
  .line-numbers {
    line-height: 1.55rem;
  }
  .active-line {
    top: calc(1.2rem + 3 * 1.55rem);
    height: 1.55rem;
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
  .terminal-stage::before {
    transform: translate(6px, 6px);
  }
  .language-panel {
    grid-template-columns: 1fr;
  }
  .language-panel > .panel-heading {
    min-height: 2.35rem;
    border-right: 0;
    border-bottom: 1px solid #2d3943;
  }
  .language-button {
    min-height: 2.8rem;
  }
  .language-button svg {
    width: 1.15rem;
    height: 1.15rem;
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
  .active-line,
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
  .particle-canvas {
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
    transform: translateY(0);
  }
  to {
    transform: translateY(100%);
  }
}
@keyframes active-line-in {
  to {
    opacity: 1;
    transform: scaleX(1);
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

<style>
html:not(.dark) .home-shell .editor-body code {
  color: #0f172a;
}

html:not(.dark) .home-shell .code-directive,
html:not(.dark) .home-shell .code-type {
  color: #00677f;
  font-weight: 600;
}

html:not(.dark) .home-shell .code-muted {
  color: #475569;
}

html:not(.dark) .home-shell .code-function,
html:not(.dark) .home-shell .code-number {
  color: #854d0e;
  font-weight: 600;
}

html:not(.dark) .home-shell .code-object {
  color: #075985;
}

html:not(.dark) .home-shell .code-string {
  color: #166534;
}

html:not(.dark) .home-shell .code-keyword {
  color: #9f1239;
  font-weight: 600;
}
</style>
