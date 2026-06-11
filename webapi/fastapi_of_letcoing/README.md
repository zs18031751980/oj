# 代码运行 API 服务

## 介绍

这是一个基于 Flask + Flask-RESTX 框架开发的代码运行 API 服务，通过调用 Glot API 实现多种编程语言的代码在线执行功能。该服务采用分层架构设计，具有完整的 API 文档和 Swagger UI，为前端应用提供了稳定、高效的代码运行支持。

## 功能特点

- **多语言支持**: 支持 30+ 种编程语言，包括 Python、JavaScript、Java、C++ 等
- **用户认证**: 支持第三方 OIDC 登录（GitHub、自定义 OIDC 提供商）
- **JWT 鉴权**: 基于 JWT 的令牌认证和 Redis 缓存支持
- **API 文档生成**: 集成 Flask-RESTX，自动生成 Swagger 文档和交互式 UI
- **异步执行**: 使用 aiohttp 实现异步 HTTP 请求，提高并发处理能力
- **分层架构**: 控制器和服务层分离，提高代码可维护性
- **数据模型化**: 使用 dataclass 定义清晰的数据模型，提供 API 参数验证
- **错误处理**: 完善的错误处理机制，返回友好的错误信息
- **安全设计**: 实现了基本的输出转义，防止注入攻击
- **速率限制**: 基于用户的请求速率限制功能
- **环境配置**: 支持通过环境变量设置 API Token 和认证配置

## 技术栈

- **框架**: Flask 3.1.2
- **API 文档**: Flask-RESTX 1.3.2
- **异步支持**: aiohttp 3.13.2
- **数据处理**: Python 内置 dataclass
- **HTTP 客户端**: requests 2.32.5
- **认证授权**: Authlib 1.3.1, PyJWT 2.9.0
- **缓存**: Redis 5.2.1
- **外部服务**: Glot API (https://glot.io/)

## 支持的编程语言

| 语言 | 关键字 | 语言 | 关键字 | 语言 | 关键字 |
|------|--------|------|--------|------|--------|
| Assembly | assembly | C | c | C++ | cpp |
| C# | csharp | Clojure | clojure | CoffeeScript | coffeescript |
| Crystal | crystal | D | d | Elixir | elixir |
| Elm | elm | Erlang | erlang | F# | fsharp |
| Go | go | Groovy | groovy | Hare | hare |
| Haskell | haskell | Idris | idris | Java | java |
| JavaScript | javascript | Julia | julia | Kotlin | kotlin |
| Lua | lua | Mercury | mercury | Nim | nim |
| Nix | nix | OCaml | ocaml | Perl | perl |
| PHP | php | Python | python | Raku | raku |
| Ruby | ruby | Rust | rust | Scala | scala |
| Swift | swift | TypeScript | typescript | Zig | zig |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

#### 基本配置

```bash
# Glot API Token（必需）
export API_TOKEN=your_glot_api_token

# JWT 配置（推荐设置）
export JWT_SECRET_KEY=your-very-secure-secret-key-here
export JWT_ACCESS_TOKEN_EXPIRE=3600  # 1小时
export JWT_REFRESH_TOKEN_EXPIRE=604800  # 7天

# Redis 配置（推荐用于生产环境）
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=your-redis-password
export REDIS_TIMEOUT=5
```

#### OAuth 认证配置

```bash
# GitHub OAuth
export GITHUB_CLIENT_ID=your_github_client_id
export GITHUB_CLIENT_SECRET=your_github_client_secret

# 自定义 OIDC 提供商（JSON格式）
export OIDC_PROVIDERS='{
  "my_provider": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "server_metadata_url": "https://your-provider.com/.well-known/openid-configuration"
  }
}'
```

#### 配置文件方式

在项目根目录创建 `.env` 文件：

```
API_TOKEN=your_glot_api_token
JWT_SECRET_KEY=your-very-secure-secret-key-here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_TIMEOUT=5
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:6173` 启动。

## API 文档

### 🌐 Swagger 文档

- **Swagger UI**: `http://localhost:6173/swagger/`
- **API JSON**: `http://localhost:6173/swagger.json`

### 📋 API 端点

#### 认证相关 API

##### POST /auth/login

获取认证授权URL。

**请求参数:**
| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| provider | string | 是 | 认证提供商 | `github` |
| redirect_uri | string | 否 | 回调地址 | `http://localhost:3000/callback` |

**请求示例:**
```json
{
  "provider": "github"
}
```

**成功响应 (200):**
```json
{
  "success": true,
  "authorization_url": "https://github.com/login/oauth/authorize?client_id=..."
}
```

##### GET /auth/callback/{provider}

处理认证回调。

**响应示例:**
```json
{
  "success": true,
  "user_info": {
    "id": "123456",
    "username": "username",
    "email": "user@example.com",
    "provider": "github"
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

##### POST /auth/refresh

刷新访问令牌。

**请求参数:**
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

##### POST /auth/logout

登出（撤销令牌）。

**请求头:**
```
Authorization: Bearer <access_token>
```

##### GET /auth/verify

验证访问令牌有效性。

##### GET /auth/providers

获取支持的认证提供商列表。

#### 代码执行 API

##### POST /code/run

运行指定语言的代码（需要认证）。

**请求参数:**

| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| code | string | 是 | 要运行的代码 | `print("Hello World")` |
| language | string | 否 | 编程语言，默认为 javascript | `python` |
| stdin | string | 否 | 标准输入 | `input data` |

**请求示例:**

```json
{
  "code": "console.log(\"Hello, World!\")",
  "language": "javascript",
  "stdin": ""
}
```

**成功响应 (200):**

```json
{
  "message": "代码执行成功",
  "stdout": "Hello, World!\n"
}
```

**错误响应 (400):**

```json
{
  "error": "请配置API_TOKEN环境变量或ApiToken配置项。"
}
```

#### GET /api/v1/

服务健康检查端点。

**响应示例:**

```json
{
  "message": "Hello World"
}
```

### 🔍 使用示例

```bash
# 认证登录
curl -X POST http://localhost:6173/auth/login \
  -H "Content-Type: application/json" \
  -d '{"provider": "github"}'

# 使用认证后的 token 调用代码执行 API
curl -X POST http://localhost:6173/code/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "language": "python"
  }'

