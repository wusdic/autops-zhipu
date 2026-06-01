# ADR-0004 配置管理策略

## 状态
accepted

## 背景
原 config.py 存在：
1. 硬编码配置目录 `/home/zcxx/autops/configs`
2. 弱密钥默认值（`secret-key-change-in-production`）
3. 生产环境不强制设置密钥

## 决策
1. 配置优先级：环境变量 > YAML 文件 > 代码默认值
2. `AUTOPS_CONFIG_DIR` 环境变量覆盖配置目录
3. 生产环境（`AUTOPS_ENV=prod`）强制设置 JWT_SECRET
4. 敏感字段使用 `db_pass`/`redis_pass`/`jwt_secret` 避免字段名冲突
5. `.env.example` 不含真实密码

## 影响
- 部署必须设置环境变量（至少 JWT_SECRET）
- YAML 配置文件格式需扁平化（无顶层包装 key）
- 本地开发可使用 .env 文件

## 后续动作
- [x] config.py 重写
- [x] .env.example 更新
- [x] YAML 文件修复
