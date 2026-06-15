<script setup lang="ts">
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const languages = [
  { name: 'JavaScript', value: 'javascript', icon: 'vscode-icons:file-type-js-official', color: '#f7df1e' },
  { name: 'Python', value: 'python', icon: 'vscode-icons:file-type-python', color: '#3776ab' },
  { name: 'Java', value: 'java', icon: 'vscode-icons:file-type-java', color: '#ed8b00' },
  { name: 'C++', value: 'cpp', icon: 'vscode-icons:file-type-cpp', color: '#00599c' },
  { name: 'Go', value: 'go', icon: 'vscode-icons:file-type-go', color: '#00add8' },
  { name: 'Rust', value: 'rust', icon: 'vscode-icons:file-type-rust', color: '#dea584' },
  { name: 'Swift', value: 'swift', icon: 'vscode-icons:file-type-swift', color: '#fa7343' },
  { name: 'Kotlin', value: 'kotlin', icon: 'vscode-icons:file-type-kotlin', color: '#7f52ff' },
];

const features = [
  {
    icon: 'material-symbols:flash-on',
    title: '打开即写',
    description: '进入页面就能练习代码，适合课堂演示、算法练习和快速验证想法。',
  },
  {
    icon: 'material-symbols:terminal',
    title: '输出即时可见',
    description: '运行结果和报错集中展示，调试时不用反复切换窗口。',
  },
  {
    icon: 'material-symbols:school',
    title: '学习资源联动',
    description: '从学习路径、推荐课程到编辑器练习，一条链路直接贯通。',
  },
  {
    icon: 'material-symbols:verified-user',
    title: '统一认证接入',
    description: '保留社团登录体验，后续扩展个人化功能和学习记录也更顺手。',
  },
];

const metrics = [
  { value: '8+', label: '常用语言模板' },
  { value: '1s', label: '进入编辑器速度' },
  { value: '24/7', label: '随时开始练习' },
];
</script>

<template>
  <main class="overflow-hidden bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
    <section class="relative isolate">
      <div class="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.24),_transparent_34%),radial-gradient(circle_at_85%_18%,_rgba(250,204,21,0.18),_transparent_22%),linear-gradient(180deg,_#ecfeff_0%,_#f8fafc_52%,_#f8fafc_100%)] dark:bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_32%),radial-gradient(circle_at_85%_18%,_rgba(250,204,21,0.08),_transparent_22%),linear-gradient(180deg,_#020617_0%,_#020617_100%)]"></div>
      <div class="mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8 lg:py-24">
        <div class="flex flex-col justify-center">
          <span class="inline-flex w-fit items-center gap-2 rounded-full border border-cyan-200/80 bg-white/80 px-4 py-2 text-xs font-black uppercase tracking-[0.22em] text-cyan-700 shadow-sm shadow-cyan-100/80 backdrop-blur dark:border-cyan-400/20 dark:bg-slate-900/80 dark:text-cyan-300 dark:shadow-black/0">
            <span class="h-2 w-2 rounded-full bg-cyan-400"></span>
            Let Coding Online Judge
          </span>

          <h1 class="mt-6 max-w-3xl text-4xl font-black leading-tight tracking-tight sm:text-5xl lg:text-6xl">
            让写代码
            <span class="block bg-gradient-to-r from-cyan-500 via-sky-500 to-amber-400 bg-clip-text text-transparent">
              更直接、更顺手
            </span>
          </h1>

          <p class="mt-6 max-w-2xl text-base leading-8 text-slate-600 dark:text-slate-300">
            把在线编辑、运行输出、学习资源和社团登录整合到一个页面体系里。无论你是在做课堂练习、刷题，还是沿着学习路径系统推进，都可以少切工具、直接开始。
          </p>

          <div class="mt-8 flex flex-wrap gap-4">
            <button class="hero-primary" @click="router.push('/playground')">
              <Icon icon="material-symbols:play-arrow" class="h-5 w-5" />
              进入在线编辑器
            </button>
            <button class="hero-secondary" @click="authStore.isAuthenticated ? router.push('/learn') : router.push('/login')">
              <Icon :icon="authStore.isAuthenticated ? 'material-symbols:school' : 'mdi:login'" class="h-5 w-5" />
              {{ authStore.isAuthenticated ? '查看学习资源' : '登录后查看学习资源' }}
            </button>
          </div>

          <div class="mt-10 grid grid-cols-3 gap-4">
            <div v-for="metric in metrics" :key="metric.label" class="rounded-3xl border border-white/80 bg-white/75 px-4 py-5 shadow-lg shadow-slate-200/70 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70 dark:shadow-black/20">
              <div class="text-2xl font-black text-slate-950 dark:text-white">{{ metric.value }}</div>
              <div class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ metric.label }}</div>
            </div>
          </div>
        </div>

        <div class="relative flex items-center justify-center">
          <div class="absolute -left-4 top-12 hidden h-24 w-24 rounded-full bg-amber-300/40 blur-3xl lg:block dark:bg-amber-500/10"></div>
          <div class="absolute -right-6 bottom-10 hidden h-28 w-28 rounded-full bg-cyan-400/30 blur-3xl lg:block dark:bg-cyan-400/10"></div>

          <div class="w-full max-w-xl rounded-[2rem] border border-white/80 bg-white/85 p-4 shadow-2xl shadow-slate-300/60 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/30">
            <div class="flex items-center justify-between rounded-[1.5rem] bg-slate-950 px-4 py-3 text-slate-200">
              <div class="flex items-center gap-2">
                <span class="h-3 w-3 rounded-full bg-rose-400"></span>
                <span class="h-3 w-3 rounded-full bg-amber-300"></span>
                <span class="h-3 w-3 rounded-full bg-emerald-400"></span>
              </div>
              <div class="rounded-full bg-white/10 px-3 py-1 text-xs font-medium">playground/main.cpp</div>
            </div>

            <div class="mt-4 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
              <div class="rounded-[1.5rem] bg-slate-900 p-5 text-sm text-slate-100 shadow-inner shadow-slate-950/30">
                <div class="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-slate-400">
                  <Icon icon="material-symbols:code" class="h-4 w-4" />
                  Sample Code
                </div>
                <pre class="overflow-auto font-mono leading-7"><code><span class="text-cyan-300">#include</span> &lt;iostream&gt;

