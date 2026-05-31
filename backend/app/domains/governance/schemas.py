"""治理中心 Schema."""

from __future__ import annotations

from datetime import datetime

import json

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6)
    display_name: str = Field(..., min_length=1, max_length=64)
    email: str | None = None
    role_ids: list[str] | None = None


class UserUpdate(BaseModel):
    display_name: str | None = None
    email: str | None = None
    status: str | None = None
    role_ids: list[str] | None = None


class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    email: str | None
    status: str
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=64)
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)


class RoleResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str | None
    permissions: list[str]
    is_builtin: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_permissions(cls, data):
        if hasattr(data, "permissions"):
            # SQLAlchemy model instance
            raw = data.permissions
            if isinstance(raw, str):
                object.__setattr__(data, "permissions", json.loads(raw))
        elif isinstance(data, dict):
            raw = data.get("permissions")
            if isinstance(raw, str):
                data["permissions"] = json.loads(raw)
        return data


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    scope: list[str] = Field(default_factory=list)
    expires_days: int | None = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scope: list[str]
    status: str
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreateResponse(ApiKeyResponse):
    key: str  # 只在创建时返回一次
