"""Unit tests for password hashing and tokens (no database, stdlib only)."""

from app.security import hash_password, hash_token, new_token, verify_password


def test_hash_verifies_right_password_and_rejects_wrong():
    stored = hash_password("secret123")
    assert stored.startswith("scrypt$")
    assert verify_password("secret123", stored) is True
    assert verify_password("secret124", stored) is False
    assert verify_password("", stored) is False


def test_same_password_gets_different_hashes():
    assert hash_password("secret123") != hash_password("secret123")


def test_verify_never_raises_on_garbage():
    for stored in ("", "plain", "scrypt$x", "bcrypt$a$b", "scrypt$!!$??"):
        assert verify_password("secret123", stored) is False


def test_tokens_are_unique_and_hash_is_deterministic():
    tokens = {new_token() for _ in range(100)}
    assert len(tokens) == 100
    token = new_token()
    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != token
    assert len(hash_token(token)) == 64
