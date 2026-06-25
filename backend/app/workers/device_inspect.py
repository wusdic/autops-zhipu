"""设备深度信息采集器.

通过凭据登录设备采集真实指标（区别于内置采集器的黑盒探测）：

- Linux/类 Unix：SSH（asyncssh）
- Windows：WinRM（pywinrm，同步库，放入线程执行）
- 网络设备：SNMP（pysnmp）

三类第三方依赖均**懒加载**：未安装时返回结构化的 ``method_unavailable``
错误而非让进程导入失败，保证 API/Worker 在缺依赖时仍可启动。

统一返回 ``DeviceInfo`` 归一化指标，供巡检引擎按阈值评估。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.common.credentials import (
    SNMP_TYPES,
    WINDOWS_TYPES,
    DeviceCredential,
)

logger = logging.getLogger(__name__)

# 采集总超时（秒）
_DEFAULT_TIMEOUT = 15.0


def _empty_info(method: str, error: str) -> dict[str, Any]:
    return {
        "method": method,
        "reachable": False,
        "error": error,
        "os": None,
        "hostname": None,
        "cpu_count": None,
        "load_1m": None,
        "load_5m": None,
        "load_15m": None,
        "load_per_core": None,
        "mem_total_mb": None,
        "mem_used_mb": None,
        "mem_used_percent": None,
        "swap_total_mb": None,
        "swap_used_percent": None,
        "disk_used_percent_max": None,
        "disks": [],
        "inode_used_percent_max": None,
        "process_count": None,
        "zombie_count": None,
        "logged_in_users": None,
        "listening_ports_count": None,
        "ntp_synchronized": None,
        "selinux": None,
        "ssh_permit_root": None,
        "uptime_seconds": None,
        "raw": {},
    }


# ---------------------------------------------------------------------------
# SSH (Linux / 类 Unix)
# ---------------------------------------------------------------------------

_SSH_COMMANDS = {
    "hostname": "hostname",
    "uname": "uname -sr",
    "nproc": "nproc",
    "loadavg": "cat /proc/loadavg",
    "free": "free -m",
    "df": "df -P -x tmpfs -x devtmpfs",
    "df_inode": "df -P -i -x tmpfs -x devtmpfs",
    "uptime": "cat /proc/uptime",
    "ps_stat": "ps -e -o stat=",
    "who": "who",
    "listen": "ss -H -ltn",
    "timedatectl": "timedatectl 2>/dev/null",
    "sshd": "grep -iE '^[[:space:]]*PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null",
    "selinux": "getenforce 2>/dev/null",
}


def _parse_ssh(outputs: dict[str, str]) -> dict[str, Any]:
    info = _empty_info("ssh", "")
    info["reachable"] = True
    info["error"] = None
    info["hostname"] = (outputs.get("hostname") or "").strip() or None
    info["os"] = (outputs.get("uname") or "").strip() or None

    try:
        info["cpu_count"] = int((outputs.get("nproc") or "").strip())
    except (ValueError, TypeError):
        pass

    loadavg = (outputs.get("loadavg") or "").split()
    if len(loadavg) >= 3:
        try:
            info["load_1m"] = float(loadavg[0])
            info["load_5m"] = float(loadavg[1])
            info["load_15m"] = float(loadavg[2])
            if info.get("cpu_count"):
                info["load_per_core"] = round(info["load_1m"] / info["cpu_count"], 2)
        except (ValueError, ZeroDivisionError):
            pass

    # free -m: Mem 与 Swap 两行
    for line in (outputs.get("free") or "").splitlines():
        parts = line.split()
        if not parts:
            continue
        head = parts[0].lower()
        if head.startswith("mem"):
            try:
                total, used = int(parts[1]), int(parts[2])
                info["mem_total_mb"] = total
                info["mem_used_mb"] = used
                if total > 0:
                    info["mem_used_percent"] = round(used / total * 100, 1)
            except (ValueError, IndexError):
                pass
        elif head.startswith("swap"):
            try:
                total, used = int(parts[1]), int(parts[2])
                info["swap_total_mb"] = total
                if total > 0:
                    info["swap_used_percent"] = round(used / total * 100, 1)
                else:
                    info["swap_used_percent"] = 0.0
            except (ValueError, IndexError):
                pass

    # df -P: 列 = Filesystem Size Used Avail Use% Mounted
    disks = []
    for line in (outputs.get("df") or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 6 and parts[4].endswith("%"):
            try:
                disks.append({"mount": parts[5], "used_percent": float(parts[4].rstrip("%"))})
            except ValueError:
                pass
    info["disks"] = disks
    if disks:
        info["disk_used_percent_max"] = max(d["used_percent"] for d in disks)

    # df -i: inode 使用率（IUse% 在第 5 列）
    inode_pcts = []
    for line in (outputs.get("df_inode") or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 6 and parts[4].endswith("%"):
            try:
                inode_pcts.append(float(parts[4].rstrip("%")))
            except ValueError:
                pass
    if inode_pcts:
        info["inode_used_percent_max"] = max(inode_pcts)

    # 进程数 / 僵尸进程数
    ps_lines = [s.strip() for s in (outputs.get("ps_stat") or "").splitlines() if s.strip()]
    if ps_lines:
        info["process_count"] = len(ps_lines)
        info["zombie_count"] = sum(1 for s in ps_lines if s.startswith("Z"))

    # 登录用户数
    who_lines = [s for s in (outputs.get("who") or "").splitlines() if s.strip()]
    info["logged_in_users"] = len(who_lines)

    # 监听端口数
    listen_lines = [s for s in (outputs.get("listen") or "").splitlines() if s.strip()]
    info["listening_ports_count"] = len(listen_lines)

    # 时间同步（NTP）
    td = outputs.get("timedatectl") or ""
    for line in td.splitlines():
        low = line.lower()
        if "ntp synchronized" in low or "system clock synchronized" in low:
            info["ntp_synchronized"] = "yes" in low
            break

    # SSH 是否允许 root 登录（安全基线）
    sshd = (outputs.get("sshd") or "").lower()
    if sshd:
        if "permitrootlogin yes" in sshd:
            info["ssh_permit_root"] = True
        elif "permitrootlogin" in sshd:  # no / prohibit-password / without-password
            info["ssh_permit_root"] = False

    # SELinux 状态
    selinux = (outputs.get("selinux") or "").strip()
    if selinux:
        info["selinux"] = selinux

    uptime = (outputs.get("uptime") or "").split()
    if uptime:
        try:
            info["uptime_seconds"] = int(float(uptime[0]))
        except ValueError:
            pass

    return info


async def collect_via_ssh(
    host: str, port: int, cred: DeviceCredential, timeout: float = _DEFAULT_TIMEOUT
) -> dict[str, Any]:
    """通过 SSH 采集 Linux 设备信息."""
    try:
        import asyncssh  # 懒加载
    except ImportError:
        return _empty_info("ssh", "method_unavailable: asyncssh 未安装")

    connect_kwargs: dict[str, Any] = {
        "host": host,
        "port": port or 22,
        "known_hosts": None,  # 私有化环境内不校验 host key
        "username": cred.username or "root",
    }
    if cred.private_key:
        try:
            connect_kwargs["client_keys"] = [asyncssh.import_private_key(cred.private_key)]
        except Exception as exc:  # noqa: BLE001
            return _empty_info("ssh", f"私钥解析失败: {exc}")
    elif cred.password:
        connect_kwargs["password"] = cred.password

    try:
        async with asyncio.timeout(timeout):
            async with asyncssh.connect(**connect_kwargs) as conn:
                outputs: dict[str, str] = {}
                for key, cmd in _SSH_COMMANDS.items():
                    try:
                        res = await conn.run(cmd, check=False)
                        outputs[key] = res.stdout or ""
                    except Exception:  # noqa: BLE001
                        outputs[key] = ""
        return _parse_ssh(outputs)
    except Exception as exc:  # noqa: BLE001
        logger.info("SSH 采集失败 host=%s: %s", host, exc)
        return _empty_info("ssh", f"ssh_error: {str(exc)[:200]}")


# ---------------------------------------------------------------------------
# WinRM (Windows)
# ---------------------------------------------------------------------------

_WINRM_PS = r"""
$os = Get-CimInstance Win32_OperatingSystem
$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
$disks = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    @{ mount = $_.DeviceID; used_percent = [math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 1) }
}
$result = @{
    hostname = $env:COMPUTERNAME
    os = "$($os.Caption) $($os.Version)"
    cpu_count = $cpu
    mem_total_mb = [math]::Round($os.TotalVisibleMemorySize / 1024)
    mem_free_mb = [math]::Round($os.FreePhysicalMemory / 1024)
    uptime_seconds = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalSeconds)
    disks = @($disks)
}
$result | ConvertTo-Json -Depth 4 -Compress
"""


def _winrm_blocking(host: str, cred: DeviceCredential) -> dict[str, Any]:
    try:
        import winrm  # 懒加载
    except ImportError:
        return _empty_info("winrm", "method_unavailable: pywinrm 未安装")

    try:
        session = winrm.Session(
            f"http://{host}:5985/wsman",
            auth=(cred.username or "Administrator", cred.password or ""),
            transport="ntlm",
        )
        r = session.run_ps(_WINRM_PS)
        if r.status_code != 0:
            return _empty_info("winrm", f"winrm_error: {(r.std_err or b'')[:200]!r}")
        import json

        data = json.loads((r.std_out or b"{}").decode("utf-8", errors="replace"))
        info = _empty_info("winrm", "")
        info["reachable"] = True
        info["error"] = None
        info["hostname"] = data.get("hostname")
        info["os"] = data.get("os")
        info["cpu_count"] = data.get("cpu_count")
        total = data.get("mem_total_mb")
        free = data.get("mem_free_mb")
        info["mem_total_mb"] = total
        if total and free is not None:
            used = total - free
            info["mem_used_mb"] = used
            if total > 0:
                info["mem_used_percent"] = round(used / total * 100, 1)
        info["uptime_seconds"] = data.get("uptime_seconds")
        disks = data.get("disks") or []
        if isinstance(disks, dict):  # 单盘时 ConvertTo-Json 可能返回对象
            disks = [disks]
        info["disks"] = disks
        if disks:
            try:
                info["disk_used_percent_max"] = max(
                    float(d["used_percent"]) for d in disks
                )
            except (ValueError, KeyError, TypeError):
                pass
        return info
    except Exception as exc:  # noqa: BLE001
        logger.info("WinRM 采集失败 host=%s: %s", host, exc)
        return _empty_info("winrm", f"winrm_error: {str(exc)[:200]}")


async def collect_via_winrm(
    host: str, cred: DeviceCredential, timeout: float = _DEFAULT_TIMEOUT
) -> dict[str, Any]:
    """通过 WinRM 采集 Windows 设备信息（同步库放入线程）."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_winrm_blocking, host, cred), timeout=timeout
        )
    except asyncio.TimeoutError:
        return _empty_info("winrm", f"timeout({timeout}s)")


