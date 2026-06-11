<script setup lang="ts">
<<<<<<< HEAD
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();
</script>

<template>
  <main class="min-h-screen bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
    <section class="border-b border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950">
      <div class="mx-auto grid max-w-7xl gap-8 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8 lg:py-20">
        <div class="flex flex-col justify-center">
          <p class="mb-3 text-sm font-semibold uppercase tracking-wide text-blue-600 dark:text-blue-400">
            Let Coding Online Judge
          </p>
          <h1 class="text-4xl font-bold tracking-tight sm:text-5xl">
            在线写代码、运行代码、沉淀学习路径
          </h1>
          <p class="mt-5 max-w-2xl text-base leading-7 text-gray-600 dark:text-gray-300">
            Let Coding 提供在线代码编辑、语法高亮、运行反馈和学习资源入口，适合作为 OJ 系统的练习与教学首页。
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <button
              class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700"
              @click="router.push('/playground')"
            >
              <Icon icon="material-symbols:play-arrow" class="h-5 w-5" />
              开始写代码
            </button>
            <button
              class="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-5 py-3 text-sm font-semibold text-gray-800 hover:bg-white dark:border-gray-700 dark:text-gray-100 dark:hover:bg-gray-800"
              @click="authStore.isAuthenticated ? router.push('/learn') : router.push('/login')"
            >
              <Icon :icon="authStore.isAuthenticated ? 'material-symbols:school' : 'mdi:github'" class="h-5 w-5" />
              {{ authStore.isAuthenticated ? '查看学习资源' : '登录后继续' }}
            </button>
          </div>
        </div>

        <div class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div class="mb-4 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-full bg-red-400"></span>
              <span class="h-3 w-3 rounded-full bg-yellow-400"></span>
              <span class="h-3 w-3 rounded-full bg-green-400"></span>
            </div>
            <span class="text-xs text-gray-500">main.cpp</span>
          </div>
          <pre class="overflow-auto rounded-lg bg-gray-200 p-4 text-sm text-gray-900 dark:bg-gray-800 dark:text-gray-100"><code><span class="text-purple-600 dark:text-purple-300">#include</span> &lt;iostream&gt;

<span class="text-blue-700 dark:text-blue-300">int</span> main() {
  <span class="text-cyan-700 dark:text-cyan-300">std::cout</span> &lt;&lt; <span class="text-green-700 dark:text-green-300">"Hello, Let Coding!"</span>;
  <span class="text-pink-700 dark:text-pink-300">return</span> 0;
}</code></pre>
=======
// import { ref } from 'vue'; // 未使用，注释掉
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// 支持的编程语言
const languages = [
  { name: 'JavaScript', value: 'javascript', icon: 'vscode-icons:file-type-js-official', color: '#F7DF1E' },
  { name: 'Python', value: 'python', icon: 'vscode-icons:file-type-python', color: '#3776AB' },
  { name: 'Java', value: 'java', icon: 'vscode-icons:file-type-java', color: '#ED8B00' },
  { name: 'C++', value: 'cpp', icon: 'vscode-icons:file-type-cpp', color: '#00599C' },
  { name: 'Go', value: 'go', icon: 'vscode-icons:file-type-go', color: '#00ADD8' },
  { name: 'Rust', value: 'rust', icon: 'vscode-icons:file-type-rust', color: '#DEA584' },
  { name: 'Swift', value: 'swift', icon: 'vscode-icons:file-type-swift', color: '#FA7343' },
  { name: 'Kotlin', value: 'kotlin', icon: 'vscode-icons:file-type-kotlin', color: '#7F52FF' },
];

