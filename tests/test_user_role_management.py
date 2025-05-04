import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user_model import UserRole
from uuid import UUID
import jwt
from settings.config import settings
@pytest.mark.asyncio
async def test_admin_can_change_user_role(admin_token, create_user):
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
async def test_admin_cannot_change_own_role(admin_token):
    payload = jwt.decode(admin_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    admin_id = payload["sub"]

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(
            f"/users/{admin_id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_role": "MANAGER"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Admins cannot change their own role"


@pytest.mark.asyncio
async def test_non_admin_cannot_change_role(user_token, create_user):
    user = await create_user(role=UserRole.AUTHENTICATED)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(
            f"/users/{user.id}/role",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"new_role": "ADMIN"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Operation not permitted"
    
@pytest.mark.asyncio
async def test_role_change_is_logged(admin_token, create_user, db_session):
    from app.models.role_change_log_model import RoleChangeLog

    user = await create_user(role=UserRole.AUTHENTICATED)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.put(
            f"/users/{user.id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_role": "MANAGER"},
        )

    logs = await db_session.execute(
        RoleChangeLog.__table__.select().where(RoleChangeLog.target_user_id == user.id)
    )
    log_entry = logs.first()
    assert log_entry is not None
    assert log_entry["new_role"] == "MANAGER"
