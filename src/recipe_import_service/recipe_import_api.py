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

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/import",
)


@router.post(
    "",
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

    Returns:
        ImportResponse: Extracted recipe in markdown format

    Raises:
        HTTPException: If import fails or no recipe found
    """
    try:
        # Validate input
        if not request.url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="URL cannot be empty"
            )

        # Detect platform
        platform = detect_platform(request.url)

        # Route to appropriate service
        match platform:
            case Platform.TIKTOK:
                recipe = await tiktok_service.url_to_text_recipe(
                    request.url, mock=request.mock
                )
            case Platform.YOUTUBE:
                recipe = await youtube_service.url_to_text_recipe(
                    request.url, mock=request.mock
                )
            case Platform.INSTAGRAM:
                recipe = await instagram_service.url_to_text_recipe(
                    request.url, mock=request.mock
                )
            case Platform.WEB:
                recipe = await web_service.url_to_text_recipe(request.url)

        # TODO: Save recipe to database if user_id is provided
        if request.user_id and recipe:
            # Implement database save logic here
            pass

        if recipe is not None:
            return ImportResponse(recipe=recipe, no_recipe_found=False)
        else:
            return ImportResponse(recipe="", no_recipe_found=True)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        logger.error("Recipe import failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Recipe import failed",
        )
