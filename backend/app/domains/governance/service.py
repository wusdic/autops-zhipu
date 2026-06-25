"""治理中心 Service."""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.common.exceptions import (
    DuplicateError,
    NotFoundError,
    PermissionDeniedError,
    UnauthorizedError,
)
from app.domains.governance.models import ApiKey, User, UserRole
from app.domains.governance.schemas import (
    ApiKeyCreate,
    LoginRequest,
    UserCreate,
    UserUpdate,
)


class AuthService:
    """认证服务."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def login(self, data: LoginRequest, ip: str | None = None) -> dict:
        q = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.username == data.username, User.is_deleted == False)  # noqa
        )
        result = await self.session.execute(q)
        user = result.scalar_one_or_none()

        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("用户名或密码错误")
        if user.status != "active":
            raise UnauthorizedError("账户已禁用")

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()

        access = create_access_token({"sub": user.id, "username": user.username})
        refresh = create_refresh_token({"sub": user.id})
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }

    async def get_current_user(self, token: str) -> User:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError()
        # 预加载 roles 关系，避免 async 上下文 lazy-load 报错
        result = await self.session.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None or user.is_deleted or user.status != "active":
            raise UnauthorizedError()
        return user

    async def refresh_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("无效的 refresh token")
        user_id = payload.get("sub")
        user = await self.session.get(User, user_id)
        if user is None or user.status != "active":
            raise UnauthorizedError()
        access = create_access_token({"sub": user.id, "username": user.username})
        return {"access_token": access, "token_type": "bearer"}


class UserService:
    """用户管理服务."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, data: UserCreate) -> User:
        q = select(User).where(User.username == data.username)
        result = await self.session.execute(q)
        if result.scalar_one_or_none():
            raise DuplicateError(f"用户名 '{data.username}' 已存在")

        user = User(
            username=data.username,
            display_name=data.display_name,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        self.session.add(user)
        await self.session.flush()

        if data.role_ids:
            for rid in data.role_ids:
                self.session.add(UserRole(user_id=user.id, role_id=rid))
            await self.session.flush()
        return user

    async def list_users(self, page: int = 1, page_size: int = 20):
        from app.common.repository import BaseRepository

        repo = BaseRepository(User, self.session)
        return await repo.get_multi(
            page=page,
            page_size=page_size,
            filters=[User.is_deleted == False],  # noqa
            order_by=User.created_at.desc(),
        )

    async def get_user(self, user_id: str) -> User:
        user = await self.session.get(User, user_id)
        if user is None or user.is_deleted:
            raise NotFoundError("用户不存在")
        return user

    async def update_user(self, user_id: str, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        updates = data.model_dump(exclude_unset=True, exclude_none=True)
        role_ids = updates.pop("role_ids", None)
        for key, value in updates.items():
            setattr(user, key, value)
        if role_ids is not None:
            await self.session.execute(
                UserRole.__table__.delete().where(UserRole.user_id == user_id)
            )
            for rid in role_ids:
                self.session.add(UserRole(user_id=user_id, role_id=rid))
        await self.session.flush()
        return user

    async def delete_user(self, user_id: str) -> None:
        user = await self.get_user(user_id)
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def change_password(self, user_id: str, old_pw: str, new_pw: str) -> None:
        user = await self.get_user(user_id)
        if not verify_password(old_pw, user.password_hash):
            raise PermissionDeniedError("旧密码错误")
        user.password_hash = hash_password(new_pw)
        await self.session.flush()


class ApiKeyService:
    """API Key 服务."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_key(self, user_id: str, data: ApiKeyCreate) -> tuple[ApiKey, str]:
        raw_key = f"ak_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]
        expires_at = None
        if data.expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_days)

        api_key = ApiKey(
            name=data.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            user_id=user_id,
            scope=json.dumps(data.scope),
            expires_at=expires_at,
        )
        self.session.add(api_key)
        await self.session.flush()
        return api_key, raw_key

    async def list_keys(self, user_id: str):
        q = select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.status == "active")
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def revoke_key(self, key_id: str, user_id: str) -> None:
        key = await self.session.get(ApiKey, key_id)
        if key is None or key.user_id != user_id:
            raise NotFoundError("API Key 不存在")
        key.status = "revoked"
        await self.session.flush()

    async def update_key(self, key_id: str, user_id: str, **kwargs) -> ApiKey:
        """部分更新 API Key."""
        key = await self.session.get(ApiKey, key_id)
        if key is None or key.user_id != user_id:
            raise NotFoundError("API Key 不存在")
        if key.status != "active":
            raise PermissionDeniedError("只能更新活跃状态的 API Key")
        for k, v in kwargs.items():
            if v is not None:
                if k == "scope":
                    setattr(key, k, json.dumps(v))
                else:
                    setattr(key, k, v)
        await self.session.flush()
        await self.session.refresh(key)
        return key
