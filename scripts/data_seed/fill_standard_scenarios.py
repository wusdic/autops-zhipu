"""标准知识库+脚本+Playbook+策略内容填充种子脚本."""
import asyncio
import json
from app.infra.database import get_db
from sqlalchemy import text


KB_UPDATES = {
    "2cd43952-9485-4223-a41c-5edf56ead88c": {
        "title": "Linux 磁盘空间异常处置",
        "diagnosis_steps": [
            {"step":1,"name":"检查磁盘使用率","command":"df -h","expected":"使用率>85%"},
            {"step":2,"name":"定位大文件","command":"du -sh /* 2>/dev/null | sort -rh | head -20","expected":"识别占用最大的目录"},
            {"step":3,"name":"检查日志增长","command":"find /var/log -name '*.log' -size +100M","expected":"发现异常增长日志"},
            {"step":4,"name":"检查已删除未释放文件","command":"lsof +L1 2>/dev/null | head -20","expected":"发现进程占用文件"}
        ],
        "action_steps": [
            {"step":1,"name":"压缩旧日志","command":"find /var/log -name '*.log' -mtime +7 -exec gzip {} \\;","risk":"low"},
            {"step":2,"name":"清理临时文件","command":"find /tmp -type f -mtime +3 -delete 2>/dev/null","risk":"low"},
            {"step":3,"name":"清理包缓存","command":"apt-get clean || yum clean all","risk":"low"}
        ],
        "verification_steps": [{"step":1,"name":"验证磁盘使用率","command":"df -h","expected":"使用率<80%"}],
        "asset_types": ["linux_server"],
        "trigger_events": ["disk_usage_high","state_change"],
        "risk_level": "low"
    },
    "b52bc266-1e1c-4301-be3f-164c0191b89f": {
        "title": "Windows 服务未运行处置",
        "diagnosis_steps": [
            {"step":1,"name":"检查服务状态","command":"Get-Service -Name {service_name} | Format-Table Status,Name,DisplayName","expected":"Status!=Running"},
            {"step":2,"name":"检查服务依赖","command":"Get-Service -Name {service_name} -DependentServices","expected":"依赖服务状态"},
            {"step":3,"name":"检查系统事件日志","command":"Get-EventLog -LogName System -Source 'Service Control Manager' -Newest 10","expected":"服务停止原因"}
        ],
        "action_steps": [
            {"step":1,"name":"尝试启动服务","command":"Start-Service -Name {service_name}","risk":"medium"},
            {"step":2,"name":"如启动失败检查配置","command":"sc.exe qc {service_name}","risk":"low"}
        ],
        "verification_steps": [{"step":1,"name":"确认服务运行","command":"Get-Service -Name {service_name}","expected":"Status=Running"}],
        "asset_types": ["windows_server"],
        "trigger_events": ["service_down","state_change"],
        "risk_level": "medium"
    },
    "4cea8de1-dce4-4556-a9a9-7832223b79ab": {
        "title": "Web 端口不可达处置",
        "diagnosis_steps": [
            {"step":1,"name":"本地端口检查","command":"ss -tlnp | grep :{port}","expected":"端口未监听"},
            {"step":2,"name":"检查进程","command":"ps aux | grep {process_name}","expected":"进程不存在或异常"},
            {"step":3,"name":"检查防火墙规则","command":"iptables -L -n | grep {port}","expected":"可能被防火墙阻断"}
        ],
        "action_steps": [
            {"step":1,"name":"尝试重启服务","command":"systemctl restart {service_name}","risk":"medium"},
            {"step":2,"name":"检查配置语法","command":"{service_name} -t","risk":"low"}
        ],
        "verification_steps": [{"step":1,"name":"端口可达测试","command":"curl -s -o /dev/null -w '%{http_code}' http://localhost:{port}","expected":"HTTP 200-399"}],
        "asset_types": ["web_server","linux_server"],
        "trigger_events": ["port_unreachable","state_change"],
        "risk_level": "medium"
    },
    "060087d0-bc24-4f84-b29f-ad0e064f80b0": {
        "title": "数据库连接数过高处置",
        "diagnosis_steps": [
            {"step":1,"name":"查看当前连接数","command":"SHOW STATUS LIKE 'Threads_connected'","expected":"连接数接近max_connections"},
            {"step":2,"name":"查看活跃连接","command":"SHOW PROCESSLIST","expected":"发现大量Sleep或长查询"},
            {"step":3,"name":"检查慢查询","command":"SELECT * FROM information_schema.PROCESSLIST WHERE TIME > 10","expected":"发现慢查询"}
        ],
        "action_steps": [
            {"step":1,"name":"终止空闲连接","command":"CALL mysql.rds_kill({connection_id})","risk":"medium"},
            {"step":2,"name":"优化连接池配置","command":"SET GLOBAL wait_timeout=600","risk":"low"}
        ],
        "verification_steps": [{"step":1,"name":"验证连接数","command":"SHOW STATUS LIKE 'Threads_connected'","expected":"连接数<max_connections*80%"}],
        "asset_types": ["database"],
        "trigger_events": ["db_connection_high","state_change"],
        "risk_level": "medium"
    },
    "5877d79f-54a5-4a79-b107-251e45b60dcf": {
        "title": "数据库连接失败处置",
        "diagnosis_steps": [
            {"step":1,"name":"检查数据库进程","command":"systemctl status mysqld || systemctl status mariadb","expected":"进程可能未运行"},
            {"step":2,"name":"检查监听端口","command":"ss -tlnp | grep 3306","expected":"端口未监听"},
            {"step":3,"name":"检查错误日志","command":"tail -100 /var/log/mysql/error.log","expected":"发现连接错误信息"}
        ],
        "action_steps": [
            {"step":1,"name":"尝试重启数据库","command":"systemctl restart mysqld","risk":"high"},
            {"step":2,"name":"检查磁盘空间","command":"df -h /var/lib/mysql","expected":"磁盘未满"}
        ],
        "verification_steps": [{"step":1,"name":"数据库连接测试","command":"mysqladmin ping -h localhost","expected":"mysqld is alive"}],
        "asset_types": ["database"],
        "trigger_events": ["db_connection_failed","state_change"],
        "risk_level": "high"
    },
    "0c1ee948-1991-44dc-adba-f20b6deb6ce9": {
        "title": "SSL 证书即将过期处置",
        "diagnosis_steps": [
            {"step":1,"name":"检查证书过期时间","command":"echo | openssl s_client -connect {host}:{port} 2>/dev/null | openssl x509 -noout -dates","expected":"剩余天数<30"},
            {"step":2,"name":"检查证书链完整性","command":"echo | openssl s_client -connect {host}:{port} 2>/dev/null | openssl x509 -noout -text","expected":"证书链完整"}
        ],
        "action_steps": [
            {"step":1,"name":"续期证书","command":"certbot renew --cert-name {domain}","risk":"medium"},
            {"step":2,"name":"重载Web服务","command":"systemctl reload nginx","risk":"low"}
        ],
        "verification_steps": [{"step":1,"name":"验证新证书","command":"echo | openssl s_client -connect {host}:{port} 2>/dev/null | openssl x509 -noout -dates","expected":"新证书有效期>90天"}],
        "asset_types": ["web_server","linux_server"],
        "trigger_events": ["ssl_expiring","state_change"],
        "risk_level": "medium"
    },
    "e4e8bd6a-4545-4ac8-9960-62b5cda220d5": {
        "title": "采集器离线处置",
        "diagnosis_steps": [
            {"step":1,"name":"检查采集器进程","command":"ps aux | grep collector","expected":"进程不存在"},
            {"step":2,"name":"检查系统资源","command":"top -bn1 | head -5","expected":"CPU/内存是否异常"},
            {"step":3,"name":"检查网络连通","command":"ping -c 3 {autops_server}","expected":"网络是否通畅"}
        ],
        "action_steps": [
            {"step":1,"name":"尝试重启采集器","command":"systemctl restart autops-collector","risk":"low"},
            {"step":2,"name":"检查配置文件","command":"cat /etc/autops/collector.yaml","expected":"配置正确"}
        ],
        "verification_steps": [{"step":1,"name":"验证采集器状态","command":"systemctl status autops-collector","expected":"active (running)"}],
        "asset_types": ["collector"],
        "trigger_events": ["collector_offline","state_change"],
        "risk_level": "low"
    },
    "abd650d8-d5d3-42a3-9e5b-5d58b8267c26": {
        "title": "自动化执行失败处置",
        "diagnosis_steps": [
            {"step":1,"name":"查看执行日志","command":"journalctl -u autops-worker -n 100","expected":"发现错误信息"},
            {"step":2,"name":"检查目标可达性","command":"ssh -o ConnectTimeout=5 {target_host} echo ok","expected":"连接超时或拒绝"},
            {"step":3,"name":"检查凭证有效性","command":"验证凭证是否过期或变更","expected":"凭证可能失效"}
        ],
        "action_steps": [
            {"step":1,"name":"重试执行","command":"重新触发自动化任务","risk":"medium"},
            {"step":2,"name":"创建工单","command":"将失败信息转交人工处理","risk":"none"}
        ],
        "verification_steps": [{"step":1,"name":"验证执行成功","command":"检查目标状态是否恢复正常","expected":"执行成功且验证通过"}],
        "asset_types": ["linux_server","windows_server"],
        "trigger_events": ["execution_failed","automation_error"],
        "risk_level": "medium"
    },
}

