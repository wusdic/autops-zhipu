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

1. 环境检查（OS、磁盘、端口）
2. 安装 Docker（如未安装）
3. 加载镜像
4. 创建配置文件（交互式）
5. 创建数据目录
6. 执行数据库迁移
7. 导入初始数据
8. 启动服务
9. 健康检查
10. 输出访问信息

## 4. 注意事项

- 确保目标服务器磁盘空间充足（至少 20GB）
- 确保 Docker 和 Docker Compose 已安装
- 配置文件中的密码必须修改默认值
