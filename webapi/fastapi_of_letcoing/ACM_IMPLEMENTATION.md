# ACM 比赛链路优化落实记录

本轮以比赛公平性、结果可恢复性、保密性和峰值性能为重点，保留已有加固改动。没有改动前端页面、样式或组件。新增赛事控制能力通过后端 API 提供，尚未新增管理界面。

## 建议与实现对应

| 建议 | 本轮实现 | 主要验收 |
| --- | --- | --- |
| 1. 结束、解封、最终确认分离 | `thawed_at` 独立控制；结束后不自动解封；封榜前迟到结果继续更新，之后提交公开为 Pending；自身判定仍可见；FINAL 和 FINAL:n 保留历史 | 迟到 AC、最终确认仍封榜、HTTP 公开榜/自身结果隔离 |
| 2. 幂等与截止时间 | 正式提交校验题目、代码和语言；同键异内容 409；队伍共享幂等；允许截止后重取已受理结果；固定受理时间、结束边界排他；持久化请求摘要 | 同键换代码、跨队员重试、截止时间边界 |
| 3. ACM 规则 | CE/系统错误不罚时；ACM 不返回 Partial 或隐藏通过比例；同成绩共享名次；固定规则版本和允许语言；跨时区统一计分；排除缺失时间与比赛窗口外记录 | 同分、UTC/+08:00、异常时间、正式 HTTP 判题 |
| 4. 运行一致性 | CPU 时间预算与更宽松墙钟限制分开；生产 cgroup CPU 统计扣除监督器 CPU 开销；不可变镜像校验；可配置语言 CPU/内存预算；每 Worker 一个执行槽、可绑定单个 CPU | CPU 忙循环/睡眠、UTC Worker 时间戳；真实 Docker 与节点校准待部署主机验收 |
| 5. 版本化复判 | Judgement 历史、RejudgeBatch 候选执行、批次差异查询、审核应用/取消；源版本比较防止覆盖较新判定；系统错误/未审核复判阻止结算；人工改判要求本地密码重新认证及审计；最终更正生成新快照 | 重叠复判、多连接并发、候选结果保密、最终快照不覆盖 |
| 6. 榜单竞争 | 锁外计算；事件游标与比赛版本校验；仅重算变化队伍并合并投影；PostgreSQL advisory lock 避免多消费者重复构建；查询只取计分字段；读榜只读快照，支持 ETag/304 | PostgreSQL 写入不被聚合阻塞、旧版本拒绝、增量与全量一致、容量样本 |
| 7. 容量与公平调度 | 正式比赛/练习/复判/验证队列分离；Worker pool 配置；比赛按参赛实体轮转；正式活动上限按比赛和队伍隔离；心跳、恢复、榜单分线程，心跳不依赖 DB | 独立队列、公平认领、失效数据库不阻断心跳、既有租约/Redis 恢复测试 |
| 8. 执行效率 | ACM 固定测试顺序、首个失败提前结束；编译一次、多点执行；可选编译缓存按源码/语言/镜像/策略寻址，校验文件摘要、独立复制、容量预算；详情写入判题历史，主表保留摘要 | 题包固定、无 Partial、缓存命中与损坏重编译、详情分表后 HTTP 可查询 |
| 9. 安全与裁判权限 | 比赛范围 director/jury/setter/operator 授权；审计解封、组队、角色、改判、复判、题包和结算；隐藏自定义检查器和候选结果；保留独立沙箱与严格 Docker 门禁 | 跨身份拒绝、人工重新认证、秘密数据不出公开接口；Docker 本机未通过准入 |
| 10. 不可变题包与 Checker | 题包 SHA-256、固定测试顺序/镜像/资源；text/exact/tokens/float/custom；自定义检查器在沙箱中编译一次；候选题包由验证 Worker 检查输入验证器、标准解和已知错解，审核后激活；旧提交仍绑定旧包 | 非有限浮点拒绝、自定义 Checker、校验前不可激活、输入验证失败、包损坏与版本固定 |
| 11. 赛事组织 | 独立队伍和成员、报名截止与名单锁定；裁判提问/认领/私密回复/广播；按身份过滤的持久事件及游标分页；后台 API 无 UI 改动 | 队伍成绩合并、赛后/开赛后组队拒绝、私有答疑不泄露 |
| 12. 容量与恢复验收 | 临时 PostgreSQL/Redis 与完整 HTTP 链路；300 人容量样本；HTTPS 预演负载脚本；节点校准脚本；等待时间、队列和阶段耗时指标 | 本地验证结果见下文；生产容量、硬件故障恢复承诺需目标部署验证 |