SCRIPT_UPDATES = {
    "b444b94a-75ae-4b6a-9cb8-e2cdf93a4a1c": {  # Disk check
        "content": "#!/bin/bash\nDF_OUT=$(df -h | grep -v tmpfs | grep -v udev)\necho \"$DF_OUT\"\necho '---'\nwhile read line; do\n  USAGE=$(echo \"$line\" | awk '{print $5}' | sed 's/%//')\n  MOUNT=$(echo \"$line\" | awk '{print $6}')\n  if [ \"$USAGE\" -gt 85 ] 2>/dev/null; then\n    echo \"WARN: $MOUNT usage ${USAGE}%\"\n  fi\ndone <<< \"$(echo \"$DF_OUT\" | tail -n +2)\""
    },
    "db6531a5-b14d-4591-be6e-f0a004791571": {  # Disk cleanup
        "content": "#!/bin/bash\nfind /var/log -name '*.log' -mtime +7 -exec gzip {} \\; 2>/dev/null\nfind /tmp -type f -mtime +3 -delete 2>/dev/null\nif command -v apt-get &>/dev/null; then apt-get clean; elif command -v yum &>/dev/null; then yum clean all; fi\necho 'Cleanup completed'"
    },
    "b07b233e-4bbb-4396-b529-d2b8a4a17b96": {  # CPU check
        "content": "#!/bin/bash\nCPU_IDLE=$(top -bn1 | grep 'Cpu(s)' | awk '{print $8}' | cut -d. -f1)\nCPU_USED=$((100 - CPU_IDLE))\necho \"CPU Usage: ${CPU_USED}%\"\nif [ \"$CPU_USED\" -gt 90 ]; then\n  echo 'WARN: CPU usage high'\n  ps aux --sort=-%cpu | head -10\nfi"
    },
    "21e4b065-5190-49f9-ba15-3b1050ad5fa1": {  # Memory check
        "content": "#!/bin/bash\nMEM_INFO=$(free -m)\necho \"$MEM_INFO\"\nMEM_USED=$(echo \"$MEM_INFO\" | awk 'NR==2{print $3}')\nMEM_TOTAL=$(echo \"$MEM_INFO\" | awk 'NR==2{print $2}')\nMEM_PCT=$((MEM_USED * 100 / MEM_TOTAL))\nif [ \"$MEM_PCT\" -gt 90 ]; then\n  echo \"WARN: Memory ${MEM_PCT}% used\"\n  ps aux --sort=-%mem | head -10\nfi"
    },
    "4121615b-9d4f-4fa6-880b-c57b5c744caa": {  # Port check
        "content": "#!/bin/bash\nHOST=${1:-localhost}\nPORT=${2:-80}\nif timeout 3 bash -c \"echo >/dev/tcp/$HOST/$PORT\" 2>/dev/null; then\n  echo \"OK: Port $PORT is open on $HOST\"\nelse\n  echo \"FAIL: Port $PORT is NOT reachable on $HOST\"\nfi"
    },
    "f3d8d376-d9f9-4853-a2a0-5face07cfc11": {  # SSL check
        "content": "#!/bin/bash\nHOST=${1:-localhost}\nPORT=${2:-443}\nEXPIRY=$(echo | openssl s_client -connect $HOST:$PORT 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null)\nif [ -z \"$EXPIRY\" ]; then\n  echo \"ERROR: Cannot get certificate from $HOST:$PORT\"\n  exit 1\nfi\necho \"Certificate: $EXPIRY\"\nEXPIRY_EPOCH=$(date -d \"${EXPIRY#*=}\" +%s 2>/dev/null)\nNOW_EPOCH=$(date +%s)\nDAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))\nif [ \"$DAYS_LEFT\" -lt 30 ]; then\n  echo \"WARN: Certificate expires in $DAYS_LEFT days\"\nelse\n  echo \"OK: Certificate valid for $DAYS_LEFT more days\"\nfi"
    },
    "da38fa0b-3348-4250-a750-df4d1bc6b646": {  # Win service
        "content": "$ServiceName = $args[0]\nif (-not $ServiceName) { Write-Host 'Usage: service_check.ps1 <service_name>'; exit 1 }\n$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue\nif (-not $svc) { Write-Host \"ERROR: Service $ServiceName not found\"; exit 1 }\nWrite-Host \"Service: $($svc.Name)\"\nWrite-Host \"Status: $($svc.Status)\"\nif ($svc.Status -ne 'Running') { Write-Host 'WARN: Service not running' }"
    },
    "c19f9b82-f9a6-4444-b153-2c0964007c29": {  # DB test
        "content": "#!/bin/bash\nHOST=${1:-localhost}\nPORT=${2:-3306}\nUSER=${3:-root}\nif command -v mysqladmin &>/dev/null; then\n  mysqladmin -h $HOST -P $PORT -u $USER ping 2>/dev/null\n  if [ $? -eq 0 ]; then\n    echo 'OK: Database is alive'\n  else\n    echo 'FAIL: Database not responding'\n  fi\nelse\n  echo 'WARN: mysqladmin not found'\nfi"
    },
}

