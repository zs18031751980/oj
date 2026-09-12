# 后端优化与部署验收（2026-09-13）

本轮只修改后端、测试、CI 和部署配置，前端 UI 与前端源码未改动。建议的八项工作对应如下。

| 建议 | 已实现 | 验收状态 |
| --- | --- | --- |
| 1. 数据库迁移与就绪 | Docker/Nixpacks 启动包装器先预检、显式迁移、验证 schema，再启动 Gunicorn；`/readyz` 检查全部已知迁移及模型需要的表/列；允许较新版本的额外迁移/列 | 真实 PostgreSQL 验证缺迁移/缺列拒绝、迁移重跑保留数据；线上 500 的具体根因仍待新日志确认 |
| 2. 真实判题发布门禁 | 全部 CI 成功后才允许把验收 SHA 快进到 production 分支；拒绝已经落后 main 的任务、拒绝非快进覆盖 | 本地真实 Git 仓库验证通过；需配置 GitHub 变量并把 Zeabur 关联到 production；没有修改远程配置 |
| 3. 判题健康 | 支持 contest/practice/rejudge/validation/all 分池检查；心跳有效期、接单状态和排空状态共同决定可用性；监控与健康检查使用同一判断 | 真实 Redis 回归通过；真实判题探测使用 smoke 脚本；没有执行生产提交 |
| 4. 列表性能 | 比赛人数数据库聚合，状态下推 SQL；题库只读取摘要字段并在数据库筛选公开已结束比赛；可选分页、搜索、分类与难度过滤；ETag 条件请求 | SQLite/PostgreSQL 均验证；12 场比赛列表从原 13 条 SQL 降到 1 条；私有化后旧 ETag 不能继续返回 304 |
| 5. 锁与连接预算 | 保留公平性相关比赛锁；新增完整事务耗时直方图，保留锁等待直方图；预检计算 API 进程、Worker 与维护任务连接预算；新增只读数据库连接/权限报告 | 事务失败回滚与指标回归通过；未凭本地数据缩小锁范围或宣称生产吞吐量 |
| 6. 配置与最小权限 | 聚合缺失/错误配置，使用 FLASK_SECRET_KEY 等实际变量名；拒绝 APP_ENV 拼写错误；支持 CA 文件和池等待超时；可要求 verify-full；审计运行账号的高权限 | 预检、证书参数传递、真实 PostgreSQL 权限审计通过；生产 TLS、角色授权及证书仍需实际配置 |
| 7. 沙箱诊断与清理 | 保留有限错误分类、退出码和关联容器 ID，不记录原始 stderr/用户源码；清理失败不覆盖原异常/结果；容器过期标签与有界回收；可信 Docker CLI 独立环境白名单 | 本地故障注入通过；Docker daemon 缺失，真实沙箱门禁未通过 |
| 8. 故障与容量验收 | 新增进程 SIGKILL 后恢复、未提交事务断连回滚、Redis 进程重启后 Outbox 重建、ENOSPC 清理测试；保留已有真实 PostgreSQL 恢复验证及开放到达率压测脚本 | 隔离故障测试通过；专用 Docker 节点、HTTPS 预演容量、生产 PITR/RPO/RTO 仍待环境 |

## Zeabur 启动方式

服务根目录为 `webapi/fastapi_of_letcoing`。如果 Zeabur 中仍配置了自定义 Gunicorn 启动命令，需要改成：

```sh
python -m deploy.start_api
```

Dockerfile 和 Nixpacks 已采用此入口。应用工厂和 Gunicorn Worker 不执行迁移；启动包装器只在启动 Gunicorn 之前运行迁移。

- 默认 `DB_MIGRATION_MODE=migrate`：现有单服务部署使用数据库迁移锁执行迁移，再检查兼容性；失败则不接流量。
- 使用最小权限运行账号时设置 `DB_MIGRATION_MODE=check`：由独立迁移任务使用迁移账号先执行 `python manage.py migrate`，API 只做兼容性检查。Compose 模板采用此模式，迁移任务成功后才启动 API。
- 不要给受限 API 账号增加超级用户权限来绕过检查；迁移与 API 应分别注入各自的凭证。当前 Compose 模板的 env_file 仍需运维按角色拆分。
- 保留已有持久卷和数据库；本轮未删除/重建生产数据库，也未自动执行 seed 或修改业务数据。
- `FLASK_SECRET_KEY` 与 `JWT_SECRET_KEY` 必须独立；预检只报告变量名，不打印变量值。

先运行以下只读预检（环境变量由部署平台注入）：

```sh
python -m deploy.preflight
python -m deploy.audit_database
# 仅对 API/Worker 运行账号使用；迁移账号本来就需要 DDL 权限。
python -m deploy.audit_database --require-least-privilege
```

权限报告检查超级用户、创建角色/数据库、应用表所有权及 schema CREATE 权限；它不替代对具体表 DML 授权和网络访问控制的审计。`lock_waiters_visible_to_role` 只统计当前角色能观察的锁等待。

可选连接预算：

