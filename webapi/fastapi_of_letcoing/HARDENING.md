# 后端优化交付与部署说明

本次实现覆盖此前 14 项建议。前端仅调整 OAuth code 兑换、刷新令牌单次轮换和跨标签页协调；Vue 模板、样式、页面布局未修改。以下区分代码实现、已完成验证和仍需部署环境验证的部分。

## 逐项对应

| 项目 | 已实现的改造 | 核心位置/验证 |
|---|---|---|
| 1. 执行隔离 | API/Worker 分离；编译和每个测试点使用独立 Docker 容器，禁网、只读根目录、cgroup、非 root 用户程序、监督器身份隔离；生产拒绝 local | sandbox_service.py、execution_runtime.py、Dockerfile.sandbox；专用 Docker 集成测试待有 daemon 的环境执行 |
| 2. 提交越权 | 查询必须登录，仅本人/manager 可见；普通结果只读数据库，过滤隐藏输入和答案 | submission_controller.py；真实持久化记录的跨用户访问回归 |
| 3. 会话撤销 | PostgreSQL 会话状态；验证时检查最新用户；退出、停用、密码修改撤销会话；刷新令牌一次性轮换，重放撤销整会话；第三方同步不能重新启用本地停用账号 | jwt_service.py、user_service.py；停用、退出、重放、改密、Redis 故障测试 |
| 4. OAuth 与密钥 | 回调 URL 不含 access/refresh token，只含 60 秒、单次、绑定浏览器 session 的 code；生产独立随机密钥强校验，安全 Cookie；前端异步兑换 | auth_controller.py、runtime_config.py；OAuth 绑定/重放与 Playwright 回归 |
| 5. 资源滥用 | 分路由、方法及用户/IP 限流；密码登录另有跨 IP 账号预算；Redis 不可用时限流请求返回 503；同步运行全局 16、每主体 2 并发；普通/比赛各自每用户 3 个未完成提交 | auth_middleware.py、redis_service.py；真实 Redis 限流/并发测试 |
| 6. 普通提交持久化 | Submission 与 outbox 同事务；幂等键去重；数据库失败返回 503；无测试点返回 SystemError；Redis 丢失后从数据库补投 | submission_outbox.py、judge_service.py；队列丢失、重复投递、空测试集测试 |
| 7. 队列恢复 | Lua 原子认领与租约、唯一 receipt、续租、数据库 attempt 栅栏、延迟重试、5 次死信、终态持久化与有界死信归档；maintenance 独立线程 | redis_service.py、judge_service.py；过期 ACK、多次 Worker 崩溃、死信、补投测试 |
| 8. 进程监督 | stdin/stdout/stderr 非阻塞同截止时间；输出 1 MiB；清理进程组；cgroup 统计完整进程树；墙钟时间不含容器启动 | execution_runtime.py；堵塞 stdin 测试；Docker 资源验收单独执行 |
| 9. 数据库稳健性 | contextmanager 仅 yield 一次；写操作默认不自动重试；共享连接池、请求/任务结束归还；连接/池/SQL/锁超时；事务错误响应回滚；严格解析 DATABASE_URL | db_robust.py、db_models.py、contest_lifecycle.py；真实 PostgreSQL 迁移和错误回滚测试 |
| 10. HTTP 客户端 | aiohttp session 由单独长期事件循环拥有；连接池、DNS 缓存、超时、并发上限、有限熔断、流式响应上限、退出清理 | glot_service.py；真实本地 HTTP 服务跨事件循环调用回归 |
| 11. 查询性能 | 参赛者 JOIN/批量取数；终态事务推进榜单版本，后台构建 LIVE 快照；普通榜单 15 秒缓存和可选分页；提交历史/AC/比赛榜单索引 | rankings/contest_rankings_controller.py；1 人到 40 人查询次数不增长、快照版本回归 |
| 12. 请求与上传 | JSON 对象/字段类型/字节长度校验、语言白名单、资源限制；头像真实解码验证、尺寸限制、重新编码 JPEG、随机文件名 | request_validation.py、request_middleware.py、user_controller.py；伪 MIME、null 源码、测试数据类型/体积测试 |
| 13. 部署与监控 | 无迁移/Worker 副作用的应用工厂，Gunicorn、独立 CLI、非 root API/Worker 镜像、两份 Compose；分离 liveness/readiness；保护的 Prometheus、JSON 脱敏日志、request_id | app_factory.py、manage.py、deploy/、observability.py；工厂、日志、迁移失败、seed 失败回归 |
| 14. 测试/CI/文档 | 真实 Redis/PostgreSQL 测试、浏览器回归、严格 Docker 验收、依赖漏洞审计；更新 README/判题架构/AGENTS/配置模板 | tests/、.github/workflows/backend.yml；依赖锁定版本更新 |

