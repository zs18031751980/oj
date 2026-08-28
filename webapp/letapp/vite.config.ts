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
        let updatedAt = s.mtime.toISOString();
        if (fm) {
          const p = fm[1].match(/^permission:\s*(\S+)/m);
          if (p) permission = p[1];
          const d = fm[1].match(/^date:\s*(.+)/m);
          if (d) {
            const parsed = new Date(d[1].trim());
            if (!isNaN(parsed.getTime())) updatedAt = parsed.toISOString();
          }
        }
        return {file: f, title, permission, updatedAt};
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
        chunkSizeWarningLimit: 4000,
        rollupOptions: {
            output: {
                manualChunks(id) {
                    if (!id.includes('node_modules')) return
                    if (id.includes('vue-router') || id.includes('pinia') || id.includes('/vue/')) return 'vendor-vue'
                    if (id.includes('naive-ui')) return 'vendor-naive'
                    if (id.includes('markdown-it')) return 'vendor-markdown'
                    if (id.includes('@iconify')) return 'vendor-icons'
                    if (id.includes('prismjs')) return 'vendor-prism'
                    if (id.includes('mermaid')) return 'vendor-mermaid'
                },
            },
        },
    },
    css: {
        devSourcemap: false,
    },
})
