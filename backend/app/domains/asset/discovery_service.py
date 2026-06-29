"""资产发现 Service - 真实网络扫描引擎."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud_service import model_to_dict
from app.common.events import AssetEvents, DomainEvent, get_event_bus
from app.domains.asset.discovery_models import DiscoveryResult, DiscoveryTask
from app.domains.asset.models import Asset

logger = logging.getLogger(__name__)

# Worker 进程内运行的扫描任务句柄集合，防止 task 被 GC 回收
_scan_tasks: set[asyncio.Task] = set()


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


def _ping_args(ip: str, timeout: float) -> list[str]:
    """按平台返回 ping 参数（Windows 与 *nix 不兼容）.

    - Windows: ``ping -n 1 -w <ms> ip``（-w 单位毫秒）
    - Linux/macOS: ``ping -c 1 -W <sec> ip``（-W 单位秒）
    """
    import platform

    if platform.system().lower().startswith("win"):
        return ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
    return ["ping", "-c", "1", "-W", str(max(int(timeout), 1)), ip]


async def _icmp_ping(ip: str, timeout: float = 2.0) -> bool:
    """ICMP Ping检测（跨平台参数）."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *_ping_args(ip, timeout),
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


async def _ssh_probe(ip: str, port: int = 22, timeout: float = 2.0) -> tuple[bool, str | None]:
    """SSH 探测：连 TCP 端口并读取 banner（SSH 服务器连接即回 "SSH-2.0-..."）.

    返回 (是否疑似SSH, banner)。端口可连即视为开放；banner 以 SSH- 开头则确认为 SSH。
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=timeout
        )
    except Exception:
        return False, None
    banner = ""
    try:
        raw = await asyncio.wait_for(reader.readline(), timeout=timeout)
        banner = raw.decode("latin-1", "ignore").strip()
    except Exception:
        banner = ""
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
    # 端口可连即算开放；有 SSH banner 则更可信
    return True, (banner or None)


def _ber_len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    out = bytearray()
    while n:
        out.insert(0, n & 0xFF)
        n >>= 8
    return bytes([0x80 | len(out)]) + bytes(out)


def _ber_tlv(tag: int, content: bytes) -> bytes:
    return bytes([tag]) + _ber_len(len(content)) + content


def _encode_oid(arcs: tuple[int, ...]) -> bytes:
    body = bytearray([arcs[0] * 40 + arcs[1]])
    for a in arcs[2:]:
        if a < 0x80:
            body.append(a)
        else:
            stack = [a & 0x7F]
            a >>= 7
            while a:
                stack.append((a & 0x7F) | 0x80)
                a >>= 7
            body.extend(reversed(stack))
    return bytes(body)


def _snmp_get_packet(community: str = "public") -> bytes:
    """构造 SNMPv2c GetRequest(sysDescr 1.3.6.1.2.1.1.1.0) 报文."""
    oid = _ber_tlv(0x06, _encode_oid((1, 3, 6, 1, 2, 1, 1, 1, 0)))
    varbind = _ber_tlv(0x30, oid + _ber_tlv(0x05, b""))
    pdu = _ber_tlv(
        0xA0,
        _ber_tlv(0x02, (1).to_bytes(4, "big"))   # request-id
        + _ber_tlv(0x02, b"\x00")                 # error-status
        + _ber_tlv(0x02, b"\x00")                 # error-index
        + _ber_tlv(0x30, varbind),                # variable-bindings
    )
    return _ber_tlv(
        0x30,
        _ber_tlv(0x02, b"\x01")                    # version: 1 = v2c
        + _ber_tlv(0x04, community.encode())       # community
        + pdu,
    )


async def _snmp_probe(ip: str, timeout: float = 2.0, community: str = "public") -> bool:
    """SNMP 探测：向 UDP/161 发 v2c GetRequest，收到合法响应即视为存活."""
    import socket

    pkt = _snmp_get_packet(community)

    def _probe() -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        try:
            s.sendto(pkt, (ip, 161))
            data, _ = s.recvfrom(4096)
            return bool(data) and data[:1] == b"\x30"  # SNMP 响应为 SEQUENCE
        except Exception:
            return False
        finally:
            s.close()

    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(loop.run_in_executor(None, _probe), timeout=timeout + 1)
    except Exception:
        return False


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
    # SNMP 多见于网络设备（且未命中上述端口时）
    if 161 in open_ports:
        return "network_device"
    return "unknown"


class DiscoveryService:
    # _run_scan 内部自建 session，因此 Worker 侧可用 db=None 实例化
    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    async def _load_template(self, template_id: str):
        """加载发现模板（用于任务继承），不存在返回 None."""
        from app.domains.asset.discovery_template_models import DiscoveryTemplate

        return (
            await self.db.execute(
                select(DiscoveryTemplate).where(DiscoveryTemplate.id == template_id)
            )
        ).scalar_one_or_none()

    async def create_task(self, data: dict) -> dict:
        """创建发现任务（DB持久化）.

        当 auto_onboard=True（默认）时，创建后自动启动扫描。
        支持 template_id：未显式提供的字段从发现模板继承。
        """
        ip_range = data.get("ip_range") or data.get("cidr") or ""
        if not ip_range:
            ip_range = "127.0.0.1"

        # 引用发现模板时，未显式提供的字段从模板继承（B.1：模板应用到任务）
        template_id = data.get("template_id")
        tpl_protocols = tpl_ports = tpl_cred = tpl_timeout = None
        if template_id:
            tpl = await self._load_template(template_id)
            if tpl:
                # template.protocol 为 "ssh,snmp" 形式，拆成小写列表
                tpl_protocols = [
                    p.strip().lower() for p in (tpl.protocol or "").split(",") if p.strip()
                ] or None
                tpl_ports = tpl.port_range
                tpl_cred = tpl.credential_id
                tpl_timeout = tpl.timeout

        task = DiscoveryTask(
            name=data.get(
                "name", "discovery-" + datetime.now().strftime("%Y%m%d%H%M%S")
            ),
            ip_range=ip_range,
            ip_mode=data.get("ip_mode", "cidr"),
            protocols=data.get("protocols") or tpl_protocols or ["icmp"],
            ports=data.get("ports") or tpl_ports,
            credential_id=data.get("credential_id") or tpl_cred,
            template_id=template_id,
            timeout=data.get("timeout") or tpl_timeout or 30,
            auto_onboard=data.get("auto_onboard", True),
            status="pending",
            discovered_count=0,
            onboarded_count=0,
            created_by=data.get("created_by"),
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)

        # 自动纳管模式：创建后立即启动扫描（fire-and-forget 后台执行）
        if task.auto_onboard:
            try:
                start_result = await self.start_task(str(task.id))
                logger.info(
                    "auto_onboard: 任务 %s 已自动启动扫描: %s",
                    task.id,
                    start_result,
                )
            except Exception:
                logger.exception("auto_onboard: 自动启动扫描失败 task=%s", task.id)
                # 自启动失败不影响任务创建，用户仍可手动启动

        # 重新查询以返回最新状态（start_task 已将状态改为 running）
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

        # 不在 API 进程内跑扫描（多副本/重启会丢任务），改为发事件：
        # status=running 与 scan_requested 事件复用同一事务原子落库，
        # 由 Worker 进程的 on_discovery_scan_requested 领取执行（P1-07）。
        bus = get_event_bus()
        await bus.publish(
            DomainEvent(
                domain="asset",
                event_type=AssetEvents.DISCOVERY_SCAN_REQUESTED,
                payload={"task_id": task_id},
                source="discovery_service",
            ),
            session=self.db,
        )
        return {"task_id": task_id, "status": "running"}

    async def stop_task(self, task_id: str) -> dict:
        """停止发现任务：将 pending/running 任务置为 cancelled。

        扫描在 Worker 进程异步执行，跨进程无法强杀；此处标记 DB 终态，
        _run_scan 完成前会校验该状态、不再覆盖（见 _run_scan 守卫）。
        """
        task = (
            await self.db.execute(
                select(DiscoveryTask).where(DiscoveryTask.id == task_id)
            )
        ).scalar_one_or_none()
        if not task:
            return {"error": "任务不存在"}
        if task.status not in ("pending", "running"):
            return {"error": f"任务状态为 {task.status}，无需停止"}
        task.status = "cancelled"
        task.completed_at = datetime.now(timezone.utc)
        task.error_message = "用户手动停止"
        await self.db.flush()
        return {"task_id": task_id, "status": "cancelled"}

    async def delete_task(self, task_id: str) -> dict:
        """删除发现任务及其发现结果（无论任务处于何种状态）。"""
        from sqlalchemy import delete as _delete

        task = (
            await self.db.execute(
                select(DiscoveryTask).where(DiscoveryTask.id == task_id)
            )
        ).scalar_one_or_none()
        if not task:
            return {"error": "任务不存在"}
        await self.db.execute(
            _delete(DiscoveryResult).where(DiscoveryResult.task_id == task_id)
        )
        await self.db.execute(
            _delete(DiscoveryTask).where(DiscoveryTask.id == task_id)
        )
        await self.db.flush()
        return {"task_id": task_id, "deleted": True}

    async def requeue_stuck_tasks(self) -> int:
        """Worker 启动时恢复孤儿任务：重新派发 pending/running 状态的发现任务。

        场景：任务创建时 Worker 未运行、或 Worker 在扫描中途崩溃，任务会卡在
        pending/running。Worker 启动后调用本方法，重发 DISCOVERY_SCAN_REQUESTED，
        由 outbox→handler 重新执行（_run_scan 会先清空旧结果，幂等安全）。
        """
        rows = (
            (
                await self.db.execute(
                    select(DiscoveryTask).where(
                        DiscoveryTask.status.in_(["pending", "running"])
                    )
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            return 0
        bus = get_event_bus()
        for task in rows:
            task.status = "running"
            await bus.publish(
                DomainEvent(
                    domain="asset",
                    event_type=AssetEvents.DISCOVERY_SCAN_REQUESTED,
                    payload={"task_id": str(task.id)},
                    source="discovery_recovery",
                ),
                session=self.db,
            )
        await self.db.flush()
        logger.info("discovery: 启动恢复，重新派发 %d 个未完成任务", len(rows))
        return len(rows)

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

                # 幂等：清除本任务历史发现结果，避免重跑（孤儿恢复/手动重启）产生重复行
                from sqlalchemy import delete as _delete

                await session.execute(
                    _delete(DiscoveryResult).where(DiscoveryResult.task_id == task_id)
                )

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
                        proto_hits: dict = {}

                        # ICMP检测
                        if "icmp" in protocols or "ping" in protocols:
                            if await _icmp_ping(ip, timeout=2.0):
                                alive = True
                                proto_hits["icmp"] = True

                        # TCP端口扫描
                        if "tcp" in protocols or ports:
                            # 端口并发探测，单端口超时取固定区间（0.5~3s），不能按端口数均摊，
                            # 否则全量(65535)端口时每端口超时趋近于0、全部误判为关闭。
                            port_timeout = max(0.5, min(3.0, (timeout or 30) / 20))
                            tcp_ports = await _tcp_scan(ip, ports, timeout=port_timeout)
                            if tcp_ports:
                                alive = True
                                open_ports_list = tcp_ports
                                proto_hits["tcp"] = tcp_ports

                        # SSH 探测（TCP/22 + banner）
                        if "ssh" in protocols:
                            ssh_ok, ssh_banner = await _ssh_probe(ip, timeout=2.0)
                            if ssh_ok:
                                alive = True
                                if 22 not in open_ports_list:
                                    open_ports_list.append(22)
                                proto_hits["ssh"] = ssh_banner or True

                        # SNMP 探测（UDP/161 v2c GetRequest）
                        if "snmp" in protocols:
                            if await _snmp_probe(ip, timeout=2.0):
                                alive = True
                                if 161 not in open_ports_list:
                                    open_ports_list.append(161)
                                proto_hits["snmp"] = True

                        if not alive:
                            return

                        open_ports_list = sorted(set(open_ports_list))

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
                                "protocol_hits": proto_hits,
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

                # 若扫描期间用户已停止/删除该任务，则不覆盖其终态
                cur_status = (
                    await session.execute(
                        select(DiscoveryTask.status).where(DiscoveryTask.id == task_id)
                    )
                ).scalar_one_or_none()
                if cur_status is None or cur_status == "cancelled":
                    logger.info("discovery: 任务 %s 已被停止/删除，跳过完成写入", task_id)
                    return

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

                # 自动纳管：扫描成功后，若任务开启 auto_onboard，
                # 将全部 discovered 状态的结果纳管为资产。
                # onboard_results 天然幂等（状态门槛 + IP 去重），重复纳管安全。
                if task.auto_onboard and discovered > 0:
                    try:
                        onboard_svc = DiscoveryService(session)
                        onboard_result = await onboard_svc._auto_onboard_task(task_id)
                        logger.info(
                            "auto_onboard: 任务 %s 自动纳管完成: %s",
                            task_id,
                            onboard_result,
                        )
                    except Exception:
                        logger.exception(
                            "auto_onboard: 自动纳管失败 task=%s（扫描结果已保存，可手动纳管）",
                            task_id,
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
            # status 专表生命周期(active)，在线性写 reachability（发现存活即 reachable）
            asset = Asset(
                name=dr.hostname or dr.ip,
                hostname=dr.hostname or dr.ip,
                ip=dr.ip,
                asset_type=at,
                status="active",
                reachability="reachable",
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

    async def _auto_onboard_task(self, task_id: str) -> dict:
        """自动纳管指定任务的全部 discovered 结果（由 _run_scan 扫描完成后调用）.

        复用 onboard_results 的幂等逻辑，自动查询该 task 下所有 discovered 状态的结果。
        用 self.db（即 _run_scan 的 session）提交，纳管后由调用方统一 commit。
        """
        result = await self.db.execute(
            select(DiscoveryResult).where(
                DiscoveryResult.task_id == task_id,
                DiscoveryResult.status == "discovered",
            )
        )
        result_ids = [str(r.id) for r in result.scalars().all()]
        if not result_ids:
            return {"onboarded": 0, "errors": 0, "total": 0, "message": "无可纳管结果"}
        onboard_result = await self.onboard_results(result_ids, asset_type="auto")
        await self.db.commit()
        return onboard_result

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
            status="active",
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


# ---------------------------------------------------------------------------
# Worker 进程事件处理器
# ---------------------------------------------------------------------------


async def on_discovery_scan_requested(event: DomainEvent) -> None:
    """Worker：收到发现扫描请求 → 后台执行扫描（不阻塞 outbox 消费循环）。

    扫描可能耗时较长，若在 OutboxConsumer 串行派发中同步执行会卡住事件消费，
    因此在 Worker 进程内以 tracked task 运行；_run_scan 内部自建 session。
    """
    task_id = event.payload.get("task_id")
    if not task_id:
        return
    svc = DiscoveryService()
    t = asyncio.create_task(svc._run_scan(task_id))
    _scan_tasks.add(t)
    t.add_done_callback(_scan_tasks.discard)
    logger.info("discovery: 已在 Worker 启动扫描 task=%s", task_id)
