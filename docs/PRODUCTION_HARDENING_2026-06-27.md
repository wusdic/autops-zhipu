# 生产级改进评审与处置（2026-06-27）

针对外部提出的三大生产级方向逐条核对**当前代码实际状态**，只补真正缺失的部分，
不重复造轮子、不打临时补丁。

## 1. 事件驱动架构 —— 已具备（无需重做）
评审建议 | 现状
---|---
`bus.publish()` 原子写 outbox | ✅ `events.py::_persist_to_outbox` 随业务 session 同事务写 `event_outbox`
Worker 持久化消费 outbox | ✅ `outbox.py::OutboxConsumer.run_forever` + `runner.py::WorkerRunner`
崩溃/重启不丢（lease+心跳） | ✅ `consume_once` 先恢复过期租约（`locked_until < NOW()` 回 pending），`FOR UPDATE SKIP LOCKED` 抢占
失败重试 + 死信 | ✅ 指数退避 `2^n*5s` 重试，超 `max_retries` 置 `status='dead'`

> 结论：本项目事件驱动核心已是生产级，本轮不动。

## 2. 故障自愈 —— 补齐关键缺口
- **（关键）新增 `autops-worker.service`**：此前 `install.sh` 只装了 `autops-backend`（API），
  而 outbox 消费 / 采集调度 / 巡检调度 / 执行队列**全部跑在 worker 进程**里。
  没有 worker → outbox 永不消费、采集与执行全部停滞。本轮：
  - `deploy/systemd/autops-worker.service` + `install.sh` 自动创建/enable/start；
  - `Restart=always` + `RestartSec=5` + `StartLimitIntervalSec/Burst`（近似指数退避，避免狂重启）；
  - `AmbientCapabilities=CAP_NET_RAW CAP_NET_BIND_SERVICE`（R12：ping/SNMP 需原始套接字）。
- backend unit 同步补 `StartLimitIntervalSec/Burst`；明文 `DB_PASSWORD=***` 改为变量并提示用 `EnvironmentFile`。
- `docker-compose.yml` worker 已 `restart: always`，本轮补 `cap_add: [NET_RAW]`。
- `self_check.sh` 增 `autops-worker` 服务与进程检查。

## 3. 可观测性 —— 补齐
- **Worker 存活信号**：`runner.py` 心跳循环每 60s 写 Redis `autops:worker:heartbeat:<id>`（TTL 180s）。
- **综合诊断端点** `GET /api/v1/platform/diagnostics`（三级告警 ok/warning/critical，13 项）：
  database、redis、outbox 积压、outbox 死信、outbox 卡住（租约过期）、巡检积压、执行积压、
  管理员账户、角色、迁移版本、worker 存活、磁盘用量、API 自身；整体取最严重项。
  - outbox 积压此前已有（`platform_extra.py`），本轮统一纳入诊断并补死信/卡住/worker 存活/磁盘/数据完整性。
- **日志轮转**：`deploy/systemd/autops.logrotate` → 安装到 `/etc/logrotate.d/autops`
  （应用文件日志；systemd 服务日志由 journald 配额管理）。

## 验证
- `py_compile` health.py / runner.py 通过；`ruff -F` 通过。
- `bash -n` install.sh / self_check.sh 通过。
- 诊断端点与心跳依赖运行态（DB/Redis/worker），须在可运行环境端到端复核。
