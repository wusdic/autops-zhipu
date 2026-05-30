# AUTOPS 后端架构设计

> 文档状态：current  
> 是否为事实源：yes  
> 建议路径：`docs/01-architecture/BACKEND_ARCHITECTURE.md`

---

## 1. 技术栈

| 组件 | 选择 | 版本 |
|---|---|---|
| 语言 | Python | 3.10+ |
| Web 框架 | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据验证 | Pydantic | V2 |
| 数据库迁移 | Alembic | 1.12+ |
| 测试 | pytest | 7.4+ |
| 代码检查 | ruff | 最新 |
| 格式化 | black | 最新 |
| 类型检查 | mypy | 最新 |
| 异步任务 | ARQ (Redis-based) | 最新 |
| WebSocket | FastAPI 原生 | - |
| 链路追踪 | OpenTelemetry | 最新 |

---

## 2. 分层架构

```text
┌─────────────────────────────────────────────────┐
│                    API 层                        │
│  FastAPI Router / Pydantic Schema / Auth Guard  │
├─────────────────────────────────────────────────┤
│                  Service 层                      │
│  业务逻辑编排 / 领域事件发布 / 权限校验          │
├─────────────────────────────────────────────────┤
│                Repository 层                     │
│  数据访问抽象 / 查询封装 / 无业务逻辑            │
├─────────────────────────────────────────────────┤
│                 Model 层                         │
│  SQLAlchemy ORM 模型 / 表结构定义                │
├─────────────────────────────────────────────────┤
│               Infrastructure 层                 │
│  DB / Redis / 配置 / 日志 / 加密 / OTel         │
└─────────────────────────────────────────────────┘
```

### 2.1 API 层

**职责：**
- 定义 HTTP 路由和方法
- 请求参数验证（Pydantic Schema）
- 认证和权限检查（依赖注入）
- 调用 Service 层
- 统一响应封装

**规范：**
- 所有 API 在 `backend/app/api/v1/` 下
- 按领域分文件：`asset.py`, `config.py`, `collector.py` ...
- 使用 FastAPI `APIRouter` 前缀 `/api/v1/{domain}`
- 所有响应使用 `ApiResponse[T]` 统一封装

### 2.2 Service 层

**职责：**
- 核心业务逻辑
- 编排多个 Repository
- 发布领域事件
- 调用其他领域 Service（通过接口）
- 权限校验
- 审计日志记录

**规范：**
- 每个领域一个 `service.py`
- Service 接受 Repository 作为依赖注入
- 领域间调用通过 Service 接口，不直接导入 Repository
- 跨领域操作优先使用事件驱动

### 2.3 Repository 层

**职责：**
- 数据库 CRUD 操作
- 查询构建和分页
- 数据访问隔离

**规范：**
- 每个领域一个 `repository.py`
- 使用 SQLAlchemy 2.0 select 风格
- 所有查询通过 Repository，业务代码不直接写 SQL
- 原生 SQL 集中管理在 Repository 中
- 不包含业务逻辑

### 2.4 Model 层

**职责：**
- SQLAlchemy ORM 模型定义
- 表结构、字段类型、索引、约束
- 模型关系定义

**规范：**
- 每个领域一个 `models.py`
- 使用 SQLAlchemy 2.0 Declarative Base
- 所有模型继承自 `Base`
- 字段使用 `Mapped` 和 `mapped_column`
- 关系使用 `relationship`

---

## 3. 目录结构

