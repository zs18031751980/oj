<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch, withDefaults } from 'vue';
import { Icon } from '@iconify/vue';
import { useRoute } from 'vue-router';
import MarkdownIt from 'markdown-it';
import markdownitFootnote from 'markdown-it-footnote';
import markdownitTaskList from 'markdown-it-task-lists';
import markdownitAttrs from 'markdown-it-attrs';
import mdExpandTabs from 'markdown-it-expand-tabs';
import mdSup from 'markdown-it-sup';
import mdMark from 'markdown-it-mark';
import markdownItAnchor from 'markdown-it-anchor';
import markdownItContainer from 'markdown-it-container';
import markdownItMermaid from '@jsonlee_12138/markdown-it-mermaid';
import Prism from 'prismjs';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-markup-templating';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-typescript';
import 'prismjs/themes/prism-tomorrow.min.css';

interface Content {
  title?: string;
  date?: string;
  watch?: number;
  content: string;
}

interface HeadingItem {
  id: string;
  text: string;
  level: number;
  href: string;
  children: HeadingItem[];
}

const props = withDefaults(defineProps<{
  content?: Content;
  source?: string;
  showNav?: boolean;
  showHeadingLinks?: boolean;
  baseDir?: string;
}>(), {
  showNav: true,
  showHeadingLinks: true,
  baseDir: '',
});

const emit = defineEmits<{
  (e: 'navigate', file: string): void;
}>();

const route = useRoute();
const headings = ref<HeadingItem[]>([]);
const html = ref('');
const readingProgress = ref(0);
const activeHeadingId = ref('');
const markdownBody = ref<HTMLElement | null>(null);
const copiedIndex = ref<number | null>(null);

const normalizeLanguage = (language: string) => {
  const aliases: Record<string, string> = {
    js: 'javascript',
    ts: 'typescript',
    py: 'python',
    sh: 'bash',
    shell: 'bash',
    cplusplus: 'cpp',
    html: 'markup',
    xml: 'markup',
    svg: 'markup',
    vue: 'markup',
    svelte: 'markup',
    template: 'markup',
    jsx: 'javascript',
    mjs: 'javascript',
    cjs: 'javascript',
    script: 'javascript',
  };

  const key = language.trim().toLowerCase();
  return aliases[key] || key;
};

const highlightSafe = (code: string, language: string, fallback: string = 'javascript'): string => {
  const grammar = Prism.languages[language] || Prism.languages[fallback];
  if (!grammar) return escapeHtml(code);
  return Prism.highlight(code, grammar, language);
};

const escapeHtml = (value: string) => value
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: false,
  highlight: (code: string, language: string): string => {
    const lang = (language || '').trim().toLowerCase();
    let targetLang = normalizeLanguage(lang);
    if (!targetLang) {
      if (code.includes('<script') || code.includes('<template') || code.includes('<style')) {
        targetLang = 'markup';
      } else {
        targetLang = 'javascript';
      }
    }

    const highlighted = highlightSafe(code, targetLang);
    const escapedCode = code.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    return `<div class="code-block-wrapper" data-lang="${targetLang}"><div class="code-block-header"><span class="code-lang-label">${targetLang}</span><button class="code-copy-btn" onclick="window.__copyCode(this)" data-code="${escapedCode}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg> 复制</button></div><pre class="language-${targetLang}"><code class="language-${targetLang}">${highlighted}</code></pre></div>`;
  },
});

md.use(markdownItAnchor, {
  permalink: markdownItAnchor.permalink.ariaHidden({
    placement: 'before',
    space: true,
    class: 'heading-anchor',
    renderHref: (href: string) => `${route.path}#${href}`,
  }),
});
md.use(markdownitFootnote);
md.use(markdownitTaskList, { label: false, labelAfter: false });
md.use(markdownitAttrs, {
  allowedAttributes: ['id', 'class', 'target', 'src', 'alt', 'title'],
});
md.use(mdExpandTabs)
  .use(mdSup)
  .use(mdMark)
  .use(markdownItMermaid({ delay: 100 }));

