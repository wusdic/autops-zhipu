"""凭证加密工具.

使用独立的 ``CREDENTIAL_ENCRYPT_KEY``（与 JWT 密钥分离）通过 PBKDF2 派生
Fernet 密钥，并为每条凭证生成随机盐（密文格式 ``<salt_b64>:<token>``）。

注意：本实现与旧版（复用 jwt_secret + 固定盐）不兼容，旧密文无法解密。
"""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.infra.config import get_config

# PBKDF2 迭代次数（OWASP 2023 建议 >= 600000，此处取 600000）
_ITERATIONS = 600000
_SALT_LEN = 16


def _master_key() -> bytes:
    """获取凭证加密主密钥（独立于 JWT 密钥）."""
    config = get_config()
    # 优先用独立的 credential_encrypt_key，未配置时回退 jwt_secret（避免启动失败）
    key = config.security.credential_encrypt_key or config.security.jwt_secret
    return key.encode()


def _derive_key(master_key: bytes, salt: bytes) -> bytes:
    """从主密钥 + 盐派生 Fernet 密钥."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_key))


def encrypt_credential(plain: str) -> str:
    """加密凭证.

    每次加密生成随机盐，密文格式为 ``<salt_b64>:<fernet_token>``。
    相同明文每次产生不同密文，且盐随机使离线碰撞失效。
    """
    salt = os.urandom(_SALT_LEN)
    key = _derive_key(_master_key(), salt)
    token = Fernet(key).encrypt(plain.encode()).decode()
    return f"{base64.urlsafe_b64encode(salt).decode()}:{token}"


def decrypt_credential(encrypted: str) -> str:
    """解密凭证.

    密文格式 ``<salt_b64>:<fernet_token>``，用其中携带的盐重新派生密钥。
    """
    if ":" not in encrypted:
        raise ValueError("密文格式非法（缺少盐分隔符）")
    salt_b64, token = encrypted.split(":", 1)
    salt = base64.urlsafe_b64decode(salt_b64)
    key = _derive_key(_master_key(), salt)
    return Fernet(key).decrypt(token.encode()).decode()
