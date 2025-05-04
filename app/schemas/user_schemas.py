"""File to define user schema"""
# pylint: disable=unused-argument
# pylint: disable=unused-import

import re
import uuid
from builtins import ValueError, any, bool, str
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, root_validator, validator

from app.models.user_model import UserRole
from app.utils.nickname_gen import generate_nickname

def validate_url(url: Optional[str]) -> Optional[str]:
    """Validate url function"""
    if url is None:
        return url
    url_regex = r"^https?:\/\/[^\s/$.?#].[^\s]*$"
    if not re.match(url_regex, url):
        raise ValueError("Invalid URL format")
    return url


class UserBase(BaseModel):
    """User Base model declaration"""
    email: EmailStr = Field(..., example="john.doe@example.com")
    nickname: Optional[str] = Field(
        None, min_length=3, pattern=r"^[\w-]+$", example=generate_nickname()
    )
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    bio: Optional[str] = Field(
        None, example="Experienced software developer specializing in web applications."
    )
    profile_picture_url: Optional[str] = Field(
        None, example="https://example.com/profiles/john.jpg"
    )
    linkedin_profile_url: Optional[str] = Field(
        None, example="https://linkedin.com/in/johndoe"
    )
    github_profile_url: Optional[str] = Field(
        None, example="https://github.com/johndoe"
    )
    role: UserRole

    _validate_urls = validator(
        "profile_picture_url",
        "linkedin_profile_url",
        "github_profile_url",
        pre=True,
        allow_reuse=True,
    )(validate_url)

    class Config:
        """Configuration"""
        from_attributes = True


class UserCreate(UserBase):
    """Create user function"""
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="Secure*1234")

class UserUpdate(UserBase):
    """Update user with API endpoint"""
    email: Optional[EmailStr] = Field(None, example="john.doe@example.com")
    nickname: Optional[str] = Field(
        None, min_length=3, pattern=r"^[\w-]+$", example="john_doe123"
    )
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    bio: Optional[str] = Field(
        None, example="Experienced software developer specializing in web applications."
    )
    profile_picture_url: Optional[str] = Field(
        None, example="https://example.com/profiles/john.jpg"
    )
    linkedin_profile_url: Optional[str] = Field(
        None, example="https://linkedin.com/in/johndoe"
    )
    github_profile_url: Optional[str] = Field(
        None, example="https://github.com/johndoe"
    )
    role: Optional[str] = Field(None, example="AUTHENTICATED")

    @root_validator(pre=True)
    def check_at_least_one_value(cls, values):
        """Need one value or more to update"""
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values


class UserResponse(UserBase):
    """User response from server"""
    id: uuid.UUID = Field(..., example=uuid.uuid4())
    email: EmailStr = Field(..., example="john.doe@example.com")
    nickname: Optional[str] = Field(
        None, min_length=3, pattern=r"^[\w-]+$", example=generate_nickname()
    )
    is_professional: Optional[bool] = Field(default=False, example=True)
    role: UserRole


class LoginRequest(BaseModel):
    """Login API function"""
    email: str = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="Secure*1234")


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., example="Not Found")
    details: Optional[str] = Field(
        None, example="The requested resource was not found."
    )


class UserListResponse(BaseModel):
    """UserListResponse schema"""
    items: List[UserResponse] = Field(
        ...,
        example=[
            {
                "id": uuid.uuid4(),
                "nickname": generate_nickname(),
                "email": "john.doe@example.com",
                "first_name": "John",
                "bio": "Experienced developer",
                "role": "AUTHENTICATED",
                "last_name": "Doe",
                "profile_picture_url": "https://example.com/profiles/john.jpg",
                "linkedin_profile_url": "https://linkedin.com/in/johndoe",
                "github_profile_url": "https://github.com/johndoe",
            }
        ],
    )
    total: int = Field(..., example=100)
    page: int = Field(..., example=1)
    size: int = Field(..., example=10)
