"""JSON 字段解析工具.

领域模型中部分字段（如 ``trigger_condition``、``action_chain``、
``event_types``、``asset_ids``）以 ``Text`` 列存储 JSON 字符串，而事件
处理器期望直接拿到 dict/list。直接对字符串调用 ``.get()`` / 下标会在运行时
抛 ``AttributeError`` / ``TypeError``，且常被上层 ``try/except`` 吞掉导致
链路静默失效。统一用本工具解析，避免裸字符串被当作结构化数据消费。
"""

from __future__ import annotations

import json
from typing import Any


def parse_json_field(value: Any, default: Any) -> Any:
    """将可能是 JSON 字符串的字段安全解析为 dict/list.

    - 已是 dict/list：原样返回
    - None / 空串：返回 ``default``
    - 合法 JSON 字符串：解析返回
    - 非法 JSON：返回 ``default``（不抛异常）
    """
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default
    return default
