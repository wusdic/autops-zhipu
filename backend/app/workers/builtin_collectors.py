"""内置采集器 - Ping/TCP/HTTP/Cert/DB."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import ssl
import sys
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


def _build_ping_args(ip: str, count: int, timeout: float) -> list[str]:
    """按平台构造 ping 命令参数.

    Linux/macOS: -c <count> -W <seconds>
    Windows:     -n <count> -w <milliseconds>
    """
    if sys.platform == "win32":
        return ["ping", "-n", str(count), "-w", str(int(timeout * 1000)), ip]
    return ["ping", "-c", str(count), "-W", str(int(timeout)), ip]


class BaseBuiltinCollector:
    """采集器基类."""

    name: str = "base"
    collector_type: str = "base"

    async def collect(
        self, ip: str, port: int | None = None, config: dict | None = None
    ) -> dict:
        raise NotImplementedError


class PingCollector(BaseBuiltinCollector):
    """ICMP Ping 可达性检测."""

    name = "ping-collector"
    collector_type = "ping"

    async def collect(
        self, ip: str, port: int | None = None, config: dict | None = None
    ) -> dict:
        config = config or {}
        timeout = config.get("timeout", 3.0)
        # 校验 IP，防止参数注入（拒绝含空白/分号/反引号等可疑字符的输入）
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return {
                "collector": self.name,
                "ip": ip,
                "alive": False,
                "status": "invalid_ip",
                "error": "非法 IP 地址",
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
        try:
            proc = await asyncio.create_subprocess_exec(
                *_build_ping_args(ip, 3, timeout),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout * 3 + 2
            )
            alive = proc.returncode == 0
            output = (stdout or b"").decode("utf-8", errors="replace")
            # 提取延迟（Linux: rtt min/avg/max；Windows: 最小/最大/平均 ms）
            latency = None
            if alive:
                try:
                    if "min/avg/max" in output:
                        stats_line = [
                            l for l in output.split("\n") if "min/avg/max" in l
                        ]
                        if stats_line:
                            parts = stats_line[0].split("=")[-1].strip().split("/")
                            latency = float(parts[1])  # avg
                    elif "=" in output and "ms" in output:
                        # Windows ping 输出: "最小 = 0ms, 最大 = 0ms, 平均 = 0ms"
                        avg_seg = [
                            s
                            for s in output.split(",")
                            if "平均" in s or "Average" in s
                        ]
                        if avg_seg:
                            latency = float(
                                avg_seg[0].split("=")[-1].replace("ms", "").strip()
                            )
                except Exception:
                    logger.debug("解析 ping 延迟失败: %s", output[:200])

            return {
                "collector": self.name,
                "ip": ip,
                "alive": alive,
                "latency_ms": latency,
                "status": "success" if alive else "unreachable",
                "output": output[:2000],
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
        except asyncio.TimeoutError:
            return {
                "collector": self.name,
                "ip": ip,
                "alive": False,
                "status": "timeout",
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.exception("Ping 采集异常: ip=%s", ip)
            return {
                "collector": self.name,
                "ip": ip,
                "alive": False,
                "status": "error",
                "error": str(e)[:500],
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }


class TCPPortCollector(BaseBuiltinCollector):
    """TCP端口扫描."""

    name = "tcp-port-collector"
    collector_type = "tcp_port"

    async def collect(
        self, ip: str, port: int | None = None, config: dict | None = None
    ) -> dict:
        config = config or {}
        ports_str = config.get("ports", "22,80,443,3389,3306,5432,6379,8080,8443")
        timeout = config.get("timeout", 2.0)

        ports = []
        for p in str(ports_str).split(","):
            try:
                ports.append(int(p.strip()))
            except ValueError:
                pass
        if port and port not in ports:
            ports.append(port)

        open_ports = []

        async def check(p: int):
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, p), timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                open_ports.append(p)
            except (asyncio.TimeoutError, OSError):
                pass  # 连接被拒或超时，端口未开放

        await asyncio.gather(*[check(p) for p in ports])

        return {
            "collector": self.name,
            "ip": ip,
            "scanned_ports": ports,
            "open_ports": sorted(open_ports),
            "open_count": len(open_ports),
            "status": "success",
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }


class HTTPCollector(BaseBuiltinCollector):
    """HTTP/HTTPS 服务检测."""

    name = "http-collector"
    collector_type = "http"

    async def collect(
        self, ip: str, port: int | None = None, config: dict | None = None
    ) -> dict:
        config = config or {}
        timeout = config.get("timeout", 10.0)
        use_https = config.get("https", port in (443, 8443) if port else False)
        scheme = "https" if use_https else "http"
        target_port = port or (443 if use_https else 80)
        url = f"{scheme}://{ip}:{target_port}/"
        path = config.get("path", "/")

        try:
            async with httpx.AsyncClient(
                timeout=timeout, verify=False, follow_redirects=True
            ) as client:
                start_time = asyncio.get_event_loop().time()
                resp = await client.get(f"{scheme}://{ip}:{target_port}{path}")
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000

                return {
                    "collector": self.name,
                    "ip": ip,
                    "url": str(resp.url),
                    "status_code": resp.status_code,
                    "response_time_ms": round(elapsed, 2),
                    "content_length": len(resp.content),
                    "title": self._extract_title(resp.text),
                    "status": "success" if resp.status_code < 500 else "error",
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as e:
            return {
                "collector": self.name,
                "ip": ip,
                "url": url,
                "status": "error",
                "error": str(e)[:500],
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }

    @staticmethod
    def _extract_title(html: str) -> str | None:
        try:
            if "<title>" in html:
                start = html.index("<title>") + 7
                end = html.index("</title>", start)
                return html[start:end].strip()[:200]
        except Exception:
            pass
        return None


class CertCollector(BaseBuiltinCollector):
    """SSL/TLS 证书检测."""

    name = "cert-collector"
    collector_type = "certificate"

    async def collect(
        self, ip: str, port: int | None = None, config: dict | None = None
    ) -> dict:
        config = config or {}
        target_port = port or 443
        timeout = config.get("timeout", 10.0)

        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, target_port, ssl=context),
                timeout=timeout,
            )
            ssl_object = writer.get_extra_info("ssl_object")
            writer.close()
            await writer.wait_closed()

            # getpeercert()（非 binary）返回 dict，含 notAfter/subject/issuer
            # 注意：verify_mode=CERT_NONE 时返回的 dict 字段可能不完整，
            # 但 notAfter 始终可用，足够做证书到期检测。
            parsed = ssl_object.getpeercert() or {}

            # 提取有效期
            not_after = parsed.get("notAfter", "")
            subject = (
                dict(x[0] for x in parsed.get("subject", ()))
                if parsed.get("subject")
                else {}
            )
            issuer = (
                dict(x[0] for x in parsed.get("issuer", ()))
                if parsed.get("issuer")
                else {}
            )

            # 计算剩余天数
            days_remaining = None
            if not_after:
                try:
                    from email.utils import parsedate_to_datetime

                    expiry = parsedate_to_datetime(not_after)
                    days_remaining = (expiry - datetime.now(timezone.utc)).days
                except Exception:
                    pass

            return {
                "collector": self.name,
                "ip": ip,
                "port": target_port,
                "subject": subject.get("commonName", ""),
                "issuer": issuer.get("organizationName", ""),
                "not_after": not_after,
                "days_remaining": days_remaining,
                "status": "warning"
                if (days_remaining is not None and days_remaining < 30)
                else "success",
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "collector": self.name,
                "ip": ip,
                "port": target_port,
                "status": "error",
                "error": str(e)[:500],
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }


class DBCollector(BaseBuiltinCollector):
    """数据库连接检测."""

    name = "db-collector"
    collector_type = "database"

    async def collect(
        self, ip: str, port: int | None = None, config: dict | None = None
    ) -> dict:
        config = config or {}
        db_type = config.get("db_type", "mysql")
        target_port = port or {"mysql": 3306, "postgresql": 5432, "redis": 6379}.get(
            db_type, 3306
        )
        timeout = config.get("timeout", 5.0)

        # 简单TCP连接测试（仅做连通性判断，不再用同步 recv 读 banner 以免阻塞事件循环）
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, target_port), timeout=timeout
            )
            # MySQL 连接后主动发送 banner，可异步读取；其它 DB 无主动推送则跳过
            banner = ""
            try:
                banner_data = await asyncio.wait_for(reader.read(200), timeout=1.0)
                if banner_data:
                    banner = banner_data.decode("utf-8", errors="replace")[:200]
            except asyncio.TimeoutError:
                pass  # 多数 DB（postgres/redis）不会主动推送 banner，正常情况
            except Exception:
                logger.debug("读取 DB banner 失败: %s:%s", ip, target_port)
            writer.close()
            await writer.wait_closed()

            return {
                "collector": self.name,
                "ip": ip,
                "port": target_port,
                "db_type": db_type,
                "banner": banner,
                "status": "success",
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "collector": self.name,
                "ip": ip,
                "port": target_port,
                "db_type": db_type,
                "status": "error",
                "error": str(e)[:500],
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }


# 采集器注册表
COLLECTOR_REGISTRY: dict[str, BaseBuiltinCollector] = {
    "ping": PingCollector(),
    "tcp_port": TCPPortCollector(),
    "http": HTTPCollector(),
    "certificate": CertCollector(),
    "database": DBCollector(),
}


async def run_collection(
    collector_type: str, ip: str, port: int | None = None, config: dict | None = None
) -> dict:
    """运行采集."""
    collector = COLLECTOR_REGISTRY.get(collector_type)
    if not collector:
        return {
            "error": f"未知采集器类型: {collector_type}",
            "collector": collector_type,
            "ip": ip,
            "status": "error",
        }
    return await collector.collect(ip, port, config)
