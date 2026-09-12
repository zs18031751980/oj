# 本轮审查建议落实记录

> 后续 ACM 专项优化已更新封榜、复判、队伍及队列行为；当前契约以 [ACM_IMPLEMENTATION.md](ACM_IMPLEMENTATION.md) 为准。

本轮保留页面布局、Vue template 和 style；修改服务端、前端数据交互与安全渲染、依赖和部署配置。沿用工作区前一轮的后端加固改动，没有替换用户已有修改。

## 逐项落实

| 建议 | 实现 | 验证入口 |
| --- | --- | --- |
| 1. 题库判题结果泄露 | 登录、提交所有者/管理员、练习类型三重检查；数据库为结果事实源；不返回隐藏输入、期望输出、实际输出 | `test_review_regressions.py`、`test_review_http_pipeline.py` |
| 2. Markdown XSS / 浏览器凭证 | DOMPurify 净化原始 HTML 和最终 HTML；移除内联复制事件；生产 CSP 限制脚本；刷新凭证只在 HttpOnly Cookie 中 | `markdown-security.spec.ts`、`check-production.mjs`、HTTP Cookie 测试 |
| 3. 赛后题目提交丢失 | ContestSubmission + ContestJudgeOutbox + job_id；数据库自增 ID；幂等键分域和请求一致性检查；代码/语言上限、限流与最多 3 个活动提交；`contest_eligible=False` | Redis 不可用仍持久化、重复提交、实际 Worker 执行、缓存清空后可查、练习不计比赛成绩 |
| 4. OIDC 校验 | 默认使用 Authlib 的 ID Token 验证；仅显式布尔开关可选 UserInfo-only OAuth 兼容模式；不再解码未验证 JWT 作为身份/角色来源；UserInfo 与已验证 ID Token 的 sub 必须一致 | 默认校验和伪造角色回归；第三方密码登录也调用认证后的 UserInfo |
| 5. 资源权限 | 题库仅公开且确实结束的比赛；不信任过期 past 字段；公告列表/详情共用权限查询；学习目录重扫要求管理员并限流；学习文件拒绝符号链接越界 | 私有比赛、管理员公告、匿名 rescan 回归 |
| 6. 依赖与供应链 | 升级锁文件和 Monaco；显式统一 DOMPurify 修复版本，移除旧 Mermaid 包装插件；CI 增加 npm audit | npm audit、pip-audit；Monaco 实际输入及生产构建 |
| 7. 封榜缓存读取错误 | 修复缺失 return、删除不可达代码；封榜快照首次创建后不可变；不再在未封榜 GET 中写公开快照 | 快照往返、初始化投影版本回归 |
| 8. 结算与提交竞争 | 结算全事务，Contest 行锁与提交/取消/Worker 状态迁移一致；提交锁内复核时间；只等待正式比赛活动提交；最终快照与生命周期原子提交；结算重试读取同一快照 | 结算写入失败回滚、练习不阻塞结算、已有生命周期回归 |
| 9. 讨论区全量/N+1 | SQL 热度排序和分页；作者 join、点赞批量查询；列表只返回至多 200 字摘要；回复独立分页；页面滚动时增量加载，保留原模板样式 | 分页上限和固定查询数量、PostgreSQL SQL 实测 |
| 10. 讨论计数竞争 | 明确 liked=true/false 幂等操作；行锁、唯一约束、数据库原子增减；回复创建/删除和计数同事务；统一 Discussion → Reply 锁顺序 | 幂等点赞、真实 PostgreSQL 多连接并发点赞 |
| 11. 普通排行榜击穿 | UserJudgeStats 持久化投影；Worker 每 30 秒最多重建一次；数据库锁跳过其他重建者；原子发布；API 按持久化 rank 分页，缓存故障不触发全表聚合 | 重复 AC 不重复计分、分页名次、PostgreSQL 投影 |
| 12. 请求/轮询健壮性 | 请求 15 秒超时覆盖响应体；AbortController；提交轮询顺序执行、指数退避、最多 5 次连续失败/10 分钟总时限；识别完整中间状态；离开页面取消 | `runtime-contract.spec.ts`；题库和 Playground 共用轮询器 |
| 13. 跨标签页刷新 | Web Locks 串行化刷新，共用 HttpOnly Cookie；不再依赖各标签页复制的 refresh_token；响应丢失后复用请求编号，30 秒内取回加密保存的同一轮换结果；其他请求重放仍撤销 | 双标签页、丢失响应、PostgreSQL 并发、重放撤销 |
| 14. 角色同步降权 | 区分 provider_role、local_role 和生效 role；默认跟随提供商最新角色，本地覆盖需显式运维命令；生效角色改变撤销旧会话；提供商不能重新启用本地停用账号 | 降权撤销、本地覆盖与来源分离、停用边界 |
| 15. 重型前端依赖 | Markdown 只解析一次，Prism 在渲染阶段高亮，DOM 查询限制在组件内；Mermaid 仅图表需要时加载；Monaco 保留所需贡献模块；拆分共享依赖，避免动态导入被打包拉回主路径 | manifest 静态依赖图门禁和生产浏览器网络验证 |
| 16. 部署一致性 | 生产默认同源 `/api`；Nginx 反代 8080 并重写 Cookie 路径；生产 HTTPS/Origin 启动校验；实际登录/刷新/幂等提交/判题验收脚本；CI 保留不可跳过的 Docker 隔离测试 | 构建、生产浏览器门禁；Docker 与真实站点验收见下文 |

