# iOS Club 代码综合平台

iOS Club 代码综合平台是一个集**在线编程、代码评测、学习资源**于一体的综合性 Web 应用，为社团成员提供便捷的编程学习和实践环境。

## 核心功能

| 模块 | 说明 |
|------|------|
| **在线编程** | Monaco Editor 驱动的在线代码编辑器，支持 8 种编程语言，快捷键 `Ctrl+Enter` 运行 |
| **代码评测** | 在线判题系统（OJ），支持题目浏览、代码提交、测试用例验证 |
| **学习资源** | Markdown 驱动的学习文档，支持 Mermaid 图表、代码高亮、任务列表等扩展语法 |
| **用户系统** | OIDC 统一认证（iOSClub 账号登录），支持 GitHub OAuth，三级角色权限（管理员 / 部长 / 部员 / 成员） |
| **公告管理** | 公告 CRUD，副部长及以上可编辑，支持 Markdown 富文本 |
| **主题切换** | 浅色 / 深色 / 跟随系统，偏好持久化到服务端 |

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                     前端 (LetApp)                    │
│  Vue 3 + TypeScript + Vite                           │
│  ├─ Naive UI / Tailwind CSS / Monaco Editor         │
│  ├─ Pinia 状态管理 / Vue Router 路由                 │
│  └─ markdown-it 文档渲染 (Mermaid + Prism.js)       │
├─────────────────────────────────────────────────────┤
│                    HTTP / REST API                   │
├─────────────────────────────────────────────────────┤
│                   后端 (FastAPI of LetCoding)        │
│  Flask + Flask-RESTX + Swagger                       │
│  ├─ 控制器层 controllers/                            │
│  │   ├─ auth_controller   (OIDC/JWT 认证)           │
│  │   ├─ code_controller   (代码执行)                │
│  │   ├─ submission_controller (判题提交)            │
│  │   ├─ announcement_controller (公告管理)          │
│  │   └─ user_code_controller (用户代码存储)         │
│  ├─ 服务层 services/                                 │
│  │   ├─ oidc_service  (Authlib OAuth/OIDC)          │
│  │   ├─ jwt_service   (PyJWT + Redis 缓存)          │
│  │   ├─ judge_service (后台判题 Worker)             │
│  │   ├─ glot_service  (Glot.io 代码执行)            │
│  │   └─ user_service  (Peewee ORM)                  │
│  ├─ 中间件 middleware/auth_middleware                 │
│  │   └─ JWT 验证 / 角色权限 / 速率限制              │
│  └─ 工具 utils/role_utils (角色标准化与优先级选取)   │
├─────────────────────────────────────────────────────┤
│                   数据层                              │
│  ├─ PostgreSQL  (用户/题目/提交/公告)                │
│  ├─ Redis       (JWT 缓存 / 会话 / 限流)            │
│  └─ Glot.io API (远程代码执行沙箱)                   │
└─────────────────────────────────────────────────────┘
```

### 认证流程

```
用户 ──→ iOSClub OIDC / GitHub OAuth ──→ 授权回调 ──→ JWT 签发
  │                                                    │
  └──── 角色归一化 (多身份取最高) ←── 数据库同步 ←─────┘
                        │
          manager / staff / member
                        │
          ┌─────────────┴─────────────┐
          │  Redis 缓存 ←→ 令牌验证   │
          │  黑名单机制    令牌刷新    │
          └───────────────────────────┘
