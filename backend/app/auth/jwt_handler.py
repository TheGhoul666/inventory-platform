"""
JWT verification — Supabase edition.

Supports both:
  - ES256 (newer Supabase projects): keys fetched from JWKS endpoint
  - HS256 (older Supabase projects): uses SUPABASE_JWT_SECRET directly

Tries ES256 first; falls back to HS256 automatically.
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
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url)
            resp.raise_for_status()
        return resp.json().get("keys", [])
    except Exception:
        return []


def _get_key_for_token(token: str) -> dict | None:
    global _cached_keys
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            return None

        with _lock:
            for k in _cached_keys:
                if k.get("kid") == kid:
                    return k
            _cached_keys = _fetch_jwks()
            for k in _cached_keys:
                if k.get("kid") == kid:
                    return k
    except Exception:
        pass
    return None


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def decode_supabase_token(token: str) -> dict:
    """Verify and decode a Supabase JWT.

    Tries ES256 via JWKS first (newer projects), then falls back to
    HS256 via SUPABASE_JWT_SECRET (older projects).
    """
    from app.config.settings import get_settings

    # Try ES256 via JWKS
    ec_key = _get_key_for_token(token)
    if ec_key:
        try:
            return jwt.decode(token, ec_key, algorithms=["ES256"], audience="authenticated")
        except JWTError:
            pass

    # Fallback: HS256 with SUPABASE_JWT_SECRET
    secret = get_settings().SUPABASE_JWT_SECRET
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    except JWTError:
        pass

    # Last attempt: HS256 without audience check (some Supabase configs omit it)
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
    except JWTError as e:
        raise JWTError(f"Token verification failed with both ES256 and HS256: {e}") from e


def extract_user_from_token(token: str) -> dict:
    payload = decode_supabase_token(token)
    app_meta = payload.get("app_metadata") or {}
    user_meta = payload.get("user_metadata") or {}
    role_permissions = app_meta.get("permissions", [])
    extra_permissions = app_meta.get("extra_permissions", [])
    return {
        "sub": payload["sub"],
        "email": payload.get("email", ""),
        "username": user_meta.get("username") or payload.get("email", ""),
        "full_name": user_meta.get("full_name", ""),
        "roles": app_meta.get("roles", []),
        "permissions": sorted(set(role_permissions) | set(extra_permissions)),
        "extra_permissions": extra_permissions,
        "is_superadmin": app_meta.get("is_superadmin", False),
    }
