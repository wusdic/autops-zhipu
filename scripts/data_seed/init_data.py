"""初始化数据种子 - 默认管理员和角色."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import string
import sys
from pathlib import Path

# 允许从仓库根目录或 scripts/ 下运行：把 backend 加入 path
_BACKEND_DIR = Path(__file__).resolve().parents[3] / "backend"
if _BACKEND_DIR.exists():
    sys.path.insert(0, str(_BACKEND_DIR))

from app.common.auth import hash_password
from app.infra.config import get_config
from app.infra.database import Base, init_db_engine
from app.domains.governance.models import Role, User, UserRole

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _generate_random_password(length: int = 16) -> str:
    """生成随机初始口令."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def seed():
    config = get_config()
    engine = create_async_engine(config.database.url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # 创建预定义角色
        builtin_roles = [
            {"name": "super_admin", "display_name": "超级管理员",
             "permissions": ["*:*"], "is_builtin": True},
            {"name": "admin", "display_name": "管理员",
             "permissions": ["asset:*", "config:*", "collector:*", "event:*",
                            "alert:*", "policy:*", "automation:*", "log:*",
                            "ticket:*", "knowledge:*"],
             "is_builtin": True},
            {"name": "operator", "display_name": "运维工程师",
             "permissions": ["asset:read", "asset:write", "config:read",
                            "collector:read", "event:read", "alert:*",
                            "policy:read", "automation:execute", "log:read",
                            "ticket:*", "knowledge:read"],
             "is_builtin": True},
            {"name": "viewer", "display_name": "只读查看",
             "permissions": ["asset:read", "config:read", "collector:read",
                            "event:read", "alert:read", "policy:read",
                            "log:read", "ticket:read", "knowledge:read"],
             "is_builtin": True},
            {"name": "ai_operator", "display_name": "AI运维",
             "permissions": ["asset:read", "alert:read", "log:read",
                            "knowledge:*", "aiops:*"],
             "is_builtin": True},
        ]

        for r in builtin_roles:
            from sqlalchemy import select
            q = select(Role).where(Role.name == r["name"])
            existing = (await session.execute(q)).scalar_one_or_none()
            if existing is None:
                role = Role(
                    name=r["name"],
                    display_name=r["display_name"],
                    permissions=json.dumps(r["permissions"]),
                    is_builtin=r["is_builtin"],
                )
                session.add(role)
                print(f"  Created role: {r['name']}")

        await session.flush()

        # 创建默认管理员
        q = select(User).where(User.username == "admin")
        existing = (await session.execute(q)).scalar_one_or_none()
        if existing is None:
            # 初始口令：优先用环境变量 ADMIN_INITIAL_PASSWORD，否则随机生成并打印一次
            initial_password = os.getenv("ADMIN_INITIAL_PASSWORD") or _generate_random_password()
            admin = User(
                username="admin",
                display_name="管理员",
                password_hash=hash_password(initial_password),
            )
            session.add(admin)
            await session.flush()

            # 分配超级管理员角色
            q = select(Role).where(Role.name == "super_admin")
            super_admin_role = (await session.execute(q)).scalar_one()
            session.add(UserRole(user_id=admin.id, role_id=super_admin_role.id))
            print("  Created admin user")
            print(f"  初始口令（仅显示一次，请立即登录修改）: {initial_password}")
        else:
            print("  Admin user already exists")

        await session.commit()
        print("Seed data created successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
