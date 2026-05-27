"""
FastAPI dependency: verify Supabase JWT and resolve current user.

Usage:
  current_user: CurrentUser = Depends(get_current_user)
  current_user: CurrentUser = Depends(require_permission("inventory:write"))

The token is a standard Supabase JWT sent in the Authorization header:
  Authorization: Bearer <supabase_access_token>

Verification is LOCAL — uses SUPABASE_JWT_SECRET, no network call.
"""
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth.jwt_handler import extract_user_from_token

security = HTTPBearer(auto_error=True)


class CurrentUser:
    """Principal resolved from a verified Supabase JWT."""

    def __init__(self, data: dict):
        self.id = uuid.UUID(data["sub"])
        self.email: str = data["email"]
        self.username: str = data.get("username", "")
        self.full_name: str = data.get("full_name", "")
        self.roles: list[str] = data.get("roles", [])
        self.permissions: list[str] = data.get("permissions", [])
        self.is_superadmin: bool = data.get("is_superadmin", False)

    def has_permission(self, permission: str) -> bool:
        if self.is_superadmin or "*" in self.permissions:
            return True
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        return role in self.roles


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)]
) -> CurrentUser:
    """Verify Supabase JWT and return the resolved principal."""
    try:
        data = extract_user_from_token(credentials.credentials)
        return CurrentUser(data)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(permission: str):
    """Permission-checking dependency factory."""
    async def _guard(
        current_user: Annotated[CurrentUser, Depends(get_current_user)]
    ) -> CurrentUser:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return current_user
    return _guard


def require_role(role: str):
    async def _guard(
        current_user: Annotated[CurrentUser, Depends(get_current_user)]
    ) -> CurrentUser:
        if not current_user.has_role(role) and not current_user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return current_user
    return _guard


# Pre-built permission shortcuts
RequireInventoryRead = Depends(require_permission("inventory:read"))
RequireInventoryWrite = Depends(require_permission("inventory:write"))
RequireWarehouseAdmin = Depends(require_permission("warehouse:admin"))
RequireSuperAdmin = Depends(require_role("SuperAdmin"))