const resolveMdLink = (href: string, baseDir: string): string | null => {
  if (!href || href.startsWith('#') || href.startsWith('http://') || href.startsWith('https://') || href.startsWith('mailto:') || href.startsWith('javascript:')) {
    return null;
  }
  const cleanHref = (href.split('?')[0] || '').split('#')[0] || '';
  if (!cleanHref.endsWith('.md')) {
    return null;
  }
  const resolved = cleanHref.startsWith('/')
    ? cleanHref.replace(/^\//, '')
    : `${baseDir}${baseDir && !baseDir.endsWith('/') ? '/' : ''}${cleanHref}`;
  return resolved;
};

md.core.ruler.push('resolve_md_links', (state) => {
  const baseDir = (state.env as any)?.baseDir || '';
  if (!baseDir) return;
  const tokens = state.tokens;
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    if (!token || token.type !== 'inline') continue;
    const inlineTokens = token.children || [];
    for (let j = 0; j < inlineTokens.length; j++) {
      const inlineToken = inlineTokens[j];
      if (!inlineToken || inlineToken.type !== 'link_open') continue;
      const hrefAttr = inlineToken.attrGet('href');
      if (!hrefAttr) continue;
      const resolved = resolveMdLink(hrefAttr, baseDir);
      if (resolved) {
        inlineToken.attrSet('data-md-link', resolved);
      }
    }
  }
});

/** 重写图片路径：将相对路径转为同源静态资源 URL */
md.core.ruler.push('resolve_images', (state) => {
  const baseDir = (state.env as any)?.baseDir || '';
  const tokens = state.tokens;
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    if (!token || token.type !== 'inline') continue;
    const inlineTokens = token.children || [];
    for (let j = 0; j < inlineTokens.length; j++) {
      const inlineToken = inlineTokens[j];
      if (!inlineToken || inlineToken.type !== 'image') continue;
      const src = inlineToken.attrGet('src');
      if (!src) continue;
      // 跳过已经是绝对 URL 的图片
      if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('data:')) continue;
      // 解析相对路径
      const cleanSrc = (src.split('?')[0] || '').split('#')[0] || '';
      let resolvedPath: string;
      if (cleanSrc.startsWith('/')) {
        resolvedPath = cleanSrc.replace(/^\//, '');
      } else if (baseDir) {
        resolvedPath = `${baseDir}/${cleanSrc}`;
      } else {
        resolvedPath = cleanSrc || '';
      }
      // 规范化路径（处理 ../）
      const parts = resolvedPath.split('/');
      const normalized: string[] = [];
      for (const p of parts) {
        if (p === '..') { normalized.pop(); }
        else if (p !== '.' && p !== '') { normalized.push(p); }
      }
      const finalPath = normalized.join('/');
      // 设置为同源静态资源 URL（学习资料由前端 public/learn 托管）
      inlineToken.attrSet('src', `/learn/${finalPath}`);
    }
  }
});

[
  { name: 'warning', className: 'warning' },
  { name: 'danger', className: 'danger' },
  { name: 'tip', className: 'tip' },
].forEach(({ name, className }) => {
  md.use(markdownItContainer, name, {
    validate: (params: string) => Boolean(params.trim().match(new RegExp(`^${name}\\s+(.*)$`))),
    render: (tokens: any[], idx: number) => {
      const match = tokens[idx].info.trim().match(new RegExp(`^${name}\\s+(.*)$`));
      if (tokens[idx].nesting === 1) {
        return `<div class="${className} custom-block"><p class="custom-block-title">${md.utils.escapeHtml(match?.[1] || '')}</p>\n`;
      }

      return '</div>\n';
    },
  });
});

const extractHeadings = (markdown: string) => {
  const tokens = md.parse(markdown, {});
  const extractedHeadings: HeadingItem[] = [];

  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    if (token?.type !== 'heading_open') {
      continue;
    }

    const level = Number.parseInt(token.tag.slice(1), 10);
    const nextToken = tokens[i + 1];

    if (nextToken?.type === 'inline') {
      const text = nextToken.content;
      const id = text.toLowerCase()
        .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
        .replace(/^-+|-+$/g, '');

      extractedHeadings.push({
        id,
        text,
        level,
        href: `#${id}`,
        children: [],
      });
    }
  }

  return extractedHeadings;
};

