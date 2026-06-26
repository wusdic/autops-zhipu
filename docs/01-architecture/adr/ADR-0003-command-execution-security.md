# ADR-0003 命令执行安全边界

## 状态
accepted

## 背景
原 automation/service.py 直接使用 `/bin/bash -c` 执行脚本，存在：
1. 无命令策略校验
2. 无高危命令拦截
3. 无审批流程
4. AI 可绕过安全边界

## 决策
1. 新增 `CommandPolicy` — 白名单 + 黑名单 + 路径策略 + 风险分级
2. 新增 `Executor` Protocol — 执行器抽象，支持 LocalDev/SSH/Sandbox
3. 命令执行必须通过 Executor Adapter
4. 高风险命令需要审批
5. 禁止命令硬编码黑名单，统一由 CommandPolicy 管理

## 影响
- 所有自动化执行路径经过 CommandPolicy
- Executor 可替换（开发用 LocalDev，生产用 SSH）
- AI 推荐动作必须进入策略校验，无法绕过

## 后续动作
- [x] CommandPolicy 实现
- [x] LocalDevExecutor 实现
- [x] SSHExecutor 实现（0.7.0，`executor/ssh.py`；由 `AUTOPS_EXECUTOR=auto|local_dev|ssh` 选择，生产默认 ssh）
- [ ] 单元测试覆盖
