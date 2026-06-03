"""
Auth Application Service — Supabase edition.

System roles are code-defined (SYSTEM_ROLES dict).
Custom roles are stored in the PostgreSQL roles/permissions tables.
Per-user extra permissions are stored in Supabase app_metadata.extra_permissions.
"""
import asyncio
import uuid as _uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.supabase.client import get_supabase_admin
from app.domain.exceptions import DuplicateResourceError
from app.domain.models.user import Role, Permission


SYSTEM_ROLES: dict[str, list[str]] = {
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

ALL_PERMISSIONS: list[str] = sorted({p for perms in SYSTEM_ROLES.values() for p in perms})


class AuthService:
    """Server-side auth operations using the Supabase Admin API."""

    def __init__(self) -> None:
        self._admin = get_supabase_admin()

    # ── Roles ──────────────────────────────────────────────────────────────

    async def get_roles(self, db: AsyncSession) -> list[dict]:
        """Returns system roles (code-defined) + custom roles (DB-stored)."""
        result = []
        for name, perms in SYSTEM_ROLES.items():
            result.append({"name": name, "permissions": perms, "is_system": True, "description": None})

        stmt = select(Role).where(Role.is_system_role == False).options(selectinload(Role.permissions))
        rows = (await db.scalars(stmt)).all()
        for role in rows:
            result.append({
                "name": role.name,
                "permissions": [p.name for p in role.permissions],
                "is_system": False,
                "description": role.description,
            })
        return result

    async def create_custom_role(
        self,
        db: AsyncSession,
        name: str,
        description: Optional[str],
        permission_names: list[str],
    ) -> dict:
        """Creates a custom role in the PostgreSQL DB."""
        if name in SYSTEM_ROLES:
            raise ValueError(f"'{name}' conflicts with a system role name")

        existing = await db.scalar(select(Role).where(Role.name == name))
        if existing:
            raise DuplicateResourceError("Role", "name", name)

        permissions: list[Permission] = []
        for pname in permission_names:
            p = await db.scalar(select(Permission).where(Permission.name == pname))
            if p is None:
                parts = pname.split(":", 1)
                p = Permission(
                    name=pname,
                    resource=parts[0],
                    action=parts[1] if len(parts) > 1 else "access",
                )
                db.add(p)
                await db.flush()
            permissions.append(p)

        role = Role(name=name, description=description, is_system_role=False)
        role.permissions = permissions
        db.add(role)
        await db.flush()
        return {
            "name": name,
            "permissions": permission_names,
            "is_system": False,
            "description": description,
        }

    async def delete_custom_role(self, db: AsyncSession, name: str) -> None:
        """Deletes a custom role. System roles cannot be deleted."""
        if name in SYSTEM_ROLES:
            raise ValueError("Cannot delete a system role")
        role = await db.scalar(select(Role).where(Role.name == name))
        if role is None:
            raise ValueError(f"Role '{name}' not found")
        await db.delete(role)

    # ── Role assignment & per-user permissions ──────────────────────────────

    async def assign_role(
        self,
        user_id: str,
        role: str,
        db: Optional[AsyncSession] = None,
    ) -> None:
        """Assign a role (system or custom) to a Supabase user."""
        if role in SYSTEM_ROLES:
            permissions = SYSTEM_ROLES[role]
        elif db is not None:
            role_obj = await db.scalar(
                select(Role).where(Role.name == role).options(selectinload(Role.permissions))
            )
            if role_obj is None:
                raise ValueError(f"Unknown role: {role}")
            permissions = [p.name for p in role_obj.permissions]
        else:
            raise ValueError(f"Unknown role: {role}. Valid system roles: {list(SYSTEM_ROLES.keys())}")

        is_superadmin = role == "SuperAdmin"

        existing = await asyncio.to_thread(self._admin.auth.admin.get_user_by_id, user_id)
        existing_meta: dict = {}
        if existing and existing.user:
            existing_meta = existing.user.app_metadata or {}

        await asyncio.to_thread(
            self._admin.auth.admin.update_user_by_id,
            user_id,
            {"app_metadata": {**existing_meta, "roles": [role], "permissions": permissions, "is_superadmin": is_superadmin}},
        )

    async def update_user_extra_permissions(
        self, user_id: str, add: list[str], remove: list[str]
    ) -> dict:
        """Grants/revokes individual permissions for a user beyond their role."""
        existing = await asyncio.to_thread(self._admin.auth.admin.get_user_by_id, user_id)
        existing_meta: dict = {}
        if existing and existing.user:
            existing_meta = existing.user.app_metadata or {}

        current: set[str] = set(existing_meta.get("extra_permissions", []))
        current.update(add)
        current.difference_update(remove)

        await asyncio.to_thread(
            self._admin.auth.admin.update_user_by_id,
            user_id,
            {"app_metadata": {**existing_meta, "extra_permissions": sorted(current)}},
        )
        return {"extra_permissions": sorted(current)}

    # ── User CRUD ──────────────────────────────────────────────────────────

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        username: str,
        role: str = "Viewer",
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Create a user via Supabase Admin API with role assignment."""
        if role in SYSTEM_ROLES:
            permissions = SYSTEM_ROLES[role]
        elif db is not None:
            role_obj = await db.scalar(
                select(Role).where(Role.name == role).options(selectinload(Role.permissions))
            )
            if role_obj is None:
                raise ValueError(f"Unknown role: {role}. Valid system roles: {list(SYSTEM_ROLES.keys())}")
            permissions = [p.name for p in role_obj.permissions]
        else:
            raise ValueError(f"Unknown role: {role}. Valid roles: {list(SYSTEM_ROLES.keys())}")

        try:
            result = await asyncio.to_thread(
                self._admin.auth.admin.create_user,
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"full_name": full_name, "username": username},
                    "app_metadata": {
                        "roles": [role],
                        "permissions": permissions,
                        "is_superadmin": role == "SuperAdmin",
                        "extra_permissions": [],
                    },
                },
            )
        except Exception as e:
            if "already registered" in str(e).lower() or "already exists" in str(e).lower():
                raise DuplicateResourceError("User", "email", email)
            raise

        return {"id": result.user.id, "email": result.user.email, "roles": [role]}

    async def list_users(self, page: int = 1, per_page: int = 50) -> list[dict]:
        """List users with roles and extra permissions (paginated)."""
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
                "permissions": app_meta.get("permissions", []),
                "extra_permissions": app_meta.get("extra_permissions", []),
                "created_at": str(u.created_at),
            })
        return users

    async def delete_user(self, user_id: str) -> None:
        await asyncio.to_thread(self._admin.auth.admin.delete_user, user_id)

    # ── Audit ──────────────────────────────────────────────────────────────

    async def log_audit(
        self,
        actor_id: str,
        actor_email: str,
        action: str,
        resource_type: str,
        resource_id: str,
        notes: str,
    ) -> None:
        """Writes a permission-change audit entry to Supabase. Never raises."""
        try:
            await asyncio.to_thread(
                lambda: self._admin.table("audit_logs").insert({
                    "id": str(_uuid.uuid4()),
                    "user_id": actor_id,
                    "username": actor_email,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "notes": notes,
                }).execute()
            )
        except Exception:
            pass
