/// <reference types="vite/client" />

// 声明 Vite 环境变量
declare interface ImportMetaEnv {
  readonly VITE_API_URL: string
  // 可以在这里添加更多的环境变量声明
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv
}