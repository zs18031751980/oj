# OJ 项目（iOS Club 代码综合平台）

> 一个集**在线编程、代码评测、学习资源**于一体的 Web 应用，为社团成员提供编程学习和实践环境。

## 基本信息

| 项目 | 说明 |
|------|------|
| 项目名称 | LetCoding / iOS Club 代码综合平台 |
| 前端地址 | https://oj.xauat.site |
| 后端地址（API/Swagger） | https://ojapi.xauat.site |
| 本地代码路径 | `/home/z/桌面/code/oj` |
| 许可证 | MIT |

## 核心功能

| 模块 | 说明 |
|------|------|
| **在线编程** | Monaco Editor 代码编辑器，支持 8 种语言，`Ctrl+Enter` 运行 |
| **代码评测** | 在线判题系统（OJ），题目浏览、代码提交、测试用例验证 |
| **学习资源** | Markdown 文档（Mermaid 图表、代码高亮、任务列表） |
| **用户系统** | OIDC 统一认证（iOSClub）+ GitHub OAuth，三级角色 |
| **公告管理** | 公告 CRUD，部长及以上可编辑，Markdown 富文本 |
| **主题切换** | 浅色 / 深色 / 跟随系统，持久化到服务端 |

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   前端 (webapp/letapp)              │
│  Vue 3 + TypeScript + Vite 7                        │
│  ├─ Naive UI / Tailwind CSS 4 / Monaco Editor      │
│  ├─ Pinia 状态管理 / Vue Router 4                   │
│  └─ markdown-it 渲染 (Mermaid + Prism.js + KaTeX)  │
├─────────────────────────────────────────────────────┤
│                    HTTP / REST API                  │
├─────────────────────────────────────────────────────┤
│              后端 (webapi/fastapi_of_letcoing)      │
│  Flask 3 + Flask-RESTX + Swagger                    │
│  ├─ controllers/   控制器层（auth/code/submission/  │
│  │                  announcement/user_code）        │
│  ├─ services/      服务层（oidc/jwt/judge/glot/     │
│  │                  user/database/redis）           │
│  ├─ models/        Peewee ORM 模型 + DTO            │
│  ├─ middleware/    中间件（JWT 验证/角色权限/限流） │
│  ├─ interfaces/    抽象接口（ABC + DI 依赖注入）    │
│  ├─ core/          核心（DI 容器/服务配置）         │
│  └─ utils/         工具（角色归一化等）             │
├─────────────────────────────────────────────────────┤
│                   数据层                             │
│  ├─ PostgreSQL  用户/题目/提交/公告                 │
│  ├─ Redis       JWT 缓存/会话/限流/公告缓存         │
│  └─ Glot.io API 远程代码执行沙箱                    │
└─────────────────────────────────────────────────────┘
```

## 认证与角色

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

> 多身份用户自动取最高权限角色（manager > staff > member）。

### 登录方式

| 方式 | 接口 | 说明 |
|------|------|------|
| iOSClub OAuth 页面登录 | `/auth/login/iOSClub` | 浏览器跳转到 iOSClub 授权页 |
| iOSClub 账号密码登录（ROPC） | `/auth/login/iOSClub/password` | 前端 Login 页主登录方式，调用 iOSClub `/Auth/login` |
| 本地密码登录 | `/auth/login/password` | 用本地数据库账号验证 |
| GitHub OAuth | `/auth/login/github` | 需配置 GITHUB_CLIENT_ID/SECRET |

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
| `/auth/logout` | POST | 登出（令牌撤销） | Bearer |
| `/auth/theme` | PATCH | 更新主题偏好 | Bearer |
| `/auth/providers` | GET | 支持的认证提供商 | 否 |
| `/code/run` | POST | 执行代码 | Bearer |
| `/submissions/` | GET/POST | 判题提交 | Bearer |
| `/announcement/` | GET/POST | 公告列表/创建 | GET 公开 |
| `/announcement/?published=true` | GET | 仅已发布公告（公开页） | 否 |
| `/announcement/<id>` | GET/PUT/DELETE | 公告详情/编辑/删除 | 编辑需 manager |
| `/user/code` | GET/POST | 用户代码存储 | Bearer |

## 数据库（PostgreSQL + Peewee）

### 表结构（`models/db_models.py`）

| 表 | 说明 | 关键字段 |
|----|------|---------|
| `users` | 用户 | username/email(唯一)、password_hash、role、provider、provider_id、theme_preference |
| `problems` | 题目 | title、difficulty、time_limit、memory_limit、is_public |
| `testcases` | 测试用例 | problem(FK)、input_data、output_data、is_sample |
| `user_codes` | 用户代码 | user(FK)、problem_id、language（唯一约束） |
| `submissions` | 提交记录 | user(FK)、problem(FK)、status、testcase_results |
| `announcements` | 公告 | title、content(Markdown)、permission、is_published、published_at |

### 性能索引（迁移时自动创建）

- `users(provider, provider_id)` — OAuth 登录查询加速
- `announcements(is_published, published_at DESC)` — 公告列表
- `submissions(user_id, created_at DESC)` — 判题历史
- `submissions(problem_id, status)` — 判题结果面板

## 环境变量

### 后端

```bash
# 数据库
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lettest
DB_USER=postgres
DB_PASSWORD=postgres
DB_MAX_CONNECTIONS=20
DB_STALE_TIMEOUT=300

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# JWT
JWT_SECRET_KEY=your-key
JWT_ACCESS_TOKEN_EXPIRE=3600
JWT_REFRESH_TOKEN_EXPIRE=604800

