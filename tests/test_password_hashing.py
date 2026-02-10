import pytest

from src.infrastructure.security.hashing import Hasher


def test_hash_and_verify_happy_path():
    pw = "chin@123"
    hashed = Hasher.get_password_hash(pw)
    assert Hasher.verify_password(pw, hashed)
    assert not Hasher.verify_password("wrong-password", hashed)


def test_long_password_does_not_crash_and_verifies_consistently():
    # > 72 bytes when encoded
    pw = "a" * 200
    hashed = Hasher.get_password_hash(pw)
    assert Hasher.verify_password(pw, hashed)


def test_multibyte_password_truncation_is_safe_and_consistent():
    # Each char is 4 bytes in UTF-8, so this exceeds 72 bytes.
    pw = "🔥" * 30
    assert len(pw.encode("utf-8")) > 72

    hashed = Hasher.get_password_hash(pw)
    assert Hasher.verify_password(pw, hashed)

