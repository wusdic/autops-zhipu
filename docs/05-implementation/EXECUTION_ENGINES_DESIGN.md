# AUTOPS 核心执行引擎设计

> 文档状态: accepted  
> 事实源: yes  
> 日期: 2026-06-01

---

## 1. 背景与问题

AUTOPS 平台当前具备完整的数据模型、API层、事件总线、前端UI，但核心"执行层"是模拟的：

- **资产发现**: `DiscoveryService.create_task()` 返回mock数据，`list_tasks()` 返回空
- **采集器**: `CollectorService` 只有CRUD，没有真正的SSH/Ping/HTTP探测逻辑
- **自动化执行**: `create_execution()` 只创建DB记录，不执行任何命令
- **定时调度**: `workers/` 目录为空，没有定时任务
- **前端接口不匹配**: 资产发现前端发送 `name/cidr/protocols/ports`，后端schema只接受 `ip_range/scan_type`

**后果**: 用户无法体验"自动发现资产 → 自动采集状态 → 自动发现异常 → 自动分析处理"的自治运维闭环。

---

## 2. 设计目标

1. **真实可运行**: 所有执行引擎在本机环境可实际运行
2. **安全可控**: 高危命令黑名单、执行审批、dry-run 模式
3. **事件驱动**: 执行结果通过事件总线自动触发下游流程
4. **渐进降级**: 采集/执行失败不影响平台运行
5. **前后端一致**: API schema 统一，前端请求格式匹配后端

---

## 3. 架构概览

```
用户/定时触发
    │
    ├─[1] 资产发现引擎 (DiscoveryEngine)
    │     IP扫描 → TCP端口探测 → 创建资产记录
    │
    ├─[2] 采集调度器 (SchedulerWorker)  
    │     定时/手动 → 创建采集Job → 调用采集器 → 记录状态
    │
    ├─[3] 内置采集器 (Built-in Collectors)
    │     PingCollector / TCPCollector / HTTPCollector / CertCollector / SSHCollector / DBCollector
    │
    ├─[4] 执行引擎 (ExecutionWorker)
    │     运行脚本 → 记录步骤/日志 → 触发验证 → 发布事件
    │
    └─[5] LLM集成 (已有实现，需启动服务)
          AI分析 → 结构化输出 → 推荐动作
```

事件流:
```
采集结果 → 状态变更 → 事件创建 → 告警规则匹配 → 告警创建
  → 策略匹配 → 自动化执行 → 执行日志 → 验证 → 知识沉淀
```

---

## 4. 资产发现引擎 (DiscoveryEngine)

### 4.1 后端Schema修改

```python
# backend/app/domains/asset/discovery_schemas.py

class DiscoveryTaskCreate(BaseModel):
    """发现任务创建 - 对齐前端字段"""
    name: str                          # 任务名称
    ip_mode: str = "cidr"              # "cidr" | "range"
    cidr: str | None = None            # CIDR格式: 10.168.1.0/24
    ip_start: str | None = None        # 起始IP (range模式)
    ip_end: str | None = None          # 结束IP (range模式)
    protocols: list[str] = ["icmp"]    # ["icmp","tcp","ssh","http","snmp"]
    ports: str | None = None           # "22,80,443,3306"
    credential_id: str | None = None   # 绑定凭证(SSH探测用)
    timeout: int = 30                  # 超时秒数
    scan_type: str = "ping"            # 兼容旧字段
    asset_type: str = "linux_server"   # 兼容旧字段
```

### 4.2 DiscoveryTask持久化

新增 `discovery_tasks` 表和 `discovery_results` 表，替代当前的mock返回。

```sql
CREATE TABLE discovery_tasks (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    ip_range VARCHAR(500) NOT NULL,
    ip_mode VARCHAR(20) DEFAULT 'cidr',
    protocols JSON,
    ports VARCHAR(200),
    credential_id VARCHAR(36),
    timeout INT DEFAULT 30,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/running/completed/failed
    discovered_count INT DEFAULT 0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME
);

CREATE TABLE discovery_results (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    ip VARCHAR(45) NOT NULL,
    hostname VARCHAR(200),
    asset_type VARCHAR(50) DEFAULT 'linux_server',
    open_ports JSON,                     -- [22, 80, 443]
    status VARCHAR(20) DEFAULT 'discovered',  -- discovered/onboarded/ignored
    metadata JSON,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    onboarded_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES discovery_tasks(id)
);
```