const buildHeadingTree = (flatHeadings: HeadingItem[]) => {
  const tree: HeadingItem[] = [];
  const stack: HeadingItem[] = [];

  flatHeadings.forEach((heading) => {
    const item = { ...heading, children: [] };

    while (stack.length > 0) {
      const lastItem = stack[stack.length - 1];
      if (!lastItem || lastItem.level < heading.level) {
        break;
      }

      stack.pop();
    }

    if (stack.length === 0) {
      tree.push(item);
    } else {
      const parent = stack[stack.length - 1];
      if (parent) {
        parent.children.push(item);
      } else {
        tree.push(item);
      }
    }

    stack.push(item);
  });

  return tree;
};

const render = async (markdown: string) => {
  headings.value = buildHeadingTree(extractHeadings(markdown));
  const renderedHtml = md.render(markdown, { baseDir: props.baseDir });
  const finalHtml = props.showHeadingLinks
    ? renderedHtml
    : renderedHtml.replace(/<a\b[^>]*class="[^"]*heading-anchor[^"]*"[^>]*>[\s\S]*?<\/a>/g, '');
  await nextTick();
  setTimeout(() => {
    Prism.highlightAll();
    processCodeBlocks();
  }, 50);
  return finalHtml;
};

const processCodeBlocks = () => {
  if (!markdownBody.value) return;
  const blocks = markdownBody.value.querySelectorAll('.code-block-wrapper');
  blocks.forEach((block) => {
    const btn = block.querySelector('.code-copy-btn');
    if (btn && !btn.getAttribute('data-bound')) {
      btn.setAttribute('data-bound', 'true');
    }
  });
};

const copyCode = async (code: string, index?: number) => {
  try {
    await navigator.clipboard.writeText(code);
    if (typeof index === 'number') {
      copiedIndex.value = index;
      setTimeout(() => { copiedIndex.value = null; }, 2000);
    }
  } catch {
    const textarea = document.createElement('textarea');
    textarea.value = code;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    if (typeof index === 'number') {
      copiedIndex.value = index;
      setTimeout(() => { copiedIndex.value = null; }, 2000);
    }
  }
};

watch(
  () => [props.content, props.source, props.showHeadingLinks] as const,
  async ([content, source]) => {
    const md = content?.content || source || '';
    html.value = md ? await render(md) : '';
  },
  { immediate: true },
);

const anchorLinks = computed(() => headings.value);
const date = computed(() => (props.content?.date ? new Date(props.content.date).toLocaleDateString('zh-CN') : ''));
const hasHeaderMeta = computed(() => Boolean(props.content?.title || props.content?.date || props.content?.watch));

const handleAnchorClick = (event: Event, href: string) => {
  event.preventDefault();
  const targetElement = document.querySelector(href);

  if (targetElement) {
    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

let scrollTicking = false;

const handleMarkdownClick = (event: Event) => {
  const target = event.target as HTMLElement;
  const anchor = target.closest('a');
  if (!anchor) return;
  const mdLink = anchor.getAttribute('data-md-link');
  if (mdLink) {
    event.preventDefault();
    emit('navigate', mdLink);
  }
};

const handleScroll = () => {
  if (scrollTicking) return;
  scrollTicking = true;

  requestAnimationFrame(() => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    readingProgress.value = docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) : 0;

    const articleHeadings = document.querySelectorAll('.markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4, .markdown-content h5, .markdown-content h6');
    let foundId = '';

    for (let i = articleHeadings.length - 1; i >= 0; i -= 1) {
      const heading = articleHeadings[i];
      if (heading && heading.getBoundingClientRect().top <= 120) {
        foundId = heading.id;
        break;
      }
    }

    activeHeadingId.value = foundId;
    scrollTicking = false;
  });
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true });
  (window as any).__copyCode = (btn: HTMLElement) => {
    const code = btn.getAttribute('data-code') || '';
    const decoded = code.replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    copyCode(decoded);
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> 已复制';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.innerHTML = originalHTML;
      btn.classList.remove('copied');
    }, 2000);
  };
  if (markdownBody.value) {
    markdownBody.value.addEventListener('click', handleMarkdownClick);
  }
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  delete (window as any).__copyCode;
  if (markdownBody.value) {
    markdownBody.value.removeEventListener('click', handleMarkdownClick);
  }
});
</script>

