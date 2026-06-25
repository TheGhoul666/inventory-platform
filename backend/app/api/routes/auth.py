"""
Auth routes — Supabase edition.

Login/signup/logout are handled by the frontend Supabase JS client.
This router provides user management, role management, and per-user permissions.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user, CurrentUser, require_permission
from app.auth.service import AuthService, ALL_PERMISSIONS
from app.domain.exceptions import DuplicateResourceError
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Request models ────────────────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(default="Viewer")
    phone: Optional[str] = Field(
        default=None,
        max_length=30,
        pattern=r"^\+?1?\d{9,15}$",
        description="International format (e.g. +972501234567)"
    )


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    phone: Optional[str] = Field(
        default=None,
        max_length=30,
        pattern=r"^\+?1?\d{9,15}$",
        description="International format (e.g. +972501234567)"
    )


class AssignRoleRequest(BaseModel):
    role: str


class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)


class UpdatePermissionsRequest(BaseModel):
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)


# ── Identity ──────────────────────────────────────────────────────────────────

@router.get("/me")
async def me(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "roles": current_user.roles,
        "permissions": current_user.permissions,
        "extra_permissions": current_user.extra_permissions,
        "is_superadmin": current_user.is_superadmin,
    }


@router.patch("/me/profile")
async def update_my_profile(
    body: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update the current user's own profile (full_name / username / phone).

    Lets a SuperAdmin set the phone number that receives SMS alerts.
    """
    svc = AuthService()
    result = await svc.update_user_profile(
        str(current_user.id), body.full_name, body.username, body.phone,
    )
    return result


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/roles")
async def list_roles(
    current_user: CurrentUser = Depends(require_permission("users:manage")),
    db: AsyncSession = Depends(get_db),
):
    """List all roles (system + custom) with their permissions."""
    svc = AuthService()
    roles = await svc.get_roles(db)
    return {"roles": roles, "all_permissions": ALL_PERMISSIONS}


@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_role(
    body: CreateRoleRequest,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom role."""
    svc = AuthService()
    try:
        role = await svc.create_custom_role(db, body.name, body.description, body.permissions)
        await svc.log_audit(
            str(current_user.id), current_user.email,
            "create", "role", body.name, f"Created custom role '{body.name}'",
        )
        return role
    except DuplicateResourceError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/roles/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    name: str,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom role (system roles are protected)."""
    svc = AuthService()
    try:
        await svc.delete_custom_role(db, name)
        await svc.log_audit(
            str(current_user.id), current_user.email,
            "delete", "role", name, f"Deleted custom role '{name}'",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    page: int = 1,
    per_page: int = 50,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
):
    """List all users with roles and extra permissions (paginated)."""
    svc = AuthService()
    return {"users": await svc.list_users(page=page, per_page=per_page)}


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Admin: create a new user with an assigned role."""
    svc = AuthService()
    try:
        user = await svc.create_user(
            email=body.email, password=body.password,
            full_name=body.full_name, username=body.username,
            role=body.role, phone=body.phone, db=db,
        )
        await svc.log_audit(
            str(current_user.id), current_user.email,
            "create", "user", user["id"], f"Created user {body.email} with role {body.role}",
        )
        return user
    except DuplicateResourceError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/users/{user_id}/role")
async def assign_role(
    user_id: str,
    body: AssignRoleRequest,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Admin: assign a role to an existing user."""
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    svc = AuthService()
    try:
        await svc.assign_role(user_id, body.role, db=db)
        await svc.log_audit(
            str(current_user.id), current_user.email,
            "update", "user_role", user_id, f"Assigned role '{body.role}'",
        )
        return {"status": "ok", "user_id": user_id, "role": body.role}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.patch("/users/{user_id}/profile")
async def update_user_profile(
    user_id: str,
    body: UpdateProfileRequest,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
):
    """Admin: update a user's profile (full_name / username / phone)."""
    svc = AuthService()
    result = await svc.update_user_profile(
        user_id, body.full_name, body.username, body.phone,
    )
    await svc.log_audit(
        str(current_user.id), current_user.email,
        "update", "user_profile", user_id,
        f"Updated profile (phone set: {bool(body.phone)})",
    )
    return result


@router.patch("/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: str,
    body: UpdatePermissionsRequest,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
):
    """Admin: grant or revoke individual permissions for a user beyond their role."""
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot modify your own extra permissions")
    svc = AuthService()
    result = await svc.update_user_extra_permissions(user_id, body.add, body.remove)
    await svc.log_audit(
        str(current_user.id), current_user.email,
        "update", "user_permissions", user_id,
        f"add={body.add} remove={body.remove}",
    )
    return result


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
):
    """Admin: permanently delete a user."""
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    svc = AuthService()
    await svc.delete_user(user_id)
    await svc.log_audit(
        str(current_user.id), current_user.email,
        "delete", "user", user_id, "User deleted",
    )


# ── Bootstrap (first-time setup) ─────────────────────────────────────────────

@router.post("/bootstrap-admin", status_code=200)
async def bootstrap_admin():
    """
    One-time endpoint: promotes the FIRST registered Supabase user to SuperAdmin.
    Disabled automatically once any SuperAdmin already exists.
    Call this after your first sign-up via the login page.
    No authentication required (by design — used before any admin exists).
    """
    svc = AuthService()
    users = await svc.list_users(page=1, per_page=100)

    # Check if any SuperAdmin already exists
    admins = [u for u in users if "SuperAdmin" in u.get("roles", [])]
    if admins:
        raise HTTPException(
            status_code=409,
            detail="Bootstrap already complete — a SuperAdmin already exists. Use the Permissions page to manage users.",
        )

    if not users:
        raise HTTPException(
            status_code=404,
            detail="No users found. Register an account via the login page first, then call this endpoint.",
        )

    # Promote the first user (oldest) to SuperAdmin — no DB needed for system roles
    first_user = users[0]
    await svc.assign_role(first_user["id"], "SuperAdmin")  # db not needed for system roles

    return {
        "message": "Bootstrap complete",
        "promoted_user": first_user["email"],
        "role": "SuperAdmin",
        "next_step": "Log out and log back in so your session picks up the new permissions.",
    }
