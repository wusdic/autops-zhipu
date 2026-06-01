# AUTOPS Changelog

所有重要变更将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.5.0] - 2026-06-01

### 执行层实现 + 集成修复

#### Added — 执行层
- **发现引擎**：TCP/ICMP/CIDR网段扫描，自动推断资产类型（Linux/Windows/数据库/Web），异步扫描，纳管接口
- **内置采集器**：Ping、TCP端口、HTTP、SSL证书、数据库检查 5个采集器
- **采集调度器**：定时采集周期（默认900秒）、资产创建事件触发采集、Ping状态变更检测
- **策略→自动化执行链路**：EXECUTION_CREATED事件消费者，自动创建执行记录并运行脚本
- **告警自动恢复**：执行完成后自动将告警状态更新为resolved

#### Fixed
- collection-jobs API参数位置错位导致items返回空列表
- 双重策略匹配（移除重复的on_alert_created_match_policy订阅）
- 策略匹配JSON字段（trigger_condition/action_chain）未解析为dict
- ExecutionStep.append_execution_log使用不存在的DB字段
- ExecutionCreate.asset_ids不允许空列表

#### 前端修复
- 发现结果IP列空白（API字段`ip` vs 前端`ip_address`）
- 纳管向导HTML结构损坏（恢复完整wizard四步流程）
- 凭证步骤强制必填改为可选
- discovered状态未映射（前端只识别'new'/'managed'）
- NotificationBell/ConfigInheritance硬编码API路径改用routes.ts常量

#### 清理
- 删除39个测试残留采集器，只保留5个标准内置采集器

### 验证
- ✅ 完整事件链路验证通过：Ping采集→状态变更→事件→告警→策略→自动化执行→恢复
- ✅ 浏览器E2E：登录→发现资产→纳管→采集→告警→策略→自动化 全流程可用

---

## [0.4.0] - 2026-06-01

### M5增强 + 前端全面增强

#### Added
- AI Agent LLM集成（智谱GLM）
- 数据库方言抽象层（MySQL/PostgreSQL/openGauss/达梦/人大金仓）
- 前端M3/M5页面实现
- 前端功能全面增强：CollectorPage(103→770行)、CommandCenterPage(155→807行)等
- 批量操作框架
- 集成测试完善
- 通知渠道API

---

## [0.3.0] - 2026-05-31

### M3标准场景闭环

#### Added
- 8个标准场景的事件规则、策略、自动化动作
- 故障处置台、执行日志流、验证结果
- 工单升级和知识沉淀
- E2E测试

---

## [0.2.0] - 2026-05-30

### M2平台主干完成

#### Added
- 13个领域模块核心实现（models/schemas/repository/service/events/handlers）
- 统一事件总线
- 前端7大工作台基础页面
- 145+ API端点

---

## [0.1.0] - 2026-05-29

### M1基础骨架完成

#### Added
- FastAPI项目初始化
- SQLAlchemy + Alembic配置
- MySQL/Redis连接
- 统一响应结构 `{code, message, data, trace_id}`
- 统一错误码
- JWT认证和RBAC权限框架
- Vue 3 + TypeScript + Vite前端项目
- Element Plus UI + 主题
- 路由守卫和布局框架

---

## [0.0.1] - 2026-05-28

### M0设计完成

#### Added
- 项目初始化：目录结构、核心设计文档
- 37份设计文档
- 8份ADR技术决策记录
- 全局约束和目标架构定义
- 开发计划和测试策略
