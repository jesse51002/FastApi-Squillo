"""API router for technique service endpoints."""

import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.dependencies import DependencyManager
from src.technique_service.schemas import (
    BatchTechniquesRequest,
    BatchTechniquesResponse,
    SimplifiedTechnique,
)
from src.technique_service.technique_service import TechniqueService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/techniques",
    tags=["techniques"],
)


@router.post(
    "/batch",
    response_model=BatchTechniquesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get multiple techniques by IDs",
    description=(
        "Returns a list of simplified techniques for the provided technique IDs. "
        "All IDs must be valid or the request will fail."
    ),
)
@inject
async def get_techniques_batch(
    request: BatchTechniquesRequest,
    service: TechniqueService = Depends(Provide[DependencyManager.technique_service]),
) -> BatchTechniquesResponse:
    """Get multiple techniques by their IDs.

    Args:
        request: The request containing list of technique IDs
        service: Injected technique service

    Returns:
        BatchTechniquesResponse: List of simplified techniques

    Raises:
        HTTPException: If any technique ID is not found
    """
    try:
        techniques = service.get_techniques_by_ids(request.technique_ids)

        # Convert to SimplifiedTechnique format
        simplified_techniques = [
            SimplifiedTechnique(
                id=technique.id,
                name=technique.name,
                description=technique.description,
                video_url=technique.video_url,
                image=technique.image,
                badge_image=technique.badge_image,
            )
            for technique in techniques
        ]

        return BatchTechniquesResponse(techniques=simplified_techniques)

    except ValueError as e:
        logger.error("Batch technique retrieval failed", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        logger.error("Batch technique retrieval failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch technique retrieval failed",
        )