### 4.3 扫描算法

```python
async def scan_network(self, task: DiscoveryTask) -> list[dict]:
    """异步并发TCP端口探测"""
    ips = self._expand_ip_range(task.ip_range)  # CIDR或range展开
    semaphore = asyncio.Semaphore(50)  # 并发控制
    results = []
    
    async def probe(ip):
        async with semaphore:
            open_ports = []
            for port in ports_to_scan:
                if await self._tcp_check(ip, port, timeout=1):
                    open_ports.append(port)
            if open_ports or await self._ping_check(ip):
                return {"ip": ip, "open_ports": open_ports}
            return None
    
    tasks = [probe(ip) for ip in ips]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            results.append(result)
    
    return results
```

- **并发控制**: 50个并发探测
- **探测方式**: TCP connect (asyncio.open_connection) + ICMP ping (subprocess ping)
- **IP展开**: ipaddress模块处理CIDR和range
- **结果判定**: 任一端口开放或ping通即为存活

### 4.4 自动纳管

发现的IP自动创建资产记录:
- 根据开放端口推断 asset_type: 22→linux_server, 3306→database, 80/443→web_service, 135→windows_server
- hostname 通过反解DNS或留空
- 状态设为 `discovered`，后续采集任务更新为 `online`/`offline`

### 4.5 前端对齐

前端 `AssetDiscoveryPage.vue` 的 `createTask()` 已发送正确格式(name/cidr/protocols/ports等)，
后端修改schema接受即可，无需改前端。

---

## 5. 内置采集器 (Built-in Collectors)

### 5.1 采集器基类

```python
# backend/app/workers/collectors/base.py

class BaseCollector:
    name: str
    collector_type: str
    
    async def collect(self, asset: Asset, config: dict) -> CollectorResult:
        """执行采集，返回结果"""
        raise NotImplementedError
    
    async def check_available(self) -> bool:
        """检查采集器是否可用"""
        return True

class CollectorResult:
    status: str           # success / failed / timeout
    metrics: dict         # 采集指标
    state_type: str       # reachability / cpu / memory / disk / port / cert
    state_status: str     # normal / warning / critical / unknown
    state_value: str      # 指标值
    raw_output: str       # 原始输出
    error_message: str | None
    duration_ms: int
```

### 5.2 六种内置采集器

| 采集器 | 类型 | 探测方式 | 状态类型 |
|--------|------|----------|----------|
| PingCollector | ping | asyncio TCP :22 或 subprocess ping | reachability |
| TCPCollector | tcp | asyncio TCP connect | port |
| HTTPCollector | http | httpx GET | port + health |
| CertCollector | cert | ssl.SSLSocket getpeercert() | cert_expiry |
| SSHCollector | ssh | subprocess ssh (凭据) | reachability + os_info |
| DBCollector | database | pymysql/aiomysql connect | database_health |

### 5.3 PingCollector (最基础)

```python
async def collect(self, asset, config):
    # 优先TCP探测(快)
    for port in [22, 80, 443]:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(asset.ip, port), timeout=3
            )
            writer.close()
            await writer.wait_closed()
            return CollectorResult(
                status="success", state_type="reachability",
                state_status="normal", state_value="reachable"
            )
        except:
            continue
    
    # TCP失败，尝试ICMP ping
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "1", "-W", "2", asset.ip,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=3)
        if proc.returncode == 0:
            return CollectorResult(status="success", ...)
    except:
        pass
    
    return CollectorResult(status="failed", state_status="critical", state_value="unreachable")
```

### 5.4 HTTPCollector

```python
async def collect(self, asset, config):
    url = config.get("url", f"http://{asset.ip}:{config.get('port', 80)}")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        return CollectorResult(
            status="success" if resp.status_code < 500 else "warning",
            state_type="port",
            state_status="normal" if resp.status_code < 500 else "warning",
            state_value=f"HTTP {resp.status_code}",
            metrics={"status_code": resp.status_code, "response_time_ms": ...}
        )
```

### 5.5 CertCollector (SSL证书过期检测)

```python
async def collect(self, asset, config):
    import ssl, socket
    port = config.get("port", 443)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((asset.ip, port), timeout=5) as sock:
        with ctx.wrap_socket(sock, server_hostname=asset.hostname or asset.ip) as ssock:
            cert = ssock.getpeercert()
            # Parse expiry date
            expire_date = ...
            days_left = (expire_date - datetime.now()).days
            if days_left < 0:
                status = "critical"
            elif days_left < 30:
                status = "warning"
            else:
                status = "normal"
            return CollectorResult(
                state_type="cert_expiry",
                state_status=status,
                state_value=f"{days_left} days",
            )
```

