"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.dependencies import container
from src.database.database_api import router as database_router
from src.educational_engine.educational_engine_api import (
    router as educational_router,
)
from src.recipe_import_service.recipe_import_api import router as import_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods.split(","),
        allow_headers=settings.cors_headers.split(","),
    )

    # Wire dependency injection container
    container.wire(
        modules=[
            __name__,
            "src.recipe_import_service.recipe_import_api",
            "src.database.database_api",
            "src.educational_engine.educational_engine_api",
        ]
    )

    # Include routers
    app.include_router(import_router)
    app.include_router(database_router)
    app.include_router(educational_router)

    return app


app = create_app()


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for health check.

    Returns:
        dict: Basic application information
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}
