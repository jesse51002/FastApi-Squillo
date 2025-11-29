from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, Field


class TechniqueDifficulty(IntEnum):
    beginner = 1
    novice = 2
    intermediate = 3
    advanced = 4
    expert = 5


class SimplifiedTechnique(BaseModel):
    """Simplified technique information for recommendations."""

    id: str = Field(..., description="Technique ID")
    name: str = Field(..., description="Technique name")
    description: str = Field(..., description="Technique description")
    video_url: str = Field(..., description="Technique video URL")
    image: str = Field(..., description="Base technique image")
    badge_image: Optional[str] = Field(None, description="Technique badge image")
    background_color: str = Field(
        default="#B1C4E2", description="Hex color of background for technique"
    )


class BatchTechniquesRequest(BaseModel):
    """Request schema for batch technique retrieval."""

    technique_ids: list[str] = Field(
        ...,
        description="List of technique IDs to retrieve",
        min_length=1,
    )


class BatchTechniquesResponse(BaseModel):
    """Response schema for batch technique retrieval."""

    techniques: list[SimplifiedTechnique] = Field(
        ...,
        description="List of simplified techniques",
    )


class Technique(BaseModel):
    """Response schema for technique extraction."""

    id: str = Field(..., description="Id for the technique")
    name: str = Field(..., description="Name of the technique")
    description: str = Field(..., description="Description of the technique")
    difficulty: TechniqueDifficulty = Field(
        ..., description="Technique difficulty on a scale of one to five"
    )
    tips: list[str] = Field(
        default_factory=list,
        description="Tips that can be used to fully understand the technique",
    )
    image: str = Field(
        "https://drive.google.com/uc?export=download&id=1EBNx0AQZdndF-6tfct4_w_kp90Ad009M",
        description="Base technique image",
    )
    badge_image: Optional[str] = Field(None, description="Technique badge image")
    video_url: str = Field("", description="Technique video url")
    background_color: str = Field(
        "#000000", description="Hex color of background for technique"
    )
    restrict_classification: bool = Field(
        False,
        description="Whether or not to let this technique be classified during technique extractions (some techniques should be manually recommended based on other techniques)",
    )
    prerequisite_video: Optional[str] = Field(
        None,
        description="Video to be recommended to user before they watch this one (This is usually a saftey or basics technique)",
    )
    video_overwrite: Optional[str] = Field(
        None,
        description="Video to overwrite if it was also recommended (this is usually when there is a less specific version of the technique)",
    )
