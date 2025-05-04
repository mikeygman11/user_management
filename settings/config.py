"""Application configuration loaded from environment or .env file."""
from pydantic import Field, AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Pydantic settings for application configuration."""

    max_login_attempts: int = Field(
        default=3,
        description="Maximum allowed failed login attempts",
    )

    server_base_url: AnyUrl = Field(
        default='http://localhost',
        description="Base URL of the server",
    )
    server_download_folder: str = Field(
        default='downloads',
        description="Folder for storing downloaded files",
    )

    secret_key: str = Field(
        default='secret-key',
        description="Secret key for encryption",
    )
    algorithm: str = Field(
        default='HS256',
        description="Algorithm used for encryption",
    )
    access_token_expire_minutes: int = Field(
        default=15,
        description="Expiration time for access tokens (minutes)",
    )
    refresh_token_expire_minutes: int = Field(
        default=1440,
        description="Expiration time for refresh tokens (minutes)",
    )

    admin_user: str = Field(
        default='admin',
        description="Default admin username",
    )
    admin_password: str = Field(
        default='secret',
        description="Default admin password",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode outputs errors and SQLAlchemy queries",
    )

    database_url: str = Field(
        default='postgresql+asyncpg://user:password@postgres/myappdb',
        description="URL for connecting to the database",
    )
    postgres_user: str = Field(
        default='user',
        description="PostgreSQL username",
    )
    postgres_password: str = Field(
        default='password',
        description="PostgreSQL password",
    )
    postgres_server: str = Field(
        default='localhost',
        description="PostgreSQL server address",
    )
    postgres_port: str = Field(
        default='5432',
        description="PostgreSQL port",
    )
    postgres_db: str = Field(
        default='myappdb',
        description="PostgreSQL database name",
    )

    discord_bot_token: str = Field(
        default='NONE',
        description="Discord bot token",
    )
    discord_channel_id: int = Field(
        default=1234567890,
        description="Default Discord channel ID for the bot to interact",
    )

    openai_api_key: str = Field(
        default='NONE',
        description="OpenAI API key",
    )
    send_real_mail: bool = Field(
        default=False,
        description="Whether to send real emails or use mocks",
    )

    smtp_server: str = Field(
        default='smtp.mailtrap.io',
        description="SMTP server for sending emails",
    )
    smtp_port: int = Field(
        default=2525,
        description="SMTP port for sending emails",
    )
    smtp_username: str = Field(
        default='your-mailtrap-username',
        description="Username for SMTP server",
    )
    smtp_password: str = Field(
        default='your-mailtrap-password',
        description="Password for SMTP server",
    )

    class Config:
        """Configuration for reading environment variables."""
        env_file = ".env"
        env_file_encoding = 'utf-8'


# Instantiate settings to be imported in application modules
settings = Settings()
