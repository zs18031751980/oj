# 比赛生产保障实施记录

最新一轮（2026-09-13）的八项优化与真实验收边界见 [DEPLOYMENT_UPGRADE.md](DEPLOYMENT_UPGRADE.md)。以下保留历史实施记录；历史通过数不代表本轮结果。

本轮在提交 a90f4e5 的基础上落实九项建议。只修改后端、测试、CI 与部署材料；没有修改前端源码、页面、布局和样式。未连接生产数据库、未发布，也未修改远程仓库规则。

## 九项建议对应

| 项目 | 实现与证据 | 部署条件 |
| --- | --- | --- |
| 1. 真实判题验收 | 沙箱验收增加磁盘/文件大小、进程数量和后代进程清理用例；节点报告可检查镜像一致、节点内波动、节点间 CPU 中位数比值 | Docker daemon 当前不可用；新增真实沙箱用例与实际节点校准仍待目标主机执行 |
| 2. 持续写入下榜单推进 | PostgreSQL REPEATABLE READ 只读事务固定提交、事件与版本；在另一短事务中发布对应历史版本，再追赶新版本；较新快照不能被旧计算覆盖，取消/最终确认及控制字段变化会拒绝发布 | SQLite 保留乐观版本拒绝；需要生产 PostgreSQL |
| 3. 可恢复备份 | 同一导出快照内运行 pg_dump 和逐表摘要；恢复到唯一新数据库逐表比对并删除该临时库；损坏备份在恢复前拒绝；WAL 归档器同步文件和目录，拒绝覆盖冲突内容 | 真实临时 PostgreSQL 已验证逻辑备份恢复；生产 PITR、异地存储、同步复制、RPO/RTO 尚需运维实测 |
| 4. 提交锁竞争 | 移除已被比赛行锁覆盖的全局用户锁，减少重复队伍查询；持锁后重新读取当前题包指针；保留比赛状态、受理时间、幂等和额度事务；新增请求锁等待直方图 | 比赛行锁仍存在；未承诺某个生产吞吐量，后续按真实压测决定是否拆分 |
| 5. 有界恢复与公平调度 | 每次最多读取 1001 条事件；超出 1000 条则在一致快照内全量重建；全量 ACM 提交按受理时间+ID每批最多 500 条流式计分；每轮最多 20 场并按 ID 轮转 | 计分状态与榜单结果仍随参赛者×题目数增长；OI 保留原有全量实现 |
| 6. 指标与告警 | 判题排队、编译、执行、落库、总耗时按 Worker pool 累计直方图；存活/空闲槽位；7 条告警及触发、恢复测试 | Redis 累计指标是观测数据，Redis 清空会重置，指标写入失败不回滚已提交判定；不是审计账本 |
| 7. 裁判权限与审计 | 重新读取用户角色及启用状态；敏感操作持锁后复核权限；可配置敏感复判双人复核；当前密码/TOTP、SSO 会话+TOTP；数据库时间步防重放；可选独立线程导出审计副本 | 密钥、独立审计存储须部署配置；未增加 OIDC 提供商主动重新认证流程或管理 UI |
| 8. 发布门禁 | Actions 固定已查询的官方提交 SHA；显式只读权限、超时、并发控制、JUnit 保留；后端/前端聚合 release-gate；迁移成功后 API 才启动；启动前拒绝可变镜像标签 | 需要在 GitHub 仓库规则中将 Required release gate 设为必过；本轮未改远程规则，亦未运行远程 CI |
| 9. 归档清理 | 默认只归档；显式 --prune 才清理已同步到磁盘的旧终态 DISPATCHED Outbox；排除 Pending、SystemError、复判候选及待审核批次引用；批量和最短保留时间受限 | 正式源码、Judgement、事件、审计、题包和 FINAL 均不删除；实际保留策略须满足赛事复核需求 |

额外修复：封榜到时即使没有新提交，也会调度生成 PUBLIC_FREEZE，避免公开榜长期返回尚未准备好。

## 安全启用裁判控制