# 查看 Redis 服务器状态
redis-cli ping

# 测试代码执行接口（会使用 Redis 缓存）
curl -X POST http://localhost:6173/code/run/public \
  -H "Content-Type: application/json" \
  -d '{
    "code": "console.log(\"Hello, World!\")",
    "language": "javascript"
  }'

# 查看完整 API 文档
open http://localhost:6173/swagger/
```

## 项目架构

### 目录结构

```
fastapi_of_letcoing/
├── controllers/           # 控制器层
│   ├── __init__.py
│   ├── code_controller.py    # 代码执行控制器，API 路由和参数验证
│   └── auth_controller.py    # 认证控制器，OAuth 和 JWT 相关接口
├── core/                  # 核心模块
│   ├── di_container.py        # 依赖注入容器
│   └── service_config.py     # 服务配置
├── interfaces/            # 接口定义
│   ├── __init__.py
│   └── service_interfaces.py # 服务接口定义
├── middleware/            # 中间件
│   └── auth_middleware.py     # JWT 认证中间件
├── models/                # 数据模型
│   ├── __init__.py
│   ├── auth_models.py         # 认证相关数据模型
│   └── glot_models.py         # Glot API 数据模型
├── services/              # 服务层
│   ├── config_service.py      # 配置服务
│   ├── glot_service.py        # Glot API 调用服务，业务逻辑
│   ├── jwt_service.py         # JWT 认证服务
│   ├── logger_service.py      # 日志服务
│   ├── oidc_service.py        # OIDC 认证服务
│   └── redis_service.py       # Redis 缓存服务
├── main.py               # Flask 应用入口，API 配置
├── requirements.txt       # 项目依赖列表
├── .gitignore            # Git 忽略文件配置
└── README.md             # 项目说明文档
```

### 架构设计

#### 分层架构

1. **控制器层 (Controllers)**
   - 处理 HTTP 请求和响应
   - 参数验证和序列化
   - API 文档注解
   - 错误处理
   - 认证相关的路由处理

2. **服务层 (Services)**
   - 业务逻辑实现
   - 外部 API 调用
   - 数据转换和处理
   - JWT 和 OIDC 认证服务
   - Redis 缓存服务
   - 日志和配置管理

3. **数据层 (Models)**
   - 使用 dataclass 定义数据结构
   - 类型提示和验证
   - 认证和业务数据模型

4. **中间件层 (Middleware)**
   - JWT 认证中间件
   - 速率限制中间件
   - 权限控制中间件

5. **核心层 (Core)**
   - 依赖注入容器
   - 服务配置管理

6. **接口层 (Interfaces)**
   - 服务接口抽象
   - 提高可测试性和可扩展性

### 核心代码说明

#### CodeExecutionController 类

控制器类，负责：
- API 路由定义 (`/api/v1/code/run`)
- 请求参数验证 (使用 Flask-RESTX 模型)
- 响应格式化
- Swagger 文档生成

#### GlotService 类

核心服务类，负责：
- 与 Glot API 异步交互
- 代码执行逻辑
- 错误处理和转义
- 语言映射管理

#### 数据模型

- `PostFile`: 表示代码文件的数据模型
- `PostDataModel`: 表示发送给 Glot API 的请求数据模型
- `RunResult`: 表示代码执行结果的数据模型

## 环境要求

- Python 3.7+
- 网络连接（需要访问 Glot API）

## 开发指南

### 添加新的 API 端点

1. 在 `controllers/` 目录下创建新的控制器文件
2. 定义命名空间和数据模型
3. 实现资源类和业务逻辑
4. 在 `main.py` 中注册命名空间

```python
# 示例：新增控制器
from flask_restx import Namespace, Resource, fields

api = Namespace('new_feature', description='新功能')

@api.route('/action')
class NewController(Resource):
    def get(self):
        return {'message': 'Hello from new feature'}
```

### 代码规范

- 使用 4 空格缩进
- 遵循 PEP 8 代码风格
- 使用类型提示
- 编写完整的文档字符串
- 控制器只处理 HTTP 逻辑，业务逻辑放在服务层

### 测试

```bash
# 运行应用
python main.py

# 测试 API 端点
curl http://localhost:6173/

# 测试认证提供商列表
curl http://localhost:6173/auth/providers

# 查看 Swagger 文档
open http://localhost:6173/swagger/

# 测试 Redis 连接
redis-cli ping

# 测试公共代码执行接口（无需认证，使用 Redis 缓存）
curl -X POST http://localhost:6173/code/run/public \
  -H "Content-Type: application/json" \
  -d '{
    "code": "console.log(\"Hello, World!\")",
    "language": "javascript"
  }'
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../../../LICENSE) 文件了解详情。
