"""Main application entry point for the FastAPI service."""

from builtins import Exception

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.database import Database
from app.dependencies import get_settings
from app.routers import user_routes
from app.utils.api_description import getDescription

# Initialize the FastAPI app with metadata and description
app = FastAPI(
    title="User Management",
    description=getDescription(),
    version="0.0.1",
    contact={
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

# CORS middleware configuration
# This middleware will enable CORS and allow requests from any origin
# It can be configured to allow specific methods, headers, and origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,  # Support credentials (cookies, authorization headers, etc.)
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)


@app.on_event("startup")
async def startup_event():
    """Initialize the database connection on application startup."""
    settings = get_settings()
    Database.initialize(settings.database_url, settings.debug)


@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """Global exception handler for unexpected server errors."""
    return JSONResponse(
        status_code=500, content={"message": "An unexpected error occurred."}
    )


# Register the user-related API routes
app.include_router(user_routes.router)
