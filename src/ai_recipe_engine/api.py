"""API router for technique extraction endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from dependency_injector.wiring import inject, Provide

from src.core.dependencies import DependencyManager
from .schema import TechniqueExtractionRequest, TechniqueExtractionResponse
from .service import TechniqueExtractionService


router = APIRouter(
    prefix="/v1",
)


@router.post(
    "/techinque-extract",
    response_model=TechniqueExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract cooking techniques from recipe",
    description="Analyzes raw recipe text and extracts structured steps with cooking techniques",
)
@inject
async def extract_techniques(
    request: TechniqueExtractionRequest,
    service: TechniqueExtractionService = Depends(
        Provide[DependencyManager.technique_extraction_service]
    ),
) -> TechniqueExtractionResponse:
    """Extract cooking techniques from recipe text.

    Args:
        request: The request containing raw recipe text
        service: Injected technique extraction service

    Returns:
        TechniqueExtractionResponse: Structured recipe with extracted techniques

    Raises:
        HTTPException: If extraction fails
    """
    try:
        # Validate input
        if not request.recipe_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipe text cannot be empty",
            )

        # Call service layer
        result = await service.extract_techniques(request.recipe_text)
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Technique extraction failed: {str(e)}",
        )
