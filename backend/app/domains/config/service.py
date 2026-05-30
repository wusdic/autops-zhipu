"""配置中心 Service."""

from __future__ import annotations
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.common.crypto import encrypt_credential, decrypt_credential
from app.common.repository import BaseRepository
from app.domains.config.models import (
    ConfigDefinition, ConfigVersion, ConfigBinding, Credential, CredentialBinding,
)


class ConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.def_repo = BaseRepository(session, ConfigDefinition)
        self.ver_repo = BaseRepository(session, ConfigVersion)
        self.bind_repo = BaseRepository(session, ConfigBinding)
        self.cred_repo = BaseRepository(session, Credential)
        self.cred_bind_repo = BaseRepository(session, CredentialBinding)

    # ConfigDefinition
    async def create_definition(self, name: str, config_type: str, **kw) -> ConfigDefinition:
        existing = await self.session.execute(
            select(ConfigDefinition).where(ConfigDefinition.name == name, ConfigDefinition.is_deleted == False)
        )
        if existing.scalar():
            raise DuplicateError(f"""配置定义 '{name}' 已存在""")
        defn = await self.def_repo.create(name=name, config_type=config_type, **kw)
        await self.session.flush()
        await self.session.refresh(defn)
        return defn

    async def list_definitions(self, config_type: str | None = None, page: int = 1, page_size: int = 20):
        stmt = select(ConfigDefinition).where(ConfigDefinition.is_deleted == False)
        if config_type:
            stmt = stmt.where(ConfigDefinition.config_type == config_type)
        stmt = stmt.order_by(ConfigDefinition.created_at.desc())
        total_result = await self.session.execute(
            select(__import__('sqlalchemy').func.count()).select_from(ConfigDefinition).where(ConfigDefinition.is_deleted == False)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_definition(self, def_id: str) -> ConfigDefinition:
        defn = await self.def_repo.get_by_id(def_id)
        if not defn or defn.is_deleted:
            raise NotFoundError(f"""配置定义 {def_id} 不存在""")
        return defn

    # ConfigVersion
    async def create_version(self, definition_id: str, content: str) -> ConfigVersion:
        defn = await self.get_definition(definition_id)
        # Get latest version number
        result = await self.session.execute(
            select(__import__('sqlalchemy').func.max(ConfigVersion.version)).where(ConfigVersion.definition_id == definition_id)
        )
        max_ver = result.scalar() or 0
        ver = await self.ver_repo.create(definition_id=definition_id, version=max_ver + 1, content=content)
        await self.session.flush()
        await self.session.refresh(ver)
        return ver

    async def publish_version(self, version_id: str, user_id: str | None = None) -> ConfigVersion:
        ver = await self.ver_repo.get_by_id(version_id)
        if not ver:
            raise NotFoundError(f"""版本 {version_id} 不存在""")
        # Archive previous published version
        result = await self.session.execute(
            select(ConfigVersion).where(
                ConfigVersion.definition_id == ver.definition_id,
                ConfigVersion.status == "published",
            )
        )
        for old in result.scalars().all():
            old.status = "archived"
        ver.status = "published"
        from datetime import datetime, timezone
        ver.published_by = user_id
        ver.published_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(ver)
        return ver

    async def list_versions(self, definition_id: str):
        result = await self.session.execute(
            select(ConfigVersion).where(ConfigVersion.definition_id == definition_id)
            .order_by(ConfigVersion.version.desc())
        )
        return list(result.scalars().all())

    # Credential
    async def create_credential(self, name: str, cred_type: str, data: str, **kw) -> Credential:
        existing = await self.session.execute(
            select(Credential).where(Credential.name == name, Credential.is_deleted == False)
        )
        if existing.scalar():
            raise DuplicateError(f"""凭证 '{name}' 已存在""")
        encrypted = encrypt_credential(data)
        cred = await self.cred_repo.create(name=name, cred_type=cred_type, encrypted_data=encrypted, **kw)
        await self.session.flush()
        await self.session.refresh(cred)
        return cred

    async def list_credentials(self, cred_type: str | None = None, page: int = 1, page_size: int = 20):
        stmt = select(Credential).where(Credential.is_deleted == False)
        if cred_type:
            stmt = stmt.where(Credential.cred_type == cred_type)
        stmt = stmt.order_by(Credential.created_at.desc())
        total_result = await self.session.execute(
            select(__import__('sqlalchemy').func.count()).select_from(Credential).where(Credential.is_deleted == False)
        )
        total = total_result.scalar() or 0
        result = await self.session.execute(stmt.offset((page-1)*page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_credential(self, cred_id: str) -> Credential:
        cred = await self.cred_repo.get_by_id(cred_id)
        if not cred or cred.is_deleted:
            raise NotFoundError(f"""凭证 {cred_id} 不存在""")
        return cred

    async def bind_credential(self, credential_id: str, asset_id: str) -> CredentialBinding:
        binding = await self.cred_bind_repo.create(credential_id=credential_id, asset_id=asset_id)
        await self.session.flush()
        await self.session.refresh(binding)
        return binding