PLAYBOOK_UPDATES = {
    "439b0ea6-be67-481f-8a74-08741bb0e64b": json.dumps([  # Disk Full Response
        {"step":1,"name":"磁盘使用率检查","timeout":30},
        {"step":2,"name":"定位大文件目录","timeout":30},
        {"step":3,"name":"执行日志清理","timeout":120},
        {"step":4,"name":"验证清理效果","timeout":30}
    ]),
    "b5f942a3-797e-40c0-8110-55ee8a6c4bb6": json.dumps([  # High CPU
        {"step":1,"name":"CPU使用率检查","timeout":30},
        {"step":2,"name":"识别高CPU进程","timeout":30},
        {"step":3,"name":"评估是否需要重启","timeout":60}
    ]),
    "81ba3be3-6233-42d0-85c9-abf6e222f8a3": json.dumps([  # Service Recovery
        {"step":1,"name":"检查服务状态","timeout":30},
        {"step":2,"name":"尝试重启服务","timeout":60},
        {"step":3,"name":"验证服务恢复","timeout":30}
    ]),
    "f61484b4-a56f-48d2-993c-37ec1e0fb1d8": json.dumps([  # Port Recovery
        {"step":1,"name":"端口检查","timeout":30},
        {"step":2,"name":"重启目标服务","timeout":60},
        {"step":3,"name":"验证端口恢复","timeout":30}
    ]),
    "d3b84d48-a4b4-49f7-86ae-46ca5e88f50e": json.dumps([  # SSL Renewal
        {"step":1,"name":"证书过期检查","timeout":30},
        {"step":2,"name":"续期证书","timeout":120},
        {"step":3,"name":"重载服务","timeout":30},
        {"step":4,"name":"验证新证书","timeout":30}
    ]),
    "f194e58b-6a96-4e10-aceb-10f12eafb5bb": json.dumps([  # Collector Restart
        {"step":1,"name":"检查采集器状态","timeout":30},
        {"step":2,"name":"重启采集器","timeout":60},
        {"step":3,"name":"验证采集器恢复","timeout":30}
    ]),
    "8ac3f25c-5704-4d5c-8a6e-8848161c3a0b": json.dumps([  # DB Failover
        {"step":1,"name":"数据库连接检查","timeout":30},
        {"step":2,"name":"尝试重启数据库","timeout":120},
        {"step":3,"name":"验证数据库恢复","timeout":30}
    ]),
    "b27d46a4-aebd-4d46-8bf0-cd3362df7cf5": json.dumps([  # Memory Optimization
        {"step":1,"name":"内存使用检查","timeout":30},
        {"step":2,"name":"识别高内存进程","timeout":30},
        {"step":3,"name":"清理缓存","timeout":60},
        {"step":4,"name":"验证内存恢复","timeout":30}
    ]),
}

