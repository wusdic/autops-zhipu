# ADR-0005 前端框架选择

## 状态
accepted

## 背景
需要选择前端框架构建运维管理界面。

## 决策
Vue 3 + TypeScript + Element Plus + Vite。

## 备选方案
1. React + Ant Design — 团队不熟悉
2. 纯后端渲染 — 交互能力弱
3. Angular — 过于重量级

## 影响
- 组件库统一使用 Element Plus
- 所有页面必须 TypeScript
- 状态管理使用 Pinia
