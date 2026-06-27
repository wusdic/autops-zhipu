"""配置中心 Service."""

from __future__ import annotations
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.common.crypto import encrypt_credential
from app.common.repository import BaseRepository
from app.domains.config.models import (
    ConfigDefinition,
    ConfigVersion,
    ConfigBinding,
    Credential,
    CredentialBinding,
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
    async def create_definition(
        self, name: str, config_type: str, **kw
    ) -> ConfigDefinition:
        existing = await self.session.execute(
            select(ConfigDefinition).where(
                ConfigDefinition.name == name, ConfigDefinition.is_deleted == False
            )
        )
        if existing.scalar():
            raise DuplicateError(f"""配置定义 '{name}' 已存在""")
        defn = await self.def_repo.create(name=name, config_type=config_type, **kw)
        await self.session.flush()
        await self.session.refresh(defn)
        return defn

    async def list_definitions(
        self, config_type: str | None = None, page: int = 1, page_size: int = 20
    ):
        from sqlalchemy import func

        stmt = select(ConfigDefinition).where(ConfigDefinition.is_deleted == False)
        count_stmt = (
            select(func.count())
            .select_from(ConfigDefinition)
            .where(ConfigDefinition.is_deleted == False)
        )
        if config_type:
            stmt = stmt.where(ConfigDefinition.config_type == config_type)
            count_stmt = count_stmt.where(ConfigDefinition.config_type == config_type)
        stmt = stmt.order_by(ConfigDefinition.created_at.desc())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        result = await self.session.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        )
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
            select(__import__("sqlalchemy").func.max(ConfigVersion.version)).where(
                ConfigVersion.definition_id == definition_id
            )
        )
        max_ver = result.scalar() or 0
        ver = await self.ver_repo.create(
            definition_id=definition_id, version=max_ver + 1, content=content
        )
        await self.session.flush()
        await self.session.refresh(ver)
        return ver

    async def publish_version(
        self, version_id: str, user_id: str | None = None
    ) -> ConfigVersion:
        ver = await self.ver_repo.get_by_id(version_id)
        if not ver:
            raise NotFoundError(f"""版本 {version_id} 不存在""")
        # 行锁防止并发发布产生多个 published 版本（archive 旧 published + 置新 published
        # 必须原子完成）
        result = await self.session.execute(
            select(ConfigVersion)
            .where(
                ConfigVersion.definition_id == ver.definition_id,
                ConfigVersion.status == "published",
            )
            .with_for_update()
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
            select(ConfigVersion)
            .where(ConfigVersion.definition_id == definition_id)
            .order_by(ConfigVersion.version.desc())
        )
        return list(result.scalars().all())

    async def diff_versions(
        self, definition_id: str, version_id_a: str, version_id_b: str
    ) -> dict:
        """对比两个配置版本的差异."""
        import difflib

        va = await self.session.get(ConfigVersion, version_id_a)
        vb = await self.session.get(ConfigVersion, version_id_b)
        if not va or not vb:
            raise NotFoundError("配置版本不存在")
        try:
            content_a = (
                json.loads(va.content) if isinstance(va.content, str) else va.content
            )
            content_b = (
                json.loads(vb.content) if isinstance(vb.content, str) else vb.content
            )
        except Exception:
            content_a = va.content
            content_b = vb.content
        # 对比
        lines_a = json.dumps(content_a, indent=2, ensure_ascii=False).splitlines(
            keepends=True
        )
        lines_b = json.dumps(content_b, indent=2, ensure_ascii=False).splitlines(
            keepends=True
        )
        diff = difflib.unified_diff(
            lines_a, lines_b, fromfile=f"v{va.version}", tofile=f"v{vb.version}"
        )
        return {
            "definition_id": definition_id,
            "version_a": {"id": str(va.id), "version": va.version, "status": va.status},
            "version_b": {"id": str(vb.id), "version": vb.version, "status": vb.status},
            "diff": "".join(diff),
            "has_changes": content_a != content_b,
        }

    async def rollback_version(
        self, definition_id: str, target_version_id: str, user_id: str = ""
    ) -> ConfigVersion:
        """回滚配置到指定版本（创建新版本并自动发布）."""
        target = await self.session.get(ConfigVersion, target_version_id)
        if not target or str(target.definition_id) != definition_id:
            raise NotFoundError("目标版本不存在或不属于该配置定义")
        # 获取当前最大版本号
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.max(ConfigVersion.version)).where(
                ConfigVersion.definition_id == definition_id
            )
        )
        max_ver = result.scalar() or 0
        # 创建新版本（内容从目标版本复制），先置 draft，再复用 publish_version 的
        # 归档逻辑发布——保证同一 definition 只有一个 published 版本（修复回滚后
        # 可能出现多个 published 的问题）。
        new_version = ConfigVersion(
            definition_id=definition_id,
            version=max_ver + 1,
            content=target.content,
            status="draft",
        )
        self.session.add(new_version)
        await self.session.flush()
        await self.session.refresh(new_version)
        return await self.publish_version(str(new_version.id), user_id)

    async def detect_drift(self, definition_id: str) -> dict:
        """检测配置漂移."""
        # 获取最新发布的版本
        result = await self.session.execute(
            select(ConfigVersion)
            .where(
                ConfigVersion.definition_id == definition_id,
                ConfigVersion.status == "published",
            )
            .order_by(ConfigVersion.version.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        if not latest:
            return {
                "definition_id": definition_id,
                "has_drift": False,
                "message": "无已发布版本",
            }
        # 获取该 definition 下所有版本的绑定（而非只查已绑定到最新版本的绑定——
        # 后者逻辑上永远查不出漂移）。再逐个与最新发布版本比较。
        ver_ids_result = await self.session.execute(
            select(ConfigVersion.id).where(
                ConfigVersion.definition_id == definition_id
            )
        )
        ver_ids = [str(v) for v in ver_ids_result.scalars().all()]
        bindings = []
        if ver_ids:
            result = await self.session.execute(
                select(ConfigBinding).where(ConfigBinding.version_id.in_(ver_ids))
            )
            bindings = result.scalars().all()
        # 检查是否有绑定指向非最新版本（即存在漂移）
        drifted = []
        for binding in bindings:
            if str(binding.version_id) != str(latest.id):
                drifted.append(
                    {
                        "binding_id": str(binding.id),
                        "target_type": binding.target_type,
                        "target_id": binding.target_id,
                        "bound_version": str(binding.version_id),
                        "latest_version": str(latest.id),
                    }
                )
        return {
            "definition_id": definition_id,
            "latest_version": {"id": str(latest.id), "version": latest.version},
            "has_drift": len(drifted) > 0,
            "drifted_bindings": drifted,
        }

    # Credential
    async def create_credential(
        self, name: str, cred_type: str, data: str, **kw
    ) -> Credential:
        existing = await self.session.execute(
            select(Credential).where(
                Credential.name == name, Credential.is_deleted == False
            )
        )
        if existing.scalar():
            raise DuplicateError(f"""凭证 '{name}' 已存在""")
        encrypted = encrypt_credential(data)
        cred = await self.cred_repo.create(
            name=name, cred_type=cred_type, encrypted_data=encrypted, **kw
        )
        await self.session.flush()
        await self.session.refresh(cred)
        return cred

    async def list_credentials(
        self, cred_type: str | None = None, page: int = 1, page_size: int = 20
    ):
        from sqlalchemy import func

        stmt = select(Credential).where(Credential.is_deleted == False)
        count_stmt = (
            select(func.count())
            .select_from(Credential)
            .where(Credential.is_deleted == False)
        )
        if cred_type:
            stmt = stmt.where(Credential.cred_type == cred_type)
            count_stmt = count_stmt.where(Credential.cred_type == cred_type)
        stmt = stmt.order_by(Credential.created_at.desc())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        result = await self.session.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_credential(self, cred_id: str) -> Credential:
        cred = await self.cred_repo.get_by_id(cred_id)
        if not cred or cred.is_deleted:
            raise NotFoundError(f"""凭证 {cred_id} 不存在""")
        return cred

    async def update_credential(
        self, cred_id: str, name: str | None = None,
        description: str | None = None, data: str | None = None,
    ) -> Credential:
        cred = await self.get_credential(cred_id)
        if name is not None:
            cred.name = name
        if description is not None:
            cred.description = description
        if data:
            cred.encrypted_data = encrypt_credential(data)
            cred.test_status = "unknown"
        await self.session.flush()
        await self.session.refresh(cred)
        return cred

    async def delete_credential(self, cred_id: str) -> None:
        cred = await self.get_credential(cred_id)
        cred.is_deleted = True
        await self.session.flush()

    async def bind_credential(
        self, credential_id: str, asset_id: str
    ) -> CredentialBinding:
        binding = await self.cred_bind_repo.create(
            credential_id=credential_id, asset_id=asset_id
        )
        await self.session.flush()
        await self.session.refresh(binding)
        return binding

    async def get_inheritance(self) -> dict:
        """获取配置继承关系."""
        # Get all definitions with their versions and bindings
        defn_result = await self.session.execute(
            select(ConfigDefinition).where(ConfigDefinition.is_deleted == False)
        )
        definitions = defn_result.scalars().all()
        inheritance = []
        for d in definitions:
            ver_result = await self.session.execute(
                select(ConfigVersion).where(ConfigVersion.definition_id == d.id)
            )
            versions = ver_result.scalars().all()
            bindings_for_def = []
            for v in versions:
                binding_result = await self.session.execute(
                    select(ConfigBinding).where(ConfigBinding.version_id == v.id)
                )
                bindings = binding_result.scalars().all()
                for b in bindings:
                    bindings_for_def.append(
                        {
                            "id": b.id,
                            "version_id": b.version_id,
                            "target_type": b.target_type,
                            "target_id": b.target_id,
                        }
                    )
            inheritance.append(
                {
                    "definition_id": d.id,
                    "name": d.name,
                    "config_type": d.config_type,
                    "versions": [
                        {"id": v.id, "version": v.version, "status": v.status}
                        for v in versions
                    ],
                    "bindings": bindings_for_def,
                }
            )
        return {"inheritance": inheritance}
