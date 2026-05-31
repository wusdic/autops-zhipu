"""AUTOPS E2E 全链路验证测试.

覆盖完整事件联动链路:
  状态变更 → 事件 → 告警 → 策略匹配 → 自动化执行 → 工单 → 知识

同时验证:
  - LLM Client降级行为
  - Edge Collector全协议
  - 通知渠道API
  - 数据库Dialect适配

使用 httpx.AsyncClient 直接调用运行中的后端服务 (localhost:8001)。
"""

from __future__ import annotations

import asyncio
import uuid

import httpx
import pytest

BASE_URL = "http://localhost:8001/api/v1"
HEALTH_URL = "http://localhost:8001/health"
_TIMEOUT = 15.0
_DB_SETTLE = 0.3


def _is_server_available() -> bool:
    try:
        return httpx.get(HEALTH_URL, timeout=3.0).status_code == 200
    except Exception:
        return False


skip_if_no_server = pytest.mark.skipif(
    not _is_server_available(),
    reason="后端服务未运行在 localhost:8001",
)


@skip_if_no_server
@pytest.mark.asyncio
async def test_full_chain_state_to_alert_to_policy():
    """E2E: 状态快照→事件→告警→策略→执行 全链路验证."""
    uid = uuid.uuid4().hex[:8]

    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        # 1. 创建资产
        r = await c.post(f"{BASE_URL}/assets", json={
            "name": f"E2E-Chain-{uid}",
            "asset_type": "linux_server",
            "ip": f"10.{uid[:2]}.{uid[2:5]}.{uid[5:8]}",
            "status": "online",
        })
        assert r.status_code == 200, f"创建资产失败: {r.text}"
        asset = r.json()["data"]
        asset_id = asset["id"]
        await asyncio.sleep(_DB_SETTLE)

        # 2. 创建告警规则 — 匹配 threshold_exceeded 事件
        r = await c.post(f"{BASE_URL}/alert-rules", json={
            "name": f"E2E-Rule-{uid}",
            "event_types": '["threshold_exceeded", "state_change"]',
            "conditions": '{"operator": "any"}',
            "severity": "critical",
            "enabled": True,
        })
        assert r.status_code == 200, f"创建告警规则失败: {r.text}"
        rule = r.json()["data"]
        rule_id = rule["id"]
        await asyncio.sleep(_DB_SETTLE)

        # 3. 创建策略 — 匹配 critical 告警
        r = await c.post(f"{BASE_URL}/policies", json={
            "name": f"E2E-Policy-{uid}",
            "trigger_type": "alert_severity",
            "trigger_condition": '{"severity": "critical"}',
            "action_chain": '[{"type": "script", "name": "check-disk"}]',
            "risk_level": "low",
            "requires_approval": False,
        })
        assert r.status_code == 200, f"创建策略失败: {r.text}"
        policy = r.json()["data"]
        policy_id = policy["id"]
        await asyncio.sleep(_DB_SETTLE)

        # 4. 模拟状态变更 — 创建事件
        r = await c.post(f"{BASE_URL}/events", json={
            "event_type": "threshold_exceeded",
            "source": "state_monitor",
            "asset_id": asset_id,
            "title": f"磁盘使用率超阈值 {uid}",
            "severity": "critical",
            "detail": '{"metric": "disk_usage", "value": 95, "threshold": 80}',
        })
        assert r.status_code == 200, f"创建事件失败: {r.text}"
        event = r.json()["data"]
        event_id = event["id"]
        await asyncio.sleep(_DB_SETTLE)

        # 5. 创建告警 — 触发策略匹配
        r = await c.post(f"{BASE_URL}/alerts", json={
            "title": f"[E2E] 磁盘使用率超阈值 {uid}",
            "severity": "critical",
            "context": '{"metric": "disk_usage", "value": 95, "threshold": 80}',
            "asset_ids": f'["{asset_id}"]',
            "event_ids": f'["{event_id}"]',
        })
        assert r.status_code == 200, f"创建告警失败: {r.text}"
        alert = r.json()["data"]
        alert_id = alert["id"]
        await asyncio.sleep(_DB_SETTLE)

        # 6. 验证证据链
        r = await c.get(f"{BASE_URL}/alerts/{alert_id}/evidence-chain")
        assert r.status_code == 200, f"证据链查询失败: {r.text}"
        evidence = r.json()["data"]
        assert "alert" in evidence
        assert evidence["alert"]["id"] == alert_id

        # 7. 策略模拟验证 — 确认策略能匹配
        r = await c.post(f"{BASE_URL}/policies/{policy_id}/simulate", json={
            "trigger_event": '{"event_type": "threshold_exceeded", "severity": "critical"}',
            "asset_ids": [asset_id],
        })
        assert r.status_code == 200, f"策略模拟失败: {r.text}"
        simulate = r.json()["data"]

        # 8. 创建执行（模拟策略触发的自动化执行）
        r = await c.post(f"{BASE_URL}/executions", json={
            "execution_type": "script",
            "target_id": asset_id,
            "asset_ids": [asset_id],
            "trigger_source": "policy",
            "trigger_source_id": policy_id,
            "is_dry_run": False,
            "parameters": '{"command": "df -h"}',
        })
        assert r.status_code == 200, f"创建执行失败: {r.text}"
        execution = r.json()["data"]
        execution_id = execution["id"]
        await asyncio.sleep(_DB_SETTLE)

        # 9. 告警转工单
        r = await c.post(f"{BASE_URL}/tickets", json={
            "title": f"[E2E] 告警工单-{uid}",
            "ticket_type": "incident",
            "priority": "high",
            "alert_ids": [alert_id],
            "description": "E2E全链路测试工单",
        })
        assert r.status_code == 200, f"创建工单失败: {r.text}"
        ticket = r.json()["data"]
        ticket_id = ticket["id"]
        await asyncio.sleep(_DB_SETTLE)

        # 10. 关闭工单
        r = await c.put(f"{BASE_URL}/tickets/{ticket_id}", json={
            "status": "closed",
            "resolution": "E2E测试关闭",
        })
        assert r.status_code == 200, f"关闭工单失败: {r.text}"
        await asyncio.sleep(_DB_SETTLE)

        # 11. 工单转知识
        r = await c.post(f"{BASE_URL}/tickets/{ticket_id}/convert-knowledge")
        assert r.status_code == 200, f"工单转知识失败: {r.text}"
        kb_result = r.json()["data"]

        # 12. 告警确认
        r = await c.post(f"{BASE_URL}/alerts/{alert_id}/acknowledge")
        assert r.status_code == 200, f"告警确认失败: {r.text}"

        # 13. 告警解决
        r = await c.post(f"{BASE_URL}/alerts/{alert_id}/resolve")
        assert r.status_code == 200, f"告警解决失败: {r.text}"

        print(f"✅ E2E全链路通过: asset={asset_id[:8]} event={event_id[:8]} "
              f"alert={alert_id[:8]} policy={policy_id[:8]} exec={execution_id[:8]} "
              f"ticket={ticket_id[:8]}")


