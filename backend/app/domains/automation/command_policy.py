"""自动化命令安全策略.

不使用简单黑名单，而是基于白名单+路径策略+风险等级的综合校验。
"""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass

from app.infra.config import get_config


# Shell metacharacters that must be blocked in all commands
SHELL_METACHAR_PATTERNS: list[str] = [
    ";", "&&", "||", "|", ">", "<", ">>", "<<",
    "$(", "`", "\n", "sudo su", "sudo -i",
]


@dataclass
class CommandPolicyResult:
    """命令策略评估结果."""
    allowed: bool
    risk_level: str  # low / medium / high / critical
    reason: str
    requires_approval: bool


class CommandPolicy:
    """命令安全策略评估器."""

    # 绝对禁止的命令
    DANGEROUS_COMMANDS = frozenset({
        "mkfs", "fdisk", "parted", "format",
        "shutdown", "reboot", "halt", "poweroff", "init",
    })

    # 禁止操作的系统路径
    FORBIDDEN_PATHS = frozenset({
        "/", "/boot", "/etc/passwd", "/etc/shadow",
        "/bin", "/sbin", "/usr/bin", "/usr/sbin",
        "/var/lib/mysql", "/var/lib/postgresql",
    })

    # 允许的诊断命令 (低风险)
    ALLOWED_DIAGNOSTICS = frozenset({
        "df", "du", "ls", "find", "cat", "head", "tail",
        "grep", "awk", "wc", "sort", "uniq", "top", "ps",
        "free", "uptime", "whoami", "hostname", "uname",
        "netstat", "ss", "ping", "traceroute", "curl", "wget",
        "journalctl", "systemctl status", "docker ps", "docker logs",
        "mysqladmin", "redis-cli", "nginx -t",
    })

    # 中风险命令 (需要审批)
    MEDIUM_RISK_COMMANDS = frozenset({
        "rm", "truncate", "mv", "cp",
        "systemctl restart", "systemctl stop", "systemctl start",
        "docker restart", "docker stop", "docker start",
    })

    def evaluate(self, command: str, allowed_paths: set[str] | None = None) -> CommandPolicyResult:
        """评估命令是否允许执行.

        Args:
            command: 要执行的命令字符串
            allowed_paths: 允许操作的路径集合
        """
        allowed_paths = allowed_paths or set()

        if not command or not command.strip():
            return CommandPolicyResult(False, "low", "空命令", False)

        # ── Shell metacharacter detection (checked FIRST) ──────────────
        for pattern in SHELL_METACHAR_PATTERNS:
            if pattern in command:
                return CommandPolicyResult(
                    False,
                    "critical",
                    f"Shell metacharacter detected: {pattern!r}",
                    True,
                )

        # 解析命令
        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            return CommandPolicyResult(False, "high", f"命令解析失败: {exc}", True)

        if not tokens:
            return CommandPolicyResult(False, "low", "空命令", False)

        executable = tokens[0].split("/")[-1]

        # 1. 检查绝对禁止命令
        if executable in self.DANGEROUS_COMMANDS:
            return CommandPolicyResult(
                False, "critical",
                f"禁止执行高危命令: {executable}",
                True,
            )

        # 2. 检查fork炸弹等恶意模式
        if ":(){:|:&}" in command or "fork bomb" in command.lower():
            return CommandPolicyResult(
                False, "critical",
                "检测到fork炸弹模式",
                True,
            )

        # 3. 检查危险重定向
        if ">" in command and any(p in command for p in self.FORBIDDEN_PATHS):
            return CommandPolicyResult(
                False, "critical",
                "禁止写入系统关键路径",
                True,
            )

        # 4. 检查rm -rf /
        if executable == "rm" and "-rf" in command and "/" in tokens:
            has_safe_path = False
            for t in tokens[1:]:
                if t.startswith("-"):
                    continue
                # Use realpath to resolve ../../ and symlinks
                resolved = os.path.realpath(t)
                if resolved in self.FORBIDDEN_PATHS or resolved == "/":
                    return CommandPolicyResult(
                        False, "critical",
                        f"禁止递归删除系统路径: {t} (resolved: {resolved})",
                        True,
                    )
                has_safe_path = True
            if not has_safe_path:
                return CommandPolicyResult(
                    False, "high",
                    "rm 命令缺少目标路径",
                    True,
                )

        # 5. 检查路径是否在允许范围内 (with realpath resolution)
        for token in tokens[1:]:
            if token.startswith("/") and token not in ("-",):
                resolved = os.path.realpath(token)
                if resolved in self.FORBIDDEN_PATHS:
                    return CommandPolicyResult(
                        False, "critical",
                        f"禁止操作系统关键路径: {token} (resolved: {resolved})",
                        True,
                    )
                if allowed_paths:
                    resolved_allowed = {os.path.realpath(p) for p in allowed_paths}
                    if not any(resolved.startswith(p) for p in resolved_allowed):
                        return CommandPolicyResult(
                            False, "high",
                            f"路径未授权: {token} (resolved: {resolved})",
                            True,
                        )

        # 6. 分类风险等级
        cmd_prefix = command.split()[0].split("/")[-1] if command.split() else ""
        full_cmd = command.strip()

        # 检查是否是允许的诊断命令
        is_diagnostic = any(
            full_cmd.startswith(d) or cmd_prefix == d.split()[0]
            for d in self.ALLOWED_DIAGNOSTICS
        )

        # 检查是否是中风险命令
        is_medium = any(
            full_cmd.startswith(m) or cmd_prefix == m.split()[0]
            for m in self.MEDIUM_RISK_COMMANDS
        )

        if is_diagnostic and not is_medium:
            return CommandPolicyResult(True, "low", "诊断命令通过", False)
        elif is_medium:
            return CommandPolicyResult(True, "medium", "中风险命令，需要审批", True)
        else:
            # Unknown command — in production, reject outright
            if get_config().env == "prod":
                return CommandPolicyResult(
                    False,
                    "critical",
                    f"未知命令在生产环境被拒绝: {executable}",
                    True,
                )
            # Non-prod: allow but flag high risk requiring approval
            return CommandPolicyResult(True, "high", f"未知命令: {executable}，需要审批", True)
