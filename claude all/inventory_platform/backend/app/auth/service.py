"""
Auth Application Service — Supabase edition.

All auth operations (signup, login, logout, password reset)
are delegated to Supabase Auth. The backend:
  1. Verifies the Supabase JWT on protected endpoints
  2. Enriches users with custom roles/permissions stored in app_metadata
  3. Provides an admin API for role assignment

Supabase Auth flow:
  Frontend → supabase.auth.signInWithPassword() → Supabase Auth Server
  → JWT returned to frontend → frontend sends JWT in Authorization header
  → Backend verifies JWT locally using SUPABASE_JWT_SECRET
"""
import asyncio
import uuid
from typing import Optional

from app.infrastructure.supabase.client import get_supabase_admin
from app.domain.exceptions import DuplicateResourceError


SYSTEM_ROLES = {
    "SuperAdmin": [
        "inventory:read", "inventory:write", "inventory:admin",
        "warehouse:read", "warehouse:admin",
        "alerts:read", "alerts:write",
        "analytics:read",
        "audit:read",
        "users:manage",
    ],
    "WarehouseManager": [
        "inventory:read", "inventory:write", "inventory:admin",
        "warehouse:read", "warehouse:admin",
        "alerts:read", "alerts:write",
        "analytics:read", "audit:read",
    ],
    "Technician": [
        "inventory:read", "inventory:write",
        "alerts:read",
        "analytics:read",
    ],
    "Viewer": [
        "inventory:read",
        "warehouse:read",
        "alerts:read",
        "analytics:read",
    ],
}


class AuthService:
    """
    Server-side auth operations using Supabase Admin API.

    Note: Login/signup/logout are handled by the frontend Supabase client.
    This service handles admin operations: role assignment, user management.
    """

    def __init__(self):
        self._admin = get_supabase_admin()

    async def assign_role(self, user_id: str, role: str) -> None:
        """Assign a role to a Supabase user by merging into existing app_metadata."""
        if role not in SYSTEM_ROLES:
            raise ValueError(f"Unknown role: {role}. Valid roles: {list(SYSTEM_ROLES.keys())}")

        permissions = SYSTEM_ROLES[role]
        is_superadmin = role == "SuperAdmin"

        # Read existing metadata first so unrelated fields are preserved
        existing = await asyncio.to_thread(
            self._admin.auth.admin.get_user_by_id, user_id
        )
        existing_meta: dict = {}
        if existing and existing.user:
            existing_meta = existing.user.app_metadata or {}

        merged_meta = {
            **existing_meta,
            "roles": [role],
            "permissions": permissions,
            "is_superadmin": is_superadmin,
        }

        await asyncio.to_thread(
            self._admin.auth.admin.update_user_by_id,
            user_id,
            {"app_metadata": merged_meta},
        )

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        username: str,
        role: str = "Viewer",
    ) -> dict:
        """
        Create a user via Supabase Admin API.
        Auto-assigns default Viewer role.
        """
        if role not in SYSTEM_ROLES:
            raise ValueError(f"Unknown role: {role}. Valid roles: {list(SYSTEM_ROLES.keys())}")
        permissions = SYSTEM_ROLES[role]

        try:
            result = await asyncio.to_thread(
                self._admin.auth.admin.create_user,
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": full_name,
                        "username": username,
                    },
                    "app_metadata": {
                        "roles": [role],
                        "permissions": permissions,
                        "is_superadmin": role == "SuperAdmin",
                    },
                },
            )
        except Exception as e:
            if "already registered" in str(e).lower() or "already exists" in str(e).lower():
                raise DuplicateResourceError("User", "email", email)
            raise

        return {
            "id": result.user.id,
            "email": result.user.email,
            "role": role,
        }

    async def list_users(self, page: int = 1, per_page: int = 50) -> list[dict]:
        """List users with their roles (paginated)."""
        result = await asyncio.to_thread(
            self._admin.auth.admin.list_users,
            page=page,
            per_page=min(per_page, 100),
        )
        users = []
        for u in result:
            app_meta = u.app_metadata or {}
            user_meta = u.user_metadata or {}
            users.append({
                "id": u.id,
                "email": u.email,
                "full_name": user_meta.get("full_name", ""),
                "username": user_meta.get("username", ""),
                "roles": app_meta.get("roles", ["Viewer"]),
                "created_at": str(u.created_at),
            })
        return users

    async def delete_user(self, user_id: str) -> None:
        await asyncio.to_thread(self._admin.auth.admin.delete_user, user_id)
