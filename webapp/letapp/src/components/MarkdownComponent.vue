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
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-typescript';
import 'prismjs/themes/prism-tomorrow.min.css';

interface Content {
  title?: string;
  date?: string;
  watch?: number;
  content: string;
  identity?: string;
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
}>(), {
  showNav: true,
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
  };

  const key = language.trim().toLowerCase();
  return aliases[key] || key;
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
  typographer: true,
  highlight: (code: string, language: string): string => {
    const normalizedLanguage = normalizeLanguage(language || '');
    const grammar = Prism.languages[normalizedLanguage];

    if (!grammar) {
      return `<pre class="language-text"><code>${escapeHtml(code)}</code></pre>`;
    }

    const highlighted = Prism.highlight(code, grammar, normalizedLanguage);
    return `<pre class="language-${normalizedLanguage}"><code class="language-${normalizedLanguage}">${highlighted}</code></pre>`;
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
  await nextTick();
  setTimeout(() => Prism.highlightAll(), 50);
  return renderedHtml;
};

watch(
  () => props.content,
  async (newValue) => {
    html.value = newValue ? await render(newValue.content) : '';
  },
  { immediate: true },
);

const anchorLinks = computed(() => headings.value);
const date = computed(() => (props.content?.date ? new Date(props.content.date).toLocaleDateString('zh-CN') : ''));
const hasHeaderMeta = computed(() => Boolean(props.content?.title || props.content?.date || props.content?.watch || props.content?.identity));

const getIdentityLabel = computed(() => {
  const options = [
    { label: '所有人', value: 'Member' },
    { label: '部员', value: 'Department' },
    { label: '部长', value: 'Minister' },
    { label: '社长', value: 'President' },
    { label: '创始人', value: 'Founder' },
  ];
  return options.find((item) => item.value === props.content?.identity)?.label || '未知';
});

const getIdentityClass = (identity: string) => {
  switch (identity) {
    case 'Member':
      return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-100';
    case 'Department':
      return 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-100';
    case 'Minister':
      return 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-100';
    case 'President':
      return 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-100';
    case 'Founder':
      return 'bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-100';
    default:
      return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100';
  }
};

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
              {{ content.watch }} 次阅读
            </span>
            <span v-if="content.identity" class="rounded-full px-3 py-1 text-xs font-bold" :class="getIdentityClass(content.identity)">
              {{ getIdentityLabel }}
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
  @apply rounded-2xl border border-slate-200 bg-slate-50 p-4 text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100;
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

:global(html:not(.dark)) .markdown-content :deep(.token.comment),
:global(html:not(.dark)) .markdown-content :deep(.token.prolog),
:global(html:not(.dark)) .markdown-content :deep(.token.doctype),
:global(html:not(.dark)) .markdown-content :deep(.token.cdata) {
  color: #64748b !important;
}

:global(html:not(.dark)) .markdown-content :deep(.token.punctuation),
:global(html:not(.dark)) .markdown-content :deep(.token.operator) {
  color: #334155 !important;
}

:global(html:not(.dark)) .markdown-content :deep(.token.keyword),
:global(html:not(.dark)) .markdown-content :deep(.token.selector),
:global(html:not(.dark)) .markdown-content :deep(.token.atrule) {
  color: #7c3aed !important;
}

:global(html:not(.dark)) .markdown-content :deep(.token.string),
:global(html:not(.dark)) .markdown-content :deep(.token.attr-value),
:global(html:not(.dark)) .markdown-content :deep(.token.char),
:global(html:not(.dark)) .markdown-content :deep(.token.inserted) {
  color: #059669 !important;
}

:global(html:not(.dark)) .markdown-content :deep(.token.function),
:global(html:not(.dark)) .markdown-content :deep(.token.class-name) {
  color: #2563eb !important;
}

:global(html:not(.dark)) .markdown-content :deep(.token.number),
:global(html:not(.dark)) .markdown-content :deep(.token.boolean),
:global(html:not(.dark)) .markdown-content :deep(.token.constant) {
  color: #ea580c !important;
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
</style>
