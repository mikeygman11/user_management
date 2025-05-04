"""
tests/test_user_role_management.py — Integration tests for user role management endpoints

This module tests that admin users can change roles and access protected routes.
"""

import os
import sys
from httpx import AsyncClient
from fastapi import status
import pytest
from app.main import app
from app.models.user_model import UserRole
# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.mark.asyncio
async def test_admin_can_change_user_role(admin_token, create_user):
    """Admin users should successfully change another user’s role via PUT /users/{id}/role."""
    user = await create_user(role=UserRole.AUTHENTICATED)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(
            f"/users/{user.id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_role": "MANAGER"},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("message") == "User role updated to MANAGER"

@pytest.mark.asyncio
async def test_admin_can_access_all_protected_routes(admin_token):
    """Admin users should not receive 403 on GET to protected endpoints."""
    protected_endpoints = ["/users", "/users/roles"]

    async with AsyncClient(app=app, base_url="http://test") as ac:
        for endpoint in protected_endpoints:
            response = await ac.get(
                endpoint,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code != status.HTTP_403_FORBIDDEN
