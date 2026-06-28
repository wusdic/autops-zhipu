# AUTOPS 离线部署

> 文档状态：current
> 建议路径：`docs/06-operations/OFFLINE_DEPLOYMENT.md`

---

## 1. 离线包制作

```bash
# 在有网络的环境中构建
cd autops
./deploy/scripts/build_offline.sh
# 输出: autops-offline-{version}.tar.gz
```

## 2. 离线安装

```bash
# 传输离线包到目标服务器
scp autops-offline-*.tar.gz target:/opt/

# 解压
cd /opt
tar xzf autops-offline-*.tar.gz

# 安装
./install.sh
```

## 3. install.sh 执行流程

1. 环境检查（OS、磁盘、端口、root 权限）
2. 安装 Docker（如未安装）
3. 加载镜像
4. 创建配置文件（交互式）
5. 创建数据目录
6. 执行数据库迁移（`alembic upgrade head`，含 0004 auto_onboard 等迁移）
7. 导入初始数据（创建内置角色 + admin 用户）
   - 初始 admin 口令：若设置了 `ADMIN_INITIAL_PASSWORD` 环境变量则用该值；
     否则随机生成 16 位口令并打印到安装日志（仅显示一次）
8. 启动服务（生成并启动 `autops-backend` systemd 单元）
   - 注意：当前 install.sh **仅部署后端**，worker 进程（采集调度器）需另行配置
9. 健康检查
10. 输出访问信息（前端地址、后端地址 8001、初始口令获取方式）

## 4. 注意事项

- 确保目标服务器磁盘空间充足（至少 20GB）
- 确保 Docker 和 Docker Compose 已安装
- 配置文件中的密码必须修改默认值（`MYSQL_ROOT_PASSWORD`、`DB_PASS`、`JWT_SECRET`、`CREDENTIAL_ENCRYPT_KEY`）
- `JWT_SECRET` 生产环境必须 ≥32 字符，否则启动报错
- 初始 admin 口令从安装日志获取后请立即登录修改；如需指定可在安装前设置 `ADMIN_INITIAL_PASSWORD`
- 应用（nginx :80 / 后端 :8001）绑定 `0.0.0.0`，局域网内用 `http://<服务器IP>` 即可访问；
  MySQL/Redis 仍仅绑定 `127.0.0.1`/内网，勿对公网暴露
- 局域网访问不通时放通防火墙：`sudo ufw disable`（内网/实验环境）或 `sudo ufw allow 80,443,8001/tcp`（生产推荐）