# OIDC 提供商 (iOSClub)
OIDC_PROVIDER_NAMES=iOSClub
IOSCLUB_ISSUER=https://api.xauat.site
IOSCLUB_CLIENT_ID=your-client-id
IOSCLUB_CLIENT_SECRET=your-secret
IOSCLUB_SCOPE=openid profile
IOSCLUB_REDIRECT_URI=http://localhost:6173/auth/callback/iOSClub

# 前端地址 / CORS
FRONTEND_URL=http://localhost:5173
PUBLIC_BACKEND_URL=http://localhost:6173
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Glot.io 代码执行
API_TOKEN=
```

### 前端

```bash
VITE_API_BASE_URL=http://localhost:6173
VITE_IOSCLUB_OAUTH_URL=https://api.xauat.site/SSO/authorize
VITE_IOSCLUB_CLIENT_ID=your-iosclub-client-id
VITE_IOSCLUB_REDIRECT_URI=http://localhost:6173/auth/callback/iOSClub
VITE_IOSCLUB_SCOPE=openid profile
```

### 配置文件加载机制

`main.py` 按以下优先级加载（后加载覆盖先加载）：
1. 后端层 `.env`（与 main.py 同级）
2. 项目根目录 `.env`
3. `.env.local`（本地覆盖，override=True，**不被 Git 追踪**）
4. 系统环境变量

> `.env.local` 是本地开发推荐方式，安全存放且不污染仓库。

## 本地开发

### 环境准备

本地需要：
- **PostgreSQL**（本地 5432 端口）
- **Redis**（本地 6379 端口）
- Python 3 + 后端依赖
- Node.js + 前端依赖

### 启动后端

```bash
cd webapi/fastapi_of_letcoing
pip install -r requirements.txt
cp .env.example .env.local   # 按需修改
python main.py               # 监听 :6173
```

### 启动前端

```bash
cd webapp/letapp
npm install
cp .env.example .env.local
npm run dev                  # 监听 :5173
```

### 生产构建

```bash
cd webapp/letapp
npm run build                # vue-tsc 类型检查 + vite build
```

### 本地登录验证

| 方式 | 操作 |
|------|------|
| 本地密码登录 | 数据库中创建用户（`werkzeug.security.generate_password_hash` 生成密码哈希），Login 页输入账号密码 |
| iOSClub 密码登录 | 需网络可达 `api.xauat.site`，用真实 iOSClub 账号 |
| iOSClub OAuth | 需配置 `IOSCLUB_CLIENT_SECRET` + iOSClub 服务端 redirect_uri 白名单 |

## 关键实现细节

### 认证热路径优化（jwt_service）
- `verify_access_token` 用 `mget_raw` 单次 Redis 往返同时检查黑名单 + 读取用户缓存
- JWT 载荷包含用户基础信息，Redis 不可用时回退到载荷

### 数据库连接池（关键）
- **单一连接池**：`DatabaseService` 复用 `models.db_models` 的共享连接池（`get_database()`），避免连接数翻倍
- **请求归还**：`@app.teardown_request` 请求结束后归还连接，避免高并发耗尽
- 配置：`DB_MAX_CONNECTIONS=20`，`DB_STALE_TIMEOUT=300`

### 公告数据源
- 已统一为**数据库驱动**（原为前端静态 `.md` 文件，已移除）
- 公开页调用 `/announcement/?published=true`，管理端调用 `/announcement/`
- 列表带 60s Redis 缓存，写操作时失效
- 迁移脚本 `seed_announcements.py` 可导入旧静态公告

### OIDC Provider 注册
- `client_secret` 缺失时仍可注册 provider（ROPC 密码登录只依赖 client_id）
- `client_secret` 仅 OAuth 授权码换令牌需要

## 常见问题排查

### 登录失败
1. **iOSClub 密码登录报"用户不存在或密码错误"** → 这是上游 iOSClub 的真实响应，账号或密码错误
2. **iOSClub OAuth 配置缺失** → 检查前后端 `.env.local` 的 `VITE_IOSCLUB_*` / `IOSCLUB_*` 变量
3. **`unsupported provider`** → 后端 `OIDC_PROVIDER_NAMES` 未声明或 provider 配置不完整
4. **本地连错数据库** → 确认 `.env.local` 的 DB_HOST/PORT/NAME，避免连到其他项目的库

### 后端启动问题
- 表创建失败仅警告不阻塞启动（`create_tables()` 有 try/except）
- 迁移失败同样不阻塞（`migrate_add_role_column()` 逐条 try/except）

### 前端构建
- monaco-editor 体积大（约 3.7MB），已拆分为独立 `vendor-monaco` chunk 并按需加载
- `vue-tsc -b` 类型检查在 build 前执行

## 线上部署

- 后端：Gunicorn 多 worker，监听 gunicorn 端口
- 前端：Vite 构建产物部署到静态服务器
- 线上数据库：`lettest`
- 变更流程：提交 → push → 服务器拉取 → 重启后端 + 重新构建前端
