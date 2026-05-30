# AUTOPS 部署架构设计

> 文档状态：current
> 是否为事实源：yes
> 建议路径：`docs/01-architecture/DEPLOYMENT_ARCHITECTURE.md`

---

## 1. 部署模式

| 模式 | 适用场景 | 说明 |
|---|---|---|
| 单机部署 | 开发、测试、小规模生产 | 所有组件在一台机器 |
| Docker Compose | 测试、中小规模生产 | 容器化部署 |
| 多节点部署 | 大规模生产 | 组件分离部署 |
| 物理机部署 | 信创环境、安全要求高 | 直接安装 |
| 离线部署 | 无网络环境 | 离线包安装 |
| 边缘采集器 | 多网段、多机房 | Agent + Edge Collector |

---

## 2. 组件清单

| 组件 | 说明 | 必需 | 版本要求 |
|---|---|---|---|
| Python 3.10+ | 后端运行环境 | 是 | 3.10+ |
| MySQL/MariaDB | 关系数据库 | 是 | MySQL 8.0+ / MariaDB 10.6+ |
| Redis | 缓存/锁/队列 | 是 | 7.0+ |
| Node.js 18+ | 前端构建 | 是 | 18+ |
| VictoriaMetrics | 指标存储 | 否（推荐） | v1.90+ |
| MinIO | 对象存储 | 否（推荐） | 最新 |
| Qdrant/Chroma | 向量存储 | 否（AIops 需要） | 最新 |
| vLLM/Ollama | 大模型服务 | 否（AIops 需要） | 最新 |
| Nginx | 反向代理 | 是 | 1.24+ |

---

## 3. Docker Compose 部署

### 3.1 服务编排

```yaml
# deploy/docker/docker-compose.yml
services:
  autops-backend:
    image: autops-backend:latest
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis
    env_file: ../../.env
    volumes:
      - ../../configs:/app/configs:ro
      - autops-logs:/app/logs
      - autops-data:/app/data

  autops-frontend:
    image: autops-frontend:latest
    ports:
      - "80:80"
    depends_on:
      - autops-backend

  autops-worker:
    image: autops-backend:latest
    command: python -m app.workers.worker
    depends_on:
      - mysql
      - redis
    env_file: ../../.env
    volumes:
      - ../../configs:/app/configs:ro

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: autops
      MYSQL_USER: autops
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mysql-data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"

  # 可选组件
  victoria-metrics:
    image: victoriametrics/victoria-metrics:latest
    ports:
      - "8428:8428"
    volumes:
      - vm-data:/victoria-metrics-data

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${OBJECT_STORAGE_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${OBJECT_STORAGE_SECRET_KEY}
    volumes:
      - minio-data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant-data:/qdrant/storage
    ports:
      - "6333:6333"

volumes:
  mysql-data:
  redis-data:
  vm-data:
  minio-data:
  qdrant-data:
  autops-logs:
  autops-data:
```

---

## 4. 离线部署

### 4.1 离线包结构

```text
autops-offline-{version}.tar.gz
├── install.sh                  # 一键安装
├── upgrade.sh                  # 升级脚本
├── rollback.sh                 # 回滚脚本
├── self_check.sh               # 自检脚本
├── docker/
│   ├── images/
│   │   ├── autops-backend.tar
│   │   ├── autops-frontend.tar
│   │   ├── mysql-8.0.tar
│   │   ├── redis-7.tar
│   │   └── ...
│   └── docker-compose.yml
├── backend/
│   └── dist/
│       └── autops-{version}-py3-none-any.whl
├── frontend/
│   └── dist/
│       └── (构建产物)
├── configs/
│   └── *.yaml (配置模板)
├── migrations/
│   └── (Alembic 迁移脚本)
├── scripts/
│   ├── data_seed/              # 初始数据
│   └── maintenance/            # 维护脚本
└── docs/
    └── (文档)
```

### 4.2 install.sh 流程

```text
1. 环境检查（OS、Docker、磁盘空间、端口）
2. 加载 Docker 镜像
3. 创建配置文件（从模板复制，交互式填写）
4. 创建数据目录
5. 执行数据库迁移
6. 导入初始数据
7. 启动服务
8. 健康检查
9. 输出访问信息
```

### 4.3 upgrade.sh 流程

```text
1. 版本检查（当前版本 → 目标版本）
2. 升级前备份（数据库、配置、数据目录）
3. 停止服务
4. 加载新镜像
5. 执行数据库迁移
6. 配置差异合并（保留自定义配置）
7. 启动服务
8. 升级后自检
9. 输出升级结果
```

### 4.4 rollback.sh 流程

```text
1. 确认回滚版本
2. 停止当前服务
3. 恢复数据库备份
4. 恢复配置备份
5. 加载旧版本镜像
6. 启动服务
7. 健康检查
8. 输出回滚结果
```

