"""动态脱敏工具."""

from __future__ import annotations



def mask_password(data: dict) -> dict:
    """脱敏密码字段."""
    masked = data.copy()
    for key in ("password", "secret", "token", "api_key", "private_key"):
        if key in masked:
            masked[key] = "******"
    return masked


def mask_ip(ip: str) -> str:
    """脱敏 IP 地址：192.168.1.10 -> 192.168.*.*"""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    return ip


def mask_phone(phone: str) -> str:
    """脱敏手机号：13812345678 -> 138****5678"""
    if len(phone) == 11:
        return f"{phone[:3]}****{phone[7:]}"
    return phone


def mask_email(email: str) -> str:
    """脱敏邮箱：user@example.com -> u***@example.com"""
    if "@" in email:
        name, domain = email.split("@", 1)
        if len(name) > 1:
            return f"{name[0]}***@{domain}"
    return email


def mask_dict(data: dict, rules: dict[str, str] | None = None) -> dict:
    """按规则脱敏字典.

    rules: {"field_name": "password|ip|phone|email"}
    """
    rules = rules or {}
    result = {}
    for key, value in data.items():
        rule = rules.get(key)
        if rule == "password":
            result[key] = "******"
        elif rule == "ip" and isinstance(value, str):
            result[key] = mask_ip(value)
        elif rule == "phone" and isinstance(value, str):
            result[key] = mask_phone(value)
        elif rule == "email" and isinstance(value, str):
            result[key] = mask_email(value)
        else:
            result[key] = value
    return result