<template>
  <div v-if="content || source" class="learn-reader-layout">
    <!-- 阅读进度条 -->
    <div class="reading-progress-track">
      <div class="reading-progress-bar" :style="{ width: readingProgress + '%' }"></div>
    </div>

    <!-- 正文区域 -->
    <div class="learn-reader-main" :class="[showNav && headings.length > 0 ? 'has-toc' : 'no-toc']">
      <article class="markdown-article">
        <header v-if="hasHeaderMeta" class="article-header">
          <h1 class="article-title">
            {{ content?.title }}
          </h1>
          <div class="article-meta">
            <time v-if="date" class="meta-item">
              <Icon icon="mdi:calendar" width="15" height="15" />
              {{ date }}
            </time>
            <span v-if="content?.watch" class="meta-item">
              <Icon icon="mdi:eye" width="15" height="15" />
              {{ content.watch }}
            </span>
          </div>
        </header>

        <div ref="markdownBody" class="markdown-content" v-html="html"></div>
      </article>
    </div>

    <!-- 右侧目录 -->
    <aside v-if="showNav && headings.length > 0" class="learn-reader-toc">
      <nav class="toc-nav">
        <h3 class="toc-title">目录</h3>
        <ul class="toc-list">
          <li v-for="link in anchorLinks" :key="link.href" class="toc-item">
            <a
              :href="link.href"
              class="toc-link"
              :class="{ active: activeHeadingId === link.id }"
              @click="handleAnchorClick($event, link.href)"
            >
              <span class="toc-indicator"></span>
              {{ link.text }}
            </a>
            <ul v-if="link.children.length > 0" class="toc-sublist">
              <li v-for="subLink in link.children" :key="subLink.href" class="toc-subitem">
                <a
                  :href="subLink.href"
                  class="toc-sublink"
                  :class="{ active: activeHeadingId === subLink.id }"
                  @click="handleAnchorClick($event, subLink.href)"
                >
                  {{ subLink.text }}
                </a>
              </li>
            </ul>
          </li>
        </ul>
      </nav>
    </aside>
  </div>

  <div v-else class="flex h-full flex-col items-center justify-center p-8 text-center">
    <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-100 dark:border-slate-700 dark:bg-slate-900">
      <Icon icon="mdi:file-document-outline" width="32" height="32" class="text-slate-500 dark:text-slate-400" />
    </div>
    <p class="text-lg text-slate-500 dark:text-slate-400">请选择一篇资料开始阅读</p>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

/* ===== 阅读器双栏布局 ===== */
.learn-reader-layout {
  display: flex;
  gap: 36px;
  max-width: 1320px;
  margin: 0 auto;
  position: relative;
}

.learn-reader-main {
  flex: 1;
  min-width: 0;
  max-width: 900px;
  padding: 0 8px;
}

.learn-reader-main.has-toc {
  flex: 0 0 72%;
  max-width: 72%;
}

.learn-reader-main.no-toc {
  max-width: 900px;
  margin: 0 auto;
}

/* ===== 阅读进度条 ===== */
.reading-progress-track {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: transparent;
  z-index: 100;
}

.reading-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #2563EB, #3B82F6);
  border-radius: 0 2px 2px 0;
  transition: width 0.1s ease-out;
}

/* ===== 右侧目录 ===== */
.learn-reader-toc {
  flex: 0 0 250px;
  width: 250px;
  align-self: flex-start;
  position: sticky;
  top: 88px;
  max-height: calc(100vh - 112px);
  overflow-y: auto;
  scrollbar-width: none;
}

.learn-reader-toc::-webkit-scrollbar {
  display: none;
}

.toc-nav {
  padding: 20px 20px 24px;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  background: white;
}

:global(html.dark) .toc-nav {
  border-color: #1E293B;
  background: #111827;
}

.toc-title {
  font-size: 15px;
  font-weight: 650;
  color: #1E293B;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #F1F5F9;
}

