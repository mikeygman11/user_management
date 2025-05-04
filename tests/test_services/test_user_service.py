"""Test suite for UserService operations.

This module contains asynchronous tests for the UserService class, covering
user creation, retrieval, update, deletion, registration, login, password
reset, email verification, and account locking behavior.
"""
# pylint: disable=import-error
import pytest

from app.dependencies import get_settings
from app.models.user_model import UserRole
from app.services.user_service import UserService
from app.utils.nickname_gen import generate_nickname

pytestmark = pytest.mark.asyncio


async def test_create_user_with_valid_data(db_session, email_service):
    """Ensure creating a user with valid data returns a User with correct email."""
    user_data = {
        "nickname": generate_nickname(),
        "email": "valid_user@example.com",
        "password": "ValidPassword123!",
        "role": UserRole.ADMIN.name,
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]


async def test_create_user_with_invalid_data(db_session, email_service):
    """Ensure creating a user with invalid data returns None."""
    user_data = {
        "nickname": "",
        "email": "invalidemail",
        "password": "short",
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is None


async def test_get_by_id_user_exists(db_session, user):
    """Ensure retrieving a user by valid ID returns the correct user."""
    retrieved = await UserService.get_by_id(db_session, user.id)
    assert retrieved.id == user.id


async def test_get_by_id_user_not_found(db_session):
    """Ensure retrieving a non-existent user by ID returns None."""
    retrieved = await UserService.get_by_id(db_session, "non-existent-id")
    assert retrieved is None


async def test_get_by_nickname_user_exists(db_session, user):
    """Ensure retrieving a user by valid nickname returns the correct user."""
    retrieved = await UserService.get_by_nickname(db_session, user.nickname)
    assert retrieved.nickname == user.nickname


async def test_get_by_nickname_user_not_found(db_session):
    """Ensure retrieving a non-existent user by nickname returns None."""
    retrieved = await UserService.get_by_nickname(
        db_session, "non_existent_nickname"
    )
    assert retrieved is None


async def test_get_by_email_user_exists(db_session, user):
    """Ensure retrieving a user by valid email returns the correct user."""
    retrieved = await UserService.get_by_email(db_session, user.email)
    assert retrieved.email == user.email


async def test_get_by_email_user_not_found(db_session):
    """Ensure retrieving a non-existent user by email returns None."""
    retrieved = await UserService.get_by_email(
        db_session, "non_existent@example.com"
    )
    assert retrieved is None


async def test_update_user_valid_data(db_session, user):
    """Ensure updating a user with valid data persists the change."""
    new_email = "updated_email@example.com"
    updated = await UserService.update(
        db_session, user.id, {"email": new_email}
    )
    assert updated is not None
    assert updated.email == new_email


async def test_update_user_invalid_data(db_session, user):
    """Ensure updating a user with invalid data returns None."""
    updated = await UserService.update(
        db_session, user.id, {"email": "invalidemail"}
    )
    assert updated is None


async def test_delete_user_exists(db_session, user):
    """Ensure deleting an existing user returns True."""
    success = await UserService.delete(db_session, user.id)
    assert success is True


async def test_delete_user_not_found(db_session):
    """Ensure deleting a non-existent user returns False."""
    success = await UserService.delete(
        db_session, "non-existent-id"
    )
    assert success is False


async def test_list_users_with_pagination(db_session, users_with_same_role_50_users):
    """Ensure list_users returns paginated results with correct page sizes."""
    # Use fixture to populate users, then verify pagination
    _ = users_with_same_role_50_users
    first_page = await UserService.list_users(
        db_session, skip=0, limit=10
    )
    second_page = await UserService.list_users(
        db_session, skip=10, limit=10
    )
    assert len(first_page) == 10
    assert len(second_page) == 10
    assert first_page[0].id != second_page[0].id


async def test_register_user_with_valid_data(db_session, email_service):
    """Ensure register_user creates a new user with valid data."""
    user_data = {
        "nickname": generate_nickname(),
        "email": "register_valid_user@example.com",
        "password": "RegisterValid123!",
        "role": UserRole.ADMIN.name,
    }
    user = await UserService.register_user(
        db_session, user_data, email_service
    )
    assert user is not None
    assert user.email == user_data["email"]


async def test_register_user_with_invalid_data(db_session, email_service):
    """Ensure register_user returns None with invalid data."""
    user_data = {
        "email": "registerinvalidemail",
        "password": "short",
    }
    user = await UserService.register_user(
        db_session, user_data, email_service
    )
    assert user is None


async def test_login_user_successful(db_session, verified_user):
    """Ensure login_user returns user on correct credentials."""
    logged_in = await UserService.login_user(
        db_session, verified_user.email, "MySuperPassword$1234"
    )
    assert logged_in is not None


async def test_login_user_incorrect_email(db_session):
    """Ensure login_user returns None for nonexistent email."""
    result = await UserService.login_user(
        db_session, "nonexistentuser@noway.com", "Password123!"
    )
    assert result is None


async def test_login_user_incorrect_password(db_session, user):
    """Ensure login_user returns None for incorrect password."""
    result = await UserService.login_user(
        db_session, user.email, "IncorrectPassword!"
    )
    assert result is None


async def test_account_lock_after_failed_logins(db_session, verified_user):
    """Ensure account locks after max failed login attempts."""
    max_attempts = get_settings().max_login_attempts
    for _ in range(max_attempts):
        await UserService.login_user(
            db_session, verified_user.email, "wrongpassword"
        )

    locked = await UserService.is_account_locked(
        db_session, verified_user.email
    )
    assert locked, (
        "Account should lock after maximum failed login attempts."
    )


async def test_reset_password(db_session, user):
    """Ensure reset_password returns True and updates the password."""
    new_password = "NewPassword123!"
    success = await UserService.reset_password(
        db_session, user.id, new_password
    )
    assert success is True


async def test_verify_email_with_token(db_session, user):
    """Ensure verify_email_with_token returns True for valid token."""
    token = "valid_token_example"
    user.verification_token = token
    await db_session.commit()
    result = await UserService.verify_email_with_token(
        db_session, user.id, token
    )
    assert result is True


async def test_unlock_user_account(db_session, locked_user):
    """Ensure unlock_user_account unlocks a locked user."""
    unlocked = await UserService.unlock_user_account(
        db_session, locked_user.id
    )
    assert unlocked is True
    refreshed = await UserService.get_by_id(db_session, locked_user.id)
    assert not refreshed.is_locked
