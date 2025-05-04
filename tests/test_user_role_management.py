"""Test user management RBAC"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user_model import UserRole
from settings.config import settings
@pytest.mark.asyncio
async def test_admin_can_change_user_role(admin_token, create_user):
    """Admin role check"""
    user = await create_user(role=UserRole.AUTHENTICATED)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(
            f"/users/{user.id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_role": "MANAGER"},
        )
    assert response.status_code == 200
    assert response.json()["message"] == "User role updated to MANAGER"

@pytest.mark.asyncio
async def test_admin_can_access_all_protected_routes(
    admin_token
):
    """Protected routes"""
    protected_endpoints = ["/users", "/users/roles"]
    async with AsyncClient(app=app, base_url="http://test") as ac:
        for endpoint in protected_endpoints:
            response = await ac.get(
                endpoint, headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code != 403