// 核心功能
const features = [
  {
    icon: 'material-symbols:code',
    title: '多语言支持',
    description: '支持 20+ 种编程语言，包括 JavaScript、Python、Java、C++ 等主流语言。',
  },
  {
    icon: 'material-symbols:play-arrow',
    title: '在线执行',
    description: '无需安装环境，直接在浏览器中编写和运行代码，实时查看执行结果。',
  },
  {
    icon: 'material-symbols:storage',
    title: '代码保存',
    description: '登录后可保存你的代码片段，方便随时查看和编辑。',
  },
  {
    icon: 'material-symbols:group',
    title: '社区分享',
    description: '与其他开发者分享你的代码，学习和交流编程技巧。',
  },
];
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <!-- 英雄区域 -->
    <section class="py-16 md:py-24 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row items-center justify-between gap-12">
          <div class="md:w-1/2 space-y-6">
            <h1 class="text-4xl md:text-5xl font-bold tracking-tight">
              <span class="block">让编程变得</span>
              <span class="block text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">简单有趣</span>
            </h1>
            <p class="text-lg text-gray-600 dark:text-gray-300 max-w-md">
              Let Coding 是一个在线代码执行平台，支持多种编程语言，无需安装环境，即可随时编写和运行代码。
            </p>
            <div class="flex flex-col sm:flex-row gap-4">
              <button 
                class="px-8 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
                @click="router.push('/playground')"
              >
                立即开始
              </button>
              <button 
                class="px-8 py-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-medium rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors shadow-md border border-gray-200 dark:border-gray-700"
                @click="router.push('/learn')"
              >
                学习资源
              </button>
            </div>
            <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span>支持 {{ languages.length }}+ 种编程语言</span>
              <span class="h-2 w-2 rounded-full bg-gray-300 dark:bg-gray-600"></span>
              <span>无需安装任何软件</span>
            </div>
          </div>
          <div class="md:w-1/2 relative">
            <div class="absolute -top-10 -right-10 w-32 h-32 bg-blue-400 dark:bg-blue-600 rounded-full opacity-20 blur-xl"></div>
            <div class="absolute -bottom-10 -left-10 w-32 h-32 bg-indigo-400 dark:bg-indigo-600 rounded-full opacity-20 blur-xl"></div>
            <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden border border-gray-200 dark:border-gray-700">
              <div class="bg-gray-100 dark:bg-gray-900 px-4 py-2 flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-red-500"></div>
                <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div class="w-3 h-3 rounded-full bg-green-500"></div>
                <div class="ml-auto text-sm text-gray-500 dark:text-gray-400">app.js</div>
              </div>
              <div class="p-4 overflow-auto max-h-64">
                <pre class="text-sm font-mono"><code><span class="text-blue-600 dark:text-blue-400">function</span> <span class="text-green-600 dark:text-green-400">greet</span>(<span class="text-purple-600 dark:text-purple-400">name</span>) {
  <span class="text-blue-600 dark:text-blue-400">return</span> <span class="text-orange-600 dark:text-orange-400">`Hello, ${name}!`</span>;
}

<span class="text-blue-600 dark:text-blue-400">const</span> <span class="text-purple-600 dark:text-purple-400">message</span> = <span class="text-green-600 dark:text-green-400">greet</span>(<span class="text-orange-600 dark:text-orange-400">'Let Coding'</span>);
<span class="text-gray-600 dark:text-gray-400">// 输出: Hello, Let Coding!</span>
<span class="text-blue-600 dark:text-blue-400">console</span>.<span class="text-green-600 dark:text-green-400">log</span>(<span class="text-purple-600 dark:text-purple-400">message</span>);</code></pre>
              </div>
            </div>
          </div>
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
        </div>
      </div>
    </section>

<<<<<<< HEAD
    <section class="mx-auto grid max-w-7xl gap-4 px-4 py-10 sm:px-6 md:grid-cols-3 lg:px-8">
      <article class="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
        <Icon icon="material-symbols:code" class="mb-3 h-8 w-8 text-blue-600" />
        <h2 class="text-lg font-semibold">代码高亮编辑</h2>
        <p class="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          编辑器支持多语言关键字颜色渲染，写代码时能更快识别结构。
        </p>
      </article>
      <article class="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
        <Icon icon="material-symbols:terminal" class="mb-3 h-8 w-8 text-green-600" />
        <h2 class="text-lg font-semibold">在线运行反馈</h2>
        <p class="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          支持标准输入、标准输出和错误输出，方便快速验证题解。
        </p>
      </article>
      <article class="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
        <Icon icon="material-symbols:verified-user" class="mb-3 h-8 w-8 text-purple-600" />
        <h2 class="text-lg font-semibold">GitHub 登录</h2>
        <p class="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">
          使用 GitHub OAuth 登录，登录后可走认证接口并保留用户会话。
        </p>
      </article>
    </section>
  </main>
