# 比赛判题链路设计

本文对应 `ACM-OJ 判题系统后端设计 Prompt.md`，描述当前代码已经落实的比赛判题链路和生产部署边界。

## 1. 链路

```text
提交 API
  -> PostgreSQL ContestSubmission
  -> Redis judge queue
  -> JudgeWorker claim + lease
  -> 编译进程组
  -> 测试点独立执行
  -> 输出检查
  -> 条件更新数据库
  -> Redis 状态缓存
  -> 轮询 API /healthz/judge
```

提交先写 PostgreSQL，数据库不可用时拒绝提交；Redis 只作为调度和短期缓存，不作为提交事实源。

## 2. 状态机

状态定义集中在 `services/judge_state.py`，所有比赛结果更新都带 `submission_id + attempt_id + expected_status` 条件。

```text
Pending -> Claimed -> Compiling -> Compiled -> Running -> Checking -> AC/WA/Partial
                                      |             |
                                      +-> CE        +-> TLE/MLE/OLE/RE/SIGSEGV/SIGSYS
```

终态不可被覆盖。租约过期重投时，Worker 将 attempt 加一并把旧 attempt 隔离，旧 Worker 的迟到结果条件更新必然失败。

## 3. 持久化字段

`contest_submissions` 保存：

- `job_id`、`attempt_id`、`worker_id`
- 排队、判题、编译、执行、检查和完成时间
- CPU 时间、墙钟时间、峰值内存、输出大小
- 退出码、信号、错误信息
- 测试点结果和最终状态

数据库迁移 `0013_contest_judge_lifecycle` 为幂等迁移，兼容已经执行过旧版本迁移记录但缺少实际字段的数据库。

## 4. 队列可靠性

队列采用 Redis List 的 `RPOPLPUSH` claim 模式：

- ready 任务原子转入 processing
- 每次 delivery 创建 5 分钟租约
- ACK 同时删除 processing 条目和租约
- Worker 启动以及运行期间定时只回收已过期租约
- 结果未成功持久化时不 ACK，任务保留待重试

任务 payload 带 `job_id` 和 `attempt_id`。数据库中的 `job_id` 唯一，避免重复创建提交记录。

## 5. 执行限制

当前本地执行器已经实现：

- 独立临时工作目录
- 独立 process group，超时/输出超限时杀死整个进程组
- `RLIMIT_AS` 内存限制
- `RLIMIT_CPU` CPU 硬限制
- `RLIMIT_NPROC` 进程数量限制（Java JVM 使用专门兼容策略）
- `RLIMIT_FSIZE` 文件大小限制
- stdout/stderr 64 MiB 硬上限
- 编译阶段独立超时、进程组和输出限制
- `wait` 后收集 CPU 时间、峰值 RSS、输出大小、退出码和信号

编译只执行一次，所有测试点使用同一个编译产物；每个测试点独立运行并记录结果。

## 6. 生产安全边界

本地执行器不是完整的生产沙箱。生产环境必须把 JudgeWorker 部署到独立执行节点或容器，并进一步启用：

- 非 root 用户
- network namespace / 默认禁网
- mount namespace 或只读根文件系统
- cgroup v2 的 CPU、memory、pids、io 限制
- seccomp syscall 白名单
- capability drop
- 沙箱节点与 API、PostgreSQL、Redis 网络隔离

当前应用层限制用于开发机回归和基础防护，不能替代上述内核隔离。

## 7. 可观测性

`GET /healthz/judge` 返回 Worker 是否存活、Worker ID、活动任务、失败次数、比赛队列长度和 processing 数量；`GET /healthz/db` 返回数据库连接状态。

提交结果查询优先数据库，因此 Redis TTL 到期不会导致已完成比赛提交消失。

## 8. 测试覆盖

`tests/test_contest_judge.py` 覆盖：

- 合法/非法状态迁移
- 隐藏测试数据脱敏
- 队列 claim、ACK、恢复
- Java 一次编译多次执行
- 测试点超时
- 输出超限终止
- 空白规则输出比较

生产上线前仍应补充真实容器沙箱、网络隔离、fork bomb、数据库故障和多 Worker 并发集成测试。