增量当前以“参赛队伍”为最小重算单位，重读该队伍的相关提交，不扫描其他队伍提交。最终展示仍需要合并队伍行。没有宣称已实现每题独立增量状态机或无条件的固定延迟保证。

## 新增 API

均位于 `/contests` 命名空间。POST 使用现有 Bearer 会话；操作有身份限流、比赛范围鉴权和审计。运维响应为 private/no-store。

| 路径 | 方法 | 用途 |
| --- | --- | --- |
| `/<id>/thaw` | POST | 显式解封，正文含 reason |
| `/<id>/rules` | POST | 发布前配置允许语言、活动上限、罚时和 reason |
| `/<id>/teams` | POST | name、member_ids；第一名成员为队长，1–3 人，开赛前配置 |
| `/<id>/roles` | POST | user_id、role、reason；none 撤销比赛角色 |
| `/<id>/rejudges` | POST | submission_ids、reason；每批最多 500 条 |
| `/<id>/rejudges/<batch>` | GET / POST | 查看改判差异；action=apply/cancel、reason |
| `/<id>/submissions/<submission>/override` | POST | verdict、reason、password；需要本地裁判账号重新认证 |
| `/<id>/clarifications` | GET / POST | 游标查询或发送 question |
| `/<id>/clarifications/<question>` | POST | action=claim 认领；或 answer、broadcast 回复 |
| `/<id>/events?after=<cursor>` | GET | 按身份过滤、最多 100 项、返回 next_cursor，可恢复读取 |
| `/<id>/audit?after=<cursor>` | GET | 负责人读取审计历史 |
| `/<id>/health` | GET | director/operator 读取本场比赛运行指标 |
| `/<id>/problems/<problem>/packages` | POST | package、reason，持久化并异步校验候选题包 |
| `/<id>/packages/<digest>` | GET / POST | 查询校验结果；负责人提供 reason 激活已验证版本 |

题包 package 可包含 reference、language、cases、checker_config、validator、known_wrong、time_limit、memory_limit、language_limits。自定义检查器接受标准输入 JSON：`input`、`expected`、`actual`；退出 0 接受、1 拒绝，其他退出/超时属于检查器故障。不要把这一私有题包发送给参赛前端。

language_limits 示例：`{"java":{"cpu_factor":2,"memory_extra_mb":64}}`。默认倍率 1、额外内存 0。编译预算仍为独立 20 秒、512 MiB。内存口径是容器总内存（包括语言运行时及监督器固定开销）；不同节点应使用相同镜像并实际校准。

赛事事件接口是本项目协议，参考了 ICPC 的资源与可续传事件概念；没有宣称实现完整 CLICS 兼容。交互题仍作为独立功能阶段，不启用未经验证的双向交互执行。保持每个测试点独立沙箱，尚未启用容器复用。

## 部署与升级

