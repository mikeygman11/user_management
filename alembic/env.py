import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.models.user_model import Base  # Adjust this if needed

# Alembic config object
config = context.config

# Load logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Provide your metadata for Alembic to do `autogenerate`
target_metadata = Base.metadata

# Read DB URL from env or alembic.ini
from os import getenv
db_url = getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline():
    """Run migrations without a DB connection (offline mode)."""
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations with a DB connection (online mode)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=None,
    )

    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(
                context.configure,
                connection=connection,
                target_metadata=target_metadata,
            )
            await connection.run_sync(context.run_migrations)

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