```

### 角色权限

| 角色 | 内部标识 | 包含身份 |
|------|---------|---------|
| 管理员 | `manager` | 管理员、社长、副社长、部长、副部长、部门主管 |
| 部员 | `staff` | 部员、干事 |
| 成员 | `member` | 社员、普通用户 |

多身份用户自动取最高权限角色。

## 技术栈

### 后端
- **框架**: Flask 3 + Flask-RESTX (REST API + Swagger 文档)
- **ORM**: Peewee + PostgreSQL
- **认证**: Authlib (OAuth/OIDC)、PyJWT
- **缓存**: Redis (用户信息缓存、令牌黑名单、速率限制)
- **代码执行**: Glot.io API (aiohttp 异步调用)
- **部署**: Gunicorn

### 前端
- **框架**: Vue 3 + TypeScript
- **构建**: Vite 7
- **UI**: Naive UI + Tailwind CSS 4
- **编辑器**: Monaco Editor
- **图表**: ECharts
- **图标**: Iconify
- **路由**: Vue Router 4
- **状态**: Pinia 3

## 项目结构

```
LetCoding-ShuaiGe/
├── webapi/                          # 后端
│   └── fastapi_of_letcoing/
│       ├── main.py                  # 应用入口
│       ├── controllers/             # 控制器 (API 路由)
│       ├── services/                # 业务服务层
│       ├── models/                  # 数据模型 (ORM + DTO)
│       ├── middleware/              # 中间件 (认证/限流)
│       ├── interfaces/              # 抽象接口 (ABC)
│       ├── core/                    # 核心 (DI 容器/配置)
│       └── utils/                   # 工具 (角色处理等)
│
├── webapp/                          # 前端
│   └── letapp/
│       └── src/
│           ├── pages/               # 页面组件
│           ├── components/          # 通用组件
│           ├── layouts/             # 布局组件
│           ├── stores/              # Pinia 状态管理
│           ├── services/            # API 请求封装
│           ├── composables/         # 组合式函数
│           └── types/               # TypeScript 类型
│
└── .gitignore / LICENSE / README.md
```

## API 接口

| 路径 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/auth/login` | POST | 获取 OAuth 授权 URL | 否 |
| `/auth/login/<provider>` | GET | 浏览器 OAuth 跳转 | 否 |
| `/auth/login/password` | POST | 本地密码登录 | 否 |
| `/auth/login/<provider>/password` | POST | 提供商密码登录 | 否 |
| `/auth/callback/<provider>` | GET | OAuth 回调处理 | 否 |
| `/auth/refresh` | POST | 刷新令牌 | Bearer |
| `/auth/verify` | GET | 验证令牌 | Bearer |
| `/auth/logout` | POST | 登出 (令牌撤销) | Bearer |
| `/auth/theme` | PATCH | 更新主题偏好 | Bearer |
| `/auth/providers` | GET | 支持的认证提供商 | 否 |
| `/code/run` | POST | 执行代码 | Bearer |
| `/submissions/` | GET/POST | 判题提交 | Bearer |
| `/announcement/` | GET/POST | 公告列表/创建 | GET 公开 |
| `/announcement/<id>` | GET/PUT/DELETE | 公告详情/编辑/删除 | 编辑需 manager |
| `/user/code` | GET/POST | 用户代码存储 | Bearer |

Swagger 文档地址：`https://ojapi.xauat.site/`

## 环境变量

```bash
# 数据库
DB_HOST=host
DB_PORT=5432
DB_NAME=lettest
DB_USER=user
DB_PASSWORD=pass

# Redis
REDIS_HOST=host
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=pass

# JWT
JWT_SECRET_KEY=your-key
JWT_ACCESS_TOKEN_EXPIRE=3600
JWT_REFRESH_TOKEN_EXPIRE=604800

# OIDC 提供商 (iOSClub)
IOSCLUB_ISSUER=https://api.xauat.site
IOSCLUB_CLIENT_ID=your-client-id
IOSCLUB_CLIENT_SECRET=your-secret
IOSCLUB_SCOPE=openid profile

# 前端地址
FRONTEND_URL=https://oj.xauat.site
PUBLIC_BACKEND_URL=https://ojapi.xauat.site
```

## 快速开始

### 后端

```bash
cd webapi/fastapi_of_letcoing
pip install -r requirements.txt
cp .env.example .env    # 编辑配置
python main.py
```

### 前端

```bash
cd webapp/letapp
npm install
cp .env.example .env    # 编辑 API 地址
npm run dev             # 开发模式
npm run build           # 生产构建
```

### 线上地址

- 前端：https://oj.xauat.site
- API：https://ojapi.xauat.site

## 许可证

MIT License - 详见 [LICENSE](LICENSE)
