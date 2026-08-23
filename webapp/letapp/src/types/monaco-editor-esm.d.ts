// Monaco 按需引入的类型垫片（性能优化配套）。
// monaco-editor 的 package.json exports 用 "./*": "./*" 暴露了 ESM 子路径，
// Vite 构建期可以解析，但 vue-tsc 需要显式类型声明。这里为按需引入的子路径
// 补充类型：editor.api 复用主包的命名导出（editor / languages / worker 等），
// 其余为纯副作用模块（注册编辑器功能与语言语法），声明为空模块即可。
declare module 'monaco-editor/esm/vs/editor/editor.api' {
  export * from 'monaco-editor';
}

declare module 'monaco-editor/esm/vs/editor/editor.all';

declare module 'monaco-editor/esm/vs/basic-languages/cpp/cpp.contribution';

declare module 'monaco-editor/esm/vs/basic-languages/python/python.contribution';

declare module 'monaco-editor/esm/vs/basic-languages/java/java.contribution';