1. 在比赛之外安排升级窗口，备份数据库，停止旧版本 API/Worker 写入，然后执行 `python manage.py migrate`。新增 `0020_acm_control`、赛事模型及索引。不得让新旧 Worker 同时消费已经拆分的队列。
2. 迁移保留提交、题目、FINAL；清理可重建的 PUBLIC_FREEZE 并推进旧实时榜版本。历史 FINALIZED 比赛标记为已解封，避免此前已公开的成绩迁移后消失。新比赛的解封与确认独立。
3. 发布前完成报名或队伍配置。开赛后新报名被拒绝；已有参赛者重试报名仍幂等。个人比赛继续使用个人参赛实体，队伍制使用独立队伍并合并成员提交。
4. API 与所有判题 Worker 设置相同 `JUDGE_SANDBOX_IMAGE`，使用完整镜像摘要（registry@sha256:… 或本地主机 sha256:… 镜像 ID）。API 仅记录元数据，仍不挂载 Docker socket。
5. 按 `deploy/compose.worker.yaml` 配置不同 pool：contest、practice、rejudge、validation。每个实例一个执行槽位；每槽配置不同 `JUDGE_CPUSET`。开发兼容模式 all 会轮转全部队列，正式比赛使用专用 contest 池。
6. 为缓存创建 Worker 所有、0700 的 `/var/lib/letcoding/cache`，挂载至 Worker；配置 JUDGE_COMPILE_CACHE、JUDGE_CACHE_MAX_MB。缓存不挂入选手容器，损坏时重编译。预算默认 512 MiB，使用 256 个固定锁桶限制 inode 增长。
7. 按 API 进程数、每个 Worker 的执行/恢复/投影线程预算 PostgreSQL 连接，使用 noeviction Redis；同时监控数据库 Outbox 和各类队列。备份/WAL、同步复制和故障切换必须在真实部署中演练，临时测试数据库没有证明生产掉电 RPO。
8. 实际判题主机运行 `python -m pytest tests/sandbox_integration.py -q`。Docker/cgroup/镜像缺失不跳过，也不能发布比赛。
9. 同镜像、同 CPU 槽位运行 `python deploy/calibrate_judge.py --output node-calibration.json`，比较不同节点的中位 CPU 时间与变异系数；异常节点停接任务，由运维调整硬件/负载后重验。本轮未改变主机调频、内核或安全设置。
10. 在专用预演比赛使用 `deploy/contest_load.py`。提供已报名的验收账号文件、正确代码、比赛/题目 ID、HTTPS 地址；脚本产生正式提交，核对幂等和判题结果，记录受理与端到端 P95，默认受理 P95 门槛 300 ms。不要对正在举办的比赛执行负载测试。

## 指标

`/metrics` 保持专用 Token 保护，增加独立队列、等待数、最老受理等待时间、榜单版本差距、未解决 SystemError，以及最近 5 分钟最多 1000 条正式完成提交的各阶段 P95 样本。无样本不伪造零延迟。Worker 心跳携带 pool 和编译缓存命中数。

阶段 P95 是有界样本，不能替代正式 Prometheus 直方图或全量业务压测。上线后应将队列增长、积压年龄、投影差距、系统错误与 Worker 存活关联告警。

## 验证边界

- Docker 门禁已经实际运行并失败：`/home/z/.docker/desktop/docker.sock` 不存在，daemon 未启动。因此未完成真实 Docker 隔离、节点校准及容器启动开销验收。
- 未提供生产/预演地址、验收账号与主机容量，本轮未执行线上负载脚本、修改生产数据库、发布或推送。
- 本地容量数据来自临时 PostgreSQL、Flask 测试客户端；没有网络、反向代理或 Docker 判题负载，不能外推为正式比赛吞吐量。
- 交互题、完整 CLICS 协议适配及新管理界面没有在本轮启用；现有 UI 完全保留。

## 最终本地验证结果（2026-09-12）

- 后端：`python -m pytest -q`，**122 项通过，12.04 秒**，包括真实 PostgreSQL 多连接、旧版本迁移、Redis、正式/练习 HTTP 判题、UTC 主机计时、缓存与题包、复判和容量样本。
- 前端：现有 Playwright **10 项通过，21.6 秒**；本轮未改前端文件。使用 Vue SFC 解析器比对工作区已有 7 个变更组件与 HEAD，template/style 内容一致。
- Python 模块编译、预演/校准脚本 `--help`、`git diff --check` 通过。没有新增第三方依赖。
- 最终容量样本：300 名参赛者、3001 条提交（初始源码每条 4096 字节）；实时榜+封榜全量重建 **90.15 ms**，单队增量更新 **28.13 ms**，100 次条件读取 **P95 1.89 ms**；增量结果与独立全量重算一致。原始记录见 [ACM_CAPACITY_SAMPLE.json](ACM_CAPACITY_SAMPLE.json)。这些数据仅描述本机隔离测试环境。
- Docker/cgroup 隔离验收未通过环境准入；节点校准与 HTTPS 预演负载尚未运行。以上功能测试结果不能替代这三项部署门禁。
