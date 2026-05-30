"""M3 标准场景闭环种子数据 - 告警规则 + 策略 + 脚本."""

import asyncio
import json
import sys
sys.path.insert(0, "/home/zcxx/autops/backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.common.repository import BaseRepository
from app.domains.alert.models import AlertRule
from app.domains.policy.models import Policy
from app.domains.automation.models import Script


ALERT_RULES = [
    {
        "name": "磁盘使用率告警",
        "description": "当磁盘使用率超过 85% 时触发告警",
        "event_types": '["disk_usage_high", "threshold_exceeded"]',
        "conditions": '{"metric": "disk_usage", "operator": ">", "threshold": 85}',
        "severity": "warning",
        "suppress_duration": 3600,
        "enabled": True,
    },
    {
        "name": "服务停止告警",
        "description": "当关键服务停止时触发告警",
        "event_types": '["service_stopped", "service_down"]',
        "conditions": '{"metric": "service_status", "operator": "==", "threshold": "stopped"}',
        "severity": "critical",
        "suppress_duration": 1800,
        "enabled": True,
    },
    {
        "name": "端口不可达告警",
        "description": "当服务端口不可达时触发告警",
        "event_types": '["port_unreachable", "tcp_check_failed"]',
        "conditions": '{"metric": "port_status", "operator": "==", "threshold": "unreachable"}',
        "severity": "critical",
        "suppress_duration": 900,
        "enabled": True,
    },
    {
        "name": "数据库连接数过高告警",
        "description": "当数据库活跃连接数超过最大值的 80% 时触发",
        "event_types": '["db_connections_high"]',
        "conditions": '{"metric": "db_active_connections", "operator": ">", "threshold_percent": 80}',
        "severity": "warning",
        "suppress_duration": 1800,
        "enabled": True,
    },
    {
        "name": "数据库连接失败告警",
        "description": "当数据库连接测试失败时触发",
        "event_types": '["db_connection_failed"]',
        "conditions": '{"metric": "db_connection", "operator": "==", "threshold": "failed"}',
        "severity": "critical",
        "suppress_duration": 0,
        "enabled": True,
    },
    {
        "name": "SSL证书即将过期告警",
        "description": "当 SSL 证书将在 30 天内过期时触发",
        "event_types": '["cert_expiring"]',
        "conditions": '{"metric": "cert_days_remaining", "operator": "<", "threshold": 30}',
        "severity": "warning",
        "suppress_duration": 86400,
        "enabled": True,
    },
    {
        "name": "采集器离线告警",
        "description": "当采集器超过 5 分钟未上报时触发",
        "event_types": '["collector_offline", "collector_timeout"]',
        "conditions": '{"metric": "collector_last_seen", "operator": ">", "threshold_seconds": 300}',
        "severity": "warning",
        "suppress_duration": 3600,
        "enabled": True,
    },
    {
        "name": "自动化执行失败告警",
        "description": "当自动化执行任务失败时触发",
        "event_types": '["automation_failed", "execution_error"]',
        "conditions": '{"metric": "execution_status", "operator": "==", "threshold": "failed"}',
        "severity": "warning",
        "suppress_duration": 0,
        "enabled": True,
    },
]

POLICIES = [
    {
        "name": "linux-disk-cleanup",
        "description": "Linux 磁盘空间异常自动清理",
        "trigger_type": "event_type",
        "trigger_condition": '{"event_type": "disk_usage_high"}',
        "scope": '{"asset_type": "linux_server"}',
        "action_chain": '[{"step": "check_disk", "script_name": "check-disk-usage"}, {"step": "cleanup", "script_name": "cleanup-temp-files"}]',
        "risk_level": "low",
        "requires_approval": False,
        "max_affected_assets": 5,
        "verification_steps": '["check_disk_usage_below_threshold"]',
        "rollback_actions": None,
        "status": "active",
        "enabled": True,
    },
    {
        "name": "windows-service-restart",
        "description": "Windows 服务停止自动重启",
        "trigger_type": "event_type",
        "trigger_condition": '{"event_type": "service_stopped"}',
        "scope": '{"asset_type": "windows_server"}',
        "action_chain": '[{"step": "restart_service", "script_name": "restart-windows-service"}]',
        "risk_level": "medium",
        "requires_approval": True,
        "max_affected_assets": 3,
        "verification_steps": '["verify_service_running"]',
        "rollback_actions": None,
        "status": "active",
        "enabled": True,
    },
    {
        "name": "db-connection-cleanup",
        "description": "数据库连接数过高自动清理",
        "trigger_type": "event_type",
        "trigger_condition": '{"event_type": "db_connections_high"}',
        "scope": '{"asset_type": "database"}',
        "action_chain": '[{"step": "kill_idle", "script_name": "kill-idle-db-connections"}]',
        "risk_level": "medium",
        "requires_approval": True,
        "max_affected_assets": 1,
        "verification_steps": '["check_connection_count"]',
        "rollback_actions": None,
        "status": "active",
        "enabled": True,
    },
    {
        "name": "cert-renew-alert",
        "description": "SSL 证书即将过期通知",
        "trigger_type": "event_type",
        "trigger_condition": '{"event_type": "cert_expiring"}',
        "scope": None,
        "action_chain": '[{"step": "notify", "action_type": "create_ticket", "title": "SSL证书即将过期"}]',
        "risk_level": "low",
        "requires_approval": False,
        "max_affected_assets": 10,
        "verification_steps": None,
        "rollback_actions": None,
        "status": "active",
        "enabled": True,
    },
]

SCRIPTS = [
    {
        "name": "check-disk-usage",
        "description": "检查磁盘使用率",
        "script_type": "shell",
        "content": "#!/bin/bash\nset -e\n df -h --output=pcent,target | tail -n +2 | while read pct mount; do\n  usage=${pct%\\%}\n  if [ \"$usage\" -gt 85 ]; then\n    echo \"WARNING: $mount is ${usage}% full\"\n  fi\ndone",
        "parameters": '{"threshold": {"type": "int", "default": 85, "description": "告警阈值百分比"}}',
        "timeout": 60,
        "risk_level": "low",
    },
    {
        "name": "cleanup-temp-files",
        "description": "清理临时文件",
        "script_type": "shell",
        "content": "#!/bin/bash\n# Dry-run by default\nDRY_RUN=${1:-true}\n\necho \"=== 清理临时文件 (dry_run=$DRY_RUN) ===\"\n\n# Clean /tmp files older than 7 days\nif [ \"$DRY_RUN\" = \"false\" ]; then\n  find /tmp -type f -mtime +7 -delete 2>/dev/null || true\n  find /var/tmp -type f -mtime +7 -delete 2>/dev/null || true\n  echo \"Cleanup completed\"\nelse\n  COUNT=$(find /tmp -type f -mtime +7 2>/dev/null | wc -l)\n  echo \"Would delete $COUNT files from /tmp\"\nfi",
        "parameters": '{"dry_run": {"type": "bool", "default": true}}',
        "timeout": 120,
        "risk_level": "low",
    },
    {
        "name": "restart-windows-service",
        "description": "重启 Windows 服务",
        "script_type": "powershell",
        "content": "param(\n    [string]$ServiceName\n)\nWrite-Host \"Restarting service: $ServiceName\"\nRestart-Service -Name $ServiceName -Force\n$status = (Get-Service -Name $ServiceName).Status\nWrite-Host \"Service status: $status\"",
        "parameters": '{"service_name": {"type": "string", "required": true, "description": "Windows服务名称"}}',
        "timeout": 60,
        "risk_level": "medium",
    },
    {
        "name": "kill-idle-db-connections",
        "description": "清理数据库空闲连接",
        "script_type": "sql",
        "content": "-- Kill idle connections older than 300 seconds\nSELECT CONCAT('KILL ', id, ';') as kill_cmd\nFROM information_schema.processlist\nWHERE Command = 'Sleep'\n  AND Time > 300\n  AND User NOT IN ('root', 'autops');",
        "parameters": '{"idle_timeout": {"type": "int", "default": 300, "description": "空闲超时秒数"}}',
        "timeout": 30,
        "risk_level": "medium",
    },
]


async def seed():
    engine = create_async_engine(
        "mysql+aiomysql://autops:autops_2026@127.0.0.1:3306/autops?charset=utf8mb4"
    )
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        # Alert Rules
        rule_repo = BaseRepository(session, AlertRule)
        for rule in ALERT_RULES:
            existing = await session.execute(
                select(AlertRule).where(AlertRule.name == rule["name"])
            )
            if existing.scalar():
                print(f"  SKIP rule: {rule['name']}")
                continue
            r = await rule_repo.create(**rule)
            await session.flush()
            print(f"  OK rule: {rule['name']} -> {r.id}")

        # Scripts
        script_repo = BaseRepository(session, Script)
        for script in SCRIPTS:
            existing = await session.execute(
                select(Script).where(Script.name == script["name"])
            )
            if existing.scalar():
                print(f"  SKIP script: {script['name']}")
                continue
            s = await script_repo.create(**script)
            await session.flush()
            print(f"  OK script: {script['name']} -> {s.id}")

        # Policies
        policy_repo = BaseRepository(session, Policy)
        for policy in POLICIES:
            existing = await session.execute(
                select(Policy).where(Policy.name == policy["name"])
            )
            if existing.scalar():
                print(f"  SKIP policy: {policy['name']}")
                continue
            p = await policy_repo.create(**policy)
            await session.flush()
            print(f"  OK policy: {policy['name']} -> {p.id}")

        await session.commit()
    await engine.dispose()
    print("\nM3 seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
