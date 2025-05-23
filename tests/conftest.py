"""
File: test_database_operations.py

Overview:
This Python test file utilizes pytest to manage database states and HTTP clients for testing a web application built with FastAPI and SQLAlchemy. It includes detailed fixtures to mock the testing environment, ensuring each test is run in isolation with a consistent setup.

Fixtures:
- `async_client`: Manages an asynchronous HTTP client for testing interactions with the FastAPI application.
- `db_session`: Handles database transactions to ensure a clean database state for each test.
- User fixtures (`user`, `locked_user`, `verified_user`, etc.): Set up various user states to test different behaviors under diverse conditions.
- `token`: Generates an authentication token for testing secured endpoints.
- `initialize_database`: Prepares the database at the session start.
- `setup_database`: Sets up and tears down the database before and after each test.
"""
# pylint: disable=redefined-outer-name

# Standard library imports
from builtins import Exception, range, str
from datetime import timedelta
from unittest.mock import AsyncMock

# Third-party imports
import pytest
from faker import Faker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from alembic import command
from alembic.config import Config
from app.database import Base, Database
from app.dependencies import get_db, get_settings
# Application-specific imports
from app.main import app
from app.models.user_model import User, UserRole
from app.services.email_service import EmailService
from app.services.jwt_service import create_access_token
from app.services.user_service import UserService
from app.utils.security import hash_password
from app.utils.template_manager import TemplateManager

fake = Faker()

settings = get_settings()
TEST_DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)
engine = create_async_engine(TEST_DATABASE_URL, echo=settings.debug)
AsyncTestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
AsyncSessionScoped = scoped_session(AsyncTestingSessionLocal)


@pytest.fixture
def email_service():
    """Set up email"""
    # Assuming the TemplateManager does not need any arguments for initialization
    template_manager = TemplateManager()
    email_service = EmailService(template_manager=template_manager)
    return email_service


# this is what creates the http client for your api tests
@pytest.fixture(scope="function")
async def async_client(db_session):
    """Server"""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            yield client
        finally:
            app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """Initial db"""
    try:
        Database.initialize(settings.database_url)
    except Exception as e:
        pytest.fail(f"Failed to initialize the database: {str(e)}")


# this function setup and tears down (drops tales) for each test function, so you have a clean database for each test.
@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Database set up"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        # you can comment out this line during development if you are debugging a single test
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(setup_database):
    """Database session set up"""
    async with AsyncSessionScoped() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="function")
async def locked_user(db_session):
    """Define locked"""
    unique_email = fake.email()
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": unique_email,
        "hashed_password": hash_password("MySuperPassword$1234"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": False,
        "is_locked": True,
        "failed_login_attempts": settings.max_login_attempts,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture(scope="function")
async def user(db_session):
    """User create"""
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "hashed_password": hash_password("MySuperPassword$1234"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": False,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture(scope="function")
async def verified_user(db_session):
    """Test verified"""
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "hashed_password": hash_password("MySuperPassword$1234"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": True,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture(scope="function")
async def unverified_user(db_session):
    """Test unverified"""
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "hashed_password": hash_password("MySuperPassword$1234"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": False,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture(scope="function")
async def users_with_same_role_50_users(db_session):
    """Recreating users"""
    users = []
    used_nicknames = set()

    for i in range(50):
        nickname = fake.user_name()
        while nickname in used_nicknames:
            nickname = fake.user_name()
        used_nicknames.add(nickname)

        user_data = {
            "nickname": nickname,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),  # optional: helps ensure email uniqueness too
            "hashed_password": hash_password("MySuperPassword$1234"),
            "role": UserRole.AUTHENTICATED,
            "email_verified": False,
            "is_locked": False,
        }
        user = User(**user_data)
        db_session.add(user)
        users.append(user)

    await db_session.commit()
    return users


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """Admin user"""
    user = User(
        nickname="admin_user",
        email="admin@example.com",
        first_name="John",
        last_name="Doe",
        hashed_password="securepassword",
        role=UserRole.ADMIN,
        is_locked=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def manager_user(db_session: AsyncSession):
    """Manager user"""
    user = User(
        nickname="manager_john",
        first_name="John",
        last_name="Doe",
        email="manager_user@example.com",
        hashed_password="securepassword",
        role=UserRole.MANAGER,
        is_locked=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


# Configure a fixture for each type of user role you want to test
@pytest.fixture(scope="function")
def admin_token(admin_user):
    """Admin token create"""
    token_data = {"sub": str(admin_user.id), "role": admin_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))


@pytest.fixture(scope="function")
def manager_token(manager_user):
    """Manager tokens"""
    token_data = {"sub": str(manager_user.id), "role": manager_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))


@pytest.fixture(scope="function")
def user_token(user):
    """Assign token"""
    token_data = {"sub": str(user.id), "role": user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))


@pytest.fixture
def email_service():
    """Email service"""
    if settings.send_real_mail == "true":
        # Return the real email service when specifically testing email functionality
        return EmailService()
    else:
        # Otherwise, use a mock to prevent actual email sending
        mock_service = AsyncMock(spec=EmailService)
        mock_service.send_verification_email.return_value = None
        mock_service.send_user_email.return_value = None
        return mock_service


@pytest.fixture
async def create_user(db_session):
    """Create user function"""
    async def _create_user(
        email: str = "test@example.com",
        password: str = "SecurePass123!",
        nickname: str = "testuser",
        role: UserRole = UserRole.AUTHENTICATED,
        email_verified: bool = True,
    ):
        # Mock the email service with no-op behavior
        mock_email_service = AsyncMock()
        mock_email_service.send_verification_email = AsyncMock(return_value=None)

        user_data = {
            "email": email,
            "password": password,
            "nickname": nickname,
            "role": role,
            "email_verified": email_verified,
        }

        return await UserService.create(db_session, user_data, mock_email_service)

    return _create_user


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Migrate alembic"""
    alembic_cfg = Config("alembic.ini")  # or your actual path
    command.upgrade(alembic_cfg, "head")
