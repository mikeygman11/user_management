"""Integration tests for RBAC role update endpoints."""
import pytest
from httpx import AsyncClient

from app.models.user_model import UserRole


@pytest.mark.asyncio
async def test_admin_can_update_user_role(
    admin_token: str,
    create_user,
    async_client: AsyncClient,
):
    """Admins can successfully change another user's role."""
    user = await create_user(role=UserRole.AUTHENTICATED)
    response = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": UserRole.MANAGER.name},
    )
    assert response.status_code == 200
    assert "User role updated to MANAGER" in response.json().get("message", "")


@pytest.mark.asyncio
async def test_non_admin_cannot_update_user_role(
    user_token: str,
    create_user,
    async_client: AsyncClient,
):
    """Non-admins are forbidden from changing user roles."""
    user = await create_user(role=UserRole.AUTHENTICATED)
    response = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"new_role": UserRole.ADMIN.name},
    )
    assert response.status_code == 403
    assert response.json().get("detail") == "Operation not permitted"


@pytest.mark.asyncio
async def test_admin_cannot_change_own_role(
    admin_token: str,
    admin_user,
    async_client: AsyncClient,
):
    """Admins should not be allowed to change their own role."""
    response = await async_client.put(
        f"/users/{admin_user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": UserRole.MANAGER.name},
    )
    assert response.status_code == 400
    assert response.json().get("detail") == "Admins cannot change their own role"


@pytest.mark.asyncio
async def test_update_user_role_invalid_role(
    admin_token: str,
    create_user,
    async_client: AsyncClient,
):
    """Invalid role names should be rejected with a 400 error."""
    user = await create_user(role=UserRole.AUTHENTICATED)
    response = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": "GODMODE"},
    )
    assert response.status_code == 400
    assert response.json().get("detail") == "Invalid role name"


@pytest.mark.asyncio
async def test_admin_updates_nonexistent_user_role(
    admin_token: str,
    async_client: AsyncClient,
):
    """Updating the role of a non-existent user should return 404."""
    fake_id = "11111111-1111-1111-1111-111111111111"
    response = await async_client.put(
        f"/users/{fake_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": UserRole.MANAGER.name},
    )
    assert response.status_code == 404
    assert response.json().get("detail") == "User not found"


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_update_role(
    create_user,
    async_client: AsyncClient,
):
    """Requests with invalid tokens should be unauthorized."""
    user = await create_user(role=UserRole.AUTHENTICATED)
    response = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": "Bearer invalid.token.here"},
        json={"new_role": UserRole.MANAGER.name},
    )
    assert response.status_code == 401
    assert response.json().get("detail") in [
        "Could not validate credentials",
        "Not authenticated",
    ]


@pytest.mark.asyncio
async def test_manager_cannot_update_user_role(
    manager_token: str,
    create_user,
    async_client: AsyncClient,
):
    """Managers do not have permission to change roles."""
    user = await create_user(role=UserRole.AUTHENTICATED)
    response = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"new_role": UserRole.ADMIN.name},
    )
    assert response.status_code == 403
    assert response.json().get("detail") in [
        "Permission denied",
        "Operation not permitted",
    ]


@pytest.mark.asyncio
async def test_admin_assigns_same_role(
    admin_token: str,
    create_user,
    async_client: AsyncClient,
):
    """Assigning the same role a user already has should be a no-op with 200."""
    user = await create_user(role=UserRole.MANAGER)
    response = await async_client.put(
        f"/users/{user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"new_role": UserRole.MANAGER.name},
    )
    assert response.status_code == 200
    assert "User role updated to MANAGER" in response.json().get("message", "")


@pytest.mark.asyncio
async def test_update_user_role_missing_auth(
    create_user,
    async_client: AsyncClient,
):
    """Requests without auth headers should be unauthorized."""
    user = await create_user(role=UserRole.AUTHENTICATED)
    response = await async_client.put(
        f"/users/{user.id}/role",
        json={"new_role": UserRole.ADMIN.name},
    )
    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"
