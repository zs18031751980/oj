import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
    plugins: [vue(), tailwindcss()],
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
