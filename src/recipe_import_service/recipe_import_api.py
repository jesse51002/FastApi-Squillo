"""API router for recipe import endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from dependency_injector.wiring import inject, Provide

from src.core.dependencies import DependencyManager
from src.recipe_import_service.services.tiktok_service import TiktokImportService
from src.recipe_import_service.schemas.tiktok_schema import TikTokImportRequest, TikTokImportResponse


router = APIRouter(
    prefix="/v1/import",
)


@router.post(
    "/tiktok",
    response_model=TikTokImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import recipe from TikTok video",
    description="Extracts recipe from TikTok video by analyzing audio narration and video description"
)
@inject
async def import_tiktok_recipe(
    request: TikTokImportRequest,
    service: TiktokImportService = Depends(Provide[DependencyManager.tiktok_import_service])
) -> TikTokImportResponse:
    """Import recipe from TikTok video.

    Args:
        request: The request containing TikTok video URL
        service: Injected TikTok import service

    Returns:
        TikTokImportResponse: Extracted recipe in markdown format

    Raises:
        HTTPException: If import fails or no recipe found
    """
    try:
        # Validate input
        if not request.url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TikTok URL cannot be empty"
            )

        # Call service layer
        recipe = await service.url_to_text_recipe(request.url)

        if recipe is not None:
            return TikTokImportResponse(recipe=recipe, no_recipe_found=False)
        else:
            return TikTokImportResponse(recipe="", no_recipe_found=True)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TikTok recipe import failed: {str(e)}"
        )
