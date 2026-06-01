"""JWT 认证工具."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.common.exceptions import UnauthorizedError
from app.infra.config import get_config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密码哈希."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """密码验证."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建 Access Token."""
    config = get_config()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=config.security.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, config.security.jwt_secret, algorithm=config.security.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """创建 Refresh Token."""
    config = get_config()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=config.security.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, config.security.jwt_secret, algorithm=config.security.jwt_algorithm)


def decode_token(token: str) -> dict:
    """解码 Token."""
    config = get_config()
    try:
        payload = jwt.decode(token, config.security.jwt_secret, algorithms=[config.security.jwt_algorithm])
        return payload
    except JWTError:
        raise UnauthorizedError("Token 无效或已过期")
