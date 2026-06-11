<<<<<<< HEAD
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
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

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const highlightedCodeRef = ref<HTMLElement | null>(null);

const languages = [
  { name: 'JavaScript', value: 'javascript', prism: 'javascript', icon: 'vscode-icons:file-type-js-official', color: '#F7DF1E' },
  { name: 'Python', value: 'python', prism: 'python', icon: 'vscode-icons:file-type-python', color: '#3776AB' },
  { name: 'Java', value: 'java', prism: 'java', icon: 'vscode-icons:file-type-java', color: '#ED8B00' },
  { name: 'C++', value: 'cpp', prism: 'cpp', icon: 'vscode-icons:file-type-cpp', color: '#00599C' },
  { name: 'Go', value: 'go', prism: 'go', icon: 'vscode-icons:file-type-go', color: '#00ADD8' },
  { name: 'Rust', value: 'rust', prism: 'rust', icon: 'vscode-icons:file-type-rust', color: '#DEA584' },
  { name: 'Swift', value: 'swift', prism: 'swift', icon: 'vscode-icons:file-type-swift', color: '#FA7343' },
  { name: 'Kotlin', value: 'kotlin', prism: 'kotlin', icon: 'vscode-icons:file-type-kotlin', color: '#7F52FF' },
];

const selectedLanguage = ref('javascript');
const isLanguageMenuOpen = ref(false);
const code = ref(`function greet(name) {
  return \`Hello, ${name}!\`;
}

const message = greet('Let Coding');
console.log(message);`);
const stdin = ref('');
const stdout = ref('');
const stderr = ref('');
const isExecuting = ref(false);

const currentLanguageInfo = computed(() => (
  languages.find((lang) => lang.value === selectedLanguage.value) || languages[0]!
));

const highlightedCode = computed(() => {
  const language = currentLanguageInfo.value.prism;
  const grammar = Prism.languages[language];
  return grammar ? Prism.highlight(code.value, grammar, language) : Prism.util.encode(code.value);
});

const syncEditorScroll = (event: Event) => {
  const target = event.target as HTMLTextAreaElement;
  if (!highlightedCodeRef.value) {
    return;
  }

  highlightedCodeRef.value.scrollTop = target.scrollTop;
  highlightedCodeRef.value.scrollLeft = target.scrollLeft;
};

onMounted(() => {
  const languageParam = route.query.language as string;
  if (languageParam && languages.some((lang) => lang.value === languageParam)) {
    selectedLanguage.value = languageParam;
  }
});

