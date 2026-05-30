# ADR-0001 关系数据库选择

## 状态
accepted

## 背景
AUTOPS 需要选择关系数据库作为主要数据存储。需要考虑国产化兼容、私有化部署、运维简单性。

## 决策
选择 MySQL 8.0 / MariaDB 作为默认关系数据库。

## 备选方案
1. PostgreSQL — 功能强大但国产化迁移困难
2. SQLite — 不支持并发
3. 达梦/OceanBase — 过于重量级

## 影响
- 通过 SQLAlchemy Repository 层隔离数据库方言
- 避免使用 PostgreSQL 独有特性（如 JSONB）
- 存储过程和触发器不在业务层使用