1. 升级前备份并停止旧 API/Worker 写入，执行 `python manage.py migrate`。新增 0021_production_controls，创建 JuryMFAState 防重放状态表。
2. `CONTEST_DUAL_REVIEW_MIN`：生产默认 50，非生产默认 0；范围 0–500。大于 0 时，达到阈值的复判或最终成绩更正不能由批次创建者自行应用。审核者须保持当前赛事权限。0 明确关闭双人复核。
3. 为需要 MFA 的裁判通过 Secret 管理器分发 `JURY_TOTP_SECRETS`，格式为用户 ID 到 Base32 密钥的 JSON。每个密钥至少 20 随机字节；所有 API 实例应一致。不要使用测试向量作为真实密钥。
4. `JURY_REQUIRE_MFA=1` 要求人工改判与复判应用验证动态码。POST 增加 `totp` 字段；本地账号还须提供当前 `password`。无本地密码的 SSO 账号可以使用登录会话+已配置 TOTP。人工改判账号只要配置了 TOTP，即使全局开关为 0 也要求动态码。
5. TOTP 使用 30 秒时间步、前后一步时钟容差、数据库原子消费；相同或更早已消费时间步拒绝重复使用。主机须保持准确时钟。密钥轮换通过部署 Secret 完成；不能通过公开 API 查询密钥。
6. 给一个 Worker 配置 `AUDIT_EXPORT_DIR`，将独立受控存储挂载到该目录；不要挂载到选手容器。独立线程每 10 秒导出至多 500 条记录并循环复核历史副本，覆盖晚提交事务；既有文件内容不同会拒绝覆盖并记录后台任务失败。增加一个数据库连接预算。
7. 副本默认目录 0700、文件 0600；部署应进一步限制副本存储的修改/删除权限或启用存储保留锁。本地文件不是不可篡改存储，也不能替代独立备份。

手工导出：`python manage.py audit-export --directory /secure/audit --after 0 --limit 500`。游标遍历完成后应从 0 开始复核，避免跨事务序列号乱序造成漏导。

## 恢复演练

连接通过受保护的 `pg_service.conf` / `PGPASSFILE` 提供，命令参数和正常输出不包含数据库密码。备份目录包含全库数据，应使用独立加密存储和最小访问权限。

```sh
python deploy/recovery.py backup --service oj_backup --directory /secure/backups/run-001
python deploy/recovery.py verify --service oj_restore_drill --directory /secure/backups/run-001
```

`oj_restore_drill` 必须连接隔离的恢复演练集群。工具只创建 `oj_restore_<随机UUID>` 数据库，恢复、验证后仅删除自己刚创建的库，不覆盖已有数据库。需要匹配的 PostgreSQL 客户端、创建数据库权限和可访问的扩展。输出实际恢复秒数和核对表数。备份在 MVCC 快照中生成，原始表只读；大表摘要排序会使用数据库临时空间，安排在低峰期。

逻辑恢复演练不等于物理 PITR。`deploy/postgresql-recovery.conf.example` 提供 WAL 归档与恢复配置示例。正式启用后必须在独立主机从基础备份+WAL 恢复到指定时间，核对最近已确认受理的提交与 FINAL。记录归档延迟、最后恢复提交时间和恢复耗时后，才能给出实际 RPO/RTO；archive_timeout=60s 本身不是丢失时间保证。还须备份镜像摘要对应镜像、部署 Secret 和上传文件。

## 归档

```sh
python manage.py archive-outboxes --directory /secure/outbox --retain-days 30 --limit 500
# 核对归档目标和保留政策后，显式启用清理：
python manage.py archive-outboxes --directory /secure/outbox --retain-days 30 --limit 500 --prune
```

最少保留七天；一批最多 1000 条。正式比赛提交事实与判题历史永久留在数据库，删除的只是已完成投递记录。归档成功须经过文件与目录 fsync，已有不同内容文件拒绝覆盖；异常会使数据库事务回滚。

## 上线步骤和运行验收

