"""Educational engine schemas for technique recommendations."""

from typing import Optional

from pydantic import BaseModel, Field


class TechniqueRecommendationRequest(BaseModel):
    """Request schema for getting technique recommendation."""

    recipe_id: str = Field(..., description="Unique identifier for the recipe")
    user_id: str = Field(..., description="Unique identifier for the user")
    step_number: str = Field(
        ..., description="Step number in the recipe (can be decimal like 1.1)"
    )


class SimplifiedTechnique(BaseModel):
    """Simplified technique information for recommendations."""

    id: str = Field(..., description="Technique ID")
    name: str = Field(..., description="Technique name")
    description: str = Field(..., description="Technique description")
    video_url: str = Field(..., description="Technique video URL")
    image: str = Field(..., description="Base technique image")
    badge_image: Optional[str] = Field(None, description="Technique badge image")


class TechniqueRecommendationResponse(BaseModel):
    """Response schema for technique recommendation.

    Returns a recommended technique for the user based on the recipe step
    and their learning history.
    """

    technique: Optional[SimplifiedTechnique] = Field(
        None,
        description=(
            "Recommended technique for the step. None if step has no techniques."
        ),
    )
    prerequisite: Optional[SimplifiedTechnique] = Field(
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