const runCode = async () => {
  if (!code.value.trim()) {
    stderr.value = '代码不能为空\n';
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
        code: code.value,
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

const saveCode = () => {
  const languageMap: Record<string, { ext: string; name: string }> = {
    javascript: { ext: 'js', name: 'script' },
    python: { ext: 'py', name: 'script' },
    java: { ext: 'java', name: 'Main' },
    cpp: { ext: 'cpp', name: 'main' },
    go: { ext: 'go', name: 'main' },
    rust: { ext: 'rs', name: 'main' },
    swift: { ext: 'swift', name: 'main' },
    kotlin: { ext: 'kt', name: 'Main' },
  };

  const langInfo = languageMap[selectedLanguage.value] || { ext: 'txt', name: 'code' };
  const blob = new Blob([code.value], { type: 'text/plain;charset=utf-8' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${langInfo.name}.${langInfo.ext}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
};

const resetCode = () => {
  code.value = '';
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
      selectedLanguage.value = extToLanguage[ext] || selectedLanguage.value;
    };
    reader.readAsText(file);
  };

  fileInput.click();
};
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-16 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <button class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" @click="router.back()">
            <Icon icon="material-symbols:arrow-back" class="w-5 h-5" />
          </button>
          <h1 class="text-2xl font-bold">在线代码编辑器</h1>
        </div>

        <div class="flex items-center gap-3 flex-wrap">
          <div class="relative">
            <button
              class="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors border border-gray-200 dark:border-gray-600"
              :title="currentLanguageInfo.name"
              @click="isLanguageMenuOpen = !isLanguageMenuOpen"
            >
              <Icon :icon="currentLanguageInfo.icon" class="w-4 h-4" :style="{ color: currentLanguageInfo.color }" />
              <span class="hidden sm:inline">{{ currentLanguageInfo.name }}</span>
              <Icon icon="material-symbols:arrow-drop-down" class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': isLanguageMenuOpen }" />
            </button>

            <div
              v-if="isLanguageMenuOpen"
              class="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-900 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50"
            >
              <div class="p-2">
                <button
                  v-for="lang in languages"
                  :key="lang.value"
                  type="button"
                  class="w-full flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
                  @click="selectedLanguage = lang.value; isLanguageMenuOpen = false"
                >
                  <Icon :icon="lang.icon" class="w-4 h-4" :style="{ color: lang.color }" />
                  <span class="text-sm font-medium">{{ lang.name }}</span>
                  <span v-if="selectedLanguage === lang.value" class="ml-auto w-2 h-2 rounded-full bg-blue-500 dark:bg-blue-400"></span>
                </button>
              </div>
            </div>
          </div>

          <button class="tool-button bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800" @click="importCode">
            <Icon icon="material-symbols:upload" class="w-4 h-4" />
            <span class="hidden sm:inline">导入</span>
          </button>
          <button class="tool-button bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800" @click="saveCode">
            <Icon icon="material-symbols:save" class="w-4 h-4" />
            <span class="hidden sm:inline">保存</span>
          </button>
          <button class="tool-button bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600" @click="resetCode">
            <Icon icon="material-symbols:refresh" class="w-4 h-4" />
            <span class="hidden sm:inline">重置</span>
          </button>
          <button
            class="tool-button bg-blue-600 text-white font-medium hover:bg-blue-700 shadow-md disabled:opacity-60"
            :disabled="isExecuting"
            @click="runCode"
          >
            <Icon :icon="isExecuting ? 'material-symbols:hourglass-top' : 'material-symbols:play-arrow'" class="w-4 h-4" :class="{ 'animate-spin': isExecuting }" />
            <span>{{ isExecuting ? '执行中...' : '运行' }}</span>
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="space-y-4">
          <section class="panel">
            <div class="panel-header">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:code" class="w-5 h-5 text-gray-600 dark:text-gray-300" />
                <span class="font-medium">代码</span>
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">{{ code.split('\n').length }} 行</div>
            </div>
            <div class="editor-shell">
              <pre ref="highlightedCodeRef" :class="`editor-highlight language-${currentLanguageInfo.prism}`"><code v-html="highlightedCode"></code></pre>
              <textarea
                v-model="code"
                spellcheck="false"
                class="editor-input"
                placeholder="在此输入你的代码..."
                @scroll="syncEditorScroll"
              ></textarea>
            </div>
          </section>

          <section class="panel">
            <div class="panel-header">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:input" class="w-5 h-5 text-gray-600 dark:text-gray-300" />
                <span class="font-medium">标准输入</span>
              </div>
            </div>
            <textarea v-model="stdin" class="plain-textarea h-[150px]" placeholder="在此输入标准输入..."></textarea>
          </section>
        </div>

        <div class="space-y-4">
          <section class="panel">
            <div class="panel-header">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:output" class="w-5 h-5 text-green-600 dark:text-green-400" />
                <span class="font-medium">标准输出</span>
              </div>
            </div>
            <div class="output-box">
              <pre v-if="stdout" class="text-green-600 dark:text-green-400">{{ stdout }}</pre>
              <div v-else class="text-gray-400 dark:text-gray-500 italic">执行结果将显示在这里...</div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-header">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:error" class="w-5 h-5 text-red-600 dark:text-red-400" />
                <span class="font-medium">错误输出</span>
              </div>
            </div>
            <div class="output-box">
              <pre v-if="stderr" class="text-red-600 dark:text-red-400">{{ stderr }}</pre>
              <div v-else class="text-gray-400 dark:text-gray-500 italic">错误信息将显示在这里...</div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
@import "prismjs/themes/prism.min.css";
</style>

<style scoped>
@reference 'tailwindcss';

.tool-button {
  @apply flex items-center gap-2 px-4 py-2 rounded-lg transition-colors;
}

.panel {
  @apply bg-gray-50 dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border border-gray-200 dark:border-gray-700;
}

.panel-header {
  @apply bg-gray-100 dark:bg-gray-700 px-4 py-2 flex items-center justify-between;
}

.editor-shell {
  @apply relative h-[430px] bg-gray-200 dark:bg-gray-700 overflow-hidden;
}

.editor-highlight,
.editor-input {
  @apply absolute inset-0 m-0 h-full w-full overflow-auto whitespace-pre p-4 font-mono text-sm leading-6;
  tab-size: 2;
}

.editor-highlight {
  @apply pointer-events-none bg-transparent text-gray-900 dark:text-gray-100;
}

.editor-highlight :deep(code) {
  @apply font-mono text-sm leading-6;
}

.editor-input {
  @apply resize-none border-none bg-transparent text-transparent caret-gray-900 dark:caret-white outline-none;
}

.editor-input::selection {
  background: rgba(96, 165, 250, 0.35);
}

.plain-textarea {
  @apply w-full p-4 font-mono text-sm bg-white dark:bg-gray-900 border-none resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 rounded-b-lg;
}

.output-box {
  @apply w-full h-[275px] p-4 font-mono text-sm bg-white dark:bg-gray-900 overflow-auto rounded-b-lg;
}
</style>
=======
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Icon } from '@iconify/vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

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

// 当前选择的语言
const selectedLanguage = ref('javascript');
// 语言菜单显示状态
const isLanguageMenuOpen = ref(false);

// 代码编辑器内容
const code = ref(`function greet(name) {
  return \`Hello, ${name}!\`;
}

const message = greet('Let Coding');
console.log(message);`);

// 标准输入
const stdin = ref('');

// 执行结果
const stdout = ref('');
const stderr = ref('');
const isExecuting = ref(false);

// 计算属性：获取当前语言的图标和名称
const currentLanguageInfo = computed(() => {
  return languages.find(lang => lang.value === selectedLanguage.value) || languages[0];
});

// 处理URL参数，设置默认语言
onMounted(() => {
  const languageParam = route.query.language as string;
  if (languageParam) {
    const isValidLanguage = languages.some(lang => lang.value === languageParam);
    if (isValidLanguage) {
      selectedLanguage.value = languageParam;
    }
  }
});

// 运行代码
const runCode = async () => {
  isExecuting.value = true;
  stdout.value = '';
  stderr.value = '';
  
  try {
    // 这里需要调用后端 API 来执行代码
    // 暂时使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    if (selectedLanguage.value === 'javascript') {
      stdout.value = 'Hello, Let Coding!\n';
    } else if (selectedLanguage.value === 'python') {
      stdout.value = 'Hello, Let Coding!\n';
    } else {
      stdout.value = `Hello, Let Coding! (${selectedLanguage.value})\n`;
    }
  } catch (error) {
    stderr.value = `执行错误: ${error instanceof Error ? error.message : '未知错误'}\n`;
  } finally {
    isExecuting.value = false;
  }
};

