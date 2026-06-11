<script setup lang="ts">
import {nextTick, ref, watch, computed, onMounted, withDefaults} from "vue";
import {Icon} from "@iconify/vue";

import MarkdownIt from 'markdown-it'
import markdownitFootnote from 'markdown-it-footnote'
import markdownitTaskList from 'markdown-it-task-lists'
import markdownitAttrs from 'markdown-it-attrs'
import mdExpandTabs from 'markdown-it-expand-tabs'
import mdSup from 'markdown-it-sup'
import mdSub from 'markdown-it-sub'
import mdMark from 'markdown-it-mark'
import markdownItAnchor from 'markdown-it-anchor'
import markdownItContainer from 'markdown-it-container'

import markdownItMermaid from '@jsonlee_12138/markdown-it-mermaid';
import Prism from "prismjs"
import "prismjs/components/prism-bash"
import "prismjs/components/prism-c"
import "prismjs/components/prism-cpp"
import "prismjs/components/prism-css"
import "prismjs/components/prism-go"
import "prismjs/components/prism-java"
import "prismjs/components/prism-json"
import "prismjs/components/prism-python"
import "prismjs/components/prism-rust"
import "prismjs/components/prism-typescript"
import {useRoute} from "vue-router";

interface Content {
  title: string
  date: string
  watch: number
  content: string,
  identity?: string
}

const props = withDefaults(defineProps<{
  content?: Content
  showNav?: boolean
}>(), {
  showNav: true
})

const route = useRoute();

// 存储标题结构
const headings = ref<Array<{ id: string; text: string; level: number; href: string; children: any[] }>>([])

// 创建 markdown-it 实例
const normalizeLanguage = (language: string) => {
  const aliases: Record<string, string> = {
    js: 'javascript',
    ts: 'typescript',
    py: 'python',
    sh: 'bash',
    shell: 'bash',
    cplusplus: 'cpp',
  }

  const key = language.trim().toLowerCase()
  return aliases[key] || key
}

const escapeHtml = (value: string) => value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (code: string, language: string): string => {
    const normalizedLanguage = normalizeLanguage(language || '')
    const grammar = Prism.languages[normalizedLanguage]

    if (!grammar) {
      return `<pre class="language-text"><code>${escapeHtml(code)}</code></pre>`
    }

    const highlighted = Prism.highlight(code, grammar, normalizedLanguage)
    return `<pre class="language-${normalizedLanguage}"><code class="language-${normalizedLanguage}">${highlighted}</code></pre>`
  }
})

// 使用 anchor 插件
md.use(markdownItAnchor, {
  permalink: markdownItAnchor.permalink.ariaHidden({
    placement: 'before',
    space: true,
    class: 'apple-link-no-icon',
    renderHref: (href: string) => `${route.path}#${href}`,
  })
})
md.use(markdownitFootnote)
md.use(markdownitTaskList, {label: false, labelAfter: false})
md.use(markdownitAttrs, {
  allowedAttributes: ['id', 'class', 'target', 'src']
})

md.use(mdExpandTabs)
    .use(mdSup)
    .use(mdSub)
    .use(mdMark)
    .use(markdownItMermaid({delay: 100}))

// 配置自定义容器
const containerOptions = [
  {
    name: 'warning',
    className: 'warning'
  },
  {
    name: 'danger',
    className: 'danger'
  },
  {
    name: 'tip',
    className: 'tip'
  }
]

containerOptions.forEach(({name, className}) => {
  md.use(markdownItContainer, name, {
    validate: (params: string) => {
      return params.trim().match(new RegExp(`^${name}\\s+(.*)$`))
    },
    render: (tokens: any[], idx: number) => {
      const m = tokens[idx].info.trim().match(new RegExp(`^${name}\\s+(.*)$`))
      if (tokens[idx].nesting === 1) {
        return `<div class="${className} custom-block"><p class="custom-block-title">${md.utils.escapeHtml(m[1])}</p>\n`
      } else {
        return '</div>\n'
      }
    }
  })
})

