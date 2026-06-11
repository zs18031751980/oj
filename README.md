# 代码综合平台

## 介绍
iOS Club 代码综合平台是一个集代码编辑、运行和学习于一体的综合性平台，旨在为开发者提供便捷的代码开发和学习环境。

## 项目结构

```
LetCoding/
├── webapi/                  # 后端 API 服务
│   └── fastapi_of_letcoing/ # FastAPI 实现的代码运行服务
├── webapp/                  # 前端应用
│   └── letapp/              # Vue 3 + TypeScript 实现的单页应用
├── LICENSE                  # 许可证文件
├── README.en.md             # 英文 README
└── README.md                # 中文 README
```

## 技术栈

### 后端 (webapi/fastapi_of_letcoing)
- **框架**: Flask (Python)
- **主要功能**: 提供代码运行服务，支持多种编程语言
- **外部服务**: Glot API (代码执行)

### 前端 (webapp/letapp)
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI 组件**: 自定义组件
- **状态管理**: Pinia
- **路由**: Vue Router
- **Markdown 支持**: markdown-it 及其插件

## 功能特点

1. **多语言代码运行**: 支持多种编程语言的代码在线运行
2. **Markdown 编辑器**: 支持 Markdown 语法的实时预览和编辑
3. **主题切换**: 支持明暗主题切换
4. **响应式设计**: 适配不同屏幕尺寸
5. **模块化架构**: 前后端分离，便于扩展和维护

## 快速开始

### 后端服务

1. 进入后端目录
   ```bash
   cd webapi/fastapi_of_letcoing
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量
   ```bash
   export API_TOKEN=your_glot_api_token
   ```

4. 启动服务
   ```bash
   python main.py
   ```

### 前端应用

1. 进入前端目录
   ```bash
   cd webapp/letapp
   ```

2. 安装依赖
   ```bash
   npm install
   ```

3. 启动开发服务器
   ```bash
   npm run dev
   ```

4. 访问应用
   打开浏览器访问 `http://localhost:5173`

## 目录说明

### webapi/fastapi_of_letcoing
- `main.py`: 应用入口，定义 API 路由
- `services/glot_service.py`: 调用 Glot API 执行代码的服务
- `requirements.txt`: 项目依赖列表

### webapp/letapp
- `src/`: 源代码目录
  - `components/`: Vue 组件
  - `layouts/`: 布局组件
  - `pages/`: 页面组件
  - `stores/`: Pinia 状态管理
  - `types/`: TypeScript 类型定义
  - `App.vue`: 根组件
  - `main.ts`: 应用入口
  - `router.ts`: 路由配置
- `public/`: 静态资源
- `index.html`: HTML 模板

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