// 保存代码到用户选择路径
const saveCode = () => {
  try {
    // 根据语言生成文件名和扩展名
    const languageMap: { [key: string]: { ext: string; name: string } } = {
      javascript: { ext: 'js', name: 'script' },
      python: { ext: 'py', name: 'script' },
      java: { ext: 'java', name: 'Main' },
      cpp: { ext: 'cpp', name: 'main' },
      go: { ext: 'go', name: 'main' },
      rust: { ext: 'rs', name: 'main' },
      swift: { ext: 'swift', name: 'main' },
      kotlin: { ext: 'kt', name: 'Main' }
    };
    
    const langInfo = languageMap[selectedLanguage.value] || { ext: 'txt', name: 'code' };
    const fileName = `${langInfo.name}.${langInfo.ext}`;
    
    // 创建Blob对象
    const blob = new Blob([code.value], { type: 'text/plain;charset=utf-8' });
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    
    // 触发下载
    document.body.appendChild(link);
    link.click();
    
    // 清理
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    
    // 显示成功提示
    alert('代码已成功保存！');
  } catch (error) {
    console.error('保存代码失败:', error);
    alert(`保存代码失败: ${error instanceof Error ? error.message : '未知错误'}`);
  }
};

// 重置代码
const resetCode = () => {
  code.value = '';
  stdin.value = '';
  stdout.value = '';
  stderr.value = '';
};