## 本地验证与限制

- 后端 `python -m pytest -q`：60 项全部通过，包含 PostgreSQL 临时集群、Redis Unix socket、本地 HTTP 上游和显式开发执行器；不连接用户部署数据库。
- 前端 `npm run build` 已成功，`npx playwright test` 的 5 项登录/现有样式测试全部通过。
- 依赖审计初次报告 11 个包、125 条已知漏洞记录；升级锁定版本后 `pip-audit -r requirements.txt` 返回 `No known vulnerabilities found`。这表示查询时的公开公告结果，不代表不存在未知漏洞。
- 两份 Compose 已通过 `docker compose config --no-env-resolution --quiet` 的配置语法验证。
- 本机没有可用 Docker daemon，未完成镜像构建或容器隔离验收。CI 包含镜像构建及 `tests/sandbox_integration.py`，缺少 daemon、镜像或 cgroup v2 会失败，不会跳过。必须在部署环境完成该项后再开放比赛判题。
- 没有执行生产数据迁移、线上 OAuth 提供商联调或生产负载测试；没有给出虚构的 QPS、P95 或性能提升比例。上线前应用真实数据量与并发基线验证索引计划、队列等待时间和 JVM/Go 冷编译开销。

## 部署步骤

所有命令在本后端目录执行。API 与 Worker 分别部署到 API 主机和独立判题主机；PostgreSQL/Redis 由受限内网提供。Worker 可连数据库/Redis/Judge0，用户程序所在的容器禁网。Compose 不包含数据库或 Judge0 服务的自动安装。

1. 备份数据库，并验证备份可恢复。暂停新的提交，等待旧 Worker 排空后停掉旧 API/Worker，避免旧版本继续写入。
2. 从 `.env.example` 创建 `.env.production` 和判题主机的 `.env.worker.production`。分别用 `python -c 'import secrets; print(secrets.token_urlsafe(48))'` 生成 JWT、Flask Session、监控密钥。模板占位值不能作为部署密钥。两端业务密钥、数据库和 Redis 必须匹配；禁止把实际 env 文件加入版本库。
3. 设置 HTTPS `FRONTEND_URL`、`PUBLIC_BACKEND_URL`、精确 `ALLOWED_ORIGINS`。代理重写并清除外部传入的转发头；仅当 API 无法被绕过代理直连时设置正确 `TRUSTED_PROXY_HOPS`。生产 Cookie 为 Secure/HttpOnly/SameSite=None；前后端宜在同一站点下，跨站 Cookie 受浏览器策略影响，需联调 OAuth 跳转和兑换。
4. 在构建环境生成镜像，推送到自己的镜像仓库并以固定 digest 发布；示例本地标签只用于说明：

   ```sh
   docker build -t letcoding-api:local .
   docker build -f Dockerfile.worker -t letcoding-worker:local .
   docker build -f Dockerfile.sandbox -t letcoding-sandbox:local .
   ```

5. 使用新 API 镜像显式迁移和 seed；任何非零退出必须停止发布。大型数据库可仅为迁移命令提高 SQL 超时，应用继续使用 15 秒默认值：

   ```sh
   docker run --rm --env-file .env.production -e DB_STATEMENT_TIMEOUT_MS=300000 letcoding-api:local python manage.py migrate
   docker run --rm --env-file .env.production letcoding-api:local python manage.py seed
   ```

6. API 主机创建 `/var/lib/letcoding/uploads`，判题主机创建 `/var/lib/letcoding/jobs`，两者属主均为 UID/GID 10001；把原有头像数据复制到新的上传目录。Worker 工作目录的宿主机和容器绝对路径必须相同，因为 Docker daemon 在宿主机解析 bind mount。
7. 在独立判题主机以非 root、有权使用 Docker 的账号运行沙箱验收。该账号 UID/GID 必须大于 0，Docker 使用 cgroup v2；按实际镜像名设置 `JUDGE_SANDBOX_IMAGE`：

   ```sh
   python -m pytest tests/sandbox_integration.py -q
   ```

