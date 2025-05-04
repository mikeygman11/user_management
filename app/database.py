"""Database configuration module for setting up async SQLAlchemy engine and session."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Database:
    """Handles database connections and sessions."""

    _engine = None
    _session_factory = None

    @classmethod
    def initialize(cls, database_url: str, echo: bool = False):
        """Initialize the async engine and sessionmaker.

        Args:
            database_url (str): The database connection URL.
            echo (bool): Whether to enable SQLAlchemy query logging.
        """
        if cls._engine is None:  # Ensure engine is created once
            cls._engine = create_async_engine(database_url, echo=echo, future=True)
            cls._session_factory = sessionmaker(
                bind=cls._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                future=True,
            )

    @classmethod
    def get_session_factory(cls):
        """Returns the session factory, ensuring it's initialized.

        Raises:
            ValueError: If the session factory has not been initialized yet.

        Returns:
            sessionmaker: A configured SQLAlchemy session factory.
        """
        if cls._session_factory is None:
            raise ValueError("Database not initialized. Call `initialize()` first.")
        return cls._session_factory
