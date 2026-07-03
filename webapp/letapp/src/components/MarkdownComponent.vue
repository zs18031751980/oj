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
  showNav?: boolean;
  showHeadingLinks?: boolean;
}>(), {
  showNav: true,
  showHeadingLinks: true,
});

const route = useRoute();
const headings = ref<HeadingItem[]>([]);
const html = ref('');

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
    return `<pre class="language-${targetLang}"><code class="language-${targetLang}">${highlighted}</code></pre>`;
  },
});

md.use(markdownItAnchor, {
  permalink: markdownItAnchor.permalink.ariaHidden({
    placement: 'before',
    space: true,
    class: 'apple-link-no-icon',
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
  const renderedHtml = md.render(markdown);
  const finalHtml = props.showHeadingLinks
    ? renderedHtml
    : renderedHtml.replace(/<a\b[^>]*class="[^"]*apple-link-no-icon[^"]*"[^>]*>[\s\S]*?<\/a>/g, '');
  await nextTick();
  setTimeout(() => Prism.highlightAll(), 50);
  return finalHtml;
};

watch(
  () => [props.content, props.showHeadingLinks] as const,
  async ([newValue]) => {
    html.value = newValue ? await render(newValue.content) : '';
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

const handleScroll = () => {
  const articleHeadings = document.querySelectorAll('.markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4, .markdown-content h5, .markdown-content h6');
  let activeHeadingId = '';

  for (let i = articleHeadings.length - 1; i >= 0; i -= 1) {
    const heading = articleHeadings[i];
    if (heading && heading.getBoundingClientRect().top <= 120) {
      activeHeadingId = heading.id;
      break;
    }
  }

  document.querySelectorAll('.toc-link').forEach((link) => {
    link.classList.toggle('active', link.getAttribute('href') === `#${activeHeadingId}`);
  });
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <div v-if="content" class="flex flex-col md:flex-row">
    <div class="w-full p-4 md:p-8" :class="[showNav && headings.length > 0 ? 'md:w-4/5' : 'md:w-full']">
      <article class="markdown-article prose prose-slate max-w-none dark:prose-invert">
        <header v-if="hasHeaderMeta" class="mb-8 border-b border-slate-200 pb-6 dark:border-slate-800">
          <h1 class="mb-4 text-3xl font-black text-slate-950 dark:text-white md:text-4xl">
            {{ content.title }}
          </h1>
          <div class="flex flex-wrap items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
            <time class="flex items-center gap-1">
              <Icon icon="mdi:calendar" width="16" height="16" />
              {{ date }}
            </time>
            <span class="flex items-center gap-1">
              <Icon icon="mdi:eye" width="16" height="16" />
            </span>
          </div>
        </header>

        <div class="markdown-content">
          <div v-html="html"></div>
        </div>
      </article>
    </div>

    <aside v-if="showNav && headings.length > 0" class="hidden w-1/5 self-start p-4 md:sticky md:top-24 md:block">
      <nav class="rounded-3xl border border-slate-200 bg-white p-4 shadow-lg shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20">
        <h3 class="mb-3 text-sm font-black text-slate-950 dark:text-white">目录</h3>
        <ul class="space-y-1">
          <li v-for="link in anchorLinks" :key="link.href">
            <a :href="link.href" class="toc-link block rounded-lg px-2 py-1 text-sm font-bold" @click="handleAnchorClick($event, link.href)">
              {{ link.text }}
            </a>
            <ul v-if="link.children.length > 0" class="ml-3 mt-1 space-y-1">
              <li v-for="subLink in link.children" :key="subLink.href">
                <a :href="subLink.href" class="toc-link block rounded-lg px-2 py-1 text-xs" @click="handleAnchorClick($event, subLink.href)">
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
    <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-3xl border-2 border-dashed border-slate-300 bg-slate-100 dark:border-slate-700 dark:bg-slate-900">
      <Icon icon="mdi:file-document-outline" width="32" height="32" class="text-slate-500 dark:text-slate-400" />
    </div>
    <p class="text-lg text-slate-500 dark:text-slate-400">请选择一篇资料开始阅读</p>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

:deep(.custom-block) {
  @apply my-4 rounded-2xl p-4;
}

:deep(.custom-block-title) {
  @apply mb-2 text-base font-black;
}

.markdown-content :deep(.warning) {
  @apply bg-amber-100 dark:bg-amber-950;
}

.markdown-content :deep(.danger) {
  @apply bg-rose-100 dark:bg-rose-950;
}

.markdown-content :deep(.tip) {
  @apply bg-cyan-50 dark:bg-cyan-950;
}

.toc-link {
  @apply text-slate-500 transition hover:bg-slate-100 hover:text-cyan-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-cyan-300;
}

.toc-link.active {
  @apply bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  @apply font-black tracking-tight text-slate-950 dark:text-white;
}

.markdown-content :deep(p),
.markdown-content :deep(li) {
  @apply leading-8 text-slate-700 dark:text-slate-200;
}

.markdown-content :deep(pre) {
  @apply rounded-2xl border border-slate-200 bg-slate-50 p-4 text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100;
}

.markdown-content :deep(pre[class*='language-']),
.markdown-content :deep(code[class*='language-']) {
  background: transparent !important;
  color: inherit;
}

:global(html:not(.dark)) .markdown-content :deep(pre),
:global(html:not(.dark)) .markdown-content :deep(pre[class*='language-']),
:global(html:not(.dark)) .markdown-content :deep(code[class*='language-']) {
  background: #f8fafc !important;
  color: #0f172a !important;
}

:global(html.dark) .markdown-content :deep(pre[class*='language-']),
:global(html.dark) .markdown-content :deep(code[class*='language-']) {
  background: #1e293b !important;
  border-color: #334155;
}



.markdown-content :deep(table) {
  @apply my-4 min-w-full border-collapse;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  @apply border border-slate-300 px-4 py-2 dark:border-slate-700;
}

.markdown-content :deep(th) {
  @apply bg-slate-100 font-black dark:bg-slate-800;
}
</style>

<style>
html:not(.dark) .markdown-article {
  color: #0f172a;
}

html.dark .markdown-article {
  color: #f8fafc;
}

html:not(.dark) .markdown-article .markdown-content,
html.dark .markdown-article .markdown-content {
  color: inherit;
}

html:not(.dark) .markdown-article .markdown-content :is(p, li, blockquote, td, th, dd, dt, figcaption, span, strong, em),
html:not(.dark) .markdown-article header,
html:not(.dark) .markdown-article header time,
html:not(.dark) .markdown-article header span,
html:not(.dark) .markdown-article .toc-link {
  color: #0f172a;
}

html.dark .markdown-article .markdown-content :is(p, li, blockquote, td, th, dd, dt, figcaption, span, strong, em),
html.dark .markdown-article header,
html.dark .markdown-article header time,
html.dark .markdown-article header span,
html.dark .markdown-article .toc-link {
  color: #f8fafc;
}

html:not(.dark) .markdown-article .toc-link {
  color: #475569;
}

html.dark .markdown-article .toc-link {
  color: #cbd5e1;
}

html:not(.dark) .markdown-article .toc-link.active {
  color: #0e7490;
}

html.dark .markdown-article .toc-link.active {
  color: #67e8f9;
}

html:not(.dark) .markdown-article .markdown-content :is(h1, h2, h3, h4, h5, h6) {
  color: #020617;
}

html.dark .markdown-article .markdown-content :is(h1, h2, h3, h4, h5, h6) {
  color: #ffffff;
}

html:not(.dark) .markdown-article .markdown-content :is(a, a:visited) {
  color: #0891b2;
}

html.dark .markdown-article .markdown-content :is(a, a:visited) {
  color: #67e8f9;
}

html:not(.dark) .markdown-article .markdown-content :is(code):not(pre code) {
  color: #0f172a;
}

html.dark .markdown-article .markdown-content :is(code):not(pre code) {
  color: #f8fafc;
}

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
</style>