# ---------------------------------------------------------------------------
# SNMP (网络设备)
# ---------------------------------------------------------------------------

_OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"
_OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
_OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"


async def collect_via_snmp(
    host: str, cred: DeviceCredential, timeout: float = _DEFAULT_TIMEOUT
) -> dict[str, Any]:
    """通过 SNMP v2c 采集网络设备基础信息."""
    try:
        from pysnmp.hlapi.asyncio import (  # 懒加载
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )
    except ImportError:
        return _empty_info("snmp", "method_unavailable: pysnmp 未安装")

    community = cred.community or "public"
    info = _empty_info("snmp", "")
    try:
        async with asyncio.timeout(timeout):
            engine = SnmpEngine()
            target = UdpTransportTarget((host, 161), timeout=timeout / 3, retries=1)
            error_indication, error_status, _, var_binds = await getCmd(
                engine,
                CommunityData(community, mpModel=1),
                target,
                ContextData(),
                ObjectType(ObjectIdentity(_OID_SYS_DESCR)),
                ObjectType(ObjectIdentity(_OID_SYS_NAME)),
                ObjectType(ObjectIdentity(_OID_SYS_UPTIME)),
            )
        if error_indication or error_status:
            return _empty_info("snmp", f"snmp_error: {error_indication or error_status}")
        values = [str(vb[1]) for vb in var_binds]
        info["reachable"] = True
        info["error"] = None
        info["os"] = values[0] if len(values) > 0 else None
        info["hostname"] = values[1] if len(values) > 1 else None
        if len(values) > 2:
            try:
                # sysUpTime 单位为 1/100 秒
                info["uptime_seconds"] = int(int(values[2]) / 100)
            except (ValueError, TypeError):
                pass
        info["raw"] = {"sys_descr": info["os"]}
        return info
    except Exception as exc:  # noqa: BLE001
        logger.info("SNMP 采集失败 host=%s: %s", host, exc)
        return _empty_info("snmp", f"snmp_error: {str(exc)[:200]}")


