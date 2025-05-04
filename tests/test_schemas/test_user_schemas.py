"""Tests for user Pydantic schemas: UserBase, UserCreate, UserUpdate, UserResponse, and LoginRequest."""
# pylint: disable=redefined-outer-name
import copy
import uuid
import pytest
from pydantic import ValidationError

from user_management.app.schemas.user_schemas import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
)


@pytest.fixture
def user_base_data() -> dict:
    """Base data for a valid user schema."""
    return {
        "nickname": "john_doe_123",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "AUTHENTICATED",
        "bio": (
            "I am a software engineer with over 5 years of experience."
        ),
        "profile_picture_url": (
            "https://example.com/profile_pictures/john_doe.jpg"
        ),
        "linkedin_profile_url": "https://linkedin.com/in/johndoe",
        "github_profile_url": "https://github.com/johndoe",
    }


@pytest.fixture
def user_create_data(user_base_data: dict) -> dict:
    """Data for creating a user, including password."""
    data = copy.deepcopy(user_base_data)
    data["password"] = "SecurePassword123!"
    return data


@pytest.fixture
def user_update_data() -> dict:
    """Data for updating user fields."""
    return {
        "email": "john.doe.new@example.com",
        "nickname": "j_doe",
        "first_name": "John",
        "last_name": "Doe",
        "bio": (
            "I specialize in backend development with Python and Node.js."
        ),
        "profile_picture_url": (
            "https://example.com/profile_pictures/john_doe_updated.jpg"
        ),
    }


@pytest.fixture
def user_response_data(user_base_data: dict) -> dict:
    """Data matching the UserResponse schema (includes id and links)."""
    data = copy.deepcopy(user_base_data)
    data["id"] = uuid.uuid4()
    data["links"] = []
    return data


@pytest.fixture
def login_request_data() -> dict:
    """Data for login request schema."""
    return {"email": "john.doe@example.com", "password": "SecurePassword123!"}


# --- Tests for schema instantiation ---

def test_user_base_valid(user_base_data: dict):
    """UserBase accepts valid data without error."""
    user = UserBase(**user_base_data)
    assert user.nickname == user_base_data["nickname"]
    assert user.email == user_base_data["email"]


def test_user_create_valid(user_create_data: dict):
    """UserCreate accepts valid data including password."""
    user = UserCreate(**user_create_data)
    assert user.nickname == user_create_data["nickname"]
    assert user.password == user_create_data["password"]


def test_user_update_valid(user_update_data: dict):
    """UserUpdate accepts valid partial update data."""
    update = UserUpdate(**user_update_data)
    assert update.email == user_update_data["email"]
    assert update.bio == user_update_data["bio"]


def test_user_response_valid(user_response_data: dict):
    """UserResponse accepts data with id and links."""
    resp = UserResponse(**user_response_data)
    assert resp.id == user_response_data["id"]
    assert resp.links == []


def test_login_request_valid(login_request_data: dict):
    """LoginRequest accepts valid email and password."""
    login = LoginRequest(**login_request_data)
    assert login.email == login_request_data["email"]
    assert login.password == login_request_data["password"]


# --- Parametrized validation tests ---

@pytest.mark.parametrize(
    "nickname",
    ["test_user", "test-user", "testuser123", "123test"],
)
def test_user_base_nickname_valid(nickname: str, user_base_data: dict):
    """Valid nicknames should pass validation."""
    data = dict(user_base_data)
    data["nickname"] = nickname
    user = UserBase(**data)
    assert user.nickname == nickname


@pytest.mark.parametrize(
    "nickname",
    ["test user", "test?user", "", "us"],
)
def test_user_base_nickname_invalid(nickname: str, user_base_data: dict):
    """Invalid nicknames should raise ValidationError."""
    data = dict(user_base_data)
    data["nickname"] = nickname
    with pytest.raises(ValidationError):
        UserBase(**data)


@pytest.mark.parametrize(
    "url",
    ["http://valid.com/pic.jpg", "https://valid.com/pic.png", None],
)
def test_user_base_profile_url_valid(url, user_base_data: dict):
    """Valid or null URLs should pass validation."""
    data = dict(user_base_data)
    data["profile_picture_url"] = url
    user = UserBase(**data)
    assert user.profile_picture_url == url


@pytest.mark.parametrize(
    "url",
    ["ftp://invalid.com/pic.jpg", "http//invalid", "https//invalid"],
)
def test_user_base_profile_url_invalid(url: str, user_base_data: dict):
    """Invalid URL formats should raise ValidationError."""
    data = dict(user_base_data)
    data["profile_picture_url"] = url
    with pytest.raises(ValidationError):
        UserBase(**data)