### 5.6 DBCollector (数据库连接检测)

```python
async def collect(self, asset, config):
    import pymysql
    try:
        conn = pymysql.connect(
            host=asset.ip, port=config.get("port", 3306),
            user=config.get("username"), password=config.get("password"),
            connect_timeout=5,
        )
        # 查询连接数、状态等
        with conn.cursor() as cur:
            cur.execute("SHOW STATUS LIKE 'Threads_connected'")
            connections = cur.fetchone()[1]
            cur.execute("SHOW STATUS LIKE 'Threads_running'")
            running = cur.fetchone()[1]
        conn.close()
        return CollectorResult(
            status="success", state_type="database_health",
            state_status="normal", state_value="connected",
            metrics={"connections": int(connections), "running_threads": int(running)}
        )
    except Exception as e:
        return CollectorResult(status="failed", state_status="critical", ...)
```

---

## 6. 采集调度器 (SchedulerWorker)

### 6.1 架构

```python
# backend/app/workers/scheduler.py

class SchedulerWorker:
    """定时采集调度器 - 作为后台任务运行"""
    
    def __init__(self):
        self.interval = 60  # 默认60秒一个周期
        self.running = False
    
    async def start(self):
        """启动调度循环"""
        self.running = True
        while self.running:
            await self._run_cycle()
            await asyncio.sleep(self.interval)
    
    async def _run_cycle(self):
        """一个调度周期"""
        # 1. 查询所有注册的内置采集器
        # 2. 查询所有在线资产
        # 3. 为每个资产创建采集Job
        # 4. 执行采集
        # 5. 记录结果和状态
        # 6. 发布状态变更事件
```

### 6.2 自动采集触发流程

```
SchedulerWorker._run_cycle()
  → 遍历所有资产
    → 为每个资产匹配合适的采集器 (根据 asset_type)
    → 创建 CollectionJob (status=pending)
    → 调用 Collector.collect()
    → 保存 CollectionResult
    → 调用 StateService.record_snapshot()
      → StateService 检测状态变更
        → 发布 StateEvents.STATE_CHANGED
          → EventHandlers.on_state_changed_create_event()
            → EventService.create_event()
              → 发布 EventEvents.EVENT_CREATED
                → AlertHandlers.on_event_created_match_rules()
                  → 匹配告警规则
                    → 创建告警
                      → PolicyHandlers.on_alert_created_match_policy()
                        → 匹配策略
                          → AutomationHandlers 创建执行
```

### 6.3 启动方式

在 `main.py` 的 `lifespan` 中启动:

```python
@app.on_event("startup")
async def startup():
    # ... 现有启动逻辑
    scheduler = SchedulerWorker()
    asyncio.create_task(scheduler.start())
```

---

## 7. 自动化执行引擎 (ExecutionWorker)

### 7.1 架构

```python
# backend/app/workers/executor.py

class ExecutionWorker:
    """自动化执行引擎"""
    
    async def run_execution(self, execution_id: str):
        """执行一个自动化任务"""
        exe = await self._get_execution(execution_id)
        
        # 1. 加载脚本/Playbook内容
        content = await self._load_content(exe)
        
        # 2. 检查高危命令
        if self._is_blocked(content):
            raise ValueError("高危命令已被阻断")
        
        # 3. 创建执行步骤记录
        step = await self._create_step(execution_id, content)
        
        # 4. 实际执行
        stdout, stderr, exit_code = await self._execute(content, exe.parameters)
        
        # 5. 记录结果
        await self._complete_step(step, stdout, stderr, exit_code)
        
        # 6. 发布事件
        if exit_code == 0:
            await self._publish_step_completed(execution_id, step.id, stdout)
        else:
            await self._publish_step_failed(execution_id, step.id, stderr)
```

### 7.2 执行方式

- **本地脚本**: `asyncio.create_subprocess_exec("/bin/bash", "-c", content)`
- **SSH远程**: `asyncio.create_subprocess_exec("ssh", f"{user}@{ip}", content)` (使用凭证)
- **安全限制**: 
  - 黑名单: `rm -rf /`, `mkfs.`, `dd if=`, `:(){ :|:& };:`
  - 超时: 默认300秒
  - 资源限制: 不能修改系统关键文件

