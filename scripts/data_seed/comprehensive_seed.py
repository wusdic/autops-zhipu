"""
AUTOPS 综合种子数据 - 严格基于实际表结构
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta
import aiomysql

DB = {'host': '127.0.0.1', 'port': 3306, 'user': 'autops', 'password': 'autops_2026', 'db': 'autops', 'charset': 'utf8mb4'}
NOW = datetime.now()
def uid(): return str(uuid.uuid4())
def rip(): return f'192.168.{random.randint(1,254)}.{random.randint(1,254)}'
def rpast(m=1440): return NOW - timedelta(minutes=random.randint(1, m))

async def seed():
    async with aiomysql.connect(**DB) as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT id FROM users WHERE username=%s', ('admin',))
            row = await cur.fetchone()
            ADMIN = row[0] if row else uid()
            print(f'Admin ID: {ADMIN}')

            for t in ['notifications','audit_logs','ticket_comments','tickets',
                      'knowledge_articles','execution_steps','executions',
                      'policies','playbooks','scripts',
                      'state_changes','state_snapshots','collection_results','collection_jobs',
                      'credential_bindings','credentials',
                      'asset_timeline','asset_relations','asset_ips','asset_group_members','asset_groups',
                      'alerts','alert_rules','events','api_keys','collectors','assets']:
                await cur.execute(f'DELETE FROM {t}')
            print('cleared old data')

            # 1. ASSETS (25)
            asset_ids = []
            types = ['linux_server','windows_server','network_device','database','web_service','container']
            envs = ['production','staging','development']
            for i in range(25):
                aid = uid(); asset_ids.append(aid)
                await cur.execute(
                    'INSERT INTO assets (id,name,asset_type,ip,port,hostname,os_type,os_version,description,business_system,environment,location,status,health_status,reachability,tags,is_deleted,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (aid, f'asset-{i+1:03d}', types[i%6], rip(), random.randint(22,9090), f'host-{i+1}',
                     random.choice(['linux','windows','linux','linux','linux','windows']),
                     random.choice(['CentOS 7.9','Ubuntu 22.04','Windows 2019','RHEL 8.5']),
                     f'Demo asset {i+1}', f'biz-{i%4+1}', envs[i%3], f'rack-{i%6+1}',
                     random.choice(['online','online','online','offline','maintenance']),
                     random.choice(['healthy','healthy','healthy','warning','critical']),
                     random.choice(['reachable','reachable','unreachable']),
                     '["tag1","tag2"]', 0, rpast(10080), rpast(60)))
            print('assets: 25')

            # 2. ASSET GROUPS (5)
            group_ids = []
            for gn in ['Production','Staging','Development','Database Cluster','Web Servers']:
                gid = uid(); group_ids.append(gid)
                await cur.execute(
                    'INSERT INTO asset_groups (id,name,description,created_at,updated_at) VALUES (%s,%s,%s,%s,%s)',
                    (gid, gn, f'{gn} group', rpast(10080), rpast(60)))
                for j in range(5):
                    idx = len(group_ids)*5-5+j
                    if idx < len(asset_ids):
                        await cur.execute(
                            'INSERT INTO asset_group_members (id,group_id,asset_id) VALUES (%s,%s,%s)',
                            (uid(), gid, asset_ids[idx]))
            print('groups: 5')

            # 3. CREDENTIALS (8)
            cred_ids = []
            for j, (name, ct) in enumerate([('SSH Key','ssh_key'),('WinRM Admin','winrm'),('DB Root','database'),
                         ('API Token','api_token'),('SNMP v2','snmp'),('SSH Password','ssh_password'),
                         ('DB Readonly','database'),('HTTP Basic','http')]):
                cid = uid(); cred_ids.append(cid)
                await cur.execute(
                    'INSERT INTO credentials (id,name,cred_type,encrypted_data,description,test_status,last_tested_at,is_deleted,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (cid, name, ct, f'encrypted_{j}', f'{name} credential', 'success', rpast(60), 0, rpast(10080), rpast(60)))
            print('credentials: 8')

            # 4. EVENTS (60)
            event_ids = []
            etypes = ['threshold_breach','state_change','service_down','port_unreachable','cert_expiring','collection_failed','custom']
            for i in range(60):
                eid = uid(); event_ids.append(eid)
                await cur.execute(
                    'INSERT INTO events (id,event_type,source,source_id,asset_id,title,detail,raw_data,severity,fingerprint,is_deduplicated,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (eid, random.choice(etypes), random.choice(['collector','system','policy','user']),
                     uid()[:8], random.choice(asset_ids), f'Event {i+1}',
                     f'Description for event {i+1}', '{"metric":"value"}',
                     random.choice(['info','warning','error','critical']),
                     uid()[:16], 0, rpast(4320)))
            print('events: 60')

            # 5. ALERT RULES (8)
            rule_ids = []
            for name, cond in [('CPU high','cpu > 90'),('Memory high','mem > 85'),
                               ('Disk high','disk > 85'),('Service down','svc == stopped'),
                               ('Port unreachable','port == false'),('DB conn high','conn > 80'),
                               ('SSL expiring','cert < 30'),('Collector offline','hb > 300')]:
                rid = uid(); rule_ids.append(rid)
                await cur.execute(
                    'INSERT INTO alert_rules (id,name,description,event_types,conditions,severity,suppress_duration,enabled,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (rid, name, f'{name} rule', '["threshold_breach"]', cond,
                     random.choice(['high','medium','critical']), 300, 1, rpast(4320)))
            print('alert_rules: 8')

            # 5b. ALERTS (35)
            alert_ids = []
            for i in range(35):
                aid = uid(); alert_ids.append(aid)
                stat = random.choice(['firing','firing','acknowledged','resolved','suppressed'])
                await cur.execute(
                    'INSERT INTO alerts (id,title,severity,status,rule_id,event_ids,asset_ids,context,acknowledged_by,acknowledged_at,resolved_by,resolved_at,ticket_id,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (aid, f'Alert {i+1}', random.choice(['critical','high','medium','low']),
                     stat, random.choice(rule_ids), '[]', '[]', '{}',
                     ADMIN if stat in ('acknowledged','resolved') else None,
                     rpast(120) if stat in ('acknowledged','resolved') else None,
                     ADMIN if stat == 'resolved' else None,
                     rpast(60) if stat == 'resolved' else None,
                     None, rpast(4320), rpast(60)))
            print('alerts: 35')

            # 6. COLLECTORS (6)
            coll_ids = []
            for name, ct in [('SSH Collector','ssh'),('WMI Collector','wmi'),('HTTP Collector','http'),('DB Collector','database'),('Cert Collector','cert'),('SNMP Collector','snmp')]:
                cid = uid(); coll_ids.append(cid)
                await cur.execute(
                    'INSERT INTO collectors (id,name,collector_type,description,config_schema,is_builtin,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                    (cid, name, ct, f'{name} instance', '{}', 1, rpast(10080)))
            print('collectors: 6')

            # 7. SCRIPTS (12)
            script_ids = []
            for name, st, content, tout, risk in [
                ('Disk check','disk','df -h',30,'low'),
                ('Memory check','memory','free -m',30,'low'),
                ('CPU check','cpu','top -bn1',30,'low'),
                ('Log cleanup','cleanup','find /var/log -mtime +30 -delete',120,'medium'),
                ('Service restart','restart','systemctl restart SVC',60,'high'),
                ('Port check','port','import socket',30,'low'),
                ('SSL check','ssl','import ssl',30,'low'),
                ('DB test','database','import pymysql',30,'medium'),
                ('Win service','wmi','Get-Service',30,'low'),
                ('Disk cleanup','cleanup2','rm -rf /tmp/*',60,'medium'),
                ('Config backup','backup','tar czf backup.tgz /etc',120,'low'),
                ('Process check','check','ps aux',30,'low')]:
                sid = uid(); script_ids.append(sid)
                await cur.execute(
                    'INSERT INTO scripts (id,name,description,script_type,content,parameters,timeout,risk_level,is_blocked,version,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (sid, name, f'{name} script', st, content, '{}', tout, risk, 0, '1.0', rpast(4320), rpast(60)))
            print('scripts: 12')

            # 8. PLAYBOOKS (8)
            pb_ids = []
            for name in ['Disk Full Response','Service Recovery','High CPU Response','DB Failover','SSL Renewal','Collector Restart','Memory Optimization','Port Recovery']:
                pid = uid(); pb_ids.append(pid)
                await cur.execute(
                    'INSERT INTO playbooks (id,name,description,steps,risk_level,version,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                    (pid, name, f'{name} playbook',
                     '[{"step":1,"name":"Step 1"}]',
                     random.choice(['low','medium','high']), '1.0', rpast(4320), rpast(60)))
            print('playbooks: 8')

            # 9. POLICIES (8)
            pol_ids = []
            for name in ['Auto Disk Cleanup','Auto Service Restart','High CPU Alert','DB Auto Failover','SSL Auto Renew','Collector Auto Restart','Memory Alert','Port Alert']:
                pid = uid(); pol_ids.append(pid)
                await cur.execute(
                    'INSERT INTO policies (id,name,description,trigger_type,trigger_condition,scope,action_chain,risk_level,requires_approval,max_affected_assets,verification_steps,rollback_actions,version,status,enabled,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (pid, name, f'{name} policy', 'threshold',
                     '{"metric":"cpu","operator":">","value":90}', 'all',
                     '[{"type":"playbook"}]',
                     random.choice(['low','medium','high']), 0, 10, '[]', '[]',
                     '1.0', 'active', 1, rpast(4320), rpast(60)))
            print('policies: 8')

            # 10. EXECUTIONS (15)
            exec_ids = []
            for i in range(15):
                eid = uid(); exec_ids.append(eid)
                stat = random.choice(['completed','completed','completed','failed','running','pending'])
                await cur.execute(
                    'INSERT INTO executions (id,execution_type,target_id,asset_ids,parameters,status,trigger_source,trigger_source_id,policy_execution_id,is_dry_run,risk_level,approved_by,approved_at,started_at,completed_at,result,error_message,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (eid, 'playbook', random.choice(pb_ids), '[]', '{}',
                     stat, 'policy', random.choice(pol_ids), None, 0,
                     random.choice(['low','medium','high']),
                     ADMIN if stat in ('completed','failed') else None,
                     rpast(200) if stat in ('completed','failed') else None,
                     rpast(180), rpast(60) if stat in ('completed','failed') else None,
                     '{"success":true}' if stat == 'completed' else '{"success":false}',
                     'Script failed' if stat == 'failed' else None,
                     rpast(240), rpast(60)))
            print('executions: 15')

            # 11. TICKETS (10)
            ticket_ids = []
            for i in range(10):
                tid = uid(); ticket_ids.append(tid)
                stat = random.choice(['open','open','in_progress','resolved','closed'])
                await cur.execute(
                    'INSERT INTO tickets (id,title,ticket_type,status,priority,description,context,alert_ids,execution_ids,assigned_to,created_by,resolved_by,resolved_at,closed_by,closed_at,sla_deadline,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (tid, f'Ticket {i+1}', random.choice(['incident','change','task']),
                     stat, random.choice(['low','medium','high','critical']),
                     f'Description for ticket {i+1}', '{}', '[]', '[]',
                     ADMIN, ADMIN,
                     ADMIN if stat in ('resolved','closed') else None,
                     rpast(60) if stat in ('resolved','closed') else None,
                     ADMIN if stat == 'closed' else None,
                     rpast(30) if stat == 'closed' else None,
                     NOW + timedelta(hours=random.randint(4,72)),
                     rpast(4320), rpast(60)))
            print('tickets: 10')

            # 11b. TICKET COMMENTS (20)
            for _ in range(20):
                await cur.execute(
                    'INSERT INTO ticket_comments (id,ticket_id,user_id,content,created_at) VALUES (%s,%s,%s,%s,%s)',
                    (uid(), random.choice(ticket_ids), ADMIN,
                     random.choice(['Checking now','Root cause found','Applying fix','Fixed and verified','Escalating']),
                     rpast(1440)))
            print('ticket_comments: 20')

            # 12. KNOWLEDGE ARTICLES (12)
            kb_ids = []
            for name in ['Linux Disk Full','Windows Service Down','Web Port Down','DB Conn High','DB Conn Failed',
                         'SSL Expiring','Collector Offline','Exec Failed','High Memory','CPU Spike',
                         'Network Latency','Container Restart']:
                kid = uid(); kb_ids.append(kid)
                kstat = random.choice(['published','published','published','draft','review'])
                await cur.execute(
                    'INSERT INTO knowledge_articles (id,title,article_type,asset_types,trigger_events,diagnosis_steps,action_steps,verification_steps,risk_level,content,status,source,source_id,tags,version,published_by,published_at,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (kid, name, random.choice(['troubleshooting','best_practice','runbook']),
                     '["linux_server"]', '["threshold_breach"]',
                     '["Check metrics"]', '["Apply fix"]', '["Verify result"]',
                     random.choice(['low','medium','high']),
                     f'# {name}\n\n## Diagnosis\nCheck metrics.\n\n## Resolution\nApply fix.',
                     kstat, 'manual', None, '["auto"]', '1.0',
                     ADMIN if kstat == 'published' else None,
                     rpast(120) if kstat == 'published' else None,
                     rpast(4320), rpast(60)))
            print('knowledge: 12')

            # 13. NOTIFICATIONS (25)
            for _ in range(25):
                await cur.execute(
                    'INSERT INTO notifications (id,user_id,type,title,message,link,ref_id,read_at,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (uid(), ADMIN, random.choice(['alert','execution','ticket','system']),
                     random.choice(['Alert: CPU high','Alert: Disk full','Exec: done','Ticket: new','System: backup done']),
                     'Check details for this notification', None, None,
                     rpast(10) if random.choice([True, False]) else None, rpast(720)))
            print('notifications: 25')

            # 14. AUDIT LOGS (30)
            for _ in range(30):
                await cur.execute(
                    'INSERT INTO audit_logs (id,trace_id,user_id,username,action,resource_type,resource_id,detail,ip_address,user_agent,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (uid(), uid()[:16], ADMIN, 'admin',
                     random.choice(['create','update','delete','login','execute','export']),
                     random.choice(['asset','alert','ticket','script','policy','execution']),
                     uid()[:16], '{"detail":"action performed"}', rip(), 'Hermes/1.0', rpast(4320)))
            print('audit_logs: 30')

            # 15. COLLECTION JOBS (10)
            for i in range(10):
                await cur.execute(
                    'INSERT INTO collection_jobs (id,name,collector_id,asset_id,credential_id,schedule,status,timeout,last_run_at,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (uid(), f'job-{i+1}', random.choice(coll_ids), random.choice(asset_ids), random.choice(cred_ids),
                     random.choice(['*/5m','*/10m','*/30m','*/1h']),
                     random.choice(['completed','completed','failed','running']),
                     60, rpast(30), rpast(180), rpast(60)))
            print('collection_jobs: 10')

            # 16. STATE SNAPSHOTS (20)
            snap_ids = []
            for _ in range(20):
                sid = uid(); snap_ids.append(sid)
                await cur.execute(
                    'INSERT INTO state_snapshots (id,asset_id,state_type,status,value,collected_at,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                    (sid, random.choice(asset_ids), random.choice(['metric','service','port']),
                     random.choice(['normal','warning','critical']),
                     str({"cpu": random.randint(5,99)}),
                     rpast(360), rpast(360)))
            print('state_snapshots: 20')

            # 17. STATE CHANGES (15)
            for _ in range(15):
                await cur.execute(
                    'INSERT INTO state_changes (id,asset_id,state_type,old_status,new_status,old_value,new_value,snapshot_id,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (uid(), random.choice(asset_ids), random.choice(['metric','service','port']),
                     random.choice(['normal','warning','critical']),
                     random.choice(['normal','warning','critical']),
                     str(random.randint(10,50)), str(random.randint(50,99)),
                     random.choice(snap_ids), rpast(720)))
            print('state_changes: 15')

            # 18. API KEYS (3) — id,name,key_prefix,key_hash,user_id,scope,expires_at,status,last_used_at,created_at
            for i, scope in enumerate(['read_only','read_write','admin']):
                prefix = f'ak{i}_{uid()[:4]}'
                await cur.execute(
                    'INSERT INTO api_keys (id,name,key_prefix,key_hash,user_id,scope,expires_at,status,last_used_at,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (uid(), f'API Key {i+1}', prefix, f'hash_{i}_{uid()[:8]}', ADMIN, scope,
                     NOW + timedelta(days=90), 'active', rpast(60), rpast(4320)))
            print('api_keys: 3')

            await conn.commit()
            print('\n=== SEED COMPLETE ===')

asyncio.run(seed())
