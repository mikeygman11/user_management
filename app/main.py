"""Main FastAPI application setup and configuration."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import Database
from .dependencies import get_settings
from .routers.user_routes import router as user_router
from .utils.api_description import getDescription

app = FastAPI(
    title="User Management",
    description=getDescription(),
    version="0.0.1",
    contact={
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the database connection on startup."""
    settings = get_settings()
    Database.initialize(settings.database_url, settings.debug)


@app.exception_handler(Exception)
async def exception_handler(_: Request, __: Exception) -> JSONResponse:
    """
    Handle uncaught exceptions and return a generic error response.
    """
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )


app.include_router(user_router)
