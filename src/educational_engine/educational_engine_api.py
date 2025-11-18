"""API router for educational engine endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status, Depends
from dependency_injector.wiring import inject, Provide

from src.core.dependencies import DependencyManager
from src.educational_engine.schemas import (
    TechniqueRecommendationRequest,
    TechniqueRecommendationResponse,
    MarkTechniqueWatchedRequest,
    MarkTechniqueWatchedResponse,
)
from src.educational_engine.educational_engine_service import (
    EducationalEngineService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/educational-engine",
    tags=["educational-engine"],
)


@router.post(
    "/recommend",
    response_model=TechniqueRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get technique recommendation for recipe step",
    description=(
        "Returns a recommended technique for a user based on their "
        "recipe step and learning history. Prioritizes unwatched techniques."
    ),
)
@inject
async def get_technique_recommendation(
    request: TechniqueRecommendationRequest,
    service: EducationalEngineService = Depends(
        Provide[DependencyManager.educational_engine_service]
    ),
) -> TechniqueRecommendationResponse:
    """Get technique recommendation for a specific recipe step.

    Args:
        request: The request containing recipe_id, user_id, and step_number
        service: Injected educational engine service

    Returns:
        TechniqueRecommendationResponse: Recommended technique with prerequisite

    Raises:
        HTTPException: If recommendation fails
    """
    try:
        result = await service.get_technique_recommendation(
            recipe_id=request.recipe_id,
            user_id=request.user_id,
            step_number=request.step_number,
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        logger.error("Technique recommendation failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Technique recommendation failed",
        )


@router.post(
    "/mark-watched",
    response_model=MarkTechniqueWatchedResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark technique as watched",
    description=(
        "Records a watch session for a technique video, "
        "including watch percentage and timestamp."
    ),
)
@inject
async def mark_technique_watched(
    request: MarkTechniqueWatchedRequest,
    service: EducationalEngineService = Depends(
        Provide[DependencyManager.educational_engine_service]
    ),
) -> MarkTechniqueWatchedResponse:
    """Mark a technique as watched with viewing details.

    Args:
        request: The request containing user_id, technique_id, and viewing info
        service: Injected educational engine service

    Returns:
        MarkTechniqueWatchedResponse: Success status and watch session count

    Raises:
        HTTPException: If marking watched fails
    """
    try:
        result = await service.mark_technique_watched(
            user_id=request.user_id,
            technique_id=request.technique_id,
            watched_percentage=request.watched_percentage,
            skipped=request.skipped,
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        logger.error("Mark technique watched failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark technique as watched",
        )