---

## 5. 单机物理机部署

### 5.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|---|---|---|
| CPU | 4 核 | 8 核+ |
| 内存 | 8 GB | 16 GB+ |
| 磁盘 | 100 GB | 500 GB+ SSD |
| OS | CentOS 7+ / Ubuntu 20.04+ | Ubuntu 22.04 |

### 5.2 依赖安装

```bash
# Python 3.10+
# MySQL 8.0+ / MariaDB 10.6+
# Redis 7.0+
# Node.js 18+（仅构建前端时需要）
# Nginx
```

### 5.3 部署步骤

```text
1. 安装系统依赖
2. 创建 autops 用户
3. 安装 Python 虚拟环境
4. 安装后端依赖 (pip install)
5. 安装数据库（MySQL/MariaDB）
6. 创建数据库和用户
7. 执行 migration
8. 安装 Redis
9. 配置 Nginx 反向代理
10. 配置 systemd 服务
11. 导入初始数据
12. 启动服务
13. 健康检查
```

---

## 6. 数据备份与恢复

### 6.1 备份内容

| 数据 | 方式 | 频率 |
|---|---|---|
| MySQL 数据库 | mysqldump / mariabackup | 每日 |
| Redis 数据 | RDB / AOF | 每日 |
| 配置文件 | 文件复制 | 每次变更 |
| 执行日志文件 | 文件复制 | 每日 |
| 向量数据 | qdrant snapshot | 每周 |
| 对象存储 | minio mc mirror | 每日 |

### 6.2 备份脚本

```bash
#!/bin/bash
# scripts/maintenance/backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/data/backups/$DATE"

# 数据库备份
mysqldump -u autops -p autops > "$BACKUP_DIR/autops_db.sql"

# Redis 备份
redis-cli --rdb "$BACKUP_DIR/redis.rdb" BGSAVE

# 配置备份
cp -r configs/ "$BACKUP_DIR/configs/"

# 压缩
tar czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"

# 清理 30 天前的备份
find /data/backups -mtime +30 -delete
```

---

## 7. 端口规划

| 服务 | 端口 | 说明 |
|---|---|---|
| Nginx | 80 / 443 | 前端 + 反向代理 |
| FastAPI | 8000 | 后端 API（内部） |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |
| VictoriaMetrics | 8428 | 指标存储 |
| MinIO API | 9000 | 对象存储 |
| MinIO Console | 9001 | 对象存储管理 |
| Qdrant | 6333 | 向量存储 |
| vLLM | 8000 (宿主机 8001) | 大模型服务 |

---

## 8. 资源估算

### 8.1 小规模（< 500 资产）

| 组件 | CPU | 内存 | 磁盘 |
|---|---|---|---|
| 后端 | 2 核 | 4 GB | 20 GB |
| 前端 | 0.5 核 | 1 GB | 2 GB |
| MySQL | 2 核 | 4 GB | 100 GB |
| Redis | 1 核 | 2 GB | 10 GB |
| Worker | 2 核 | 4 GB | 10 GB |
| **合计** | **7.5 核** | **15 GB** | **142 GB** |

### 8.2 中规模（500-5000 资产）

| 组件 | CPU | 内存 | 磁盘 |
|---|---|---|---|
| 后端 (x2) | 4 核 | 8 GB | 50 GB |
| MySQL | 4 核 | 16 GB | 500 GB |
| Redis | 2 核 | 8 GB | 20 GB |
| Worker (x2) | 4 核 | 8 GB | 50 GB |
| VictoriaMetrics | 2 核 | 8 GB | 200 GB |
| **合计** | **24 核** | **64 GB** | **1.1 TB** |

---

## 9. 国产化兼容

### 9.1 操作系统兼容

- CentOS 7+
- Ubuntu 20.04+
- 麒麟 V10
- 统信 UOS
- openEuler

### 9.2 数据库兼容

- MySQL 8.0+
- MariaDB 10.6+
- PostgreSQL 14+（后续适配）
- openGauss（后续适配）
- 达梦 DM8（后续适配）
- 人大金仓 KingbaseES（后续适配）

### 9.3 架构兼容

- x86_64
- ARM64 / AArch64
- LoongArch（后续验证）

---

## 10. 自检脚本

### self_check.sh 检查项

```text
1. 系统资源检查（CPU、内存、磁盘）
2. 端口可用性检查
3. 数据库连接检查
4. Redis 连接检查
5. 后端健康检查 (/health, /ready)
6. 前端可达性检查
7. Migration 状态检查
8. 配置文件完整性检查
9. 服务进程状态检查
10. 日志错误检查（最近 1 小时 ERROR 数）
11. 证书有效期检查
12. 安全基线检查
```
