# 判题与任务链路

## 事实与队列

普通提交和比赛提交均在 PostgreSQL 事务中创建 submission + outbox；201 表示提交事实持久化成功。数据库故障返回 503。Redis 不可用时，outbox 留存，Worker 恢复后补投。

Redis Lua 将 ready → processing、唯一 delivery receipt 与 300 秒租约创建合为一次操作。Worker 每 20 秒续租，结果数据库提交成功后才 ACK。失败投递按 2、4、8、16 秒退避，累计 5 次进入死信；租约失效的投递也受重试次数限制。死信先幂等持久化 SystemError，再转入容量 1000 的诊断归档。

数据库 job_id 去重，attempt_id 条件更新隔离旧执行者。maintenance、执行、榜单投影和心跳分别运行；maintenance 每 2 秒补投、回收和分页核对未完成事实，心跳独立于数据库，榜单聚合不持有提交事务锁。Redis 全量丢失后，没有去重键的未完成事实会补投。Redis 必须使用 noeviction，禁止选择性手动删除队列而保留去重键。

## 进程与安全边界

API：非 root Gunicorn，只有数据库/Redis/远程执行器访问能力，不挂 Docker socket。

Worker：独立判题主机上的非 root 进程，获取每份任务的独立目录。编译一次，测试点顺序运行；管理员参考代码也通过持久化任务执行，校验通过才允许发布比赛。版本号防止过期参考校验覆盖新题目。

沙箱：每次编译、每个测试点分别创建 Docker 容器。禁网、只读根目录、运行阶段工作目录只读、Docker 默认 seccomp、no-new-privileges、cgroup v2 CPU/内存/交换/PID 限额及文件/输出上限。总 stdout+stderr 上限 1 MiB。编译内存 512 MiB，运行按题目限制。

监督器在容器内使用 root 身份，仅保留 SETUID、SETGID、KILL 能力，以便降权和回收进程树。用户程序降权至 Worker 的非 root UID/GID、清空附加组，effective capabilities 为零，不能向监督器发信号或写其结果管道；程序环境不继承服务端密钥。这里的 root 是可信监督器，不是提交程序。

selectors 非阻塞读写让 stdin、stdout、stderr 共享同一个截止时间。wait4 收集单进程数据；生产由独立 cgroup 的 memory.peak/memory.events/cpu.stat 给出整个进程树的指标。wall_ms 仅计入被监督程序执行，不包含 Docker 启动与清理。程序结束也回收派生进程，随后删除容器和临时目录。

Docker socket 的访问权限等价于控制判题主机，因此 Worker 主机必须隔离；容器共享内核，不承诺抵御未知内核漏洞。生产不得启用 local 后端。普通题库/Judge0 的隔离属于所配置 Judge0 服务的运维边界，本仓库 Docker 沙箱不替代它。

## 榜单与可观测性

比赛终态和 scoreboard_requested_version 在同一个事务推进，独立消费者重建 LIVE 快照。消费者锁定比赛行，不覆盖较新版本；FINAL/PUBLIC_FREEZE 延续既有快照规则。参赛者资料 JOIN/批量读取，消除每人单独查询；普通榜单缓存 15 秒并在普通判题终态失效。

内部指标包含请求量/延迟、队列 pending/processing/retry/dead、Worker 存活、outbox 数量/最老等待时间及依赖可用性。公共健康接口只返回状态，不泄露任务或用户信息。日志 JSON 化，携带 request_id，避免记录请求体、令牌和 URL 查询串。

## 验收

`python -m pytest -q` 覆盖真实 Redis、临时 PostgreSQL、HTTP 客户端和显式本地执行器回归。

`python -m pytest tests/sandbox_integration.py -q` 必须在非 root、有 Docker daemon、镜像及 cgroup v2 的主机单独运行，验证宿主文件/凭证/网络隔离、监督器身份隔离、超时、输出/内存限制和 C++/Java/Go 编译。前置条件不满足会失败，绝不静默跳过。

ACM 专项的队伍、题包、复判、队列、镜像固定与迁移说明见 [ACM_IMPLEMENTATION.md](ACM_IMPLEMENTATION.md)。
