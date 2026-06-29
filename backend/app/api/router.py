"""API 路由注册."""

from __future__ import annotations

from fastapi import APIRouter

from app.domains.asset.api import group_router as asset_group_router, router as asset_router
from app.domains.config.api import cred_router, router as config_router
from app.domains.collector.api import job_router, router as collector_router
from app.domains.collector.edge.api import router as edge_collector_router
from app.domains.state.api import router as state_router
from app.domains.event.api import router as event_router
from app.domains.alert.api import router as alert_router, rule_router as alert_rule_router
from app.domains.policy.api import router as policy_router
from app.domains.automation.api import (
    exec_router,
    playbook_router,
    router as script_router,
)
from app.domains.log.api import router as log_router
from app.domains.ticket.api import router as ticket_router
from app.domains.knowledge.api import router as knowledge_router
from app.domains.aiops.api import router as aiops_router
from app.domains.aiops.agent.api import router as agent_router
from app.domains.governance.api import (
    apikey_router as governance_apikey_router,
    role_router as governance_role_router,
    router as governance_router,
    user_router as governance_user_router,
)
from app.api.anomaly_router import router as anomaly_router
from app.api.audit import router as audit_router
from app.api.backup import router as backup_router
from app.api.health import platform_router
from app.api.report_router import router as report_router
from app.domains.asset.discovery_api import router as discovery_router
from app.domains.notification.api import router as notification_router
from app.integrations.api import router as channel_router
from app.api.websocket import router as ws_router
from app.api.inspection_router import router as inspection_router
from app.api.dashboard import router as dashboard_router
from app.api.business_systems import router as business_systems_router
from app.api.agents import router as agents_router
from app.api.inspection_subtypes import router as inspection_subtypes_router
from app.api.monitoring_extra import router as monitoring_extra_router
from app.api.automation_extra import (
    router as automation_stats_router,
    approvals_router,
    dryrun_router,
)
from app.api.platform_extra import (
    dict_router,
    integration_router,
    taskqueue_router,
    selfcheck_router,
    tenant_router,
)
from app.api.aiops_extra import router as aiops_extra_router
from app.api.exports import router as exports_router
from app.api.search import router as search_router
from app.api.trigger_history import router as trigger_history_router
from app.api.ai_assistant import router as ai_router
from app.api.model_service import (
    agents_router as model_agents_router,
    config_router as model_config_router,
)
from app.domains.alert.threshold_api import router as threshold_rule_router
from app.domains.notification.rule_api import router as notification_rule_router
from app.domains.asset.discovery_template_api import router as discovery_template_router

api_router = APIRouter()

# Governance (auth, users, roles, api-keys)
api_router.include_router(governance_router)
api_router.include_router(governance_user_router)
api_router.include_router(governance_role_router)
api_router.include_router(governance_apikey_router)

# Asset
api_router.include_router(asset_router)
api_router.include_router(asset_group_router)

# Config & Credentials
api_router.include_router(config_router)
api_router.include_router(cred_router)

# Collectors & Jobs
api_router.include_router(collector_router)
api_router.include_router(job_router)
api_router.include_router(edge_collector_router, prefix="/collectors")

# State
api_router.include_router(state_router)

# Events
api_router.include_router(event_router)

# Alerts
api_router.include_router(alert_router)
api_router.include_router(alert_rule_router)

# Policy
api_router.include_router(policy_router)

# Automation
api_router.include_router(script_router)
api_router.include_router(playbook_router)
api_router.include_router(exec_router)

# Logs
api_router.include_router(log_router)

# Tickets
api_router.include_router(ticket_router)

# Knowledge
api_router.include_router(knowledge_router)

# AIops
api_router.include_router(aiops_router)
api_router.include_router(agent_router, prefix="/aiops")
api_router.include_router(aiops_extra_router, prefix="/aiops")
# 模型服务（前端 ModelServicePage）：/aiops/agents、/aiops/model-config
api_router.include_router(model_agents_router, prefix="/aiops")
api_router.include_router(model_config_router, prefix="/aiops")

# AI 助手对话：/ai/chat
api_router.include_router(ai_router)

# Anomalies
api_router.include_router(anomaly_router)

# Audit
api_router.include_router(audit_router)

# Discovery
api_router.include_router(discovery_router)

# Backup
api_router.include_router(backup_router)

# Notifications
api_router.include_router(notification_router)

# Notification Channels
api_router.include_router(channel_router)

# WebSocket
api_router.include_router(ws_router)

# Report
api_router.include_router(report_router)

# Inspection
api_router.include_router(inspection_router)

# Platform
api_router.include_router(platform_router)

# Dashboard
api_router.include_router(dashboard_router)

# Business Systems
api_router.include_router(business_systems_router)

# Agents
api_router.include_router(agents_router)

# Inspection Subtypes (router has no internal prefix, routes are /page-checks etc.)
api_router.include_router(inspection_subtypes_router, prefix="/inspection")

# Monitoring Extra
api_router.include_router(monitoring_extra_router)

# Automation Extra
api_router.include_router(automation_stats_router)
api_router.include_router(approvals_router)
api_router.include_router(dryrun_router)

# Platform Extra
api_router.include_router(dict_router)
api_router.include_router(integration_router)
api_router.include_router(taskqueue_router)
api_router.include_router(selfcheck_router)
api_router.include_router(tenant_router)

# Global Search
api_router.include_router(search_router)

# Threshold Rules
api_router.include_router(threshold_rule_router)

# Notification Rules
api_router.include_router(notification_rule_router)

# Discovery Templates
api_router.include_router(discovery_template_router)

# Exports
api_router.include_router(exports_router)

# Trigger history（巡检规则/处置模板触发历史）
api_router.include_router(trigger_history_router)
