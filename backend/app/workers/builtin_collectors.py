"""内置采集器 - Ping/TCP/HTTP/Cert/DB."""
from __future__ import annotations

import asyncio
import logging
import socket
import ssl
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


class BaseBuiltinCollector:
    """采集器基类."""
    name: str = "base"
    collector_type: str = "base"

    async def collect(self, ip: str, port: int | None = None,
                      config: dict | None = None) -> dict:
        raise NotImplementedError


class PingCollector(BaseBuiltinCollector):
    """ICMP Ping 可达性检测."""
    name = "ping-collector"
    collector_type = "ping"

    async def collect(self, ip: str, port: int | None = None,
                      config: dict | None = None) -> dict:
        config = config or {}
        timeout = config.get("timeout", 3.0)
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "3", "-W", str(int(timeout)), ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout * 3 + 2)
            alive = proc.returncode == 0
            output = (stdout or b"").decode("utf-8", errors="replace")
            # 提取延迟
            latency = None
            if alive and "min/avg/max" in output:
                try:
                    stats_line = [l for l in output.split("\n") if "min/avg/max" in l]
                    if stats_line:
                        parts = stats_line[0].split("=")[-1].strip().split("/")
                        latency = float(parts[1])  # avg
                except Exception:
                    pass

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
            return {"collector": self.name, "ip": ip, "alive": False, "status": "timeout",
                    "collected_at": datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            return {"collector": self.name, "ip": ip, "alive": False, "status": "error",
                    "error": str(e)[:500], "collected_at": datetime.now(timezone.utc).isoformat()}


class TCPPortCollector(BaseBuiltinCollector):
    """TCP端口扫描."""
    name = "tcp-port-collector"
    collector_type = "tcp_port"

    async def collect(self, ip: str, port: int | None = None,
                      config: dict | None = None) -> dict:
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
            except Exception:
                pass

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

    async def collect(self, ip: str, port: int | None = None,
                      config: dict | None = None) -> dict:
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
                "collector": self.name, "ip": ip, "url": url,
                "status": "error", "error": str(e)[:500],
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

    async def collect(self, ip: str, port: int | None = None,
                      config: dict | None = None) -> dict:
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

            cert = ssl_object.getpeercert(binary_form=True)
            # 用ssl模块解析
            import ssl as _ssl
            parsed = _ssl._ssl._test_decode_cert(cert) if cert else {}

            # 提取有效期
            not_after = parsed.get("notAfter", "")
            subject = dict(x[0] for x in parsed.get("subject", ())) if parsed.get("subject") else {}
            issuer = dict(x[0] for x in parsed.get("issuer", ())) if parsed.get("issuer") else {}

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
                "status": "warning" if (days_remaining is not None and days_remaining < 30) else "success",
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "collector": self.name, "ip": ip, "port": target_port,
                "status": "error", "error": str(e)[:500],
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }


class DBCollector(BaseBuiltinCollector):
    """数据库连接检测."""
    name = "db-collector"
    collector_type = "database"

    async def collect(self, ip: str, port: int | None = None,
                      config: dict | None = None) -> dict:
        config = config or {}
        db_type = config.get("db_type", "mysql")
        target_port = port or {"mysql": 3306, "postgresql": 5432, "redis": 6379}.get(db_type, 3306)
        timeout = config.get("timeout", 5.0)

        # 简单TCP连接测试
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, target_port), timeout=timeout
            )
            # 尝试读取banner
            banner = ""
            try:
                reader = writer.transport.get_extra_info("socket")
                if reader:
                    reader.settimeout(1.0)
                    try:
                        banner_data = reader.recv(1024)
                        banner = banner_data.decode("utf-8", errors="replace")[:200]
                    except Exception:
                        pass
            except Exception:
                pass
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
                "collector": self.name, "ip": ip, "port": target_port,
                "db_type": db_type, "status": "error",
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


async def run_collection(collector_type: str, ip: str, port: int | None = None,
                         config: dict | None = None) -> dict:
    """运行采集."""
    collector = COLLECTOR_REGISTRY.get(collector_type)
    if not collector:
        return {"error": f"未知采集器类型: {collector_type}",
                "collector": collector_type, "ip": ip, "status": "error"}
    return await collector.collect(ip, port, config)