:global(html.dark) .toc-title {
  color: #E5E7EB;
  border-color: #1E293B;
}

.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc-item {
  margin-bottom: 2px;
}

.toc-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  text-decoration: none;
  transition: all 0.15s;
  line-height: 1.5;
}

.toc-link:hover {
  background: #F8FAFC;
  color: #2563EB;
}

:global(html.dark) .toc-link {
  color: #94A3B8;
}

:global(html.dark) .toc-link:hover {
  background: #1E293B;
  color: #60A5FA;
}

.toc-indicator {
  display: none;
  width: 2px;
  height: 16px;
  border-radius: 1px;
  background: #2563EB;
  flex-shrink: 0;
}

.toc-link.active {
  background: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
}

.toc-link.active .toc-indicator {
  display: block;
}

:global(html.dark) .toc-link.active {
  background: #172554;
  color: #60A5FA;
}

.toc-sublist {
  list-style: none;
  padding: 0;
  margin: 2px 0 2px 20px;
}

.toc-subitem {
  margin-bottom: 1px;
}

.toc-sublink {
  display: block;
  padding: 4px 10px;
  border-radius: 5px;
  font-size: 13px;
  color: #64748B;
  text-decoration: none;
  transition: all 0.15s;
  line-height: 1.5;
}

.toc-sublink:hover {
  background: #F8FAFC;
  color: #2563EB;
}

.toc-sublink.active {
  background: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
}

:global(html.dark) .toc-sublink {
  color: #64748B;
}

:global(html.dark) .toc-sublink:hover {
  background: #1E293B;
  color: #60A5FA;
}

:global(html.dark) .toc-sublink.active {
  background: #172554;
  color: #60A5FA;
}

/* ===== 文章头部 ===== */
.article-header {
  margin-bottom: 36px;
  padding-bottom: 28px;
  border-bottom: 1px solid #F1F5F9;
}

:global(html.dark) .article-header {
  border-color: #1E293B;
}

.article-title {
  font-size: 34px;
  font-weight: 700;
  line-height: 1.3;
  color: #0F172A;
  letter-spacing: -0.02em;
}

:global(html.dark) .article-title {
  color: #F1F5F9;
}

.article-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #94A3B8;
}

/* ===== 正文 Markdown 内容 ===== */
.markdown-content :deep(h1) {
  font-size: 28px;
  font-weight: 700;
  margin-top: 52px;
  margin-bottom: 18px;
  color: #0F172A;
  line-height: 1.35;
  letter-spacing: -0.01em;
}

.markdown-content :deep(h2) {
  font-size: 22px;
  font-weight: 650;
  margin-top: 40px;
  margin-bottom: 14px;
  color: #1E293B;
  line-height: 1.4;
}

.markdown-content :deep(h3) {
  font-size: 18px;
  font-weight: 600;
  margin-top: 32px;
  margin-bottom: 12px;
  color: #1E293B;
  line-height: 1.45;
}

.markdown-content :deep(h4) {
  font-size: 16px;
  font-weight: 600;
  margin-top: 28px;
  margin-bottom: 10px;
  color: #334155;
}

:global(html.dark) .markdown-content :deep(h1),
:global(html.dark) .markdown-content :deep(h2),
:global(html.dark) .markdown-content :deep(h3),
:global(html.dark) .markdown-content :deep(h4) {
  color: #F1F5F9;
}

.markdown-content :deep(p) {
  font-size: 15.5px;
  line-height: 1.85;
  color: #334155;
  margin-bottom: 16px;
}

:global(html.dark) .markdown-content :deep(p) {
  color: #CBD5E1;
}

.markdown-content :deep(strong) {
  font-weight: 600;
  color: #1E293B;
}

:global(html.dark) .markdown-content :deep(strong) {
  color: #F1F5F9;
}

.markdown-content :deep(a) {
  color: #2563EB;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.15s;
}

.markdown-content :deep(a:hover) {
  border-bottom-color: #2563EB;
}

:global(html.dark) .markdown-content :deep(a) {
  color: #60A5FA;
}

