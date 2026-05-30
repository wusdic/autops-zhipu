"""初始化数据种子 - 默认管理员和角色."""

from __future__ import annotations

import asyncio
import json
import sys
sys.path.insert(0, "/home/zcxx/autops/backend")

from app.common.auth import hash_password
from app.infra.config import get_config
from app.infra.database import Base, init_db_engine
from app.domains.governance.models import Role, User, UserRole

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


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
            admin = User(
                username="admin",
                display_name="管理员",
                password_hash=hash_password("admin123"),
            )
            session.add(admin)
            await session.flush()

            # 分配超级管理员角色
            q = select(Role).where(Role.name == "super_admin")
            super_admin_role = (await session.execute(q)).scalar_one()
            session.add(UserRole(user_id=admin.id, role_id=super_admin_role.id))
            print(f"  Created admin user (password: admin123)")
        else:
            print("  Admin user already exists")

        await session.commit()
        print("Seed data created successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
