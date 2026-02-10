from __future__ import annotations

from passlib.context import CryptContext

# Use bcrypt_sha256 to avoid bcrypt's 72-byte password truncation/limit.
# This hashes the password with SHA-256 first, then bcrypts the digest.
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def _bcrypt_compatible_password(password: str) -> str:
    """Normalize password for hashing/verification.

    With bcrypt_sha256 there is no 72-byte password limit, so we can pass
    the password through unchanged.
    """
    return "" if password is None else password


class Hasher:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(_bcrypt_compatible_password(plain_password), hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(_bcrypt_compatible_password(password))