```text
backend/
  pyproject.toml                    # 项目依赖和配置
  alembic.ini                       # Alembic 配置
  alembic/                          # 数据库迁移
    versions/                       # 迁移脚本
    env.py

  app/
    __init__.py
    main.py                         # FastAPI 应用入口

    api/
      __init__.py
      deps.py                       # 公共依赖注入
      v1/
        __init__.py
        router.py                   # V1 总路由
        asset.py                    # 资产 API
        config.py                   # 配置 API
        credential.py               # 凭证 API
        collector.py                # 采集器 API
        state.py                    # 状态 API
        event.py                    # 事件 API
        alert.py                    # 告警 API
        policy.py                   # 策略 API
        automation.py               # 自动化 API
        log.py                      # 日志 API
        aiops.py                    # AIops API
        knowledge.py                # 知识 API
        ticket.py                   # 工单 API
        governance.py               # 治理 API

    domains/
      __init__.py
      asset/
        __init__.py
        models.py                   # 资产 ORM 模型
        schemas.py                  # 请求/响应 Schema
        repository.py               # 数据访问
        service.py                  # 业务逻辑
        events.py                   # 领域事件定义
        handlers.py                 # 事件处理器
        permissions.py              # 权限定义
        tests/
          __init__.py
          test_service.py
          test_repository.py
      config/                       # 同上结构
      collector/
      state/
      event/
      alert/
      log/
      policy/
      automation/
      aiops/
      knowledge/
      ticket/
      governance/

    common/
      __init__.py
      response.py                   # 统一响应结构
      errors.py                     # 统一错误码
      pagination.py                 # 分页工具
      context.py                    # 请求上下文
      types.py                      # 公共类型定义
      enums.py                      # 公共枚举

    infra/
      __init__.py
      database.py                   # 数据库连接和会话管理
      redis.py                      # Redis 连接和工具
      config.py                     # 配置加载器
      security.py                   # 加密/解密工具
      logging.py                    # 日志配置
      telemetry.py                  # OpenTelemetry 配置
      events.py                     # 事件总线

    workers/
      __init__.py
      celery_app.py                 # 或 ARQ worker
      tasks/
        __init__.py
        collection_tasks.py         # 采集任务
        automation_tasks.py         # 自动化执行任务
        policy_tasks.py             # 策略检查任务
        cleanup_tasks.py            # 清理任务

    integrations/
      __init__.py
      base.py                       # BaseCollector 接口
      ssh_collector.py              # SSH 采集器
      winrm_collector.py            # WinRM 采集器
      http_collector.py             # HTTP/TCP 采集器
      db_collector.py               # 数据库采集器
      cert_collector.py             # 证书采集器
      snmp_collector.py             # SNMP 采集器

    tests/
      __init__.py
      conftest.py                   # 全局 fixtures
      test_health.py                # 健康检查测试
```

---

## 4. 统一响应结构

```python
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    trace_id: str = ""
```

**规范：**
- 所有 API 必须返回 `ApiResponse[T]`
- 成功：`code=0, message="success"`
- 错误：`code=错误码, message=错误描述`
- `trace_id` 由中间件自动注入
- 分页响应使用 `PaginatedResponse[T]`

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

---

## 5. 错误码体系

### 格式

```
{模块}{错误级别}{序号}
```

- 模块：2 位数字（00=通用, 01=资产, 02=配置, ...）
- 错误级别：1 位（1=参数错误, 2=业务错误, 3=权限错误, 4=系统错误）
- 序号：2 位数字

### 通用错误码

| 错误码 | 说明 |
|---|---|
| 00001 | 未知错误 |
| 00010 | 参数验证失败 |
| 00011 | 请求格式错误 |
| 00100 | 未认证 |
| 00101 | Token 过期 |
| 00102 | Token 无效 |
| 00103 | 权限不足 |
| 00200 | 资源不存在 |
| 00201 | 资源已存在 |
| 00202 | 资源冲突 |
| 00300 | 数据库错误 |
| 00301 | 缓存错误 |
| 00400 | 外部服务错误 |
| 00401 | AI 服务不可用 |

### 领域错误码

| 前缀 | 领域 |
|---|---|
| 01xxx | 资产中心 |
| 02xxx | 配置中心 |
| 03xxx | 凭证中心 |
| 04xxx | 采集中心 |
| 05xxx | 状态中心 |
| 06xxx | 事件中心 |
| 07xxx | 告警中心 |
| 08xxx | 策略中心 |
| 09xxx | 自动化中心 |
| 10xxx | 日志中心 |
| 11xxx | AIops |
| 12xxx | 知识中心 |
| 13xxx | 工单中心 |
| 14xxx | 治理中心 |

---

## 6. 中间件链

```text
请求 → CORS → TraceIDMiddleware → AuthMiddleware → AuditMiddleware → Router → Response
```

### 6.1 TraceIDMiddleware

- 为每个请求生成唯一 trace_id（UUID4）
- 写入 `request.state.trace_id`
- 注入响应 header `X-Trace-Id`
- 传递给日志上下文

### 6.2 AuthMiddleware

- 从 `Authorization: Bearer <token>` 提取 JWT
- 解析用户 ID、角色、权限
- 写入 `request.state.user`
- 白名单路径跳过认证（`/health`, `/ready`, `/docs`, `/openapi.json`）

### 6.3 AuditMiddleware

- 记录请求方法、路径、用户、trace_id
- 记录响应状态码
- 写入审计日志（异步）

---

## 7. 依赖注入

使用 FastAPI `Depends` 实现依赖注入：

```python
# 公共依赖
async def get_db() -> AsyncSession: ...
async def get_redis() -> Redis: ...
async def get_current_user(request: Request) -> User: ...

# Repository 依赖
def get_asset_repository(db: AsyncSession = Depends(get_db)) -> AssetRepository: ...

# Service 依赖
def get_asset_service(
    repo: AssetRepository = Depends(get_asset_repository),
    event_bus: EventBus = Depends(get_event_bus),
) -> AssetService: ...
```

