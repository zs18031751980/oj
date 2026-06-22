import {defineConfig, type ViteDevServer} from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from "@tailwindcss/vite";
import {readdirSync, statSync, readFileSync, writeFileSync} from 'fs';
import {join, extname, basename} from 'path';

function announcementsPlugin() {
  const dir = 'public/announcements';

  const scan = () => {
    try {
      const files = readdirSync(dir).filter(f => extname(f) === '.md');
      const items = files.map(f => {
        const p = join(dir, f);
        const s = statSync(p);
        const content = readFileSync(p, 'utf-8');
        const m = content.match(/^#\s+(.+)/m);
        const title = m ? m[1].trim() : basename(f, '.md');
        const fm = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
        let permission = 'member';
        if (fm) {
          const p = fm[1].match(/^permission:\s*(\S+)/m);
          if (p) permission = p[1];
        }
        return {file: f, title, permission, updatedAt: s.mtime.toISOString()};
      });
      items.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
      writeFileSync(join(dir, 'manifest.json'), JSON.stringify(items, null, 2));
    } catch {}
  };

  return {
    name: 'announcements-manifest',
    buildStart: scan,
    configureServer(server: ViteDevServer) {
      scan();
      const pattern = join(dir, '*.md').replace(/\\/g, '/');
      server.watcher.add(pattern);
      const onChange = (p: string) => { if (p.endsWith('.md')) scan(); };
      server.watcher.on('change', onChange);
      server.watcher.on('add', onChange);
      server.watcher.on('unlink', onChange);
    },
  };
}

export default defineConfig({
    plugins: [vue(), tailwindcss(), announcementsPlugin()],
    build: {
        target: 'es2020',
        cssMinify: 'esbuild',
        sourcemap: false,
        reportCompressedSize: false,
        rollupOptions: {
            output: {
                manualChunks: {
                    'vendor-vue': ['vue', 'vue-router', 'pinia'],
                    'vendor-naive': ['naive-ui'],
                    'vendor-monaco': ['monaco-editor'],
                    'vendor-echarts': ['echarts'],
                    'vendor-markdown': ['markdown-it', 'markdown-it-anchor', 'markdown-it-attrs', 'markdown-it-container', 'markdown-it-footnote', 'markdown-it-mark', 'markdown-it-sup', 'markdown-it-task-lists', 'markdown-it-expand-tabs'],
                    'vendor-icons': ['@iconify/vue'],
                    'vendor-prism': ['prismjs'],
                },
            },
        },
    },
    css: {
        devSourcemap: false,
    },
})
