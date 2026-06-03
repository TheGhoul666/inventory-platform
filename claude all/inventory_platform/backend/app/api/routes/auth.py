"""
Auth routes — Supabase edition.

Login/signup/logout are handled by the frontend Supabase JS client.
This router provides:
  - Admin user creation (with role assignment)
  - Role management
  - User listing

The frontend calls supabase.auth.signInWithPassword() directly.
The resulting access_token is sent to the backend as a Bearer token.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.api.dependencies.auth import get_current_user, CurrentUser, require_permission
from app.auth.service import AuthService
from app.domain.exceptions import DuplicateResourceError

router = APIRouter(prefix="/auth", tags=["Authentication"])


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(default="Viewer")


class AssignRoleRequest(BaseModel):
    role: str


@router.get("/me")
async def me(current_user: CurrentUser = Depends(get_current_user)):
    """Return the current user's identity from their JWT."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "roles": current_user.roles,
        "permissions": current_user.permissions,
        "is_superadmin": current_user.is_superadmin,
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
):
    """Admin: create a new user with an assigned role."""
    svc = AuthService()
    try:
        user = await svc.create_user(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            username=body.username,
            role=body.role,
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
):
    """Admin: assign a role to an existing user."""
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )
    svc = AuthService()
    try:
        await svc.assign_role(user_id, body.role)
        return {"status": "ok", "user_id": user_id, "role": body.role}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/users")
async def list_users(
    page: int = 1,
    per_page: int = 50,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
):
    """Admin: list all users with their roles (paginated)."""
    svc = AuthService()
    return {"users": await svc.list_users(page=page, per_page=per_page)}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_permission("users:manage")),
):
    """Admin: permanently delete a user."""
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    svc = AuthService()
    await svc.delete_user(user_id)