</template>
=======
    <!-- 功能介绍 -->
    <section class="py-16 bg-white dark:bg-gray-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold mb-4">核心功能</h2>
          <p class="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Let Coding 提供了一系列强大的功能，帮助你更高效地学习和编写代码。
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div 
            v-for="(feature, index) in features" 
            :key="index"
            class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow border border-gray-200 dark:border-gray-700 hover:translate-y-[-4px] transition-transform"
          >
            <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4">
              <Icon :icon="feature.icon" class="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 class="text-xl font-semibold mb-2">{{ feature.title }}</h3>
            <p class="text-gray-600 dark:text-gray-300">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 支持的编程语言 -->
    <section class="py-16 bg-gray-50 dark:bg-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold mb-4">支持的编程语言</h2>
          <p class="text-gray-600 dark:text-gray-300">
            选择你喜欢的编程语言，开始编写代码吧！
          </p>
        </div>
        
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-6">
          <div 
            v-for="lang in languages" 
            :key="lang.value"
            class="bg-white dark:bg-gray-900 p-4 rounded-lg shadow-md hover:shadow-lg transition-all border border-gray-200 dark:border-gray-700 flex flex-col items-center justify-center gap-2 hover:translate-y-[-2px] cursor-pointer"
            @click="router.push(`/playground?language=${lang.value}`)"
          >
            <div class="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center transition-transform hover:scale-110">
              <Icon :icon="lang.icon" class="w-6 h-6" :style="{ color: lang.color }" />
            </div>
            <span class="text-sm font-medium">{{ lang.name }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 快速开始 -->
    <section class="py-16 bg-white dark:bg-gray-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold mb-4">快速开始</h2>
          <p class="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            只需三步，即可开始使用 Let Coding 编写和运行代码。
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="flex flex-col items-center text-center">
            <div class="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-2xl mb-4">1</div>
            <h3 class="text-xl font-semibold mb-2">选择语言</h3>
            <p class="text-gray-600 dark:text-gray-300">
              从 20+ 种编程语言中选择你想要使用的语言。
            </p>
          </div>
          
          <div class="flex flex-col items-center text-center">
            <div class="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-2xl mb-4">2</div>
            <h3 class="text-xl font-semibold mb-2">编写代码</h3>
            <p class="text-gray-600 dark:text-gray-300">
              在我们的在线编辑器中编写你的代码，支持语法高亮和自动补全。
            </p>
          </div>
          
          <div class="flex flex-col items-center text-center">
            <div class="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-2xl mb-4">3</div>
            <h3 class="text-xl font-semibold mb-2">运行代码</h3>
            <p class="text-gray-600 dark:text-gray-300">
              点击运行按钮，即可实时查看代码的执行结果。
            </p>
          </div>
        </div>
        
        <div class="mt-16 text-center">
          <button 
            class="px-8 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
            @click="router.push('/playground')"
          >
            开始编写代码
          </button>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="bg-gray-900 text-gray-300 py-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div class="flex items-center gap-2 mb-4">
              <img src="/assets/logo.png" alt="Let Coding" class="w-8 h-8" />
              <span class="text-white font-semibold text-lg">Let Coding</span>
            </div>
            <p class="text-gray-400 mb-4">
              让编程变得简单有趣，随时随地编写和运行代码。
            </p>
            <div class="flex gap-4">
              <a href="https://gitee.com/XAUATiOSClub" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors" title="Gitee">
                <Icon icon="simple-icons:gitee" class="w-5 h-5" />
              </a>
              <a href="https://space.bilibili.com/1283819651?spm_id_from=333.337.search-card.all.click" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors" title="B站">
                <Icon icon="simple-icons:bilibili" class="w-5 h-5" />
              </a>
              <a href="https://www.douyin.com/user/MS4wLjABAAAA042crZROwmNV69KtvhQSGtyLEZZATt4z1ewoXk-dLxCmt2S_DNus5c2KP_5S2CTY?_sw=4167573395234171&enter_from=general_search&enter_method=general_search&extra_params=%7B%22search_params%22%3A%7B%22search_result_id%22%3A%221612337042431609%22%2C%22relation_tag%22%3A0%2C%22log_pb%22%3A%7B%22impr_id%22%3A%2220241107211419AA5B58FD61D13326A614%22%7D%2C%22search_type%22%3A%22general%22%2C%22impr_id%22%3A%2220241107211419AA5B58FD61D13326A614%22%2C%22search_id%22%3A%2220241107211419AA5B58FD61D13326A614%22%2C%22search_keyword%22%3A%22%20%E8%A5%BF%E5%BB%BA%E5%A4%A7iOS%20Club%22%2C%22token_type%22%3A%22discover_list%22%7D%7D&from_tab_name=main" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors" title="抖音">
                <Icon icon="mdi:video" class="w-5 h-5" />
              </a>
              <a href="https://github.com/XAUAT-iOSClub" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors" title="GitHub">
                <Icon icon="simple-icons:github" class="w-5 h-5" />
              </a>
              <a href="https://www.zhihu.com/people/83-49-80-67" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors" title="知乎">
                <Icon icon="simple-icons:zhihu" class="w-5 h-5" />
              </a>
              <a href="https://juejin.cn/user/939445846031627" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors" title="掘金">
                <Icon icon="simple-icons:juejin" class="w-5 h-5" />
              </a>
            </div>
          </div>
          
          <div>
            <h3 class="text-white font-semibold mb-4">产品</h3>
            <ul class="space-y-2">
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">在线编辑器</a></li>
              <li><a href="https://plan.xauat.site/" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors">学习资源</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">社区论坛</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">API 文档</a></li>
            </ul>
          </div>
          
          <div>
            <h3 class="text-white font-semibold mb-4">组织</h3>
            <ul class="space-y-2">
              <li><a href="https://www.xauat.site/About" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors">关于我们</a></li>
              <li><a href="mailto:iosclubxauat@163.com" class="text-gray-400 hover:text-white transition-colors">联系我们</a></li>
              <li><a href="https://www.xauat.site/SignUp" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white transition-colors">加入我们</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">隐私政策</a></li>
            </ul>
          </div>
          
          <div>
            <h3 class="text-white font-semibold mb-4">支持</h3>
            <ul class="space-y-2">
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">帮助中心</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">常见问题</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">提交反馈</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">状态页面</a></li>
            </ul>
          </div>
        </div>
        
        <div class="mt-12 pt-8 border-t border-gray-800 text-center text-gray-500">
          <p>© {{ new Date().getFullYear() }} Let Coding. 保留所有权利。</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* 自定义滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  dark:bg-gray-800;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
