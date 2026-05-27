"""
JWT verification — Supabase edition.

Supabase now issues ES256 (ECDSA P-256) JWTs.
Public key is read from the project JWKS endpoint (hardcoded below —
re-run if the Supabase project rotates its signing key).

JWKS source: https://wrspszdkmjdrhupvjblu.supabase.co/auth/v1/.well-known/jwks.json
kid: 2d824240-8929-45c8-8e35-52fa8516579a
"""
import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePublicNumbers,
    SECP256R1,
)
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def _load_supabase_public_key():
    x = int.from_bytes(
        base64.urlsafe_b64decode("5pzaFJURTLMey5MlWviFQX2OqUcn5jTw5wJSNw15j2w=="), "big"
    )
    y = int.from_bytes(
        base64.urlsafe_b64decode("uKt2zZypokvIQ9aIcp7Mtj5v_wSzvmT8bCxAGUKCpS8=="), "big"
    )
    return EllipticCurvePublicNumbers(x, y, SECP256R1()).public_key(default_backend())


_SUPABASE_PUBLIC_KEY = _load_supabase_public_key()


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def decode_supabase_token(token: str) -> dict:
    """Verify and decode a Supabase ES256 JWT using the project's EC public key."""
    return jwt.decode(
        token,
        _SUPABASE_PUBLIC_KEY,
        algorithms=["ES256"],
        audience="authenticated",
    )


def extract_user_from_token(token: str) -> dict:
    payload = decode_supabase_token(token)
    app_meta = payload.get("app_metadata") or {}
    user_meta = payload.get("user_metadata") or {}
    return {
        "sub": payload["sub"],
        "email": payload.get("email", ""),
        "username": user_meta.get("username") or payload.get("email", ""),
        "full_name": user_meta.get("full_name", ""),
        "roles": app_meta.get("roles", []),
        "permissions": app_meta.get("permissions", []),
        "is_superadmin": app_meta.get("is_superadmin", False),
    }
