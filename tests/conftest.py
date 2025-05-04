"""
Pytest fixtures for user_management tests.
"""
# pylint: disable=wrong-import-position, import-error, broad-exception-caught, redefined-outer-name

import sys
from pathlib import Path
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from faker import Faker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, scoped_session

from app.main import app
from app.database import Base, Database
from app.dependencies import get_db, get_settings
from app.models.user_model import User, UserRole
from app.utils.security import hash_password
from app.utils.template_manager import TemplateManager
from app.services.email_service import EmailService
from app.services.jwt_service import create_access_token
from app.services.user_service import UserService

# Ensure project root is on PYTHONPATH for pytest imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Faker for generating test data
fake = Faker()
settings = get_settings()

# Use asyncpg driver for tests
TEST_DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Create async engine and session factory
engine = create_async_engine(TEST_DATABASE_URL, echo=settings.debug)
TestingSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
AsyncSessionScoped = scoped_session(TestingSessionLocal)

@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """Initialize the database (runs once for all tests)."""
    try:
        Database.initialize(settings.database_url)
    except Exception as e:
        pytest.exit(f"Failed to initialize the database: {e}", returncode=1)

@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Create and drop all tables before and after each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session():
    """Provide a transactional database session."""
    async with AsyncSessionScoped() as session:
        yield session
        await session.close()

@pytest.fixture
async def async_client(db_session):
    """Provide an HTTP client for testing with DB override."""
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def email_service():
    """Return a mock or real email service based on settings."""
    if getattr(settings, "send_real_mail", "").lower() == "true":
        return EmailService(template_manager=TemplateManager())
    mock_service = AsyncMock(spec=EmailService)
    mock_service.send_verification_email.return_value = None
    mock_service.send_user_email.return_value = None
    return mock_service

@pytest.fixture
async def create_user(db_session, email_service):
    """Factory to create a user via UserService."""
    async def _create_user(
        email: str = "test@example.com",
        password: str = "SecurePass123!",
        nickname: str = "testuser",
        role: UserRole = UserRole.AUTHENTICATED,
        email_verified: bool = True,
    ):
        user_data = {
            "email": email,
            "password": password,
            "nickname": nickname,
            "role": role,
            "email_verified": email_verified,
        }
        return await UserService.create(db_session, user_data, email_service)
    return _create_user

@pytest.fixture
async def user(db_session):
    """Create a default authenticated user."""
    u = User(
        nickname=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        hashed_password=hash_password("MySuperPassword$1234"),
        role=UserRole.AUTHENTICATED,
        email_verified=False,
        is_locked=False,
    )
    db_session.add(u)
    await db_session.commit()
    return u

@pytest.fixture
async def locked_user(db_session):
    """Create a locked user."""
    u = User(
        nickname=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        hashed_password=hash_password("MySuperPassword$1234"),
        role=UserRole.AUTHENTICATED,
        email_verified=False,
        is_locked=True,
        failed_login_attempts=settings.max_login_attempts,
    )
    db_session.add(u)
    await db_session.commit()
    return u

@pytest.fixture
async def verified_user(db_session):
    """Create a verified user."""
    u = User(
        nickname=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        hashed_password=hash_password("MySuperPassword$1234"),
        role=UserRole.AUTHENTICATED,
        email_verified=True,
        is_locked=False,
    )
    db_session.add(u)
    await db_session.commit()
    return u

@pytest.fixture
async def unverified_user(db_session):
    """Create an unverified user."""
    u = User(
        nickname=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        hashed_password=hash_password("MySuperPassword$1234"),
        role=UserRole.AUTHENTICATED,
        email_verified=False,
        is_locked=False,
    )
    db_session.add(u)
    await db_session.commit()
    return u

@pytest.fixture
async def users_with_same_role_50_users(db_session):
    """Create 50 users with the same role."""
    users = []
    for _ in range(50):
        u = User(
            nickname=fake.user_name(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            hashed_password=hash_password("password"),
            role=UserRole.AUTHENTICATED,
            email_verified=False,
            is_locked=False,
        )
        db_session.add(u)
        users.append(u)
    await db_session.commit()
    return users

@pytest.fixture
async def admin_user(db_session):
    """Create an admin user."""
    u = User(
        nickname="admin_user",
        first_name="John",
        last_name="Doe",
        email="admin@example.com",
        hashed_password=hash_password("securepassword"),
        role=UserRole.ADMIN,
        email_verified=True,
        is_locked=False,
    )
    db_session.add(u)
    await db_session.commit()
    return u

@pytest.fixture
async def manager_user(db_session):
    """Create a manager user."""
    u = User(
        nickname="manager_john",
        first_name="John",
        last_name="Doe",
        email="manager_user@example.com",
        hashed_password=hash_password("securepassword"),
        role=UserRole.MANAGER,
        email_verified=True,
        is_locked=False,
    )
    db_session.add(u)
    await db_session.commit()
    return u

@pytest.fixture
def admin_token(admin_user):
    """Generate JWT token for admin user."""
    data = {"sub": str(admin_user.id), "role": admin_user.role.name}
    return create_access_token(data=data, expires_delta=timedelta(minutes=30))

@pytest.fixture
def manager_token(manager_user):
    """Generate JWT token for manager user."""
    data = {"sub": str(manager_user.id), "role": manager_user.role.name}
    return create_access_token(data=data, expires_delta=timedelta(minutes=30))

@pytest.fixture
def user_token(user):
    """Generate JWT token for authenticated user."""
    data = {"sub": str(user.id), "role": user.role.name}
    return create_access_token(data=data, expires_delta=timedelta(minutes=30))
