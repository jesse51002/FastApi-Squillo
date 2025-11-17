"""API router for recipe import endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status, Depends
from dependency_injector.wiring import inject, Provide

from src.core.dependencies import DependencyManager
from src.recipe_import_service.services.tiktok_service import TiktokImportService
from src.recipe_import_service.services.youtube_service import YouTubeImportService
from src.recipe_import_service.services.instagram_service import InstagramImportService
from src.recipe_import_service.services.web_recipe_service import WebRecipeService
from src.recipe_import_service.services.media_utils import detect_platform, Platform
from src.recipe_import_service.schemas.import_schema import (
    ImportRequest,
    ImportResponse,
)
from src.database.database_service import DatabaseService
from src.ai_recipe_engine.ai_recipe_service import TechniqueExtractionService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
)


@router.post(
    "/import",
    response_model=ImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import recipe from any supported platform",
    description="Automatically detects platform (TikTok, YouTube, Instagram, or recipe website) and extracts recipe",
)
@inject
async def import_recipe(
    request: ImportRequest,
    tiktok_service: TiktokImportService = Depends(
        Provide[DependencyManager.tiktok_import_service]
    ),
    youtube_service: YouTubeImportService = Depends(
        Provide[DependencyManager.youtube_import_service]
    ),
    instagram_service: InstagramImportService = Depends(
        Provide[DependencyManager.instagram_import_service]
    ),
    web_service: WebRecipeService = Depends(
        Provide[DependencyManager.web_recipe_service]
    ),
    technique_extraction_service: TechniqueExtractionService = Depends(
        Provide[DependencyManager.technique_extraction_service]
    ),
    db_service: DatabaseService = Depends(Provide[DependencyManager.database_service]),
) -> ImportResponse:
    """Import recipe from any supported platform.

    Automatically detects the platform from the URL and routes to the appropriate service.
    Supported platforms: TikTok, YouTube (including Shorts), Instagram (Reels), and recipe websites.

    Args:
        request: The request containing URL, optional user_id, and mock flag
        tiktok_service: Injected TikTok import service
        youtube_service: Injected YouTube import service
        instagram_service: Injected Instagram import service
        web_service: Injected web recipe import service
        technique_service: Injected technique extraction service
        db_service: Injected database service

    Returns:
        ImportResponse: Extracted recipe in markdown format

    Raises:
        HTTPException: If import fails or no recipe found
    """
    try:
        # Validate input
        if not request.url.strip():
            raise ValueError("URL cannot be empty")

        # Detect platform
        platform = detect_platform(request.url)

        # Route to appropriate service
        service = None
        match platform:
            case Platform.TIKTOK:
                service = tiktok_service
            case Platform.YOUTUBE:
                service = youtube_service
            case Platform.INSTAGRAM:
                service = instagram_service
            case Platform.WEB:
                service = web_service

        # Use the service's import_recipe method
        return await service.import_recipe(
            url=request.url,
            user_id=request.user_id,
            technique_extraction_service=technique_extraction_service,
            db_service=db_service,
            mock=request.mock,
        )

    except ValueError as e:
        logger.error("Recipe import failed", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.error("Recipe import failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Recipe import failed",
        )