// 解析标题生成导航数据
const extractHeadings = (markdown: string) => {
  const tokens = md.parse(markdown, {})
  const extractedHeadings: Array<{ id: string; text: string; level: number; href: string; children: any[] }> = []

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i]!

    if (token && token.type === 'heading_open') {
      const level = parseInt(token.tag.slice(1)) // h1 -> 1, h2 -> 2
      const nextToken = tokens[i + 1]

      if (nextToken && nextToken.type === 'inline') {
        const text = nextToken.content
        // 生成 ID（与 markdown-it-anchor 保持一致）
        const id = text.toLowerCase()
            .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
            .replace(/^-+|-+$/g, '')

        extractedHeadings.push({
          id,
          text,
          level,
          href: `#${id}`,
          children: []
        })
      }
    }
  }

  return extractedHeadings
}

// 构建层级结构的标题树
const buildHeadingTree = (flatHeadings: Array<{ id: string; text: string; level: number; href: string }>) => {
  const tree: Array<{ id: string; text: string; level: number; href: string; children: any[] }> = []
  const stack: Array<{ id: string; text: string; level: number; href: string; children: any[] }> = []

  flatHeadings.forEach(heading => {
    const item = {...heading, children: []}

    // 找到合适的父级
<<<<<<< HEAD
    while (stack.length > 0 && stack[stack.length - 1]!.level >= heading.level) {
=======
    while (stack.length > 0) {
      const lastItem = stack[stack.length - 1]
      if (lastItem && lastItem.level < heading.level) {
        break
      }
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
      stack.pop()
    }

    if (stack.length === 0) {
      tree.push(item)
    } else {
<<<<<<< HEAD
      stack[stack.length - 1]!.children.push(item)
=======
      const lastItem = stack[stack.length - 1]
      if (lastItem) {
        lastItem.children.push(item)
      }
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
    }

    stack.push(item)
  })

  return tree
}

// 渲染 markdown 的函数
const render = async (markdown: string) => {
  // 提取标题
  const extractedHeadings = extractHeadings(markdown)
  headings.value = buildHeadingTree(extractedHeadings)

  const html = md.render(markdown)

  // 等待 DOM 更新
  await nextTick()

  // 初始化图表
  setTimeout(() => {
    // 代码高亮
    Prism.highlightAll()
  }, 50)

  return html
}

// 使用 computed 代替 ref + watch
const html = ref('')

watch(() => props.content, async (newValue) => {
      if (!md || !newValue) return '';
      html.value = await render(newValue.content);
    }, {immediate: true}
)

// 递归渲染导航链接
const renderAnchorLinks = (items: Array<{
  id: string;
  text: string;
  level: number;
  href: string;
  children: any[]
}>, depth = 0): Array<{ title: string; href: string; children?: Array<{ title: string; href: string }> }> => {
  return items.map((item: any) => ({
    title: item.text,
    href: item.href,
    children: item.children?.length > 0 ? renderAnchorLinks(item.children, depth + 1) : undefined
  }))
}

// 计算导航数据
const anchorLinks = computed(() => renderAnchorLinks(headings.value))
const date = computed(() => props.content?.date ? new Date(props.content.date).toLocaleDateString('zh-CN') : '')

// 根据权限值获取显示标签
const getIdentityLabel = computed(() => {
  const options = [
    {label: '所有人', value: 'Member'},
    {label: '部员', value: 'Department'},
    {label: '部长', value: 'Minister'},
    {label: '社长', value: 'President'},
    {label: '创始人', value: 'Founder'}
  ];
  const option = options.find(item => item.value === props.content?.identity);
  return option ? option.label : '未知';
});

// 根据权限值获取标签样式
const getIdentityClass = (identity: string) => {
  switch (identity) {
    case 'Member':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100';
    case 'Department':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100';
    case 'Minister':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100';
    case 'President':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100';
    case 'Founder':
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100';
  }
};

// 添加处理锚点点击的方法
const handleAnchorClick = (event: Event, href: string) => {
  event.preventDefault();
  const targetId = href.substring(1).toLowerCase(); // 移除 # 前缀

  // 对 targetId 进行 URL 编码
  const encodedTargetId = encodeURIComponent(targetId);

  console.log(targetId)

  // 如果仍然找不到，尝试通过属性选择器查找
  const targetElement = document.querySelector(`[id="${encodedTargetId}"]`);

  if (targetElement) {
    // 平滑滚动到目标元素
    targetElement.scrollIntoView({behavior: 'smooth'});
  }
};

onMounted(() => {
  // 添加滚动监听器以高亮当前活动的锚点
  const handleScroll = () => {
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6')
    let activeHeadingId = ''

    for (let i = headings.length - 1; i >= 0; i--) {
      const heading = headings[i]
<<<<<<< HEAD
      if (!heading) {
        continue
      }
      const rect = heading.getBoundingClientRect()
      if (rect.top <= 100) {
        activeHeadingId = heading.id
        break
=======
      if (heading) {
        const rect = heading.getBoundingClientRect()
        if (rect.top <= 100) {
          activeHeadingId = heading.id
          break
        }
>>>>>>> 53decede0e914f80980872622980c6cfd01c3018
      }
    }

    // 移除所有活动类
    document.querySelectorAll('.toc-link').forEach(link => {
      link.classList.remove('active')
    })

    // 为当前活动标题添加活动类
    if (activeHeadingId) {
      const activeLink = document.querySelector(`.toc-link[href="#${activeHeadingId}"]`)
      if (activeLink) {
        activeLink.classList.add('active')
      }
    }
  }

  window.addEventListener('scroll', handleScroll)
})
</script>

<template>
  <div v-if="content" class="flex flex-col md:flex-row">
    <!-- 文章内容区 -->
    <div class="w-full p-4 md:p-8" :class="[showNav && headings.length > 0 ? 'md:w-4/5' : 'md:w-full']">
      <article class="prose prose-gray max-w-none dark:prose-invert">
        <!-- 文章头部 -->
        <header class="mb-8 border-b border-gray-200 pb-6 dark:border-gray-700">
          <h1 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
            {{ content.title }}
          </h1>
          <div class="flex items-center gap-4 text-gray-500 dark:text-gray-400 text-sm">
            <time class="flex items-center gap-1">
              <Icon icon="mdi:calendar" width="16" height="16"/>
              {{ date }}
            </time>
            <span class="flex items-center gap-1">
              <Icon icon="mdi:eye" width="16" height="16"/>
              {{ content.watch }} 次阅读
            </span>
            <span v-if="content.identity" class="flex items-center gap-1" :class="getIdentityClass(content.identity)">
              {{ getIdentityLabel }}
            </span>
          </div>
        </header>

        <!-- 文章内容 -->
        <div class="markdown-content">
          <div v-html="html"></div>
        </div>
      </article>
    </div>

    <!-- 目录导航 -->
    <div v-if="showNav && headings.length > 0" class="hidden md:block w-1/5 sticky top-8 h-fit self-start p-4">
      <nav class="toc-nav bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
        <h3 class="text-sm font-semibold mb-3 text-gray-900 dark:text-white">
          目录
        </h3>
        <ul class="space-y-1">
          <li
              v-for="link in anchorLinks"
              :key="link.href"
              class="toc-item"
          >
            <div
                @click="handleAnchorClick($event, link.href)"
                class="toc-link block py-1 text-sm link"
            >
              {{ link.title }}
            </div>

            <!-- 子目录 -->
            <ul v-if="link.children && link.children.length > 0" class="ml-3 mt-1 space-y-1">
              <li
                  v-for="subLink in link.children"
                  :key="subLink.href"
              >
                <div
                    @click="handleAnchorClick($event, subLink.href)"
                    class="toc-link block py-1 text-xs text-blue-500"
                >
                  {{ subLink.title }}
                </div>
              </li>
            </ul>
          </li>
        </ul>
      </nav>
    </div>
  </div>

  <!-- 空状态 -->
  <div v-else class="flex flex-col items-center justify-center h-full p-8 text-center">
    <div
        class="bg-gray-200 dark:bg-gray-700 border-2 border-dashed rounded-xl w-16 h-16 flex items-center justify-center mb-4">
      <Icon icon="mdi:file-document-outline" width="32" height="32" class="text-gray-500 dark:text-gray-400"/>
    </div>
    <p class="text-gray-500 dark:text-gray-400 text-lg">
      请选择一篇文章阅读
    </p>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';
@import "prismjs/themes/prism-tomorrow.min.css";

/* 自定义块样式 */
:deep(.custom-block) {
  @apply rounded-lg p-4 my-4;
}

:deep(.custom-block-title) {
  @apply font-bold text-base mb-2;
}

.markdown-content :deep(.warning) {
  @apply bg-amber-100 ;
}

.dark .markdown-content :deep(.warning) {
  @apply bg-amber-900;
}

.markdown-content :deep(.danger) {
  @apply bg-red-100 ;
}

.dark .markdown-content :deep( .danger) {
  @apply bg-red-900;
}

.markdown-content :deep(.tip) {
  @apply bg-blue-50;
}

.dark .markdown-content :deep(.tip) {
  @apply bg-blue-900;
}

.toc-link {
  @apply text-sky-700 cursor-pointer;
}

.toc-link:hover {
  @apply text-cyan-800;
}

.dark .toc-link {
  @apply text-sky-300;
}

.dark .toc-link:hover {
  @apply text-cyan-400;
}

/* Markdown 内容样式 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  @apply font-semibold;
}

.markdown-content :deep(h1) {
  @apply text-3xl mt-8 mb-4;
}

.markdown-content :deep(h2) {
  @apply text-2xl mt-6 mb-3;
}

.markdown-content :deep(h3) {
  @apply text-xl mt-4 mb-2;
}

.markdown-content :deep(p) {
  @apply mb-4 leading-relaxed;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6),
.markdown-content :deep(p) {
  @apply text-gray-900;
}

.dark .markdown-content :deep(h1),
.dark .markdown-content :deep(h2),
.dark .markdown-content :deep(h3),
.dark .markdown-content :deep(h4),
.dark .markdown-content :deep(h5),
.dark .markdown-content :deep(h6),
.dark .markdown-content :deep(p) {
  @apply text-white;
}

.markdown-content :deep(a) {
  @apply underline;
}

.markdown-content :deep(a) {
  @apply text-blue-600 hover:text-blue-800;
}

.dark .markdown-content :deep(a) {
  @apply text-blue-400 hover:text-blue-300;
}

.markdown-content :deep(strong) {
  @apply font-semibold;
}

.markdown-content :deep(em) {
  @apply italic;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  @apply pl-6 mb-4;
}

.markdown-content :deep(li) {
  @apply mb-1;
}

.markdown-content :deep(ul li) {
  @apply list-disc;
}

.markdown-content :deep(ol li) {
  @apply list-decimal;
}

.markdown-content :deep(blockquote) {
  @apply border-l-4 pl-4 ml-2 py-1 my-4;
}

.markdown-content :deep(blockquote) {
  @apply border-gray-300 text-gray-600;
}

.dark .markdown-content :deep(blockquote) {
  @apply border-gray-600 text-gray-400;
}

.markdown-content :deep(code) {
  @apply px-1.5 py-0.5 rounded text-sm font-mono;
}

.markdown-content :deep(code) {
  @apply bg-gray-100;
}

.dark .markdown-content :deep(code) {
  @apply bg-gray-800;
}

.markdown-content :deep(pre) {
  @apply rounded-lg p-4 my-4 overflow-x-auto;
}

.markdown-content :deep(pre) {
  @apply bg-gray-800;
}

.dark .markdown-content :deep(pre) {
  @apply bg-gray-900;
}

.markdown-content :deep(pre code) {
  @apply bg-transparent p-0 rounded-none;
}

.markdown-content :deep(table) {
  @apply min-w-full border-collapse my-4;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  @apply px-4 py-2;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  @apply border border-gray-300;
}

.dark .markdown-content :deep(th),
.dark .markdown-content :deep(td) {
  @apply border border-gray-700;
}

.markdown-content :deep(th) {
  @apply font-semibold;
}

.markdown-content :deep(th) {
  @apply bg-gray-100;
}

.dark .markdown-content :deep(th) {
  @apply bg-gray-800;
}

.markdown-content :deep(img) {
  @apply rounded-lg mx-auto my-4;
}

.markdown-content :deep(hr) {
  @apply my-8;
}

.markdown-content :deep(hr) {
  @apply border-gray-300;
}

.dark .markdown-content :deep(hr) {
  @apply border-gray-700;
}
</style>
