"""标准知识库种子数据 - 8 个标准处置方案."""

import asyncio
import json
import sys
sys.path.insert(0, "/home/zcxx/autops/backend")

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.domains.knowledge.models import KnowledgeArticle
from app.common.repository import BaseRepository


STANDARD_SOLUTIONS = [
    {
        "title": "Linux 磁盘空间异常处置",
        "article_type": "standard_solution",
        "asset_types": '["linux_server"]',
        "trigger_events": '["disk_usage_high"]',
        "diagnosis_steps": '["check_disk_usage", "check_large_files", "check_log_growth"]',
        "action_steps": '["dry_run_cleanup", "compress_logs", "cleanup_temp_files"]',
        "verification_steps": '["check_disk_usage_below_threshold"]',
        "risk_level": "low",
        "content": "## 诊断\n1. 检查磁盘使用率 `df -h`\n2. 查找大文件 `find / -type f -size +100M`\n3. 检查日志增长 `du -sh /var/log/*`\n\n## 处置\n1. 先 dry-run 确认清理范围\n2. 压缩旧日志 `find /var/log -name '*.log' -mtime +7 -exec gzip {} \\;`\n3. 清理临时文件 `find /tmp -mtime +7 -delete`\n\n## 验证\n- `df -h` 确认使用率低于阈值",
        "source": "import",
    },
    {
        "title": "Windows 服务未运行处置",
        "article_type": "standard_solution",
        "asset_types": '["windows_server"]',
        "trigger_events": '["service_stopped"]',
        "diagnosis_steps": '["check_service_status", "check_event_log"]',
        "action_steps": '["restart_service", "check_service_dependencies"]',
        "verification_steps": '["verify_service_running"]',
        "risk_level": "low",
        "content": "## 诊断\n1. 检查服务状态 `Get-Service <name>`\n2. 查看 Windows 事件日志\n\n## 处置\n1. 重启服务 `Restart-Service <name>`\n2. 检查服务依赖是否正常\n\n## 验证\n- 确认服务状态为 Running",
        "source": "import",
    },
    {
        "title": "Web 端口不可达处置",
        "article_type": "standard_solution",
        "asset_types": '["linux_server", "windows_server"]',
        "trigger_events": '["port_unreachable"]',
        "diagnosis_steps": '["check_port_listen", "check_firewall", "check_process"]',
        "action_steps": '["restart_service", "check_config"]',
        "verification_steps": '["curl_health_check"]',
        "risk_level": "medium",
        "content": "## 诊断\n1. 检查端口监听 `ss -tlnp | grep <port>`\n2. 检查防火墙规则 `iptables -L`\n3. 检查进程是否存在\n\n## 处置\n1. 重启 Web 服务\n2. 检查配置文件是否有误\n\n## 验证\n- `curl -I http://localhost:<port>/health`",
        "source": "import",
    },
    {
        "title": "数据库连接数过高处置",
        "article_type": "standard_solution",
        "asset_types": '["database"]',
        "trigger_events": '["db_connections_high"]',
        "diagnosis_steps": '["show_processlist", "check_active_queries", "check_connection_pool"]',
        "action_steps": '["kill_idle_connections", "optimize_queries"]',
        "verification_steps": '["check_connection_count"]',
        "risk_level": "medium",
        "content": "## 诊断\n1. 查看当前连接 `SHOW PROCESSLIST`\n2. 检查活跃查询和锁等待\n3. 检查连接池配置\n\n## 处置\n1. Kill 空闲超过 300 秒的连接\n2. 检查慢查询并优化\n\n## 验证\n- 连接数降至阈值以下",
        "source": "import",
    },
    {
        "title": "数据库连接失败处置",
        "article_type": "standard_solution",
        "asset_types": '["database"]',
        "trigger_events": '["db_connection_failed"]',
        "diagnosis_steps": '["check_db_process", "check_db_port", "check_disk_space", "check_error_log"]',
        "action_steps": '["restart_database", "check_config", "recover_if_crash"]',
        "verification_steps": '["test_connection", "check_data_integrity"]',
        "risk_level": "high",
        "content": "## 诊断\n1. 检查数据库进程是否存活\n2. 检查端口是否监听\n3. 检查磁盘空间是否已满\n4. 查看 error log\n\n## 处置\n1. 如果磁盘满，先清理空间\n2. 重启数据库服务\n3. 检查崩溃恢复日志\n\n## 验证\n- 测试连接成功\n- 检查数据完整性",
        "source": "import",
    },
    {
        "title": "SSL 证书即将过期处置",
        "article_type": "standard_solution",
        "asset_types": '["linux_server", "windows_server"]',
        "trigger_events": '["cert_expiring"]',
        "diagnosis_steps": '["check_cert_expiry", "check_cert_chain", "check_cert_domain"]',
        "action_steps": '["renew_certificate", "deploy_certificate", "restart_services"]',
        "verification_steps": '["verify_cert_validity", "check_ssl_connection"]',
        "risk_level": "medium",
        "content": "## 诊断\n1. 检查证书过期时间 `openssl x509 -enddate`\n2. 检查证书链完整性\n3. 确认证书域名匹配\n\n## 处置\n1. 续期证书（Let's Encrypt 或企业CA）\n2. 部署新证书\n3. 重启相关服务（nginx/apache）\n\n## 验证\n- `openssl s_client -connect host:port` 验证新证书",
        "source": "import",
    },
    {
        "title": "采集器离线处置",
        "article_type": "standard_solution",
        "asset_types": '["collector"]',
        "trigger_events": '["collector_offline"]',
        "diagnosis_steps": '["check_collector_process", "check_network", "check_collector_log"]',
        "action_steps": '["restart_collector", "check_config", "verify_connectivity"]',
        "verification_steps": '["check_collector_health", "verify_data_collection"]',
        "risk_level": "low",
        "content": "## 诊断\n1. 检查采集器进程状态\n2. 检查网络连通性\n3. 查看采集器日志\n\n## 处置\n1. 重启采集器服务\n2. 检查配置是否正确\n3. 验证与目标资产的连接\n\n## 验证\n- 采集器健康检查通过\n- 确认数据正常采集",
        "source": "import",
    },
    {
        "title": "自动化执行失败处置",
        "article_type": "standard_solution",
        "asset_types": '["linux_server", "windows_server"]',
        "trigger_events": '["automation_failed"]',
        "diagnosis_steps": '["check_execution_log", "check_target_reachability", "check_script_syntax"]',
        "action_steps": '["analyze_error", "fix_and_retry", "manual_intervention"]',
        "verification_steps": '["verify_execution_success", "check_system_state"]',
        "risk_level": "medium",
        "content": "## 诊断\n1. 查看执行日志获取错误详情\n2. 检查目标资产可达性\n3. 检查脚本语法和权限\n\n## 处置\n1. 根据错误类型分析根因\n2. 修复后重试（需审批）\n3. 必要时转人工处理\n\n## 验证\n- 执行成功完成\n- 系统状态正常",
        "source": "import",
    },
]


async def seed():
    engine = create_async_engine(
        "mysql+aiomysql://autops:autops_2026@127.0.0.1:3306/autops?charset=utf8mb4"
    )
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        repo = BaseRepository(session, KnowledgeArticle)
        for sol in STANDARD_SOLUTIONS:
            existing = await session.execute(
                __import__("sqlalchemy").select(KnowledgeArticle).where(
                    KnowledgeArticle.title == sol["title"],
                    KnowledgeArticle.source == "import",
                )
            )
            if existing.scalar():
                print(f"  SKIP: {sol['title']}")
                continue
            article = await repo.create(**sol)
            await session.flush()
            await session.refresh(article)
            print(f"  OK: {sol['title']} -> {article.id}")
        await session.commit()
    await engine.dispose()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(seed())
