# 代码综合平台 - 前端应用

## 介绍

这是代码综合平台的前端应用，基于 Vue 3 + TypeScript + Vite 开发，提供代码编辑、Markdown 预览、主题切换等功能，旨在为开发者提供便捷的代码开发和学习环境。

## 功能特点

- **代码编辑器**: 集成代码编辑器，支持多种编程语言
- **Markdown 支持**: 实时预览 Markdown 内容，支持多种扩展语法
- **主题切换**: 支持明暗主题切换，适应不同使用场景
- **响应式设计**: 适配不同屏幕尺寸，提供良好的移动端体验
- **模块化架构**: 采用 Vue 3 组合式 API，代码结构清晰，便于维护和扩展
- **TypeScript 支持**: 全面使用 TypeScript，提供类型安全保障

## 技术栈

- **框架**: Vue 3.0+
- **语言**: TypeScript 5.0+
- **构建工具**: Vite 5.0+
- **状态管理**: Pinia
- **路由**: Vue Router
- **Markdown 引擎**: markdown-it 14.1.0
- **Markdown 插件**:
  - markdown-it-attrs
  - markdown-it-expand-tabs
  - markdown-it-mark
  - markdown-it-sub
  - markdown-it-sup
  - markdown-it-task-lists
- **CSS 预处理器**: 原生 CSS

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:5173` 启动。

### 3. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist` 目录。

### 4. 预览生产构建

```bash
npm run preview
```

## 目录结构

```
letapp/
├── public/                 # 静态资源
│   └── assets/            # 图片等资源文件
├── src/                   # 源代码
│   ├── components/        # Vue 组件
│   │   └── MarkdownComponent.vue  # Markdown 渲染组件
│   ├── layouts/           # 布局组件
│   │   └── MainLayout.vue         # 主布局组件
│   ├── pages/             # 页面组件
│   │   └── Home.vue               # 首页组件
│   ├── stores/            # Pinia 状态管理
│   │   └── theme.ts               # 主题状态管理
│   ├── types/             # TypeScript 类型定义
│   ├── App.vue            # 根组件
│   ├── main.ts            # 应用入口
│   ├── router.ts          # 路由配置
│   ├── style.css          # 全局样式
│   └── vite-env.d.ts      # Vite 环境类型定义
├── index.html             # HTML 模板
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
├── tsconfig.app.json      # TypeScript 应用配置
├── tsconfig.node.json     # TypeScript Node 配置
├── vite.config.ts         # Vite 配置
├── .gitignore             # Git 忽略文件
└── README.md              # 项目说明文档
```

## 核心功能说明

### Markdown 支持

应用集成了功能强大的 Markdown 渲染引擎，支持多种扩展语法：

- **任务列表**: `- [ ] 待办项`、`- [x] 已完成项`
- **标记文本**: `==标记文本==`
- **上下标**: `H~2~O`、`E=mc^2^`
- **属性支持**: `{.class #id key=value}`
- **代码高亮**: 支持多种编程语言的代码高亮

### 主题切换

应用支持明暗主题切换，通过 Pinia 进行状态管理，用户可以根据自己的偏好选择主题。

### 路由管理

目前应用包含一个首页路由，未来可以根据需求扩展更多页面。

## 开发指南

### 组件开发

推荐使用 Vue 3 组合式 API 开发组件，遵循以下规范：

1. 组件命名使用 PascalCase
2. 组件文件后缀为 `.vue`
3. 使用 TypeScript 定义组件的 Props 和 Emits
4. 组件逻辑与模板分离，保持代码清晰

### 状态管理

使用 Pinia 进行状态管理，每个状态模块对应一个单独的文件，位于 `src/stores/` 目录下。

### 路由配置

路由配置位于 `src/router.ts` 文件中，使用 Vue Router 4.x 版本。

## 脚本命令

| 命令 | 描述 |
|------|------|
| `npm install` | 安装依赖 |
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产构建 |
| `npm run typecheck` | 运行 TypeScript 类型检查 |

## 浏览器支持

- Chrome (最新版本)
- Firefox (最新版本)
- Safari (最新版本)
- Edge (最新版本)

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../../../LICENSE) 文件了解详情。

