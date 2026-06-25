"""
Pytest configuration and fixtures.

Uses an in-memory SQLite async engine for unit tests,
and a real PostgreSQL instance for integration/concurrency tests
(controlled by TEST_DATABASE_URL environment variable).
"""
import asyncio
import uuid
from decimal import Decimal
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import create_app
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import get_db
from app.domain.models.user import User, Role, Permission
from app.domain.models.warehouse import Warehouse
from app.domain.models.inventory import InventoryItem
from app.auth.jwt_handler import hash_password


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def app(db_session):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db_session
    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# --- Data fixtures ---

@pytest_asyncio.fixture
async def test_warehouse(db_session) -> Warehouse:
    wh = Warehouse(
        id=uuid.uuid4(),
        name="Test Depot",
        code="TD01",
        country="IL",
        is_active=True,
    )
    db_session.add(wh)
    await db_session.flush()
    return wh


@pytest_asyncio.fixture
async def test_user(db_session, test_warehouse) -> User:
    role = Role(id=uuid.uuid4(), name="Technician", is_system_role=True)
    perm_read = Permission(id=uuid.uuid4(), name="inventory:read", resource="inventory", action="read")
    perm_write = Permission(id=uuid.uuid4(), name="inventory:write", resource="inventory", action="write")
    role.permissions = [perm_read, perm_write]

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superadmin=False,
        warehouse_id=test_warehouse.id,
    )
    user.roles = [role]
    db_session.add(role)
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user) -> dict:
    # Supabase auth is used in production; tests that need HTTP auth
    # must supply a real Supabase token via TEST_SUPABASE_TOKEN env var.
    import os
    token = os.getenv("TEST_SUPABASE_TOKEN", "test-token-placeholder")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_item(db_session, test_warehouse) -> InventoryItem:
    item = InventoryItem(
        id=uuid.uuid4(),
        sku="TEST-BRAKE-001",
        name="Brake Pad Set",
        unit="set",
        quantity=Decimal("100"),
        reserved_quantity=Decimal("0"),
        low_stock_threshold=Decimal("10"),
        critical_stock_threshold=Decimal("3"),
        reorder_quantity=Decimal("50"),
        warehouse_id=test_warehouse.id,
    )
    db_session.add(item)
    await db_session.flush()
    return item
