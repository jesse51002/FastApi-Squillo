"""Educational engine schemas for technique recommendations."""

from typing import Optional
from pydantic import BaseModel, Field

from src.shared.technique_service.schemas import Technique


class TechniqueRecommendationRequest(BaseModel):
    """Request schema for getting technique recommendation."""

    recipe_id: str = Field(..., description="Unique identifier for the recipe")
    user_id: str = Field(..., description="Unique identifier for the user")
    step_number: str = Field(
        ..., description="Step number in the recipe (can be decimal like 1.1)"
    )


class TechniqueRecommendationResponse(BaseModel):
    """Response schema for technique recommendation.

    Returns a recommended technique for the user based on the recipe step
    and their learning history.
    """

    technique: Optional[Technique] = Field(
        None,
        description=(
            "Recommended technique for the step. " "None if step has no techniques."
        ),
    )
    prerequisite: Optional[Technique] = Field(
        None,
        description=(
            "Prerequisite technique that should be watched first. "
            "None if no prerequisite exists."
        ),
    )
    already_watched: bool = Field(
        False,
        description=(
            "True if the recommended technique was already watched by the user. "
            "Indicates all techniques in this step have been watched."
        ),
    )


class MarkTechniqueWatchedRequest(BaseModel):
    """Request schema for marking a technique as watched."""

    user_id: str = Field(..., description="Unique identifier for the user")
    technique_id: str = Field(..., description="Unique identifier for the technique")
    watched_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of the video watched (0-100)",
    )
    skipped: bool = Field(False, description="Whether the technique video was skipped")


class MarkTechniqueWatchedResponse(BaseModel):
    """Response schema for marking technique as watched."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Success or error message")
    total_watch_sessions: int = Field(
        ..., description="Total count of watch sessions for this technique"
    )
