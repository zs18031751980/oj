# LetCoding 后端

Flask + Flask-RESTX API，PostgreSQL 保存业务事实，Redis 负责限流、缓存及任务运输。目录名保留历史名称，实际框架不是 FastAPI。

普通代码运行/题库判题通过可配置 Judge0 服务；比赛提交和参考答案校验由独立 Worker 的 Docker 沙箱执行。API 进程不运行编译器、不启动 Worker、不自动迁移数据库。

## 开发与验证

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
# 配置数据库、Redis、独立密钥等环境变量；开发时 APP_ENV=development 才加载 .env。
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed
.venv/bin/python main.py
# Worker 单独启动；默认需要 Docker 沙箱镜像。
.venv/bin/python manage.py worker
.venv/bin/python -m pytest -q
```

开发 API 默认监听 `127.0.0.1:6173`。测试使用隔离的临时 Redis/PostgreSQL，需要本机安装 redis-server、PostgreSQL 工具、g++ 和 JDK；可用 `PG_BINDIR` 指定 PostgreSQL 的 bin 目录。开发测试中的本地执行不提供生产安全保证。

## 部署与接口

详细部署顺序、配置、14 项改造对应关系、迁移兼容和验收限制见 [HARDENING.md](HARDENING.md)。沙箱结构见 [JUDGE_ARCHITECTURE.md](JUDGE_ARCHITECTURE.md)。配置模板为 [.env.example](.env.example)，依赖版本以 requirements.txt 为准。

- 生产入口：`gunicorn --config gunicorn.conf.py 'app_factory:create_app()'`。
- Swagger：`/swagger/`；路由及语言支持以控制器和 `JUDGE0_LANGUAGES` 为准。
- `/healthz` 进程存活；`/readyz` 检查数据库与 Redis；`/healthz/judge` 检查 Worker 心跳。
- `/metrics` 需要独立 `METRICS_TOKEN` Bearer 凭证，应仅由内部监控访问。
- OAuth 浏览器回调只携带一次性 code；`POST /auth/exchange` 结合浏览器会话兑换令牌。
- 提交记录仅本人及 manager 可查询；响应不返回隐藏测试输入或答案。

生产保障、迁移与验收要求：[PRODUCTION_READINESS.md](PRODUCTION_READINESS.md)。
