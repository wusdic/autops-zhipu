# 设备深度采集 · 自动巡检 · 自动报告（实现说明）

> 本功能补齐"网段→发现→**深度采集→巡检→报告**"闭环中此前缺失的后三环。
> 分支：`claude/sweet-goodall-lsabb8`。**未在本环境跑过集成测试**（无依赖/无 MySQL/无目标设备），
> 需在 CI（装依赖）+ 至少一台真实设备上做冒烟验证后再合并 main。

## 新增能力

| 环节 | 实现 | 入口 |
|---|---|---|
| 深度采集 | SSH(Linux) / WinRM(Windows) / SNMP(网络设备) 采集 OS/CPU/内存/磁盘/负载/运行时间 | `app/workers/device_inspect.py` |
| 凭据接入 | 按资产绑定凭据解密并归一化（用户名/密码/私钥/community） | `app/common/credentials.py` |
| 巡检执行 | 按模板 `check_items` 逐项评估阈值，写 `InspectionResult` + `InspectionReport` | `app/domains/inspection/executor.py` |
| 定时巡检 | worker 内按 `InspectionPlan.cron_expression` 每分钟匹配触发 | `app/workers/inspection_scheduler.py` |
| 报告生成 | 汇总资产/告警/最近巡检，渲染 HTML 落盘并归档 | `app/domains/report/generator.py` |

触发改造：`POST /inspection/tasks` 与 `POST /report/generate` 现在会真正后台执行（此前只建记录）。

## 依赖（已加入 `pyproject.toml`，均懒加载）

`asyncssh`（SSH）、`pysnmp`（SNMP）、`pywinrm`（WinRM）。
未安装时对应采集方式返回 `method_unavailable`，不影响进程启动与其它方式。

## 使用前置

1. **凭据**：在凭证中心创建并绑定到资产。约定 `data` 为 JSON 对象：
   - Linux：`{"username":"root","password":"***"}` 或 `{"username":"root","private_key":"-----BEGIN..."}`（`cred_type=ssh_password`/`ssh_key`）
   - Windows：`{"username":"Administrator","password":"***"}`（`cred_type=windows_password`；需目标开启 WinRM 5985/NTLM）
   - 网络设备：`{"community":"public"}`（`cred_type=snmp_community`；SNMP v2c/161）
   - 兼容：若 `data` 为裸串，SNMP 视为 community，其余视为 password。
2. **采集方式选择**：按 `asset_type`（network/switch/router→SNMP）、`os_type`/凭据类型（windows→WinRM）判定，默认 SSH。
3. **巡检模板** `check_items`（不填用内置默认：可达性+磁盘>90/预警80+内存>90/预警80）。单项格式：
   ```json
   {"key":"disk","name":"磁盘使用率","metric":"disk_used_percent_max","op":">","threshold":90,"warn":80,"severity":"fail"}
   ```
   可用 `metric`：`reachable/cpu_count/load_1m/mem_used_percent/disk_used_percent_max/uptime_seconds`。
4. **定时巡检**：给 `InspectionPlan` 设标准 5 字段 cron（如 `0 2 * * *` 每日 02:00），`enabled=true`，由 worker 触发。
5. **报告目录**：`AUTOPS_REPORTS_DIR`（默认 `<cwd>/data/reports`）。生成后可经 `GET /report/tasks/{id}/download` 下载。

## 端到端验证清单（合并前请执行）

```text
1. pip install -e ".[dev]"（确认 asyncssh/pysnmp/pywinrm 安装成功）
2. 备一台 Linux：创建 ssh_password 凭据并绑定资产 → POST /inspection/tasks
   → 轮询 GET /inspection/tasks/{id} 直到 completed → GET /inspection/results 看到磁盘/内存项
3. POST /report/generate → GET /report/tasks/{id}/download 得到 HTML
4. 建一个 cron=*/2 * * * * 的启用计划，观察 worker 日志每 2 分钟触发
5. Windows(WinRM)/网络设备(SNMP) 各验证一台
```

## 已知边界 / 后续

- 巡检/报告的"按需触发"在 **API 进程内**后台执行（沿用 discovery 模式）；大规模建议迁 worker 队列。
- WinRM 仅 HTTP/NTLM 5985；如需 HTTPS/Kerberos/CredSSP 需扩展。
- SNMP 仅 v2c 基础 OID（sysDescr/sysName/uptime）；v3 与接口/CPU/内存 OID 待扩展。
- cron 为内置极简实现（支持 `* */n a-b a,b` 与数字），未支持 `L/W/#` 等高级语法。
