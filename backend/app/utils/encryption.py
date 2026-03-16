import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings


def _get_fernet_key() -> bytes:
    encryption_key = settings.ENCRYPTION_KEY.encode()
    salt = b"moremoney_salt_2024"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(encryption_key))
    return key


_fernet: Fernet = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_fernet_key())
    return _fernet


def encrypt_api_key(api_key: str) -> bytes:
    fernet = get_fernet()
    return fernet.encrypt(api_key.encode())


def decrypt_api_key(encrypted_key: bytes) -> str:
    fernet = get_fernet()
    return fernet.decrypt(encrypted_key).decode()


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}****{api_key[-4:]}"
