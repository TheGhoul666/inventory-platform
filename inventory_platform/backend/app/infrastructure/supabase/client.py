"""
Supabase clients — sync (admin/anon) and async (for route handlers).
"""
from functools import lru_cache
from typing import Optional, Any

from supabase import create_client, Client
from app.config.settings import get_settings

settings = get_settings()


@lru_cache
def get_supabase_admin() -> Client:
    """Sync admin client — service_role key, bypasses RLS. Used by AuthService."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@lru_cache
def get_supabase_anon() -> Client:
    """Sync anon client — respects RLS."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


# Lazy async singleton
_async_admin: Optional[Any] = None


async def get_async_admin() -> Any:
    """Async admin client — used by FastAPI route handlers."""
    global _async_admin
    if _async_admin is None:
        from supabase._async.client import create_client as _create
        _async_admin = await _create(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _async_admin


async def get_supabase_db() -> Any:
    """FastAPI dependency that returns the async Supabase admin client."""
    return await get_async_admin()
