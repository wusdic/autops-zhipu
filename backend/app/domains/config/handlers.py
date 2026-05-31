"""配置中心领域事件处理器."""
from __future__ import annotations

import logging

from app.common.events import (
    DomainEvent,
    get_event_bus,
    ConfigEvents,
    AssetEvents,
)

logger = logging.getLogger(__name__)


async def on_config_published_check_drift(event: DomainEvent) -> None:
    """配置发布时检查漂移."""
    payload = event.payload
    try:
        config_id = payload.get("config_id")
        version = payload.get("version")
        if not config_id:
            logger.debug("config: 配置发布事件缺少config_id, 跳过漂移检查")
            return

        from app.infra.database import async_session_factory
        from app.domains.config.service import ConfigService

        async with async_session_factory() as session:
            svc = ConfigService(session)
            # 获取绑定了该配置的所有资产, 检查实际配置与期望配置是否一致
            bindings = await svc.list_bindings(config_id=config_id)
            drifted_assets = []
            for binding in bindings:
                asset_id = getattr(binding, "asset_id", None)
                if asset_id:
                    # 比较期望配置与实际配置
                    actual = await svc.get_actual_config(asset_id, config_id)
                    desired = await svc.get_desired_config(config_id, version)
                    if actual != desired:
                        drifted_assets.append({
                            "asset_id": asset_id,
                            "config_id": config_id,
                            "expected_version": version,
                        })

            if drifted_assets:
                # 发布漂移检测事件
                bus = get_event_bus()
                for drift in drifted_assets:
                    await bus.publish(DomainEvent(
                        event_type=ConfigEvents.CONFIG_DRIFT_DETECTED,
                        domain="config",
                        payload={
                            "config_id": config_id,
                            "version": version,
                            "asset_id": drift["asset_id"],
                        },
                        source="config_drift_checker",
                        correlation_id=event.event_id,
                    ))
                logger.info("config: 检测到 %d 个资产配置漂移", len(drifted_assets))
            else:
                logger.info("config: 配置发布漂移检查通过, 无漂移")

            await session.commit()
        logger.info("config: 配置发布漂移检查完成 config_id=%s version=%s", config_id, version)
    except Exception as e:
        logger.error("config: 配置发布漂移检查失败: %s", e)


async def on_asset_created_bind_default_config(event: DomainEvent) -> None:
    """资产创建时自动绑定默认配置."""
    payload = event.payload
    try:
        asset_id = payload.get("asset_id")
        asset_type = payload.get("asset_type", "")
        if not asset_id:
            logger.debug("config: 资产创建事件缺少asset_id, 跳过默认配置绑定")
            return

        from app.infra.database import async_session_factory
        from app.domains.config.service import ConfigService

        async with async_session_factory() as session:
            svc = ConfigService(session)
            # 查找该资产类型的默认配置
            default_configs = await svc.list_default_configs(asset_type=asset_type)
            for default_cfg in default_configs:
                config_id = str(getattr(default_cfg, "id", ""))
                try:
                    await svc.create_binding(
                        config_id=config_id,
                        asset_id=asset_id,
                        is_auto=True,
                    )
                    logger.info(
                        "config: 自动绑定默认配置 config_id=%s asset_id=%s",
                        config_id, asset_id,
                    )
                except Exception as e:
                    logger.warning(
                        "config: 绑定默认配置失败 config_id=%s asset_id=%s: %s",
                        config_id, asset_id, e,
                    )
            await session.commit()
        logger.info("config: 资产创建默认配置绑定完成 asset_id=%s", asset_id)
    except Exception as e:
        logger.error("config: 资产创建绑定默认配置失败: %s", e)


async def on_credential_created_retry_bindings(event: DomainEvent) -> None:
    """凭证创建/变更时通知相关绑定."""
    payload = event.payload
    try:
        credential_id = payload.get("credential_id")
        if not credential_id:
            return
        logger.info("config: 凭证变更, 检查相关配置绑定 credential_id=%s", credential_id)
        # 后续可扩展: 找到使用该凭证的采集作业, 触发重试
    except Exception as e:
        logger.error("config: 凭证变更处理失败: %s", e)


def register_handlers() -> None:
    """注册配置领域的事件处理器."""
    bus = get_event_bus()
    bus.subscribe(ConfigEvents.CONFIG_VERSION_PUBLISHED, on_config_published_check_drift)
    bus.subscribe(AssetEvents.ASSET_CREATED, on_asset_created_bind_default_config)
    bus.subscribe(ConfigEvents.CREDENTIAL_CREATED, on_credential_created_retry_bindings)
    logger.info("config领域事件处理器已注册 (3个handler)")