<span class="text-sky-300">int</span> main() {
  <span class="text-violet-300">std::cout</span> &lt;&lt; <span class="text-amber-300">"Hello, Let Coding!"</span> &lt;&lt; <span class="text-amber-300">'\\n'</span>;
  <span class="text-pink-300">return</span> 0;
}</code></pre>
              </div>

              <div class="space-y-4">
                <div class="rounded-[1.5rem] bg-cyan-500 px-5 py-5 text-slate-950 shadow-lg shadow-cyan-500/25">
                  <div class="text-xs font-black uppercase tracking-[0.22em]">运行结果</div>
                  <div class="mt-3 rounded-2xl bg-slate-950 px-4 py-4 font-mono text-sm text-emerald-300">
                    Hello, Let Coding!
                  </div>
                </div>

                <div class="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
                  <div class="text-xs font-black uppercase tracking-[0.22em] text-slate-500">支持语言</div>
                  <div class="mt-4 grid grid-cols-2 gap-3">
                    <button
                      v-for="language in languages"
                      :key="language.value"
                      type="button"
                      class="grid h-14 min-w-0 place-items-center overflow-hidden rounded-2xl border border-slate-200 bg-white p-0 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
                      @click="router.push(`/playground?language=${language.value}`)"
                    >
                      <Icon :icon="language.icon" class="h-7 w-7 max-w-full" :style="{ color: language.color }" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
      <div class="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <article v-for="feature in features" :key="feature.title" class="feature-card">
          <div class="feature-icon">
            <Icon :icon="feature.icon" class="h-6 w-6" />
          </div>
          <h2 class="mt-5 text-xl font-black tracking-tight">{{ feature.title }}</h2>
          <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
            {{ feature.description }}
          </p>
        </article>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8 lg:pb-24">
      <div class="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20 lg:p-10">
        <div class="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
          <div class="max-w-2xl">
            <p class="text-sm font-black uppercase tracking-[0.22em] text-cyan-600 dark:text-cyan-300">Ready To Start</p>
            <h2 class="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
              从打开页面到运行第一段代码，只差一次点击。
            </h2>
            <p class="mt-4 text-base leading-8 text-slate-600 dark:text-slate-300">
              想立即写代码，就直接进入编辑器；想先看路线和资料，就去学习资源页按路径推进。两个入口现在是连通的，切换起来会轻松很多。
            </p>
          </div>

          <div class="flex flex-wrap gap-4">
            <button class="hero-primary" @click="router.push('/playground')">
              现在开始写代码
            </button>
            <button class="hero-secondary" @click="router.push('/learn')">
              浏览学习内容
            </button>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
@reference 'tailwindcss';

.hero-primary {
  @apply inline-flex items-center gap-2 rounded-full bg-slate-950 px-6 py-3.5 text-sm font-black text-white shadow-xl shadow-slate-900/15 transition hover:-translate-y-0.5 hover:bg-slate-800 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300;
}

.hero-secondary {
  @apply inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-3.5 text-sm font-black text-slate-800 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800;
}

.feature-card {
  @apply rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60 transition hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20;
}

.feature-icon {
  @apply grid h-14 w-14 place-items-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300;
}
</style>
