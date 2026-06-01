"""凭证加密工具."""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.infra.config import get_config


def _get_fernet() -> Fernet:
    """根据主密钥获取 Fernet 实例."""
    config = get_config()
    master_key = config.security.jwt_secret.encode()
    salt = b"AUTOPS_CREDENTIAL_SALT_v1"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key))
    return Fernet(key)


def encrypt_credential(plain: str) -> str:
    """加密凭证."""
    f = _get_fernet()
    return f.encrypt(plain.encode()).decode()


def decrypt_credential(encrypted: str) -> str:
    """解密凭证."""
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()