---

## 8. 配置加载

### 配置文件结构

```text
configs/
  app.yaml           # 应用配置（端口、调试模式、CORS）
  database.yaml      # 数据库连接配置
  redis.yaml         # Redis 连接配置
  llm.yaml           # 大模型配置
  security.yaml      # 安全配置（加密、Token过期时间）
  collectors.yaml    # 采集器配置（超时、并发数）
  policies.yaml      # 策略默认配置
```

### 加载机制

```python
from pathlib import Path
import yaml

class Settings:
    def __init__(self, config_dir: str = "configs"):
        self._config_dir = Path(config_dir)
        self._load_all()

    def _load_all(self):
        # 环境变量覆盖文件配置
        # 支持 configs/*.yaml 加载
        # 支持嵌套属性访问
        ...
```

**优先级：** 环境变量 > `.env` 文件 > `configs/*.yaml` > 默认值

---

## 9. 事件驱动架构

### 事件总线

```python
class EventBus:
    async def publish(self, event: DomainEvent) -> None: ...
    def subscribe(self, event_type: str, handler: Callable) -> None: ...
```

### 领域事件示例

```python
class AssetCreated(DomainEvent):
    asset_id: str
    asset_type: str
    timestamp: datetime

class StateChanged(DomainEvent):
    asset_id: str
    old_state: str
    new_state: str
    timestamp: datetime

class AlertTriggered(DomainEvent):
    alert_id: str
    severity: str
    asset_ids: list[str]
    timestamp: datetime
```

### 事件流转

```text
状态变更事件 → 事件中心 → 事件关联 → 告警生成 → 策略匹配 → 自动化触发
     ↓                                           ↓
  知识更新                                    执行日志记录
```

---

## 10. 后台任务

### Worker 框架

使用 ARQ（基于 Redis）作为后台任务队列：

```python
# workers/tasks/collection_tasks.py
async def run_collection(ctx, job_id: str):
    """执行采集任务"""
    ...

async def run_automation(ctx, execution_id: str):
    """执行自动化任务"""
    ...
```

### 任务类型

| 任务 | 说明 | 队列 |
|---|---|---|
| 采集任务 | 定时或手动触发采集 | default |
| 自动化执行 | 策略触发的自动化动作 | automation |
| 策略检查 | 事件触发的策略匹配 | default |
| 告警收敛 | 定时告警收敛和升级 | default |
| 清理任务 | 过期数据清理 | maintenance |
| AI 分析 | 异步 AI 根因分析 | aiops |

---

## 11. WebSocket 设计

### 连接管理

```python
class ConnectionManager:
    async def connect(self, websocket: WebSocket, user_id: str): ...
    async def disconnect(self, user_id: str): ...
    async def send_to_user(self, user_id: str, message: dict): ...
    async def broadcast(self, message: dict): ...
```

### 事件类型

| 事件 | 说明 |
|---|---|
| `state.change` | 资产状态变更 |
| `alert.new` | 新告警 |
| `alert.update` | 告警状态更新 |
| `execution.log` | 执行日志流 |
| `execution.status` | 执行状态变更 |
| `aiops.analysis` | AI 分析结果 |
| `notification` | 系统通知 |

---

## 12. 领域模块标准结构

每个领域必须包含：

| 文件 | 职责 |
|---|---|
| `models.py` | SQLAlchemy ORM 模型、表定义 |
| `schemas.py` | Pydantic 请求/响应模型 |
| `repository.py` | 数据访问层、CRUD |
| `service.py` | 业务逻辑层 |
| `events.py` | 领域事件定义 |
| `handlers.py` | 事件处理器（订阅其他领域事件） |
| `permissions.py` | 权限定义 |
| `tests/` | 单元测试 |

### 领域间交互规则

1. **同层 Service 调用：** 允许通过 Service 接口调用
2. **禁止跨领域 Repository 访问：** 不直接访问其他领域的数据库表
3. **推荐事件驱动：** 异步解耦通过事件总线
4. **循环依赖禁止：** 领域间不能出现循环导入

---

## 13. 异常处理

```python
class AppException(Exception):
    """应用异常基类"""
    code: int
    message: str
    detail: dict | None = None

class NotFoundException(AppException): ...
class ValidationException(AppException): ...
class PermissionDeniedException(AppException): ...
class BusinessRuleException(AppException): ...
class ExternalServiceException(AppException): ...
```

全局异常处理器：

```python
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.http_status,
        content=ApiResponse(
            code=exc.code,
            message=exc.message,
            trace_id=request.state.trace_id,
        ).model_dump()
    )
```