8. 启动独立服务。不要把 Docker socket 挂到 API，不要共用承载 API 的 Docker daemon：

   ```sh
   # API 主机
   docker compose -f deploy/compose.api.yaml up -d
   # 判题主机，DOCKER_GID 对应真实 socket 的组号
   export DOCKER_GID="$(stat -c '%g' /var/run/docker.sock)"
   docker compose -f deploy/compose.worker.yaml up -d
   ```

9. 检查 `/healthz`、`/readyz`、`/healthz/judge`，内部采集 `/metrics`；用测试账号完成登录、普通提交、带隐藏用例比赛提交、参考校验/发布及榜单更新。验证后恢复提交入口。

## 迁移兼容与回退

- `0017_backend_hardening` 添加普通提交的任务/幂等字段、比赛结果字段、参考校验版本及榜单推进版本；AuthSession/OAuthGrant/普通 outbox/参考任务等新表由显式迁移命令创建。迁移通过 PostgreSQL advisory lock 串行，每条迁移的 DDL 与记录在同一事务提交。
- 旧 JWT 没有持久化 session/issuer/audience，升级后用户需要重新登录；前后端登录逻辑应同批发布。不要继续接收旧 URL 形式的 access/refresh token。
- 旧普通 Pending/Running 且没有 job_id 的记录无法可靠恢复，迁移明确标为 SystemError；不为它们伪造 AC。旧 Redis-only 普通记录不自动认领为持久化结果。部署前先排空旧队列，保留备份供审计，禁止直接清空共享 Redis。
- 已发布比赛保留既有测试数据并标为已验证，避免升级改变历史赛题；草稿进入后台校验，只有提供的测试数据和参考代码通过校验后才能发布。不再依据任意参考代码猜测输入格式生成测试数据。
- 新增索引可能持锁/耗时；超时应安排维护窗口排查并重跑，不能吞掉错误继续启动。当前没有对生产数据规模做迁移时长估计。
- 回退应在暂停写入后使用成套旧应用和经验证的数据库备份；没有提供自动破坏性 down migration，也不应让旧 Worker 消费新队列后直接继续生产运行。

## 运维基线

- Redis 使用认证、受限网络、持久化 AOF 和 `maxmemory-policy noeviction`。缓存与任务共实例时必须预留容量；禁止只删除 ready/processing 键而保留去重键。完整 Redis 数据丢失会触发数据库分页补投，但进行中的执行可能重复，数据库版本栅栏负责拒绝旧结果。
- 队列 pending 上限 1000，超限的新任务留在数据库 outbox；不要仅盯 Redis 长度，必须同时监控 outbox 数量和等待时间。每个 Worker 当前串行执行一份任务，扩容数量按判题主机 CPU、编译 512 MiB 和运行最大 2048 MiB 的资源预算确定。
- 数据库连接预算按 `API 副本数 × WEB_WORKERS × DB_MAX_CONNECTIONS + Worker 进程数 × DB_MAX_CONNECTIONS + 迁移/运维预留` 计算。模板 2 个 API 进程、1 个 Worker、每池 8 条约为 24 条上限，再留管理连接；线程数和副本变化时重新计算。
- 建议告警：readiness 失败、Worker 心跳超过 30 秒、outbox 最老等待持续增加、dead 出现、5xx 比例异常及 HTTP P95 上升。Prometheus 多进程目录在每次新容器启动时为空，不能跨重启复用旧计数文件。
- 会话和 OAuth 临时代码要定期清理已过期数据库记录；执行任务目录需要磁盘配额、容量告警和宿主机异常退出后的孤儿容器/目录巡检。清理必须确认没有活跃任务，不按任意路径自动删除。
- 普通运行仍保持原有远程执行架构，生产应设置自建/受信任 `JUDGE0_BASE_URL`，在该服务启用隔离及资源限制。仓库中的 Docker 沙箱验收只覆盖比赛/参考验证执行链路。

## 本轮审查落实

后续安全、性能与健壮性优化的逐项实现、Cookie 兼容性变化、迁移和部署验收步骤见 [REVIEW_IMPLEMENTATION.md](REVIEW_IMPLEMENTATION.md)。该文件明确区分已通过的本地回归与尚未通过的 Docker/生产环境验收。

当前比赛链路与部署契约见 [ACM 专项落实记录](ACM_IMPLEMENTATION.md)。
