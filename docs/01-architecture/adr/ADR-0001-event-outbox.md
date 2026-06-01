# ADR-0001 事件持久化策略

## 状态
accepted

## 背景
原 EventBus 为纯内存实现，进程重启后事件丢失，无法重试或回溯。

## 决策
采用 Transactional Outbox Pattern：
1. 事件写入 `event_outbox` 表（与业务操作同一事务）
2. Worker 进程轮询 outbox 表分发事件
3. 处理成功标记 `done`，失败标记 `dead`
4. 启动时 `replay_pending()` 恢复未完成事件

## 备选方案
1. Redis Streams — 引入额外依赖，事务一致性弱
2. Kafka/RabbitMQ — 重量级，与离线部署冲突
3. 纯DB轮询（无outbox）— 无法保证事务一致性

## 影响
- 所有 `publish()` 调用增加一次 DB 写入（可接受延迟）
- 需要定期清理已完成事件（cron 或 TTL）
- Worker 进程是必须的部署组件

## 后续动作
- [ ] Worker 实现 outbox 轮询分发
- [ ] 添加 outbox 清理 cron
