"""Test user schemas file"""
# pylint: disable=redefined-outer-name

import uuid
import pytest
from pydantic import ValidationError

from app.schemas.user_schemas import (LoginRequest, UserBase, UserCreate,
                                      UserResponse, UserUpdate)


# Fixtures for common test data
@pytest.fixture
def user_base_data():
    """User base data"""
    return {
        "nickname": "john_doe_123",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "AUTHENTICATED",
        "bio": "I am a software engineer with over 5 years of experience.",
        "profile_picture_url": "https://example.com/profile_pictures/john_doe.jpg",
        "linkedin_profile_url": "https://linkedin.com/in/johndoe",
        "github_profile_url": "https://github.com/johndoe",
    }

@pytest.fixture
def user_create_data(user_base_data):
    """User create data"""
    return {**user_base_data, "password": "SecurePassword123!"}


@pytest.fixture
def user_update_data():
    """Update data test"""
    return {
        "email": "john.doe.new@example.com",
        "nickname": "j_doe",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "I specialize in backend development with Python and Node.js.",
        "profile_picture_url": "https://example.com/profile_pictures/john_doe_updated.jpg",
    }


@pytest.fixture
def user_response_data(user_base_data):
    """Response test"""
    return {
        "id": uuid.uuid4(),
        "nickname": user_base_data["nickname"],
        "first_name": user_base_data["first_name"],
        "last_name": user_base_data["last_name"],
        "role": user_base_data["role"],
        "email": user_base_data["email"],
        # "last_login_at": datetime.now(),
        # "created_at": datetime.now(),
        # "updated_at": datetime.now(),
        "links": [],
    }


@pytest.fixture
def login_request_data():
    """Request data test"""
    return {"email": "john_doe_123@emai.com", "password": "SecurePassword123!"}


# Tests for UserBase
def test_user_base_valid(user_base_data):
    """Test user base"""
    user = UserBase(**user_base_data)
    assert user.nickname == user_base_data["nickname"]
    assert user.email == user_base_data["email"]


# Tests for UserCreate
def test_user_create_valid(user_create_data):
    """User create valid"""
    user = UserCreate(**user_create_data)
    assert user.nickname == user_create_data["nickname"]
    assert user.password == user_create_data["password"]


# Tests for UserUpdate
def test_user_update_valid(user_update_data):
    """User update valid"""
    user_update = UserUpdate(**user_update_data)
    assert user_update.email == user_update_data["email"]
    assert user_update.first_name == user_update_data["first_name"]


# Tests for UserResponse
def test_user_response_valid(user_response_data):
    """Test response valid"""
    user = UserResponse(**user_response_data)
    assert user.id == user_response_data["id"]
    # assert user.last_login_at == user_response_data["last_login_at"]


# Tests for LoginRequest
def test_login_request_valid(login_request_data):
    """Test login request"""
    login = LoginRequest(**login_request_data)
    assert login.email == login_request_data["email"]
    assert login.password == login_request_data["password"]


# Parametrized tests for nickname and email validation
@pytest.mark.parametrize(
    "nickname", ["test_user", "test-user", "testuser123", "123test"]
)
def test_user_base_nickname_valid(nickname, user_base_data):
    """Test base nickname"""
    user_base_data["nickname"] = nickname
    user = UserBase(**user_base_data)
    assert user.nickname == nickname


@pytest.mark.parametrize("nickname", ["test user", "test?user", "", "us"])
def test_user_base_nickname_invalid(nickname, user_base_data):
    """Test invalid nickname"""
    user_base_data["nickname"] = nickname
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)


# Parametrized tests for URL validation
@pytest.mark.parametrize(
    "url", ["http://valid.com/profile.jpg", "https://valid.com/profile.png", None]
)
def test_user_base_url_valid(url, user_base_data):
    """Test user base url"""
    user_base_data["profile_picture_url"] = url
    user = UserBase(**user_base_data)
    assert user.profile_picture_url == url


@pytest.mark.parametrize(
    "url", ["ftp://invalid.com/profile.jpg", "http//invalid", "https//invalid"]
)
def test_user_base_url_invalid(url, user_base_data):
    """User base invalid test"""
    user_base_data["profile_picture_url"] = url
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)