- 在比赛之外升级，先停止旧 API 与所有旧 Worker，避免混用队列协议和模型。Compose 仅保证本机 API 等待迁移成功，不会替你停止另一主机的 Worker。
- 用同一发布清单记录 API_IMAGE、WORKER_IMAGE、JUDGE_SANDBOX_IMAGE 三个完整摘要、Git 提交和迁移版本。API/Worker 启动校验拒绝 latest 等标签；API 与 Worker 必须使用同一沙箱摘要。
- GitHub Actions 的 Required release gate 汇总后端（含真实 Docker）、前端构建/测试结果。仓库规则需单独配置必过状态；新增配置尚未在 GitHub 执行。
- 专用验收主机运行 `python -m pytest tests/sandbox_integration.py -q`，包含资源与后代清理测试。不得在有其他正式判题容器的主机上执行该验收。
- 每个节点运行 `APP_ENV=production JUDGE_BACKEND=docker python deploy/calibrate_judge.py --output node-a.json`。仍须按部署配置设置镜像摘要和 CPU 槽。
- 汇总比较：`python deploy/calibrate_judge.py --compare node-a.json node-b.json --max-ratio 1.1 --output comparison.json`。示例阈值为节点 CPU 中位数相差不超过 10%，各节点样本变异系数不超过 0.2；最终阈值应根据硬件和题目时限确定。
- 在独立预演比赛运行原有 `deploy/contest_load.py`；观察受理 P95、锁等待直方图、判题队列、榜单版本差距。没有预演地址/账号，本轮未进行 HTTPS 压测。
- 将 `deploy/alerts.yaml` 加入 Prometheus，采集任务名设为 letcoding，并配置指标 Token。告警是模板阈值；告警接收人、通知渠道和生产规模需部署配置。

## 本轮验证

测试依赖在临时虚拟环境重建；PostgreSQL、Redis 均使用临时隔离实例，没有连接部署数据库。

- 后端完整回归：`python -m pytest -q`，**142 项通过，14.04 秒**；包括真实 PostgreSQL 并发、备份恢复/跨时区比对、损坏备份拒绝、归档 fsync 故障回滚、TOTP 防重放、双人复核、封榜边界和流式榜单。
- Prometheus：`promtool check rules deploy/alerts.yaml` 验证 **7 条规则**；`promtool test rules deploy/alerts.test.yaml` 验证依赖故障、比赛槽位失联、版本积压、系统错误及恢复场景，全部通过。
- API/Worker Compose：用临时空配置文件和合成镜像摘要运行 `docker compose config --quiet`，两份配置均通过；此检查没有启动服务。
- Python 模块编译、运维 CLI 帮助入口、`git diff --check` 通过。
- `git diff --name-only -- webapp` 为空；本轮没有前端文件变动，未重复执行前端构建/浏览器测试。
- Docker 沙箱门禁实际执行 `python -m pytest tests/sandbox_integration.py -q -x`，在 docker info 准备阶段失败：daemon socket 不存在。新沙箱用例没有获得实际通过证据。
- 未提供真实节点与预演目标，因此真实节点校准、HTTPS 压测、生产 PITR/故障切换、远程 CI 和仓库必过状态尚未验收；不能据本地测试宣称生产隔离、容量或 RPO/RTO 达标。

最新本地容量样本：300 人、3001 条提交；实时+封榜全量刷新 85.47 ms，单队增量刷新 23.69 ms，条件读取 P95 1.23 ms，增量与全量重建一致。见 [PRODUCTION_CAPACITY_SAMPLE.json](PRODUCTION_CAPACITY_SAMPLE.json)。样本不含网络、反向代理或 Docker 执行负载，不用于生产吞吐量承诺。

## 并发边界复查补强（后续执行）

本次在上述未提交改动上继续复查，未修改 UI、依赖或数据库结构。

