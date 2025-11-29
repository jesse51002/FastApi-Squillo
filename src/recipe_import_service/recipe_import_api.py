"""API router for recipe import endpoints."""

import logging
from datetime import datetime, timezone

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi import status as HTTPStatus

from src.core.dependencies import DependencyManager
from src.database.database_service import DatabaseService
from src.database.database_utils import generate_recipe_id
from src.database.schemas.recipe_schema import LoadingRecipe, LoadingStatus
from src.recipe_import_service.schemas.import_schema import (
    ImportRequest,
    ImportResponse,
    PollingRequest,
    PollingResponse,
)
from src.recipe_import_service.services.instagram_service import InstagramImportService
from src.recipe_import_service.services.media_utils import Platform, detect_platform
from src.recipe_import_service.services.tiktok_service import TiktokImportService
from src.recipe_import_service.services.web_recipe_service import WebRecipeService
from src.recipe_import_service.services.youtube_service import YouTubeImportService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
)


@router.post(
    "/import",
    response_model=ImportResponse,
    status_code=HTTPStatus.HTTP_200_OK,
    summary="Import recipe from any supported platform",
    description="Automatically detects platform (TikTok, YouTube, Instagram, or recipe website) and extracts recipe",
)
@inject
async def import_recipe(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
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

        # Validate user_id is provided
        if not request.user_id:
            raise ValueError("user_id is required")

        # Generate recipe ID and add to loading queue
        recipe_id = generate_recipe_id()
        loading_recipe = LoadingRecipe(
            recipe_id=recipe_id,
            original_link=request.url,
            time_started=datetime.now(timezone.utc),
            status=LoadingStatus.PROCESSING,
        )
        await db_service.add_loading_recipe(request.user_id, loading_recipe)

        # If polling mode, queue background task and return immediately
        if request.polling:
            background_tasks.add_task(
                service.import_recipe,
                url=request.url,
                recipe_id=recipe_id,
                user_id=request.user_id,
                db_service=db_service,
                mock=request.mock,
            )

            logger.info(f"Recipe {recipe_id} queued for background processing")
            return ImportResponse(
                recipe=None,
                no_recipe_found=False,
                recipe_id=recipe_id,
            )

        # Synchronous processing - process immediately and return result
        return await service.import_recipe(
            url=request.url,
            recipe_id=recipe_id,
            user_id=request.user_id,
            db_service=db_service,
            mock=request.mock,
        )

    except ValueError as e:
        logger.error("Recipe import failed", exc_info=True)
        raise HTTPException(status_code=HTTPStatus.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.error("Recipe import failed", exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Recipe import failed",
        )


@router.post(
    "/import/poll",
    response_model=PollingResponse,
    status_code=HTTPStatus.HTTP_200_OK,
    summary="Poll recipe import status",
    description="Check the status of one or more recipe imports by recipe IDs",
)
@inject
async def poll_recipe_status(
    request: PollingRequest,
    tiktok_service: TiktokImportService = Depends(
        Provide[DependencyManager.tiktok_import_service]
    ),
) -> PollingResponse:
    """Poll the status of recipe imports.

    For each recipe_id:
    - If in loading_recipes: returns the current status (processing, extracting_techniques, error)
    - If in recipes table: returns "completed"
    - If in neither: returns "error" with message (orphaned state)

    Args:
        request: The request containing recipe_ids list and user_id
        tiktok_service: Injected service (any service can be used as they all inherit from BaseImportService)

    Returns:
        PollingResponse: Dictionary mapping recipe_id to status

    Raises:
        HTTPException: If user not found or other errors
    """
    try:
        return await tiktok_service.poll_recipe_status(request)

    except ValueError as e:
        logger.error("Poll recipe status failed", exc_info=True)
        raise HTTPException(status_code=HTTPStatus.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.error("Poll recipe status failed", exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Poll recipe status failed",
        )
