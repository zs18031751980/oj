# Zeabur 部署说明

这个仓库是一个前后端分离的 monorepo：

- 前端：`webapp/letapp`
- 后端：`webapi/fastapi_of_letcoing`

请在 Zeabur 中把前端和后端拆成两个服务部署，不要把仓库根目录直接当成一个服务发布。

## 部署结构

建议从同一个 Git 仓库创建两个服务：

1. 前端服务 
2. 后端服务

每个服务都需要在 Zeabur 中单独设置 `Root Directory`，让平台进入正确的子目录进行构建和启动。

## 前端服务

建议使用下面这组配置：

- 服务类型：静态站点，或者带静态产物输出的 Node.js 服务
- `Root Directory`：`webapp/letapp`
- 安装命令：`npm install`
- 构建命令：`npm run build`
- 输出目录：`dist`

建议配置的环境变量：

- `VITE_API_BASE_URL=https://你的后端域名.zeabur.app`
- `ZBPACK_OUTPUT_DIR=dist`

说明：

- 当前前端使用的是 Vue Router 的 history 模式。
- Zeabur 静态托管支持 SPA 回退到 `index.html`，所以像 `/learn`、`/playground` 这样的前端路由，在前端服务以静态站点方式部署后应该可以正常打开。

## 后端服务

建议使用下面这组配置：

- 服务类型：Python / Flask
- `Root Directory`：`webapi/fastapi_of_letcoing`
- 安装命令：`pip install -r requirements.txt`
- 启动命令：`python main.py`

必须配置的环境变量：

- `API_TOKEN=你的 glot API token`
- `JWT_SECRET_KEY=替换成一个足够长的随机密钥`
- `FRONTEND_URL=https://你的前端域名.zeabur.app`
- `ALLOWED_ORIGINS=https://你的前端域名.zeabur.app`
- `PUBLIC_BACKEND_URL=https://你的后端域名.zeabur.app`

可选环境变量：

- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_DB`
- `REDIS_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GITHUB_REDIRECT_URI`
- `OIDC_PROVIDERS`

说明：

- 当前后端代码已经按 Zeabur 的要求监听 `PORT`，这一点不需要你额外改代码。
- 后端部署完成后，访问根路径 `/` 会返回一段简单的 JSON 状态信息。
- Swagger 文档地址是 `/swagger/`。
- 健康检查地址可以使用 `/healthz`。

## 推荐的域名分配方式

建议前后端使用不同的域名或子域名：

- 前端：`https://你的前端域名.zeabur.app`
- 后端：`https://你的后端域名.zeabur.app`

然后把前端的 `VITE_API_BASE_URL` 指向后端域名。

## 部署完成后的检查清单

部署完成后，建议检查下面这些地址：

前端：

- `https://你的前端域名.zeabur.app/`
- `https://你的前端域名.zeabur.app/learn`
- `https://你的前端域名.zeabur.app/playground`

后端：

- `https://你的后端域名.zeabur.app/`
- `https://你的后端域名.zeabur.app/healthz`
- `https://你的后端域名.zeabur.app/swagger/`

预期结果：

- 前端路由返回 Vue 页面
- 后端 `/` 返回 JSON
- 后端 `/healthz` 返回 `{"status":"ok"}`
- 后端 `/swagger/` 能正常打开接口文档

## 常见错误

下面这些是最容易踩到的坑：

- 把整个仓库根目录直接部署成一个服务
- 把前端域名误填到 `VITE_API_BASE_URL`
- 忘记给后端服务设置 `Root Directory`
- 忘记把 `ALLOWED_ORIGINS` 设置成前端域名
- 把主站域名绑到后端服务上，却希望它显示前端首页

## 本地参考文件

- 前端环境变量模板：[webapp/letapp/.env.example](./webapp/letapp/.env.example)
- 后端环境变量模板：[webapi/fastapi_of_letcoing/.env.example](./webapi/fastapi_of_letcoing/.env.example)