- 提交幂等查询统一为一个实现。在取得比赛锁后、额度及时间检查之前重查请求；等待期间另一请求已经成功时返回既有提交，同键异内容返回 409，不再误报额度耗尽。回放只匹配正式比赛提交。
- 正式提交取得比赛锁后重新读取账号启用状态和报名资格；等待期间已停用或撤销资格时返回 403，不创建提交或 Outbox。
- 创建复判、组队、答疑回复/认领、候选题包创建/激活及规则更新，在锁内重新验证当前权限。撤权已提交的旧请求不再执行修改，也不生成成功审计。
- 新增 `tests/test_contest_race_safety.py`：11 项真实 PostgreSQL 多连接回归，先复现失败再修复；检查状态码、数据库副作用和并发事务已提交的撤权事实。
- 最终完整后端验证：**153 项通过，19.81 秒**。Python 编译、Prometheus 告警测试、`git diff --check` 通过；`git diff --name-only -- webapp` 为空。
- 上述结果是代码与隔离环境回归证据；真实 Docker、节点校准、HTTPS 压测和生产灾备验收的边界保持不变。


## 判题运维与恢复写入补强（2026-09-12）

本轮六项建议的执行状态：

| 项目 | 已落实 | 验收边界 |
| --- | --- | --- |
| 真实部署验收 | 已复查 Docker 连接条件；保留真实沙箱、节点校准、HTTPS 和 PITR 门禁命令 | 本机 Docker Desktop socket 不存在；缺少真实预演目标和节点，尚未通过 |
| 异常资源清理 | 判题程序创建后统一进入 ExitStack；覆盖 Compiled/Running 状态更新、检查器初始化、执行和检查器关闭异常 | 故障注入与真实临时目录检查通过 |
| Worker 排空 | SIGTERM/SIGINT 后停止领取新任务，活动任务继续续租和心跳；30 秒总等待预算，超时以非零退出交由租约恢复 | 单进程真实 Redis 领取/确认与超时回归通过；跨主机滚动发布仍需预演 |
| 固定到达率压测 | 新增 open 模式；调度独立于判题完成，限制在途线程数，记录生成端饱和、调度偏差、HTTP 状态、超时和错误判定 | 调度与统计回归通过；没有真实 HTTPS 容量结果 |
| 可观测性 | 欠账榜单年龄、连续刷新失败、审计最近成功时间/失败次数、备份年龄与缺失状态；排空槽位不计入接收容量；提交日志关联 request/submission/job/attempt | 指标与告警规则回归通过；实际告警渠道需部署接入 |
| 恢复后应用可写 | 比较全表数据、列、约束与索引，实际检查序列取号；在恢复库用真实控制器登录、提交、判题落库并验证榜单 | 真实隔离 PostgreSQL/Redis 通过；不替代生产权限、HTTPS、沙箱或 PITR 验收 |

### 固定到达率预演

仅在专用预演比赛执行，账号须预先报名。账号数、每账号频率和在途提交数应符合现有比赛限流、活动提交配额；HTTP 429 会计为失败，不绕过限制。

```sh
python deploy/contest_load.py --base-url https://rehearsal.example.com/api \
  --frontend-origin https://rehearsal.example.com --accounts-file /secure/load-accounts.json \
  --contest-id 123 --problem-id 456 --code-file /secure/known-ac.py \
  --mode open --arrival-rate 2 --workers 128 --submissions 10 \
  --judge-timeout 120 --accept-p95-ms 300 --output rehearsal-open.json
```

示例域名和 ID 需要替换。`--arrival-rate` 是每秒新提交数，不包含登录和结果轮询；总到达数为账号数×submissions。open 模式不重复提交幂等请求，原 closed 模式保留幂等验收。在途线程包含结果轮询，应按“到达率×端到端时延”预算；`generator_capacity` 或调度延迟超过 `--max-schedule-lag-ms` 会使门禁失败，不能据此归因于服务端。P95 使用 nearest-rank，小样本不会漏掉最慢请求。生产调优同时采集既有 queue/compile/execute/persist 阶段直方图与比赛锁等待。

### 告警接入

