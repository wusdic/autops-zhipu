"""资产发现 Service - 真实网络扫描引擎."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import socket
import struct
import subprocess
import time
from datetime import datetime, timezone

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.events import DomainEvent, get_event_bus, AssetEvents
from app.domains.asset.models import Asset
from app.domains.asset.discovery_models import DiscoveryTask, DiscoveryResult

logger = logging.getLogger(__name__)

# 后台扫描任务句柄集合，防止未被强引用的 task 被 GC 回收（导致扫描无故消失）
_background_scan_tasks: set[asyncio.Task] = set()


def _expand_ips(ip_range: str) -> list[str]:
    """展开IP范围为IP列表."""
    ips = []
    ip_range = ip_range.strip()
    if "/" in ip_range:
        # CIDR: 10.168.1.0/24
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
            for ip in network.hosts():
                ips.append(str(ip))
        except ValueError:
            pass
    elif "-" in ip_range:
        # Range: 10.168.1.1-10.168.1.50
        parts = ip_range.split("-")
        if len(parts) == 2:
            try:
                start = ipaddress.ip_address(parts[0].strip())
                end = ipaddress.ip_address(parts[1].strip())
                current = start
                while current <= end:
                    ips.append(str(current))
                    current = ipaddress.ip_address(int(current) + 1)
            except ValueError:
                pass
    else:
        # Single IP
        try:
            ipaddress.ip_address(ip_range)
            ips.append(ip_range)
        except ValueError:
            pass
    return ips[:1024]  # 安全上限


async def _icmp_ping(ip: str, timeout: float = 2.0) -> bool:
    """ICMP Ping检测."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping",
            "-c",
            "1",
            "-W",
            str(int(timeout)),
            ip,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=timeout + 1)
        return proc.returncode == 0
    except Exception:
        return False


async def _tcp_scan(ip: str, ports: list[int], timeout: float = 2.0) -> list[int]:
    """TCP端口扫描."""
    open_ports = []

    async def _check_port(port: int):
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            open_ports.append(port)
        except Exception:
            pass

    if not ports:
        return []
    # 限制并发
    sem = asyncio.Semaphore(50)

    async def _limited(p):
        async with sem:
            await _check_port(p)

    await asyncio.gather(*[_limited(p) for p in ports])
    return sorted(open_ports)


def _parse_ports(ports_str: str | None) -> list[int]:
    """解析端口字符串: '22,80,443' or '1-1024'."""
    if not ports_str:
        return [22, 80, 443, 3389, 3306, 5432, 6379, 8080, 8443, 9200]
    ports = set()
    for part in ports_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                for p in range(int(a), int(b) + 1):
                    if 1 <= p <= 65535:
                        ports.add(p)
            except ValueError:
                pass
        else:
            try:
                p = int(part)
                if 1 <= p <= 65535:
                    ports.add(p)
            except ValueError:
                pass
    return sorted(ports)


def _guess_asset_type(open_ports: list[int]) -> str:
    """根据开放端口推断资产类型."""
    if 3389 in open_ports:
        return "windows_server"
    if 3306 in open_ports or 5432 in open_ports:
        return "database"
    if 9200 in open_ports:
        return "search_engine"
    if 6379 in open_ports:
        return "cache_server"
    if 80 in open_ports or 443 in open_ports or 8080 in open_ports:
        return "web_server"
    if 22 in open_ports:
        return "linux_server"
    return "unknown"


class DiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, data: dict) -> dict:
        """创建发现任务（DB持久化）."""
        ip_range = data.get("ip_range") or data.get("cidr") or ""
        if not ip_range:
            ip_range = "127.0.0.1"
        task = DiscoveryTask(
            name=data.get(
                "name", "discovery-" + datetime.now().strftime("%Y%m%d%H%M%S")
            ),
            ip_range=ip_range,
            ip_mode=data.get("ip_mode", "cidr"),
            protocols=data.get("protocols", ["icmp"]),
            ports=data.get("ports"),
            credential_id=data.get("credential_id"),
            timeout=data.get("timeout", 30),
            status="pending",
            discovered_count=0,
            onboarded_count=0,
            created_by=data.get("created_by"),
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return model_to_dict(task)

    async def start_task(self, task_id: str) -> dict:
        """启动发现任务 - 真实扫描."""
        result = await self.db.execute(
            select(DiscoveryTask).where(DiscoveryTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return {"error": "任务不存在"}
        if task.status not in ("pending", "failed"):
            return {"error": f"任务状态为 {task.status}，不能启动"}

        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        task.error_message = None
        await self.db.flush()
        # 显式 commit，确保 running 状态落库（_run_scan 用独立 session 查询）
        await self.db.commit()

        # 异步执行扫描，保存 task 句柄防 GC
        scan_task = asyncio.create_task(self._run_scan(task_id))
        _background_scan_tasks.add(scan_task)
        scan_task.add_done_callback(_background_scan_tasks.discard)
        return {"task_id": task_id, "status": "running"}

    async def _run_scan(self, task_id: str) -> None:
        """执行实际扫描（后台任务）."""
        from app.infra.database import async_session_factory

        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    select(DiscoveryTask).where(DiscoveryTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                if not task:
                    return

                ips = _expand_ips(task.ip_range)
                if not ips:
                    task.status = "failed"
                    task.error_message = f"无法解析IP范围: {task.ip_range}"
                    task.completed_at = datetime.now(timezone.utc)
                    await session.flush()
                    await session.commit()
                    return

                logger.info(
                    "Discovery scan started: task=%s, ips=%d", task_id, len(ips)
                )

                protocols = task.protocols or ["icmp"]
                ports = _parse_ports(task.ports)
                timeout = min(task.timeout or 30, 120)
                discovered = 0

                # 并发扫描 (最多100个并发)
                sem = asyncio.Semaphore(100)

                async def _scan_host(ip: str):
                    nonlocal discovered
                    async with sem:
                        alive = False
                        open_ports_list = []

                        # ICMP检测
                        if "icmp" in protocols or "ping" in protocols:
                            alive = await _icmp_ping(ip, timeout=2.0)

                        # TCP端口扫描
                        if "tcp" in protocols or ports:
                            tcp_ports = await _tcp_scan(
                                ip, ports, timeout=timeout / max(len(ports), 1)
                            )
                            if tcp_ports:
                                alive = True
                                open_ports_list = tcp_ports

                        if not alive:
                            return

                        # 推断资产类型
                        asset_type = _guess_asset_type(open_ports_list)

                        # 保存发现结果
                        dr = DiscoveryResult(
                            task_id=task_id,
                            ip=ip,
                            hostname=None,
                            asset_type=asset_type,
                            open_ports=open_ports_list,
                            status="discovered",
                            metadata_={
                                "protocols": protocols,
                                "scan_time": datetime.now(timezone.utc).isoformat(),
                            },
                        )
                        session.add(dr)
                        discovered += 1

                # 分批扫描，避免太大并发
                batch_size = 50
                for i in range(0, len(ips), batch_size):
                    batch = ips[i : i + batch_size]
                    await asyncio.gather(*[_scan_host(ip) for ip in batch])

                # 更新任务
                task.status = "completed"
                task.discovered_count = discovered
                task.completed_at = datetime.now(timezone.utc)
                await session.flush()
                await session.commit()

                # 发事件
                bus = get_event_bus()
                await bus.publish(
                    DomainEvent(
                        domain="asset",
                        event_type="discovery.completed",
                        payload={"task_id": task_id, "discovered_count": discovered},
                    )
                )
                logger.info(
                    "Discovery scan completed: task=%s, found=%d", task_id, discovered
                )

            except Exception as e:
                logger.error("Discovery scan failed: task=%s, error=%s", task_id, e)
                # 用独立 session 写错误状态；若该 session 也已损坏（如原异常是连接断开），
                # 至少记录日志，避免任务静默卡在 running 状态。
                try:
                    result = await session.execute(
                        select(DiscoveryTask).where(DiscoveryTask.id == task_id)
                    )
                    task = result.scalar_one_or_none()
                    if task:
                        task.status = "failed"
                        task.error_message = str(e)[:2000]
                        task.completed_at = datetime.now(timezone.utc)
                        await session.flush()
                        await session.commit()
                except Exception:
                    logger.exception(
                        "写入扫描失败状态时再次异常，任务 %s 可能卡在 running", task_id
                    )

    async def list_tasks(self, page: int, page_size: int) -> tuple[list, int]:
        """列出发现任务."""
        total_result = await self.db.execute(
            select(func.count()).select_from(DiscoveryTask)
        )
        total = total_result.scalar() or 0
        result = await self.db.execute(
            select(DiscoveryTask)
            .order_by(DiscoveryTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [model_to_dict(t) for t in result.scalars().all()]
        return items, total

    async def get_task(self, task_id: str) -> dict | None:
        """获取任务详情."""
        result = await self.db.execute(
            select(DiscoveryTask).where(DiscoveryTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        return model_to_dict(task) if task else None

    async def get_results(
        self, task_id: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        """获取发现结果."""
        stmt = select(DiscoveryResult)
        count_stmt = select(func.count()).select_from(DiscoveryResult)
        if task_id:
            stmt = stmt.where(DiscoveryResult.task_id == task_id)
            count_stmt = count_stmt.where(DiscoveryResult.task_id == task_id)

        total = (await self.db.execute(count_stmt)).scalar() or 0
        result = await self.db.execute(
            stmt.order_by(DiscoveryResult.discovered_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = []
        for r in result.scalars().all():
            items.append(
                {
                    "id": r.id,
                    "task_id": r.task_id,
                    "ip": r.ip,
                    "hostname": r.hostname,
                    "asset_type": r.asset_type,
                    "open_ports": r.open_ports,
                    "status": r.status,
                    "metadata": r.metadata_,
                    "discovered_at": r.discovered_at.isoformat()
                    if r.discovered_at
                    else None,
                    "onboarded_at": r.onboarded_at.isoformat()
                    if r.onboarded_at
                    else None,
                    "asset_id": r.asset_id,
                }
            )
        return items, total

    async def onboard_results(
        self, result_ids: list[str], asset_type: str = "auto"
    ) -> dict:
        """纳管发现的资产."""
        onboarded = 0
        errors = 0
        for rid in result_ids:
            result = await self.db.execute(
                select(DiscoveryResult).where(DiscoveryResult.id == rid)
            )
            dr = result.scalar_one_or_none()
            if not dr or dr.status != "discovered":
                errors += 1
                continue

            # 检查IP是否已有资产
            existing = await self.db.execute(
                select(Asset).where(Asset.ip == dr.ip, Asset.is_deleted == False)
            )
            if existing.scalar_one_or_none():
                dr.status = "ignored"
                dr.onboarded_at = datetime.now(timezone.utc)
                continue

            at = asset_type if asset_type != "auto" else dr.asset_type
            asset = Asset(
                name=dr.hostname or dr.ip,
                hostname=dr.hostname or dr.ip,
                ip=dr.ip,
                asset_type=at,
                status="online",
            )
            self.db.add(asset)
            await self.db.flush()
            await self.db.refresh(asset)

            dr.status = "onboarded"
            dr.asset_id = str(asset.id)
            dr.onboarded_at = datetime.now(timezone.utc)
            onboarded += 1

            # 发资产创建事件 → 触发采集
            bus = get_event_bus()
            await bus.publish(
                DomainEvent(
                    domain="asset",
                    event_type=AssetEvents.ASSET_CREATED,
                    payload={
                        "asset_id": str(asset.id),
                        "asset_name": asset.hostname,
                        "asset_type": asset.asset_type,
                        "ip": asset.ip,
                    },
                )
            )

        # 更新task的onboarded_count
        if result_ids:
            first_dr = await self.db.execute(
                select(DiscoveryResult).where(DiscoveryResult.id == result_ids[0])
            )
            dr0 = first_dr.scalar_one_or_none()
            if dr0:
                await self.db.execute(
                    update(DiscoveryTask)
                    .where(DiscoveryTask.id == dr0.task_id)
                    .values(onboarded_count=DiscoveryTask.onboarded_count + onboarded)
                )

        await self.db.flush()
        return {"onboarded": onboarded, "errors": errors, "total": len(result_ids)}

    async def import_asset(self, data: dict) -> Asset:
        """导入单个资产."""
        existing = await self.db.execute(
            select(Asset).where(
                Asset.ip == data.get("ip", ""), Asset.is_deleted == False
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"IP {data.get('ip')} 已存在资产")

        asset = Asset(
            hostname=data.get("hostname", data.get("ip", "unknown")),
            ip=data.get("ip", "0.0.0.0"),
            asset_type=data.get("asset_type", "linux_server"),
            status="offline",
        )
        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)

        bus = get_event_bus()
        await bus.publish(
            DomainEvent(
                domain="asset",
                event_type=AssetEvents.ASSET_CREATED,
                payload={
                    "asset_id": str(asset.id),
                    "asset_name": asset.hostname,
                    "asset_type": asset.asset_type,
                    "ip": asset.ip,
                },
            )
        )
        return asset
