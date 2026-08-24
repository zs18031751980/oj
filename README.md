# iOS Club 代码综合平台

iOS Club 代码综合平台是一个集**在线编程、代码评测、学习资源与公告管理**于一体的综合性 Web 应用，为社团成员提供便捷的编程学习和实践环境。

## 核心功能

| 模块 | 说明 |
|------|------|
| **在线编程** | Monaco Editor 驱动的在线代码编辑器，支持 8 种编程语言，快捷键 `Ctrl+Enter` 运行 |
| **代码评测** | 在线判题系统（OJ），支持题目浏览、代码提交、测试用例验证 |
| **学习资源** | Markdown 驱动的学习文档，支持 Mermaid 图表、代码高亮、任务列表等扩展语法 |
| **用户系统** | OIDC 统一认证（iOSClub 账号登录），支持 GitHub OAuth；登录时同步资料、账号状态与最后登录时间，并按 `manager > staff > member` 管理权限 |
| **公告管理** | 公开展示已发布公告；`manager` 可创建、修改、删除及管理草稿，支持左侧 Markdown 原文、右侧实时渲染预览 |
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
用户 ──→ iOSClub OIDC / GitHub OAuth ──→ 授权回调
  │                                         │
  └──── 资料 / 状态 / 最后登录时间同步 ←────┘
                    │
       角色归一化并只升不降（保留本地提权）
                    │
          manager / staff / member
                    │
         JWT 签发与 Redis 用户缓存
                    │
       令牌验证 / 刷新 / 黑名单机制
```

第三方用户通过 `provider + provider_id` 匹配并原地更新，已有用户主键不会改变。提供方角色只会提升本地权限，不会覆盖本地手工提升的更高角色；账号状态仅在提供方返回可识别值时同步。JWT 和 Redis 缓存均携带最新的 `is_active` 与 `last_login`。

### 角色权限

| 角色 | 内部标识 | 包含身份 |
|------|---------|---------|
| 管理身份 | `manager` | 管理员、社长、副社长、部长、副部长、部门主管 |
| 部员 | `staff` | 部员、干事 |
| 成员 | `member` | 社员、普通用户 |

多身份用户自动取最高权限角色。管理后台路由（`/admin` 下）以及公告的写入、草稿读取允许 `manager` 与 `staff` 进入（见 `announcement-access.ts` 与 `announcement_controller._require_editor`）；其中用户删除、启用/停用等敏感操作仅 `manager` 可执行（见 `admin_controller._require_manager`）。后端权限校验是最终边界。

### 公告工作流

- 公开公告页通过数据库 API 加载内容，匿名用户只能查看已发布公告，草稿不会通过公开列表或详情泄露。
- `manager` 与 `staff` 可进入 `/admin/announcements` 创建、编辑、删除公告，并在已发布与草稿状态之间切换。
- 编辑器在桌面端左侧显示原始 Markdown、右侧显示与公告详情一致的渲染结果；移动端自动改为上下排列。
- 修改公告时在原 ORM 记录上保存，公告主键保持不变；保存或删除失败时保留当前编辑内容和页面状态。

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
| `/announcement/` | GET | 已发布公告列表 | 否 |
| `/announcement/?include_unpublished=true` | GET | 包含草稿的管理列表 | `manager` |
| `/announcement/` | POST | 创建公告 | `manager` |
| `/announcement/<id>` | GET | 已发布公告详情；草稿详情仅管理身份可读 | 公开 / `manager` |
| `/announcement/<id>` | PUT/DELETE | 原地修改或删除公告 | `manager` |
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
