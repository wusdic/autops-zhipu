# ADR-0006 离线部署策略

## 状态
accepted

## 背景
目标客户为私有化环境，通常无公网访问。

## 决策
1. Shell 脚本安装（install.sh）
2. Docker Compose 可选
3. 所有依赖打包为离线包
4. 支持升级回滚

## 备选方案
1. K8s Operator — 过于复杂
2. Helm Chart — 依赖 K8s
3. Ansible — 额外学习成本

## 影响
- 部署脚本自包含
- 升级前自动备份
- 回滚支持到任意版本
