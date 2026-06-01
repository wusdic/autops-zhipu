# ADR-0002 Worker/API 进程分离

## 状态
accepted

## 背景
原设计中 scheduler 在 API 进程内启动，导致：
1. 多副本部署时重复采集
2. 采集任务阻塞 API 响应
3. 无法独立扩展

## 决策
1. API 进程只处理 HTTP 请求和 WebSocket
2. Worker 进程运行 scheduler 和事件消费者
3. 通过 `AUTOPS_ENABLE_SCHEDULER` 环境变量控制
4. 开发模式可单进程运行（设 `AUTOPS_ENABLE_SCHEDULER=true`）

## 影响
- docker-compose 需要独立的 worker service
- 本地开发需要启动两个进程（或使用 `AUTOPS_ENABLE_SCHEDULER=true`）
- Worker 和 API 共享数据库和 Redis

## 后续动作
- [x] worker runner 实现
- [x] docker-compose worker service
- [ ] Kubernetes deployment manifest
