"""User and Auth Repository."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.user import User, Role, Permission, RefreshToken


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self._session.execute(
            select(User)
            .where(User.id == user_id, User.is_deleted == False)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(User)
            .where(User.email == email, User.is_deleted == False)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self._session.execute(
            select(User)
            .where(User.username == username, User.is_deleted == False)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_last_login(self, user_id: uuid.UUID, at: datetime) -> None:
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=at, failed_login_count=0)
        )

    async def increment_failed_login(self, user_id: uuid.UUID) -> None:
        from sqlalchemy import text
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(failed_login_count=User.failed_login_count + 1)
        )

    async def lock_account(self, user_id: uuid.UUID, until: datetime) -> None:
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(locked_until=until)
        )

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        result = await self._session.execute(
            select(Role)
            .where(Role.name == name)
            .options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def create_role(self, role: Role) -> Role:
        self._session.add(role)
        await self._session.flush()
        return role


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, token: RefreshToken) -> RefreshToken:
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self._session.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked == False)
            .options(selectinload(RefreshToken.user).selectinload(User.roles).selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_hash: str) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True)
        )

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
