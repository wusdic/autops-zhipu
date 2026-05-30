# 采集与状态中心 (Collector & State Center)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/collector/` + `backend/app/domains/state/`

---

## 1. 职责

- **采集中心：** 负责感知现实环境，执行采集任务，输出标准化结果
- **状态中心：** 负责回答"现在怎么样"，维护最新状态，检测状态变更

## 2. 采集器框架

### 2.1 BaseCollector 接口

```python
class BaseCollector(ABC):
    collector_type: str

    @abstractmethod
    def validate_config(self, config: dict) -> bool: ...

    @abstractmethod
    def test_connection(self, target: str, credential: dict) -> ConnectionTestResult: ...

    @abstractmethod
    def collect(self, target: str, config: dict, context: dict) -> CollectionResult: ...

    def parse(self, raw_result: Any) -> dict: ...
    def normalize(self, parsed: dict) -> dict: ...
```

### 2.2 统一输出格式

```json
{
  "collector": "ssh",
  "target_asset_id": "asset-001",
  "status": "success",
  "metrics": [
    {"name": "disk_usage_pct", "value": 92.5, "unit": "%", "labels": {"mount": "/"}}
  ],
  "facts": {
    "os": "Ubuntu 22.04",
    "kernel": "5.15.0",
    "cpu_count": 4,
    "memory_total_gb": 16
  },
  "logs": [],
  "errors": [],
  "started_at": "2026-01-01T00:00:00Z",
  "finished_at": "2026-01-01T00:00:05Z",
  "trace_id": "trace-001"
}
```

### 2.3 采集器列表

| 采集器 | 协议 | 目标类型 | 采集内容 |
|---|---|---|---|
| SSH Collector | SSH | Linux 主机 | 系统指标、磁盘、进程、日志、服务状态 |
| WMI/WinRM Collector | WMI/WinRM | Windows 主机 | 系统指标、磁盘、服务、进程、事件日志 |
| HTTP/TCP Collector | HTTP/TCP | Web 服务/API | 状态码、响应时间、SSL 证书、端口可达性 |
| Database Collector | DB 协议 | 数据库 | 连接状态、连接数、慢查询、表空间 |
| Certificate Collector | TLS | SSL/TLS 服务 | 证书有效期、颁发者、域名 |
| SNMP Collector | SNMP | 网络设备 | 接口状态、流量、CPU、内存 |
| ICMP Collector | ICMP | 所有资产 | 可达性、延迟 |

### 2.4 Collector Registry

采集器注册中心：
- 记录采集器类型、版本、能力声明
- 健康检查和心跳
- 采集器状态管理

## 3. 采集任务调度

### 3.1 调度类型

| 类型 | 说明 |
|---|---|
| manual | 手动触发 |
| cron | cron 表达式定时 |
| interval | 固定间隔 |
| event | 事件触发 |

### 3.2 采集失败分类

| 分类 | 说明 | 处理 |
|---|---|---|
| connection_failed | 连接失败 | 记录，重试 |
| authentication_failed | 认证失败 | 生成事件，不重试 |
| timeout | 超时 | 记录，重试 |
| parse_error | 解析失败 | 记录原始数据 |
| partial_success | 部分成功 | 记录成功部分和失败原因 |

## 4. 状态管理

### 4.1 状态类型

| 状态类型 | 说明 | 值示例 |
|---|---|---|
| reachability | 可达性 | reachable/unreachable |
| service | 服务状态 | running/stopped/unknown |
| disk | 磁盘使用 | {"usage_pct": 92, "mount": "/"} |
| cpu | CPU 使用率 | {"usage_pct": 75.5} |
| memory | 内存使用 | {"usage_pct": 80, "total_gb": 16} |
| network | 网络状态 | {"status": "up", "speed_mbps": 1000} |
| port | 端口状态 | {"port": 80, "status": "open"} |
| process | 进程状态 | {"name": "nginx", "status": "running", "pid": 1234} |
| certificate | 证书状态 | {"days_remaining": 15, "issuer": "Let's Encrypt"} |
| connection_count | 连接数 | {"current": 150, "max": 500} |

### 4.2 状态存储

- **最新状态：** Redis 缓存（实时查询）+ state_snapshots 表（持久化）
- **状态历史：** state_snapshots 按时间存储
- **状态变更：** state_changes 记录每次变更

### 4.3 状态变更检测

```text
采集结果 → 与当前状态对比 → 检测变更 → 生成 state_change → 发布事件 → 事件中心处理
```

### 4.4 状态恢复验证

当异常状态恢复后自动验证：
- 连续 2 次采集正常才标记恢复
- 恢复后关闭对应告警
- 恢复事件记录到时间线

## 5. 数据模型

见 `DATA_ARCHITECTURE.md` 3.5-3.6 节：
- collector_instances
- collection_jobs
- collection_results
- collection_logs
- state_snapshots
- state_changes

## 6. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/collectors | 采集器列表 |
| GET | /api/v1/collectors/{id}/health | 采集器健康 |
| GET | /api/v1/collection-jobs | 采集任务列表 |
| POST | /api/v1/collection-jobs | 创建采集任务 |
| POST | /api/v1/collection-jobs/{id}/execute | 手动执行 |
| GET | /api/v1/collection-results | 采集结果列表 |
| GET | /api/v1/collection-results/{id} | 采集结果详情 |
| GET | /api/v1/states/{asset_id} | 资产最新状态 |
| GET | /api/v1/states/{asset_id}/history | 状态历史 |
| GET | /api/v1/state-changes | 状态变更列表 |

## 7. 领域事件

| 事件 | 说明 |
|---|---|
| CollectionStarted | 采集开始 |
| CollectionCompleted | 采集完成 |
| CollectionFailed | 采集失败 |
| StateChanged | 状态变更 |
| StateRecovered | 状态恢复 |
| CollectorHeartbeatLost | 采集器心跳丢失 |

## 8. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| asset | 采集目标为资产 | service 调用 |
| config | 使用采集配置版本 | service 调用 |
| event | 状态变更发布事件 | 事件发布 |
| alert | 异常状态触发告警 | 事件订阅 |
| log | 采集日志记录 | service 调用 |
