"""Integration tests for the Users API endpoints."""
import pytest
from urllib.parse import urlencode

from httpx import AsyncClient

from app.models.user_model import UserRole
from app.services.jwt_service import decode_token
from app.utils.nickname_gen import generate_nickname


@pytest.mark.asyncio
async def test_create_user_access_denied(async_client: AsyncClient, user_token: str):
    """Regular users should not be allowed to create other users."""
    headers = {"Authorization": f"Bearer {user_token}"}
    user_data = {
        "nickname": generate_nickname(),
        "email": "test@example.com",
        "password": "StrongPassword123!",
    }

    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_retrieve_user_access_denied(async_client: AsyncClient, verified_user, user_token: str):
    """Regular users should not be allowed to retrieve other users' details."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get(f"/users/{verified_user.id}", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_retrieve_user_access_allowed(async_client: AsyncClient, admin_user, admin_token: str):
    """Admins should be able to retrieve any user's details."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get(f"/users/{admin_user.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == str(admin_user.id)


@pytest.mark.asyncio
async def test_update_user_email_access_denied(async_client: AsyncClient, verified_user, user_token: str):
    """Regular users should not be allowed to update their email via the API."""
    headers = {"Authorization": f"Bearer {user_token}"}
    updated = {"email": f"updated_{verified_user.id}@example.com"}

    response = await async_client.put(
        f"/users/{verified_user.id}", json=updated, headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_email_access_allowed(async_client: AsyncClient, admin_user, admin_token: str):
    """Admins should be able to update any user's email."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    updated = {"email": f"updated_{admin_user.id}@example.com"}

    response = await async_client.put(
        f"/users/{admin_user.id}", json=updated, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["email"] == updated["email"]


@pytest.mark.asyncio
async def test_delete_user(async_client: AsyncClient, admin_user, admin_token: str):
    """Admins should be able to delete users and retrieval then returns 404."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    delete_resp = await async_client.delete(f"/users/{admin_user.id}", headers=headers)
    assert delete_resp.status_code == 204

    fetch_resp = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert fetch_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_client: AsyncClient, verified_user):
    """Creating a user with an existing email should fail with 400."""
    data = {
        "email": verified_user.email,
        "password": "AnotherPassword123!",
        "role": UserRole.ADMIN.name,
    }
    response = await async_client.post("/register/", json=data)
    assert response.status_code == 400
    assert "Email already exists" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_create_user_invalid_email(async_client: AsyncClient):
    """Validation should reject malformed email addresses."""
    data = {"email": "notanemail", "password": "ValidPassword123!"}
    response = await async_client.post("/register/", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, verified_user):
    """Valid credentials should return a bearer token with correct role."""
    form = {"username": verified_user.email, "password": "MySuperPassword$1234"}
    encoded = urlencode(form)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = await async_client.post("/login/", data=encoded, headers=headers)
    assert response.status_code == 200

    body = response.json()
    token = body.get("access_token")
    assert token
    assert body.get("token_type") == "bearer"

    decoded = decode_token(token)
    assert decoded and decoded.get("role") == "AUTHENTICATED"


@pytest.mark.asyncio
async def test_login_user_not_found(async_client: AsyncClient):
    """Login with unknown email should return 401."""
    form = {"username": "noone@here.edu", "password": "Irrelevant123"}
    encoded = urlencode(form)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = await async_client.post("/login/", data=encoded, headers=headers)
    assert response.status_code == 401
    assert "Incorrect email or password." in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_incorrect_password(async_client: AsyncClient, verified_user):
    """Login with wrong password should return 401."""
    form = {"username": verified_user.email, "password": "WrongPassword!"}
    encoded = urlencode(form)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = await async_client.post("/login/", data=encoded, headers=headers)
    assert response.status_code == 401
    assert "Incorrect email or password." in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_unverified_user(async_client: AsyncClient, unverified_user):
    """Unverified users should not be able to log in."""
    form = {"username": unverified_user.email, "password": "MySuperPassword$1234"}
    encoded = urlencode(form)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = await async_client.post("/login/", data=encoded, headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_locked_user(async_client: AsyncClient, locked_user):
    """Locked accounts should return 400 with lock message."""
    form = {"username": locked_user.email, "password": "MySuperPassword$1234"}
    encoded = urlencode(form)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = await async_client.post("/login/", data=encoded, headers=headers)
    assert response.status_code == 400
    assert "Account locked due to too many failed login attempts." in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_delete_user_not_found(async_client: AsyncClient, admin_token: str):
    """Deleting a non-existent user should return 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = await async_client.delete(f"/users/{fake_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_profiles(async_client: AsyncClient, admin_user, admin_token: str):
    """Admins can update GitHub and LinkedIn profile URLs."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    updates = {
        "github_profile_url": "http://github.com/example",
        "linkedin_profile_url": "http://linkedin.com/example",
    }

    response = await async_client.put(f"/users/{admin_user.id}", json=updates, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("github_profile_url") == updates["github_profile_url"]
    assert data.get("linkedin_profile_url") == updates["linkedin_profile_url"]


@pytest.mark.asyncio
async def test_list_users_as_admin_and_manager(async_client: AsyncClient, admin_token: str, manager_token: str):
    """Admins and managers can list users; regular users cannot."""
    for token, allowed in [(admin_token, True), (manager_token, True), (None, False)]:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = await async_client.get("/users/", headers=headers)
        expected = 200 if allowed else 403
        assert response.status_code == expected
