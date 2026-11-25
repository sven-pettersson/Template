"""Password hashing and session tokens (standard library only)."""

import base64
import hashlib
import hmac
import secrets

# scrypt parameters: n=2**14, r=8, p=1 uses about 16 MB and is fast enough
# for a login request while being expensive to brute force.
_N, _R, _P, _DKLEN = 2**14, 8, 1, 32


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _scrypt(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN
    )


def hash_password(password: str) -> str:
    """Return 'scrypt$<salt>$<hash>' with a random salt."""
    salt = secrets.token_bytes(16)
    return f"scrypt${_b64(salt)}${_b64(_scrypt(password, salt))}"


def verify_password(password: str, stored: str) -> bool:
    """True if password matches a hash from hash_password. Never raises."""
    try:
        scheme, salt, expected = stored.split("$")
        if scheme != "scrypt":
            return False
        actual = _scrypt(password, base64.b64decode(salt))
        return hmac.compare_digest(actual, base64.b64decode(expected))
    except (ValueError, TypeError, AttributeError):
        return False


def new_token() -> str:
    """Random session token given to the client."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Only this hash is stored, so a leaked database does not leak tokens."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
