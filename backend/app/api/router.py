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
from app.domains.governance.api import (
    apikey_router as governance_apikey_router,
    role_router as governance_role_router,
    router as governance_router,
    user_router as governance_user_router,
)
from app.api.audit import router as audit_router
from app.api.backup import router as backup_router
from app.api.health import platform_router
from app.domains.asset.discovery_api import router as discovery_router
from app.domains.notification.api import router as notification_router
from app.api.websocket import router as ws_router

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

# Audit
api_router.include_router(audit_router)

# Discovery
api_router.include_router(discovery_router)

# Backup
api_router.include_router(backup_router)

# Notifications
api_router.include_router(notification_router)

# WebSocket
api_router.include_router(ws_router)

# Platform
api_router.include_router(platform_router)