# ---------------------------------------------------------------------------
# 分发器
# ---------------------------------------------------------------------------


def _choose_method(asset: dict[str, Any], cred: DeviceCredential | None) -> str:
    """按资产类型 / OS / 凭据类型选择采集方式."""
    asset_type = (asset.get("asset_type") or "").lower()
    os_type = (asset.get("os_type") or "").lower()
    ct = (cred.cred_type if cred else "").lower()

    if "network" in asset_type or "switch" in asset_type or "router" in asset_type:
        return "snmp"
    if ct in SNMP_TYPES:
        return "snmp"
    if "windows" in asset_type or "windows" in os_type or ct in WINDOWS_TYPES:
        return "winrm"
    return "ssh"


async def collect_device_info(
    asset: dict[str, Any], cred: DeviceCredential | None
) -> dict[str, Any]:
    """采集单个资产的深度信息（自动选择 SSH/WinRM/SNMP）.

    Args:
        asset: 至少包含 ip / port / asset_type / os_type 的字典
        cred: 已解析的凭据；为 None 时返回 no_credential 错误
    """
    host = asset.get("ip")
    if not host:
        return _empty_info("none", "no_ip")
    if cred is None:
        return _empty_info("none", "no_credential")

    method = _choose_method(asset, cred)
    if method == "snmp":
        return await collect_via_snmp(host, cred)
    if method == "winrm":
        return await collect_via_winrm(host, cred)
    return await collect_via_ssh(host, asset.get("port") or 22, cred)
