"""Pydantic schemas for technique extraction API."""

from pydantic import BaseModel, Field
from enum import IntEnum

from src.shared.technique_service.schemas import TechniqueDifficulty


class TechniqueExtractionRequest(BaseModel):
    """Request schema for technique extraction."""

    recipe_text: str = Field(
        ...,
        min_length=10,
        description="Raw text of the recipe to extract techniques from",
    )


class RecipeDifficulty(IntEnum):
    simple = 1
    medium = 2
    complex = 3


class TechniqueImportance(IntEnum):
    not_important = 1
    small_importance = 2
    medium_importance = 3
    strong_importance = 4
    extreme_importance = 5


class ExtractionTechniqueInfo(BaseModel):
    id: str = Field(..., description="ID of the chosen technique")
    name: str = Field(..., description="Name of technique chosen")
    importance: TechniqueImportance = Field(..., description="Technique Importance")
    difficulty: TechniqueDifficulty = Field(
        default=TechniqueDifficulty.novice,
        description="Techinque difficulty (leave empty in llm call)",
    )


class ExtractionIngredient(BaseModel):
    """A single ingredient with quantity and unit."""

    name: str = Field(..., description="Name of the ingredient")
    quantity: str = Field(
        default="",
        description="Amount of the ingredient (e.g., '2', '1/2', '3-4', or empty if not specified)",
    )
    unit: str = Field(
        default="",
        description="Unit of measurement (e.g., 'cups', 'tablespoons', 'grams', 'whole', 'to taste', 'handful', or empty if not specified)",
    )


class ExtractionRecipeStep(BaseModel):
    """A single step in a recipe with associated cooking techniques."""

    step_number: str = Field(
        ...,
        description="The sequential number of this step (supports decimals like 1.1, 1.2 for sub-steps)",
    )
    instruction: str = Field(..., description="The instruction text for this step")
    techniques: list[ExtractionTechniqueInfo] = Field(
        default_factory=list,
        description="List of cooking techniques used in this step with relevance and importance ratings",
    )
    estimated_time: float = Field(
        ...,
        description="The estimated amount of time the step will take in minutes (decimals allowed)",
    )
    is_active_step: bool = Field(
        ...,
        description="Whether it is an active step (doing) or a passive step (waiting)",
    )


class TechniqueExtractionResponse(BaseModel):
    """Response schema for technique extraction."""

    recipe_name: str = Field(..., description="Name of the recipe")
    ingredients: list[ExtractionIngredient] = Field(
        ..., description="List of ingredients needed for the recipe"
    )
    steps: list[ExtractionRecipeStep] = Field(
        ..., description="List of recipe steps with techniques"
    )
    difficulty: RecipeDifficulty = Field(..., description="Difficulty of recipe (1-3)")
    servings: int = Field(..., description="How many servings this recipe has")
    active_time: float = Field(
        default=0.0, description="Total active time for the recipe in minutes"
    )
    total_time: float = Field(
        default=0.0, description="Total time for the recipe in minutes"
    )
