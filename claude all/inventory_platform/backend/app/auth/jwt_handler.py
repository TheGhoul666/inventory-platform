"""
JWT verification — Supabase edition.

The Supabase EC public key is fetched from the project's JWKS endpoint at
first use and cached in memory. On key rotation, the kid in the token header
won't match any cached key, triggering a one-time re-fetch so the new key is
picked up automatically without a code change or redeploy.

JWKS source: {SUPABASE_URL}/auth/v1/.well-known/jwks.json
"""
import threading

import httpx
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

_lock = threading.Lock()
_cached_keys: list[dict] = []


def _fetch_jwks() -> list[dict]:
    from app.config.settings import get_settings

    url = f"{get_settings().SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    with httpx.Client(timeout=10) as client:
        resp = client.get(url)
        resp.raise_for_status()
    keys: list[dict] = resp.json().get("keys", [])
    if not keys:
        raise RuntimeError(f"No keys returned from Supabase JWKS endpoint: {url}")
    return keys


def _get_key_for_token(token: str) -> dict:
    global _cached_keys
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    with _lock:
        # Try cached keys first
        for k in _cached_keys:
            if k.get("kid") == kid:
                return k
        # kid not found — refresh once and retry
        _cached_keys = _fetch_jwks()
        for k in _cached_keys:
            if k.get("kid") == kid:
                return k

    raise JWTError(f"No matching public key found for kid={kid!r}")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def decode_supabase_token(token: str) -> dict:
    """Verify and decode a Supabase ES256 JWT, auto-refreshing on key rotation."""
    key = _get_key_for_token(token)
    return jwt.decode(token, key, algorithms=["ES256"], audience="authenticated")


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
