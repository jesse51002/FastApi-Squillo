from pydantic import BaseModel, Field
from enum import IntEnum
from typing import Optional


class TechniqueDifficulty(IntEnum):
    beginner = 1
    novice = 2
    intermediate = 3
    advanced = 4
    expert = 5


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
    image: str = Field("", description="Technique badge image")
    video_url: str = Field("", description="Technique video url")
    background_color: str = Field(
        "", description="Hex color of background for technique"
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