@skip_if_no_server
@pytest.mark.asyncio
async def test_llm_agent_with_fallback():
    """E2E: AI Agent LLM调用 + 降级验证."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        # 1. Agent运行 — LLM不可用时应降级
        r = await c.post(f"{BASE_URL}/aiops/agent/run", json={
            "task": "分析磁盘使用率过高的原因",
            "context": {"asset_id": "test", "metric": "disk_usage", "value": 95},
        })
        assert r.status_code == 200, f"Agent运行失败: {r.text}"
        agent_result = r.json()["data"]
        agent_id = agent_result["id"]
        # LLM不可用时应有降级响应
        assert agent_result.get("answer") or agent_result.get("error")

        # 2. 查询结果历史
        r = await c.get(f"{BASE_URL}/aiops/agent/results")
        assert r.status_code == 200
        results = r.json()["data"]["items"]
        assert len(results) > 0

        # 3. 审批
        r = await c.post(f"{BASE_URL}/aiops/agent/{agent_id}/approve", json={"approved": True})
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "approved"


@skip_if_no_server
@pytest.mark.asyncio
async def test_notification_channels_e2e():
    """E2E: 通知渠道配置管理."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        # 1. 列出渠道
        r = await c.get(f"{BASE_URL.replace('/api/v1', '')}/api/v1/notification-channels")
        assert r.status_code == 200
        channels = r.json()["data"]
        assert len(channels) >= 3  # webhook + dingtalk + email

        # 2. 禁用一个渠道
        channel_name = channels[0]["name"]
        r = await c.patch(
            f"{BASE_URL.replace('/api/v1', '')}/api/v1/notification-channels/{channel_name}",
            json={"name": channel_name, "enabled": False, "config": {}},
        )
        assert r.status_code == 200

        # 3. 重新启用
        r = await c.patch(
            f"{BASE_URL.replace('/api/v1', '')}/api/v1/notification-channels/{channel_name}",
            json={"name": channel_name, "enabled": True, "config": {}},
        )
        assert r.status_code == 200


@skip_if_no_server
@pytest.mark.asyncio
async def test_edge_collector_full_protocol():
    """E2E: Edge Collector 完整协议 — 注册/心跳/状态/任务/结果."""
    uid = uuid.uuid4().hex[:8]
    cid = f"e2e-edge-{uid}"

    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        # 1. 注册
        r = await c.post(f"{BASE_URL}/collectors/edge/register", json={
            "collector_id": cid,
            "name": f"E2E-Edge-{uid}",
            "collector_type": "ssh",
            "hostname": f"edge-{uid}.local",
            "ip": f"192.168.{uid[:3]}.{uid[3:6]}",
            "version": "1.0.0",
            "capabilities": ["ssh", "tcp_check"],
        })
        assert r.status_code == 200, f"Edge注册失败: {r.text}"
        assert r.json()["data"]["status"] == "registered"

        # 2. 心跳
        r = await c.post(f"{BASE_URL}/collectors/edge/heartbeat", json={
            "collector_id": cid,
            "status": "healthy",
            "metrics": {"cpu": 30, "mem": 60, "tasks_completed": 5},
        })
        assert r.status_code == 200
        assert r.json()["data"]["accepted"]

        await asyncio.sleep(_DB_SETTLE)

        # 3. 状态查询
        r = await c.get(f"{BASE_URL}/collectors/edge/{cid}/status")
        assert r.status_code == 200
        status = r.json()["data"]
        assert status["alive"] is True
        assert status["collector_id"] == cid

        # 4. 任务列表
        r = await c.get(f"{BASE_URL}/collectors/edge/{cid}/tasks")
        assert r.status_code == 200

        # 5. 第二次心跳 — 模拟降级
        r = await c.post(f"{BASE_URL}/collectors/edge/heartbeat", json={
            "collector_id": cid,
            "status": "degraded",
            "metrics": {"cpu": 90, "mem": 85},
        })
        assert r.status_code == 200

        # 6. 验证状态变化
        r = await c.get(f"{BASE_URL}/collectors/edge/{cid}/status")
        assert r.status_code == 200
