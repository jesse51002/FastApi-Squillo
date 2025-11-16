from pydantic import BaseModel, Field
from enum import IntEnum


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
        ..., description="Tips that can be used to fully understand the technique"
    )
