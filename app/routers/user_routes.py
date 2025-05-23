"""
This Python file is part of a FastAPI application, demonstrating user management 
functionalities including creating, reading, updating, and deleting (CRUD) 
user information.
"""
# pylint: disable=unused-argument
# pylint: disable=unused-import

import logging
from builtins import dict, int, len, str
from datetime import timedelta
from uuid import UUID

from fastapi import (APIRouter, Body, Depends, HTTPException, Request,
                     Response, status)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (get_current_user, get_db, get_email_service,
                              get_settings, require_role)
from app.models.user_model import UserRole
from app.schemas.pagination_schema import EnhancedPagination
from app.schemas.token_schema import TokenResponse
from app.schemas.user_schemas import (LoginRequest, UserBase, UserCreate,
                                      UserListResponse, UserResponse,
                                      UserUpdate)
from app.services.email_service import EmailService
from app.services.jwt_service import create_access_token
from app.services.user_service import UserService
from app.utils.link_generation import (create_user_links,
                                       generate_pagination_links)

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
settings = get_settings()


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    name="get_user",
    tags=["User Management Requires (Admin or Manager Roles)"],
)
async def get_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"])),
):
    """
    Endpoint to fetch a user by their unique identifier (UUID).

    Utilizes the UserService to query the database asynchronously 
    for the user and constructs a response model that includes the 
    user's details along with HATEOAS links for possible next actions.

    Args:
        user_id: UUID of the user to fetch.
        request: The request object, used to generate full URLs in the response.
        db: Dependency that provides an AsyncSession for database access.
        token: The OAuth2 access token obtained through OAuth2PasswordBearer dependency.
    """
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse.model_construct(
        id=user.id,
        nickname=user.nickname,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        profile_picture_url=user.profile_picture_url,
        github_profile_url=user.github_profile_url,
        linkedin_profile_url=user.linkedin_profile_url,
        role=user.role,
        email=user.email,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        links=create_user_links(user.id, request),
    )

# Additional endpoints for update, delete, create, and list users
# follow a similar pattern, using asynchronous database operations,
# handling security with OAuth2PasswordBearer, and enhancing response
# models with dynamic HATEOAS links.

# This approach not only ensures that the API is secure and efficient
#  but also promotes a better client experience by adhering to REST
# principles and providing self-discoverable operations. Fix DH

@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    name="update_user",
    tags=["User Management Requires (Admin or Manager Roles)"],
)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"])),
):
    """
    Update user information.

    - **user_id**: UUID of the user to update.
    - **user_update**: UserUpdate model with updated user information.
    """
    user_data = user_update.model_dump(exclude_unset=True)
    updated_user = await UserService.update(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse.model_construct(
        id=updated_user.id,
        bio=updated_user.bio,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        nickname=updated_user.nickname,
        email=updated_user.email,
        role=updated_user.role,
        last_login_at=updated_user.last_login_at,
        profile_picture_url=updated_user.profile_picture_url,
        github_profile_url=updated_user.github_profile_url,
        linkedin_profile_url=updated_user.linkedin_profile_url,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        links=create_user_links(updated_user.id, request),
    )

@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="delete_user",
    tags=["User Management Requires (Admin or Manager Roles)"],
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"])),
):
    """
    Delete a user by their ID.

    - **user_id**: UUID of the user to delete.
    """
    success = await UserService.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["User Management Requires (Admin or Manager Roles)"],
    name="create_user",
)
async def create_user(
    user: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"])),
):
    """
    Create a new user.

    This endpoint creates a new user with the provided information. If the email
    already exists, it returns a 400 error. On successful creation, it returns the
    newly created user's information along with links to related actions.

    Parameters:
    - user (UserCreate): The user information to create.
    - request (Request): The request object.
    - db (AsyncSession): The database session.

    Returns:
    - UserResponse: The newly created user's information along with navigation links.
    """
    existing_user = await UserService.get_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    created_user = await UserService.create(db, user.model_dump(), email_service)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    return UserResponse.model_construct(
        id=created_user.id,
        bio=created_user.bio,
        first_name=created_user.first_name,
        last_name=created_user.last_name,
        profile_picture_url=created_user.profile_picture_url,
        nickname=created_user.nickname,
        email=created_user.email,
        role=created_user.role,
        last_login_at=created_user.last_login_at,
        created_at=created_user.created_at,
        updated_at=created_user.updated_at,
        links=create_user_links(created_user.id, request),
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
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"])),
):
    """List users function"""
    total_users = await UserService.count(db)
    users = await UserService.list_users(db, skip, limit)

    user_responses = [UserResponse.model_validate(user) for user in users]

    pagination_links = generate_pagination_links(request, skip, limit, total_users)

    # Construct the final response with pagination details
    return UserListResponse(
        items=user_responses,
        total=total_users,
        page=skip // limit + 1,
        size=len(user_responses),
        links=pagination_links,  # Ensure you have appropriate logic to create these links
    )


@router.post("/register/", response_model=UserResponse, tags=["Login and Registration"])
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """Register a new user"""
    user = await UserService.register_user(
        session, user_data.model_dump(), email_service
    )
    if user:
        return user
    raise HTTPException(status_code=400, detail="Email already exists")


@router.post(
    "/login/", response_model=TokenResponse, tags=["Login and Registration"]
)  # fixing tags on login
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """User login"""
    if await UserService.is_account_locked(session, form_data.username):
        raise HTTPException(
            status_code=400,
            detail="Account locked due to too many failed login attempts.",
        )

    user = await UserService.login_user(session, form_data.username, form_data.password)
    if user:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)

        access_token = create_access_token(  # fixed access token so it takes a uuid
            data={"sub": str(user.id), "role": user.role.name},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect email or password.")


@router.post(
    "/login/",
    include_in_schema=False,
    response_model=TokenResponse,
    tags=["Login and Registration"],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """Login and reg"""
    if await UserService.is_account_locked(session, form_data.username):
        raise HTTPException(
            status_code=400,
            detail="Account locked due to too many failed login attempts.",
        )

    user = await UserService.login_user(session, form_data.username, form_data.password)
    if user:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)

        access_token = create_access_token(
            data={
                "sub": user.email,
                "role": str(user.role.name),
            },  # had to resolve access token issue - mismatch between user.email and user.id
            expires_delta=access_token_expires,
        )

        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect email or password.")


@router.get(
    "/verify-email/{user_id}/{token}",
    status_code=status.HTTP_200_OK,
    name="verify_email",
    tags=["Login and Registration"],
)
async def verify_email(
    user_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """
    Verify user's email with a provided token.
    
    - **user_id**: UUID of the user to verify.
    - **token**: Verification token sent to the user's email.
    """
    if await UserService.verify_email_with_token(db, user_id, token):
        return {"message": "Email verified successfully"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification token",
    )


@router.put("/users/{user_id}/role", tags=["User Management Requires (Admin Role)"])
async def update_user_role(
    user_id: UUID,
    new_role: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["ADMIN"])),
):
    """Change user role"""
    logger.info(f"Current user object: {current_user}")

    try:
        role_enum = UserRole[new_role.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid role name")

    try:
        changed_by_uuid = UUID(current_user["user_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format in token")

    if str(user_id) == str(changed_by_uuid):
        raise HTTPException(
            status_code=400, detail="Admins cannot change their own role"
        )

    updated_user = await UserService.update_role(
        db, user_id=user_id, new_role=role_enum, changed_by=changed_by_uuid
    )

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User role updated to {role_enum.name}"}