// 导入代码
const importCode = () => {
  // 创建隐藏的文件输入框
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.js,.py,.java,.cpp,.go,.rs,.swift,.kt,.txt';
  
  // 文件选择事件处理
  fileInput.onchange = (e) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) {
      const reader = new FileReader();
      
      // 文件读取成功事件
      reader.onload = (event) => {
        const content = event.target?.result as string;
        code.value = content;
        
        // 根据文件扩展名自动识别语言
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        const extToLanguage: { [key: string]: string } = {
          js: 'javascript',
          py: 'python',
          java: 'java',
          cpp: 'cpp',
          go: 'go',
          rs: 'rust',
          swift: 'swift',
          kt: 'kotlin'
        };
        
        const detectedLanguage = extToLanguage[ext] || 'javascript';
        selectedLanguage.value = detectedLanguage;
        
        // 显示成功提示
        alert('代码已成功导入！');
      };
      
      // 文件读取失败事件
      reader.onerror = () => {
        alert('读取文件失败！');
      };
      
      // 开始读取文件
      reader.readAsText(file);
    }
  };
  
  // 触发文件选择对话框
  fileInput.click();
};
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <!-- 页面标题栏 -->
    <div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-16 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <button 
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" 
            @click="router.back()"
          >
            <Icon icon="material-symbols:arrow-back" class="w-5 h-5" />
          </button>
          <h1 class="text-2xl font-bold">在线代码编辑器</h1>
        </div>
        
        <div class="flex items-center gap-3 flex-wrap">
          <!-- 语言选择 -->
          <div class="relative group">
            <button 
              class="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors border border-gray-200 dark:border-gray-600"
              :title="currentLanguageInfo?.name || ''"
              @click="isLanguageMenuOpen = !isLanguageMenuOpen"
            >
              <Icon :icon="currentLanguageInfo?.icon || ''" class="w-4 h-4" :style="{ color: currentLanguageInfo?.color || '#6B7280' }" />
              <span class="hidden sm:inline">{{ currentLanguageInfo?.name || '' }}</span>
              <Icon 
                icon="material-symbols:arrow-drop-down" 
                class="w-4 h-4 transition-transform duration-200"
                :class="{ 'rotate-180': isLanguageMenuOpen }"
              />
            </button>
            
            <!-- 语言选择折叠菜单 -->
            <div 
              v-if="isLanguageMenuOpen" 
              class="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-900 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50 transition-all duration-200"
            >
              <div class="p-2">
                <div 
                  v-for="lang in languages" 
                  :key="lang.value"
                  class="flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  @click="selectedLanguage = lang.value; isLanguageMenuOpen = false"
                >
                  <Icon :icon="lang.icon" class="w-4 h-4" :style="{ color: lang.color }" />
                  <span class="text-sm font-medium">{{ lang.name }}</span>
                  <div 
                    v-if="selectedLanguage === lang.value"
                    class="ml-auto w-2 h-2 rounded-full bg-blue-500 dark:bg-blue-400"
                  ></div>
                </div>
              </div>
            </div>
            
            <!-- 点击外部关闭菜单 -->
            <div 
              v-if="isLanguageMenuOpen"
              class="fixed inset-0 z-40"
              @click="isLanguageMenuOpen = false"
            ></div>
          </div>
          
          <!-- 导入按钮 -->
          <button 
            class="flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
            @click="importCode"
          >
            <Icon icon="material-symbols:upload" class="w-4 h-4" />
            <span class="hidden sm:inline">导入</span>
          </button>
          
          <!-- 保存按钮 -->
          <button 
            class="flex items-center gap-2 px-4 py-2 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
            @click="saveCode"
          >
            <Icon icon="material-symbols:save" class="w-4 h-4" />
            <span class="hidden sm:inline">保存</span>
          </button>
          
          <!-- 重置按钮 -->
          <button 
            class="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            @click="resetCode"
          >
            <Icon icon="material-symbols:refresh" class="w-4 h-4" />
            <span class="hidden sm:inline">重置</span>
          </button>
          
          <!-- 运行按钮 -->
          <button 
            class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors shadow-md"
            @click="runCode"
            :disabled="isExecuting"
          >
            <Icon 
              :icon="isExecuting ? 'material-symbols:hourglass-top' : 'material-symbols:play-arrow'" 
              class="w-4 h-4" 
              :class="{ 'animate-spin': isExecuting }"
            />
            <span>{{ isExecuting ? '执行中...' : '运行' }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 编辑器主体 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 代码输入区域 -->
        <div class="space-y-4">
          <!-- 代码编辑器 -->
          <div class="bg-gray-50 dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
            <div class="bg-gray-100 dark:bg-gray-700 px-4 py-2 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:code" class="w-5 h-5 text-gray-600 dark:text-gray-300" />
                <span class="font-medium">代码</span>
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                {{ code.split('\n').length }} 行
              </div>
            </div>
            <textarea 
              v-model="code" 
              class="w-full h-[400px] p-4 font-mono text-sm bg-white dark:bg-gray-900 border-none resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 rounded-b-xl"
              placeholder="在此输入你的代码..."
            ></textarea>
          </div>
          
          <!-- 标准输入 -->
          <div class="bg-gray-50 dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
            <div class="bg-gray-100 dark:bg-gray-700 px-4 py-2 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:input" class="w-5 h-5 text-gray-600 dark:text-gray-300" />
                <span class="font-medium">标准输入</span>
              </div>
            </div>
            <textarea 
              v-model="stdin" 
              class="w-full h-[150px] p-4 font-mono text-sm bg-white dark:bg-gray-900 border-none resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 rounded-b-xl"
              placeholder="在此输入标准输入..."
            ></textarea>
          </div>
        </div>
        
        <!-- 结果输出区域 -->
        <div class="space-y-4">
          <!-- 标准输出 -->
          <div class="bg-gray-50 dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
            <div class="bg-gray-100 dark:bg-gray-700 px-4 py-2 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:output" class="w-5 h-5 text-green-600 dark:text-green-400" />
                <span class="font-medium">标准输出</span>
              </div>
            </div>
            <div 
              class="w-full h-[275px] p-4 font-mono text-sm bg-white dark:bg-gray-900 border-none resize-none overflow-auto rounded-b-xl"
            >
              <pre v-if="stdout" class="text-green-600 dark:text-green-400">{{ stdout }}</pre>
              <div v-else class="text-gray-400 dark:text-gray-500 italic">执行结果将显示在这里...</div>
            </div>
          </div>
          
          <!-- 错误输出 -->
          <div class="bg-gray-50 dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
            <div class="bg-gray-100 dark:bg-gray-700 px-4 py-2 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Icon icon="material-symbols:error" class="w-5 h-5 text-red-600 dark:text-red-400" />
                <span class="font-medium">错误输出</span>
              </div>
            </div>
            <div 
              class="w-full h-[275px] p-4 font-mono text-sm bg-white dark:bg-gray-900 border-none resize-none overflow-auto rounded-b-xl"
            >
              <pre v-if="stderr" class="text-red-600 dark:text-red-400">{{ stderr }}</pre>
              <div v-else class="text-gray-400 dark:text-gray-500 italic">错误信息将显示在这里...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
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
