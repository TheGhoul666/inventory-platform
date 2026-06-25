"""
Integration tests for inventory API endpoints.
Tests the full HTTP → Service → Repository → DB pipeline.
"""
import pytest
import pytest_asyncio
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
class TestInventoryIssue:
    async def test_issue_reduces_quantity(self, client: AsyncClient, auth_headers, test_item):
        initial_qty = float(test_item.quantity)

        resp = await client.post(
            "/api/v1/inventory/transactions/issue",
            json={
                "item_id": str(test_item.id),
                "quantity": 10.0,
                "reason_code": "MAINTENANCE",
                "notes": "Brake replacement on Bus #42",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "transaction_id" in data
        assert data["status"] == "COMPLETED"

        # Verify quantity decreased
        item_resp = await client.get(
            f"/api/v1/inventory/items/{test_item.id}",
            headers=auth_headers,
        )
        assert item_resp.status_code == 200
        assert item_resp.json()["quantity"] == pytest.approx(initial_qty - 10)

    async def test_issue_insufficient_stock_returns_422(self, client, auth_headers, test_item):
        resp = await client.post(
            "/api/v1/inventory/transactions/issue",
            json={
                "item_id": str(test_item.id),
                "quantity": 999999.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert "Insufficient" in resp.json()["detail"]

    async def test_issue_requires_auth(self, client, test_item):
        resp = await client.post(
            "/api/v1/inventory/transactions/issue",
            json={"item_id": str(test_item.id), "quantity": 1},
        )
        assert resp.status_code == 403

    async def test_restock_increases_quantity(self, client, auth_headers, test_item):
        initial_qty = float(test_item.quantity)

        resp = await client.post(
            "/api/v1/inventory/transactions/restock",
            json={"item_id": str(test_item.id), "quantity": 50.0},
            headers=auth_headers,
        )
        assert resp.status_code == 201

        item_resp = await client.get(
            f"/api/v1/inventory/items/{test_item.id}",
            headers=auth_headers,
        )
        assert item_resp.json()["quantity"] == pytest.approx(initial_qty + 50)

    async def test_quantity_never_goes_negative(self, client, auth_headers, test_item):
        """The DB CHECK constraint and business rule both prevent negative stock."""
        # Drain all stock
        await client.post(
            "/api/v1/inventory/transactions/issue",
            json={"item_id": str(test_item.id), "quantity": float(test_item.quantity)},
            headers=auth_headers,
        )
        # Try to issue 1 more
        resp = await client.post(
            "/api/v1/inventory/transactions/issue",
            json={"item_id": str(test_item.id), "quantity": 1.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

        # Verify item quantity is exactly 0, not negative
        item_resp = await client.get(
            f"/api/v1/inventory/items/{test_item.id}",
            headers=auth_headers,
        )
        assert item_resp.json()["quantity"] == 0.0

    async def test_list_items_paginated(self, client, auth_headers, test_item):
        resp = await client.get(
            "/api/v1/inventory/items?limit=10&offset=0",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_create_item(self, client, auth_headers, test_warehouse):
        resp = await client.post(
            "/api/v1/inventory/items",
            json={
                "sku": "NEW-OIL-FILTER-002",
                "name": "Oil Filter",
                "unit": "piece",
                "warehouse_id": str(test_warehouse.id),
                "low_stock_threshold": 5,
                "critical_stock_threshold": 2,
                "reorder_quantity": 20,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["sku"] == "NEW-OIL-FILTER-002"
        assert data["quantity"] == 0.0


@pytest.mark.asyncio
class TestAuth:
    async def test_login_success(self, client, test_user):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, test_user):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_refresh_token_rotation(self, client, test_user):
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        refresh_token = login.json()["refresh_token"]

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        new_data = resp.json()
        assert new_data["refresh_token"] != refresh_token  # token rotated

        # Old refresh token must now be invalid
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp2.status_code == 401