## 会话和权限契约

- 登录/兑换/刷新响应仅返回 access_token；不会再把 refresh_token 写入 localStorage/sessionStorage。旧版本凭证不会自动兑换为 Cookie，升级后需要重新登录一次。
- 浏览器认证请求包含 credentials 和 `X-CSRF-Protection: 1`；刷新另带 Idempotency-Key。服务端检查 Origin，CORS 只允许显式域名。
- 同一刷新请求允许在 30 秒内恢复丢失响应，恢复材料使用独立派生密钥加密。超过恢复窗口且只持有旧 Cookie 时需重新登录；不放宽任意旧令牌重放。
- “记住登录”使用持久 Cookie；不勾选使用浏览器会话 Cookie。多个标签页共用同一浏览器会话，不能同时保持不同账号。浏览器需支持 Web Locks，生产必须 HTTPS。
- 提供商角色同步默认可以升权和降权；本地覆盖不从旧角色自动推断。运维可执行 `python manage.py set-role --user-id ID --role member|staff|manager`，或 `--role provider` 恢复提供商管理；命令会撤销该用户所有旧会话。
- 普通排行榜为最多约 30 秒延迟的最终一致投影；Worker 不可用时继续读最后完整版本，首次投影尚未生成时返回 503。投影只在 Worker 中聚合，当前仍按全量提交重建，后续若达到大规模数据应再按用户增量维护并以压测确定周期。

## 部署步骤

1. 备份数据库；使用同一版本的 API 和 Worker 镜像，先执行 `python manage.py migrate`。本轮新增 0018/0019 迁移及排行榜投影表。0019 只清理旧的派生 PUBLIC_FREEZE 缓存，不删除提交或 FINAL 快照。
2. 生产前端默认请求同源 `/api`，参考 `deploy/nginx.conf.example`。后端设置 FRONTEND_URL、PUBLIC_BACKEND_URL、ALLOWED_ORIGINS 为真实 HTTPS 地址；PUBLIC_BACKEND_URL 需要包含 `/api`。代理只允许可信入口，API 端口仅绑定回环地址。分离 API 域名时显式设置前端 VITE_API_BASE_URL，并重新构建。
3. 同源代理必须将 `/auth` Cookie 路径重写为 `/api/auth`。Cookie 请求测试、跨标签页测试、CSP 和构建静态依赖检查均在 CI 执行。
4. 在真正的判题主机上构建 sandbox 镜像，运行 `python -m pytest tests/sandbox_integration.py -q`；失败禁止发布。
5. 使用专用验收账号和已知会 AC 的赛后题目：配置环境变量 SMOKE_IDENTIFIER、SMOKE_PASSWORD，再运行 `python deploy/smoke.py --base-url https://站点/api --frontend-url https://站点 --problem-id 题目内部ID --code-file 验收代码.py --language python`。此操作新增一条练习提交并在结束时撤销会话，不打印凭证。

## 最终本地验证结果

- 后端：`python -m pytest -q`，81 项通过（4.97 秒），含真实 PostgreSQL 并发、隔离 Redis 和完整 HTTP 判题链路。
- 前端：Node 24.19.0；vue-tsc 与 Vite 生产构建通过；Playwright 10 项通过（24.0 秒）。
- 生产浏览器门禁：CSP、Markdown、Monaco 与 Mermaid 按需加载通过。
- 静态 JS 依赖（未压缩、含共享依赖）：入口 416 KiB，Markdown 621 KiB，Monaco 3084 KiB；这三条路径均不静态依赖 Mermaid。此数据不是网络压测或端到端延迟结论。
- 最终 pip-audit / npm audit 均为 0 个已知漏洞；`git diff --check` 通过。7 个发生改动的 Vue 文件，其 template/style 与 HEAD 比对一致。

## 验证边界

- 本地回归使用隔离 SQLite、真实 Redis Unix socket、临时 PostgreSQL；HTTP 完整链路在明确 test 模式执行合成 Python 程序。
- Docker 隔离门禁已实际尝试，但当前机器的 Docker daemon 没有启动，`/home/z/.docker/desktop/docker.sock` 不存在；因此**不能把本机结果视为 Docker 隔离验收通过**。
- 未提供生产站点和验收账号，所以没有执行线上登录/判题冒烟，也没有真实业务流量压测。本轮没有推送、发布或操作生产数据库。
- 本轮修改过的 Vue 文件已比对 template/style，与工作区 Git HEAD 一致。入口脚本提取到外部文件以满足 CSP，页面布局和样式未改。

## 参考依据

身份校验沿用 [Authlib Flask OIDC 集成](https://docs.authlib.org/en/latest/oauth2/client/web/flask.html)的已验证 userinfo；渲染净化使用 [DOMPurify 官方接口](https://github.com/cure53/DOMPurify)，并避免对净化后内容重新拼接未经净化的输入。
