# 业务系统 ↔ 资源 关系（生产级落地，2026-06-28）

## 背景与问题
此前"业务系统"与"资源"的归属仅靠 `assets.business_system`（名字字符串）匹配：
- 没有给资产分配业务系统的 UI（资产表单无该字段、业务系统页无成员管理）→ 关联不上、`asset_count` 恒 0、健康恒 unknown；
- 名字匹配脆弱：业务系统改名即断链，无引用完整性。

## 设计取舍（结合现有框架）
保留项目既有选择"**业务系统 = `asset_type='business_system'` 的资产行**"（不大动架构），
但把归属关系从"名字符串"升级为**稳定自引用外键**：

- 新增 `assets.business_system_id`（→ 指向业务系统资产的 `id`）作为**成员关系事实源**（改名安全、可校验）。
- 保留 `assets.business_system`（名）为**反范式展示缓存**，由 service 同步——既有报表/影响分析等按名读取的链路无需改写。
- 语义：**1 资产 → 1 业务系统**（与原单字段一致）。M2M（共享资源属多业务）作为后续演进，可用关联表扩展。

## 实现
**数据层**
- 迁移 `0013_business_system_link`：加列 + 索引；按旧名匹配**回填** `business_system_id`；down 删列。
- `Asset.business_system_id` 模型字段。

**服务/接口（后端）**
- `AssetService._resolve_business_system(id|name)`：id 优先校验、回退按名解析，统一返回 (id, name)。
- create/update 资产：经解析同步写 id + 名缓存。
- `assign_business_system(asset_id, bs_id|None)`、`list_business_members(bs_id)`。
- 业务系统**改名**：传播更新成员名缓存（事实源 id 不变）。
- 业务系统**删除**：成员 `business_system_id/business_system` 置空，避免悬挂。
- `GET/POST /business-systems/{id}/members`、`DELETE /business-systems/{id}/members/{asset_id}`。
- 业务系统列表健康聚合改按 `business_system_id`（兼容未回填的旧数据按名匹配）。
- 资产列表支持 `business_system_id` 过滤；`_to_dict`/schema 增 `business_system_id`。

**前端**
- 资产新建/编辑表单：新增"所属业务"下拉（写 `business_system_id`）。
- 资产列表：新增"所属业务"列 + 顶部"业务"过滤。
- 业务系统详情抽屉：成员资产列表 + "添加资产"（多选）/"移除"。

## 关系如何体现（闭环）
建业务系统 → 在资产表单或业务系统详情挂资产 → 列表/详情显示所属业务、可按业务过滤 →
业务系统列表与业务健康地图(M1)按成员实时聚合健康 → 影响分析按业务统计受影响资产。

## 验证
- 后端 `py_compile` + `ruff -F` 通过（仅 1 处既有 F841，非本次）。
- 前端 `vue-tsc` 0 错误、`vite build` 成功、Playwright 冒烟 107/107 正常。
- 迁移含库内 backfill，需在可运行 DB 环境执行 `alembic upgrade head` 后端到端验证回填与聚合。