```dotenv
API_REPLICAS=2
WEB_WORKERS=2
DB_MAX_CONNECTIONS=8
WORKER_REPLICAS=4
WORKER_DB_MAX_CONNECTIONS=4
DB_MAINTENANCE_CONNECTIONS=8
DB_CONNECTION_BUDGET=56
DB_POOL_TIMEOUT=5
```

该例连接上界为 `2×2×8 + 4×4 + 8 = 56`。Worker 服务自身的 `DB_MAX_CONNECTIONS` 必须与这里的 `WORKER_DB_MAX_CONNECTIONS` 一致，副本变化时同步预算；预算还需为数据库保留管理连接及其他服务余量。

跨主机数据库连接可配置 `DB_REQUIRE_TLS=1`、`sslmode=verify-full` 和 `DB_SSLROOTCERT=/certs/ca.pem`。DATABASE_URL 中显式 sslmode 优先；没有指定时使用 DB_SSLMODE。证书必须覆盖实际数据库主机名。没有核验平台数据库证书前，不自动更改现有连接模式。

## 发布约束接入

1. 保持 main 的后端、前端契约、Docker 判题及镜像构建检查。
2. 在 GitHub 仓库变量中设置 `ENABLE_PRODUCTION_PROMOTION=true`。只有 main 的 push 且聚合检查成功才执行生产分支快进。
3. 将 Zeabur API 的 Git 部署分支设置为 `production`，关闭从 main 直接触发该服务部署的路径；可以让前端同样跟随验收提交，不改变 UI。
4. 限制直接写入 production 的权限，设置 Required release gate 为必要检查。手动部署也必须选择通过验收的提交。
5. 若 production 存在分叉，发布会失败。检查分叉原因后处理，不强推覆盖。

本轮没有访问 Zeabur 管理后台或修改这些远程设置。仅合并仓库代码不会自动完成平台分支切换。基于源码的 Zeabur 部署仍会重新构建镜像；严格镜像一致性部署应使用既有不可变摘要的 Compose 流程，不能把“同一 Git SHA”解释为“同一个二进制镜像”。

## 接口兼容与性能边界

- `/contests/` 原返回数组保持不变；`?page=1&page_size=50` 可选，分页时附带 `X-Total-Count`。
- `/problems` 原返回 `{data,total}` 保持不变；支持 `page/page_size/q/category/difficulty`，total 为过滤后的完整数量。
- page_size 最大 100；旧客户端没有分页参数时保留全量摘要响应。要全面限制旧客户端的数据量，需要后续迁移客户端 API 调用；本轮不截断旧返回结果。
- ETag 采用 `private, no-cache`，每次先重新验证数据库可见性。不会为了缓存命中绕过比赛私有化/发布状态检查；这主要减少传输，不声称消除目录数据库查询。
- `letcoding_contest_lock_wait_seconds` 反映获取比赛锁所花时间，`letcoding_contest_transaction_seconds` 包含事务提交/回滚。结合 HTTP 和判题分阶段直方图观察 P95/P99 后，再决定锁粒度及扩容策略。

## 沙箱执行变更

监督器保持独立 root UID 与最小能力集合，选手进程降权后才进入其私有工作目录。目录仍为 0700，没有增加 DAC 绕过能力，也没有关闭 no-new-privileges、禁网或资源限制。

原路径的问题可由 [CPython 3.13 子进程实现](https://github.com/python/cpython/blob/3.13/Modules/_posixsubprocess.c) 中 chdir 先于 setuid 的顺序解释；Docker 整体修复效果仍需真实验收。本轮还按 [Nixpacks 官方格式](https://nixpacks.com/docs/configuration/file) 修正了 `[start]` 配置。

Worker 生产维护循环每 60 秒尝试回收容器；只匹配本应用标签且已超过执行硬截止时间的容器，每轮最多 10 个候选/5 秒，不扫描或删除其他应用容器。可信 Docker CLI 保留连接上下文白名单，选手进程仍使用独立环境，不继承数据库/JWT 密钥。

## 最终验收记录

- 最终完整后端回归：`python -m pytest -q --junitxml=/tmp/oj-backend-final.xml`，**204 项通过，0 失败、0 错误、0 跳过，32.664 秒**。包括真实临时 PostgreSQL/Redis、故障恢复和备份恢复测试。
- PostgreSQL 列表样本：12 场比赛、每场 1 名参赛者，完整列表实际执行 1 条 SQL；分页和过滤结果验证通过。该结果是查询数量证据，不是生产吞吐量承诺。
- Python 编译、工作流 YAML 解析与发布依赖检查、`git diff --check` 通过；前端文件差异为空。
- 两份 Compose 配置与 Nixpacks TOML 解析通过；配置检查没有启动服务。
- Docker 沙箱实际执行：8 项均在 `docker info` 准备阶段失败，原因是本机无 daemon socket；没有跳过，也没有生产沙箱通过结论。
- 线上截图只确认 `/problems`、`/contests/` 出现 ProgrammingError；未提供 SQLSTATE 或数据库权限，不能声称已确认/修复生产 500。
- 尚未推送或部署本轮修改，未运行生产提交/负载测试。缺少专用环境时保留上述验收项，不向正在使用的服务注入故障或压力。
