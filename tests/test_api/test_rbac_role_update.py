import pytest
from httpx import AsyncClient
from uuid import UUID
from app.models.user_model import UserRole
from app.schemas.user_schemas import UserCreate
from app.main import app

@pytest.mark.asyncio
async def test_admin_can_update_user_role(admin_token, create_user, async_client: AsyncClient):
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "MANAGER"}
    )
    assert res.status_code == 200
    assert f"User role updated to MANAGER" in res.json()["message"]


@pytest.mark.asyncio
async def test_non_admin_cannot_update_user_role(user_token, create_user, async_client: AsyncClient):
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"new_role": "ADMIN"}
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Operation not permitted"


@pytest.mark.asyncio
async def test_admin_cannot_change_own_role(admin_token, admin_user, async_client: AsyncClient):
    res = await async_client.put(
        f"/users/{admin_user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "MANAGER"}
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Admins cannot change their own role" #admins should not be able to change role"

@pytest.mark.asyncio
async def test_update_user_role_invalid_role(admin_token, create_user, async_client: AsyncClient):
    user = await create_user(role=UserRole.AUTHENTICATED)
    res = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "GODMODE"}  # invalid role
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid role name"