### 7.3 Playbook执行

```python
async def run_playbook(self, execution_id: str):
    """执行Playbook (多步骤)"""
    pb = await self._get_playbook(execution.target_id)
    steps = pb.steps  # JSON数组
    
    for i, step in enumerate(steps):
        # 检查是否需要审批
        if step.get("requires_approval") and exe.status == "approved":
            # 已审批，继续
            pass
        
        # 执行步骤
        result = await self._execute_step(step, execution.parameters)
        
        # 如果步骤失败
        if not result.success:
            if step.get("on_failure") == "abort":
                break
            elif step.get("on_failure") == "continue":
                continue
            elif step.get("on_failure") == "rollback":
                await self._execute_rollback(steps[:i])
                break
```

---

## 8. 修改范围

### 8.1 新增文件

| 文件 | 说明 |
|------|------|
| `backend/app/workers/__init__.py` | 已存在，保持 |
| `backend/app/workers/scheduler.py` | 采集调度器 |
| `backend/app/workers/executor.py` | 执行引擎 |
| `backend/app/workers/collectors/__init__.py` | 采集器包 |
| `backend/app/workers/collectors/base.py` | 采集器基类 |
| `backend/app/workers/collectors/ping.py` | Ping/TCP采集器 |
| `backend/app/workers/collectors/http.py` | HTTP采集器 |
| `backend/app/workers/collectors/cert.py` | 证书采集器 |
| `backend/app/workers/collectors/db.py` | 数据库采集器 |
| `backend/app/workers/collectors/ssh.py` | SSH采集器 |

### 8.2 修改文件

| 文件 | 修改内容 | 来源 |
|------|----------|------|
| `backend/app/domains/asset/discovery_schemas.py` | 扩展schema对齐前端 | F1 |
| `backend/app/domains/asset/discovery_service.py` | 实现真实扫描逻辑，替代mock | S1 |
| `backend/app/domains/asset/discovery_api.py` | 新增 start/result/import 端点 | S1 |
| `backend/app/domains/asset/discovery_models.py` | 新增 DiscoveryTask/DiscoveryResult 模型 | S1 |
| `backend/app/main.py` | 启动调度器worker | S3 |
| `backend/app/domains/automation/service.py` | 集成ExecutionWorker + 新增`append_execution_log` | E1+M1 |
| `backend/app/domains/collector/service.py` | 新增 `list_collectors(asset_type)`, `list_failed_jobs`, `retry_job`, `cancel_job` | M2-M5 |
| `alembic/versions/xxx.py` | 新增 discovery_tasks/results 表迁移 | S1 |

### 8.3 前端修改

前端 `AssetDiscoveryPage.vue` 无需修改（已发送正确格式）。但发现结果的纳管操作需要新API对接。

---

## 9. 安全约束

1. **资产发现**: 只扫描用户指定的IP范围，不自动扩大
2. **采集器**: 只对已纳管资产执行采集，使用用户配置的凭证
3. **执行引擎**: 
   - 高危命令黑名单阻断
   - 高风险策略需审批
   - 支持 dry-run 模式
   - 执行超时自动终止
4. **LLM**: AI推荐动作不直接执行，必须经过策略校验和审批

---

## 10. 验收标准

### 10.1 资产发现

- [ ] 用户输入CIDR → 系统真正扫描网段 → 发现存活的IP和开放端口
- [ ] 发现结果可查看 → 选择性纳管 → 自动创建资产记录
- [ ] 任务状态实时更新: pending → running → completed

### 10.2 自动采集

- [ ] 资产纳管后，调度器自动定时采集 (默认60秒)
- [ ] Ping/TCP采集器正确检测资产可达性
- [ ] HTTP采集器正确检测Web服务状态
- [ ] 采集结果记录到 states 表 → 状态变更触发事件

### 10.3 事件驱动闭环

- [ ] 状态异常(critical) → 自动创建事件 → 匹配告警规则 → 创建告警
- [ ] 告警创建 → 匹配策略 → 触发自动化执行(如dry-run)
- [ ] 状态恢复 → 自动resolve关联告警

### 10.4 自动化执行

- [ ] 脚本内容通过subprocess实际执行
- [ ] 执行结果(stdout/stderr/exit_code)记录到DB
- [ ] 执行步骤事件正确发布