POLICY_CONDITION_UPDATES = {
    "f8482805-7048-44bf-9d6f-ab29ce6fcd9d": {"event_type":"disk_usage_high","severity":["warning","critical"],"asset_types":["linux_server"]},
    "ccb6c289-3f5f-4348-a861-ba1ba8035373": {"event_type":"service_down","severity":["critical"],"asset_types":["windows_server"]},
    "da64c579-55e3-4b5e-ab9f-810efe46771d": {"event_type":"collector_offline","severity":["warning"]},
    "9e0c6429-46af-4bfd-9b3f-786c8fdc8ef2": {"event_type":"db_connection_failed","severity":["critical"]},
    "7382128f-9aec-4ff7-92f7-9bc5534f5f20": {"event_type":"cpu_usage_high","severity":["warning","critical"]},
    "8be16dc9-9bac-4301-ae6a-1fedc0cb5b0a": {"event_type":"memory_usage_high","severity":["warning","critical"]},
    "daf02a7d-df64-446b-a094-919f54dd2a47": {"event_type":"port_unreachable","severity":["critical"]},
    "ae32aba2-9fd4-4008-b85a-4c8bed16f5d9": {"event_type":"ssl_expiring","severity":["warning"]},
}


async def main():
    async for db in get_db():
        # 1. 更新知识库
        kb_count = 0
        for kb_id, fields in KB_UPDATES.items():
            params = {"id": kb_id}
            set_parts = []
            for k, v in fields.items():
                if isinstance(v, (list, dict)):
                    params[k] = json.dumps(v, ensure_ascii=False)
                else:
                    params[k] = v
                set_parts.append(f"{k}=:{k}")
            await db.execute(
                text(f"UPDATE knowledge_articles SET {', '.join(set_parts)} WHERE id=:id"),
                params
            )
            kb_count += 1
        print(f"Updated {kb_count} knowledge articles")

        # 2. 更新脚本
        sc_count = 0
        for sc_id, fields in SCRIPT_UPDATES.items():
            params = {"id": sc_id}
            set_parts = []
            for k, v in fields.items():
                params[k] = v
                set_parts.append(f"{k}=:{k}")
            await db.execute(
                text(f"UPDATE scripts SET {', '.join(set_parts)} WHERE id=:id"),
                params
            )
            sc_count += 1
        print(f"Updated {sc_count} scripts")

        # 3. 更新Playbook步骤
        pb_count = 0
        for pb_id, steps_json in PLAYBOOK_UPDATES.items():
            await db.execute(
                text("UPDATE playbooks SET steps=:steps WHERE id=:id"),
                {"id": pb_id, "steps": steps_json}
            )
            pb_count += 1
        print(f"Updated {pb_count} playbooks")

        # 4. 更新策略trigger_condition
        po_count = 0
        for po_id, condition in POLICY_CONDITION_UPDATES.items():
            await db.execute(
                text("UPDATE policies SET trigger_condition=:tc WHERE id=:id"),
                {"id": po_id, "tc": json.dumps(condition, ensure_ascii=False)}
            )
            po_count += 1
        print(f"Updated {po_count} policies")

        await db.commit()
        print("All updates committed!")
        break


if __name__ == "__main__":
    asyncio.run(main())
