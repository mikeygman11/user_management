"""Testing RBAC with Admins - new tests"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user_model import UserRole

@pytest.mark.asyncio
async def test_admin_can_update_user_role(
    admin_token, create_user, async_client: AsyncClient
):
    """Admin update test"""
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "MANAGER"},
    )
    assert res.status_code == 200
    assert f"User role updated to MANAGER" in res.json()["message"]


@pytest.mark.asyncio
async def test_non_admin_cannot_update_user_role(
    user_token, create_user, async_client: AsyncClient
):
    """Non admin update fail"""
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"new_role": "ADMIN"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Operation not permitted"


@pytest.mark.asyncio
async def test_admin_cannot_change_own_role(
    admin_token, admin_user, async_client: AsyncClient
):
    """Admin cannot change own role"""
    res = await async_client.put(
        f"/users/{admin_user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "MANAGER"},
    )
    assert res.status_code == 400
    assert (
        res.json()["detail"] == "Admins cannot change their own role"
    )  # admins should not be able to change role"


@pytest.mark.asyncio
async def test_update_user_role_invalid_role(
    admin_token, create_user, async_client: AsyncClient
):
    """Invalid role"""
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "GODMODE"},  # invalid role
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid role name"


@pytest.mark.asyncio
async def test_admin_updates_nonexistent_user_role(
    admin_token, async_client: AsyncClient
):
    """Fake role"""
    fake_user_id = "11111111-1111-1111-1111-111111111111"  # guaranteed to not exist
    res = await async_client.put(
        f"/users/{fake_user_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "MANAGER"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_update_role(
    create_user, async_client: AsyncClient
):
    """Test unauth"""
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": "Bearer invalid.token.here"},
        json={"new_role": "MANAGER"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] in [
        "Could not validate credentials",
        "Not authenticated",
    ]


@pytest.mark.asyncio
async def test_manager_cannot_update_user_role(
    manager_token, create_user, async_client: AsyncClient
):
    """Manager cannot update"""
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"new_role": "ADMIN"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] in ["Permission denied", "Operation not permitted"]


@pytest.mark.asyncio
async def test_admin_assigns_same_role(
    admin_token, create_user, async_client: AsyncClient
):
    """Same role reassigned"""
    user = await create_user(role=UserRole.MANAGER)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "MANAGER"},
    )
    assert res.status_code == 200
    assert "User role updated to MANAGER" in res.json()["message"]


@pytest.mark.asyncio
async def test_update_user_role_missing_auth(create_user, async_client: AsyncClient):
    """Missing auth test"""
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role", json={"new_role": "ADMIN"}  # No auth header
    )
    assert res.status_code == 401
    assert res.json()["detail"] in [
        "Not authenticated",
        "Not authenticated",
    ]  # 9 tests in this file added
