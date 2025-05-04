"""
app/routers/user_routes.py — FastAPI routes for user management.

This module defines registration, login, CRUD, email verification, and role-update endpoints.
Access control is enforced via OAuth2 and role-based authorization.
"""

# pylint: disable=C0413, E0401, W0613

import os
import sys
import logging
from datetime import timedelta
from uuid import UUID

# Allow imports from project root
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    Body,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db,
    get_email_service,
    get_settings,
    require_role,
)
from app.schemas.token_schema import TokenResponse
from app.schemas.user_schemas import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService
from app.services.jwt_service import create_access_token
from app.utils.link_generation import (
    create_user_links,
    generate_pagination_links,
)
from app.services.email_service import EmailService
from app.models.user_model import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["User Management Requires (Admin or Manager Roles)"],
)
async def get_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(
        require_role(["ADMIN", "MANAGER"])
    ),
):
    """Get user by ID."""
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return UserResponse.model_construct(
        **user.dict(),
        links=create_user_links(
            user.id,
            request,
        ),
    )

@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    tags=["User Management Requires (Admin or Manager Roles)"],
)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(
        require_role(["ADMIN", "MANAGER"])
    ),
):
    """Update user details."""
    updated = await UserService.update(
        db,
        user_id,
        user_update.model_dump(
            exclude_unset=True
        ),
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return UserResponse.model_construct(
        **updated.dict(),
        links=create_user_links(
            updated.id,
            request,
        ),
    )

@router.delete(
    "/users/{user_id}",
    status_code=204,
    tags=["User Management Requires (Admin or Manager Roles)"],
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(
        require_role(["ADMIN", "MANAGER"])
    ),
):
    """Delete user by ID."""
    success = await UserService.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return Response(status_code=204)

@router.post(
    "/users/",
    response_model=UserResponse,
    status_code=201,
    tags=["User Management Requires (Admin or Manager Roles)"],
)
async def create_user(
    user: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(
        get_email_service
    ),
    _current_user: dict = Depends(
        require_role(["ADMIN", "MANAGER"])
    ),
):
    """Create a new user."""
    existing = await UserService.get_by_email(
        db,
        user.email,
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already exists",
        )
    created = await UserService.create(
        db,
        user.model_dump(),
        email_service,
    )
    if not created:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user",
        )
    return UserResponse.model_construct(
        **created.dict(),
        links=create_user_links(
            created.id,
            request,
        ),
    )

@router.get(
    "/users/",
    response_model=UserListResponse,
    tags=["User Management Requires (Admin or Manager Roles)"],
)
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(
        require_role(["ADMIN", "MANAGER"])
    ),
):
    """List users with pagination."""
    total = await UserService.count(db)
    users = await UserService.list_users(
        db,
        skip,
        limit,
    )
    items = [
        UserResponse.model_validate(u)
        for u in users
    ]
    links = generate_pagination_links(
        request,
        skip,
        limit,
        total,
    )
    return UserListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        size=len(items),
        links=links,
    )

@router.post(
    "/register/",
    response_model=UserResponse,
    tags=["Login and Registration"],
)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(
        get_email_service
    ),
):
    """Register a new user."""
    user = await UserService.register_user(
        session,
        user_data.model_dump(),
        email_service,
    )
    if user:
        return user
    raise HTTPException(
        status_code=400,
        detail="Email already exists",
    )

@router.post(
    "/login/",
    response_model=TokenResponse,
    tags=["Login and Registration"],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """Authenticate user and return access token."""
    if await UserService.is_account_locked(
        session,
        form_data.username,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Account locked due to too many failed login attempts."
            ),
        )
    user = await UserService.login_user(
        session,
        form_data.username,
        form_data.password,
    )
    if user:
        token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role.name,
            },
            expires_delta=timedelta(
                minutes=settings.access_token_expire_minutes
            ),
        )
        return {
            "access_token": token,
            "token_type": "bearer",
        }
    raise HTTPException(
        status_code=401,
        detail="Incorrect email or password.",
    )

@router.get(
    "/verify-email/{user_id}/{token}",
    status_code=200,
    tags=["Login and Registration"],
)
async def verify_email(
    user_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
    _email_service=Depends(get_email_service),
):
    """Verify email using token."""
    if await UserService.verify_email_with_token(
        db,
        user_id,
        token,
    ):
        return {"message": "Email verified successfully"}
    raise HTTPException(
        status_code=400,
        detail="Invalid or expired verification token",
    )

@router.put(
    "/users/{user_id}/role",
    tags=["User Management Requires (Admin Role)"],
)
async def update_user_role(
    user_id: UUID,
    new_role: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(
        require_role(["ADMIN"])
    ),
):
    """Update user role by admin."""
    logger.info(
        "Current user object: %s",
        current_user,
    )
    try:
        role_enum = UserRole[new_role.upper()]
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid role name",
        ) from exc
    try:
        changer = UUID(
            current_user["user_id"]
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid user_id format in token"
            ),
        ) from exc
    if str(user_id) == str(changer):
        raise HTTPException(
            status_code=400,
            detail=(
                "Admins cannot change their own role"
            ),
        )
    updated = await UserService.update_role(
        db,
        user_id,
        role_enum,
        changed_by=changer,
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return {
        "message": f"User role updated to {role_enum.name}"
    }