:global(html.dark) .markdown-content :deep(a:hover) {
  border-bottom-color: #60A5FA;
}

/* ===== 标题锚点链接 ===== */
.markdown-content :deep(.heading-anchor) {
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
  color: #CBD5E1;
  font-size: 0.8em;
  opacity: 0;
  transition: opacity 0.15s;
  text-decoration: none;
  border: none;
}

.markdown-content :deep(h1:hover .heading-anchor),
.markdown-content :deep(h2:hover .heading-anchor),
.markdown-content :deep(h3:hover .heading-anchor),
.markdown-content :deep(h4:hover .heading-anchor) {
  opacity: 1;
}

:global(html.dark) .markdown-content :deep(.heading-anchor) {
  color: #475569;
}

/* ===== 列表 ===== */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}

.markdown-content :deep(li) {
  font-size: 15.5px;
  line-height: 1.85;
  color: #334155;
  padding: 3px 0;
}

:global(html.dark) .markdown-content :deep(li) {
  color: #CBD5E1;
}

.markdown-content :deep(ul li) {
  list-style-type: disc;
}

.markdown-content :deep(ol li) {
  list-style-type: decimal;
}

.markdown-content :deep(ul ul li) {
  list-style-type: circle;
}

.markdown-content :deep(ol ol li),
.markdown-content :deep(ul ol li) {
  list-style-type: lower-alpha;
}

/* ===== 引用块 ===== */
.markdown-content :deep(blockquote) {
  margin: 24px 0;
  padding: 20px 24px;
  border-left: 3px solid #2563EB;
  background: #F8FAFC;
  border-radius: 0 10px 10px 0;
  color: #475569;
}

.markdown-content :deep(blockquote p) {
  margin-bottom: 8px;
}

.markdown-content :deep(blockquote p:last-child) {
  margin-bottom: 0;
}

:global(html.dark) .markdown-content :deep(blockquote) {
  background: #0F172A;
  border-left-color: #3B82F6;
  color: #94A3B8;
}

/* ===== 代码块 ===== */
.markdown-content :deep(.code-block-wrapper) {
  margin: 20px 0;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #E2E8F0;
}

:global(html.dark) .markdown-content :deep(.code-block-wrapper) {
  border-color: #334155;
}

.markdown-content :deep(.code-block-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #F1F5F9;
  border-bottom: 1px solid #E2E8F0;
}

:global(html.dark) .markdown-content :deep(.code-block-header) {
  background: #1E293B;
  border-color: #334155;
}