- `letcoding_contest_projection_stale_seconds` 表示有版本欠账时最老已发布快照的年龄；首次未生成从比赛创建时间算，缺失封榜快照从封榜时间算。它不是精确的单事件等待时长。已追平的静止榜单输出 0，快照 upsert 会更新 updated_at。
- Worker 心跳增加 draining、accepting_jobs、后台任务失败次数和成功时间。排空期间 alive 可保持为真，新增 accepting 槽位会降为 0；`ContestPoolUnavailable` 同时考虑 contest/all 池。
- 一个 Worker 应挂载独立审计目录并启用 AUDIT_EXPORT_DIR。API 通过 Redis 心跳采集导出状态；没有导出进程也会告警。
- API 配置 BACKUP_MANIFEST_FILE，并**只读挂载最新备份 manifest 的所在目录**，不要挂载完整备份。备份作业成功后原子替换该状态文件；挂载目录可见新 inode，避免单文件 bind mount 看不到替换。必须让 API 容器运行用户有读取权限，指标端点仍须 Token。
- 备份年龄从 snapshot_at_unix 算起，状态不存在、损坏、未来时间或未启用监控均不会伪装成“刚备份”。24 小时年龄阈值是模板值，按实际恢复目标调整。
- 日志只关联服务端请求 ID、提交 ID、任务 ID 和 attempt；不记录提交源码、题目测试数据或登录凭证。

### 恢复工具新增要求

恢复验收使用当前应用依赖、redis-server 和与备份相同主版本的 PostgreSQL；读取的 manifest 为版本 2，包含结构证据。旧版仅含数据摘要的 manifest 不会被静默视为完整验收通过，应使用新版工具重新备份；已有 dump 文件不会被修改。

工具在自建的随机恢复库中消费序列号、创建随机自测账号和比赛。自测只执行内置 `print(42)`，不执行备份内选手源码；独立子进程不继承生产 Redis、判题或应用密钥配置，120 秒超时会终止其进程组。恢复库和私有 Redis 在结束后删除/关闭，源库保持只读。迁移账本缺失时失败，不自动迁移来掩盖问题。

该流程验证的是应用逻辑和恢复数据的可写性，恢复使用的演练数据库角色不能代表生产最小权限角色已验收。物理故障切换、Secret/上传文件恢复、真实沙箱与线上网络仍按前文单独演练。


本轮最终验证：完整后端 **167 项通过，24.84 秒**（在原 153 项基础上新增 14 项）；11 条 Prometheus 规则语法检查及告警触发/恢复测试通过；Python 编译、运维 CLI 帮助入口、`git diff --check` 通过。前端目录没有改动。没有执行 push，也没有将本地恢复测试标为生产灾备验收。

## 运维异常分支复查（2026-09-12）

在原有改动上继续补强，未新增数据库迁移或修改前端：

- 备份状态读取先校验 JSON 对象和数值时间戳。数组、null 或字符串等损坏状态只输出 `letcoding_backup_status_up 0`，不再让整个 `/metrics` 接口失败，数据库和 Redis 指标仍可采集。
- 编译缓存校验文件清单和启动参数的结构。损坏条目回退到真实编译；未成功交付 PreparedProgram 的恢复目录在 finally 中释放，包括非预期异常。
- 题包验证使用统一的 ExitStack 管理检查器、参考程序、输入验证器和已知错误程序。任意关闭回调失败仍继续关闭其他资源，验证结果保存为 INVALID；只有执行和清理均成功才标记 VALID。
- 节点校准报告拒绝可变镜像标签、布尔时间样本和无效样本结构；比较依据为不可变镜像摘要和 5–100 个正有限数值样本。
- 新增 `tests/test_operations_edge_cases.py`，8 个回归用例均先复现失败再修复。缓存测试执行真实 C++ 编译并检查工作目录，监控测试经过真实 Flask 指标接口。

用户确认目前没有预演 HTTPS、Docker 判题节点及验收账号配置。本轮范围为代码与隔离环境回归，真实节点校准、HTTPS 容量和生产灾备继续列为待验收；不以合成报告替代实际环境证据。

本轮最终验证：**175 项后端测试通过，26.48 秒**；11 条 Prometheus 规则检查及告警单元测试通过；Python 编译与 `git diff --check` 通过；前端目录无改动。