.markdown-content :deep(.code-lang-label) {
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

:global(html.dark) .markdown-content :deep(.code-lang-label) {
  color: #94A3B8;
}

.markdown-content :deep(.code-copy-btn) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  border: none;
  background: transparent;
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.markdown-content :deep(.code-copy-btn:hover) {
  background: #E2E8F0;
  color: #334155;
}

.markdown-content :deep(.code-copy-btn.copied) {
  color: #16A34A;
}

:global(html.dark) .markdown-content :deep(.code-copy-btn) {
  color: #94A3B8;
}

:global(html.dark) .markdown-content :deep(.code-copy-btn:hover) {
  background: #334155;
  color: #E5E7EB;
}

.markdown-content :deep(pre) {
  margin: 0;
  padding: 16px 20px;
  font-size: 13.5px;
  line-height: 1.7;
  border-radius: 0;
  border: none;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13.5px;
}

/* ===== 行内代码 ===== */
.markdown-content :deep(code):not(pre code):not(.code-block-wrapper code) {
  background: #F1F5F9;
  color: #2563EB;
  padding: 2px 7px;
  border-radius: 5px;
  font-size: 0.9em;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 500;
}

:global(html.dark) .markdown-content :deep(code):not(pre code):not(.code-block-wrapper code) {
  background: #1E293B;
  color: #60A5FA;
}

/* ===== 表格 ===== */
.markdown-content :deep(table) {
  width: 100%;
  margin: 24px 0;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  overflow: hidden;
}

:global(html.dark) .markdown-content :deep(table) {
  border-color: #334155;
}

.markdown-content :deep(th) {
  background: #F8FAFC;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 700;
  color: #475569;
  text-align: left;
  border-bottom: 1px solid #E2E8F0;
}

:global(html.dark) .markdown-content :deep(th) {
  background: #1E293B;
  color: #94A3B8;
  border-color: #334155;
}

.markdown-content :deep(td) {
  padding: 12px 16px;
  font-size: 14px;
  color: #334155;
  border-bottom: 1px solid #F1F5F9;
}

.markdown-content :deep(tr:last-child td) {
  border-bottom: none;
}

.markdown-content :deep(tr:hover td) {
  background: #F8FAFC;
}

:global(html.dark) .markdown-content :deep(td) {
  color: #CBD5E1;
  border-color: #1E293B;
}

:global(html.dark) .markdown-content :deep(tr:hover td) {
  background: #0F172A;
}

/* ===== 图片 ===== */
.markdown-content :deep(img) {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 24px auto;
  border-radius: 10px;
  border: 1px solid #E2E8F0;
}

:global(html.dark) .markdown-content :deep(img) {
  border-color: #334155;
}

/* ===== 分割线 ===== */
.markdown-content :deep(hr) {
  border: none;
  height: 1px;
  background: #E2E8F0;
  margin: 36px 0;
}

:global(html.dark) .markdown-content :deep(hr) {
  background: #334155;
}

/* ===== 自定义容器 ===== */
:deep(.custom-block) {
  margin: 20px 0;
  padding: 16px 20px;
  border-radius: 10px;
}

:deep(.custom-block-title) {
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: 700;
}

.markdown-content :deep(.warning) {
  background: #FFFBEB;
  border-left: 3px solid #F59E0B;
}

.markdown-content :deep(.danger) {
  background: #FFF1F2;
  border-left: 3px solid #F43F5E;
}

.markdown-content :deep(.tip) {
  background: #ECFEFF;
  border-left: 3px solid #06B6D4;
}

:global(html.dark) .markdown-content :deep(.warning) {
  background: #422006;
}

:global(html.dark) .markdown-content :deep(.danger) {
  background: #4C0519;
}

:global(html.dark) .markdown-content :deep(.tip) {
  background: #083344;
}

/* ===== 任务列表 ===== */
.markdown-content :deep(.task-list-item) {
  list-style: none;
  position: relative;
  padding-left: 4px;
}

.markdown-content :deep(.task-list-item input) {
  margin-right: 8px;
  accent-color: #2563EB;
}

/* ===== 脚注 ===== */
.markdown-content :deep(.footnotes) {
  margin-top: 36px;
  padding-top: 24px;
  border-top: 1px solid #E2E8F0;
  font-size: 13px;
}

:global(html.dark) .markdown-content :deep(.footnotes) {
  border-color: #334155;
}

/* ===== 移动端适配 ===== */
@media (max-width: 1024px) {
  .learn-reader-layout {
    flex-direction: column;
    gap: 0;
  }

  .learn-reader-main.has-toc,
  .learn-reader-main.no-toc {
    flex: none;
    max-width: 100%;
    width: 100%;
  }

  .learn-reader-toc {
    position: static;
    width: 100%;
    flex: none;
    max-height: none;
    order: -1;
    margin-bottom: 24px;
  }
}
</style>

<style>
/* ===== 全局 Markdown 文章样式（非 scoped，确保渲染内容生效） ===== */
html:not(.dark) .markdown-article {
  color: #334155;
}

html.dark .markdown-article {
  color: #CBD5E1;
}

html:not(.dark) .markdown-article .markdown-content :is(p, li, blockquote, td, th, dd, dt, figcaption, span),
html:not(.dark) .markdown-article header,
html:not(.dark) .markdown-article header time,
html:not(.dark) .markdown-article header span {
  color: #334155;
}

html.dark .markdown-article .markdown-content :is(p, li, blockquote, td, th, dd, dt, figcaption, span),
html.dark .markdown-article header,
html.dark .markdown-article header time,
html.dark .markdown-article header span {
  color: #CBD5E1;
}

html:not(.dark) .markdown-article .markdown-content :is(h1, h2, h3, h4, h5, h6) {
  color: #0F172A;
}

html.dark .markdown-article .markdown-content :is(h1, h2, h3, h4, h5, h6) {
  color: #F1F5F9;
}

html:not(.dark) .markdown-article .markdown-content :is(a, a:visited) {
  color: #2563EB;
}

html.dark .markdown-article .markdown-content :is(a, a:visited) {
  color: #60A5FA;
}

html:not(.dark) .markdown-article .markdown-content :is(code):not(pre code):not(.code-block-wrapper code) {
  color: #2563EB;
}

html.dark .markdown-article .markdown-content :is(code):not(pre code):not(.code-block-wrapper code) {
  color: #60A5FA;
}

html:not(.dark) .markdown-article .markdown-content thead,
html:not(.dark) .markdown-article .markdown-content thead th {
  color: #475569 !important;
  border-color: #E2E8F0 !important;
  background-color: #F8FAFC !important;
}

html.dark .markdown-article .markdown-content thead,
html.dark .markdown-article .markdown-content thead th {
  color: #94A3B8 !important;
  border-color: #334155 !important;
  background-color: #1E293B !important;
}

/* Prism token 色彩覆盖 - 亮色主题 */
html:not(.dark) .token.comment,
html:not(.dark) .token.prolog,
html:not(.dark) .token.doctype,
html:not(.dark) .token.cdata {
  color: #64748b !important;
}

html:not(.dark) .token.punctuation {
  color: #64748b !important;
}

html:not(.dark) .token.property,
html:not(.dark) .token.tag,
html:not(.dark) .token.boolean,
html:not(.dark) .token.number,
html:not(.dark) .token.constant,
html:not(.dark) .token.symbol,
html:not(.dark) .token.deleted {
  color: #ea580c !important;
}

html:not(.dark) .token.selector,
html:not(.dark) .token.attr-name,
html:not(.dark) .token.string,
html:not(.dark) .token.char,
html:not(.dark) .token.builtin,
html:not(.dark) .token.inserted {
  color: #059669 !important;
}

html:not(.dark) .token.operator,
html:not(.dark) .token.entity,
html:not(.dark) .token.url {
  color: #334155 !important;
}

html:not(.dark) .token.atrule,
html:not(.dark) .token.attr-value,
html:not(.dark) .token.keyword {
  color: #7c3aed !important;
}

html:not(.dark) .token.function,
html:not(.dark) .token.class-name {
  color: #2563eb !important;
}

html:not(.dark) .token.regex,
html:not(.dark) .token.important,
html:not(.dark) .token.variable {
  color: #d97706 !important;
}

/* Prism token 色彩覆盖 - 暗色主题 */
html.dark .token.comment,
html.dark .token.prolog,
html.dark .token.doctype,
html.dark .token.cdata {
  color: #6b7280 !important;
}

html.dark .token.punctuation {
  color: #9ca3af !important;
}

html.dark .token.property,
html.dark .token.tag,
html.dark .token.boolean,
html.dark .token.number,
html.dark .token.constant,
html.dark .token.symbol,
html.dark .token.deleted {
  color: #f59e0b !important;
}

html.dark .token.selector,
html.dark .token.attr-name,
html.dark .token.string,
html.dark .token.char,
html.dark .token.builtin,
html.dark .token.inserted {
  color: #34d399 !important;
}

html.dark .token.operator,
html.dark .token.entity,
html.dark .token.url {
  color: #d1d5db !important;
}

html.dark .token.atrule,
html.dark .token.attr-value,
html.dark .token.keyword {
  color: #a78bfa !important;
}

html.dark .token.function,
html.dark .token.class-name {
  color: #60a5fa !important;
}

html.dark .token.regex,
html.dark .token.important,
html.dark .token.variable {
  color: #fbbf24 !important;
}

/* 暗色主题代码块背景 */
html.dark .markdown-content pre[class*='language-'],
html.dark .markdown-content code[class*='language-'] {
  background: #0F172A !important;
  color: #E2E8F0 !important;
}

html:not(.dark) .markdown-content pre[class*='language-'],
html:not(.dark) .markdown-content code[class*='language-'] {
  background: #F8FAFC !important;
  color: #0F172A !important;
}
</style>
