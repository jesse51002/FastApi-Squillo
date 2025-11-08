"""Pydantic schemas for technique extraction API."""

from pydantic import BaseModel, Field
from enum import IntEnum
from typing import Optional

from src.shared.technique_service.schemas import TechniqueDifficulty

class TechniqueExtractionRequest(BaseModel):
    """Request schema for technique extraction."""
    recipe_text: str = Field(
        ...,
        min_length=10,
        description="Raw text of the recipe to extract techniques from"
    )


class TechniqueRelevance(IntEnum):
    small_relevance = 1
    medium_relevance = 2
    strong_relevance = 3

class TechniqueImportance(IntEnum):
    not_important = 1
    small_importance = 2
    medium_importance = 3
    strong_importance = 4
    extreme_importance = 5

class TechniqueInfo(BaseModel):
    id : str = Field(..., description="ID of the chosen technique")
    name: str = Field(..., description="Name of technique chosen")
    reason: str = Field(..., description="How the technique is used in this step")
    relevance: TechniqueRelevance = Field(..., description="Technique Relevance")
    importance: TechniqueImportance = Field(..., description="Technique Importance")
    difficulty: Optional[TechniqueDifficulty] = Field(default=None, description="Techinque difficulty (leave empty in llm call)")

class Ingredient(BaseModel):
    """A single ingredient with quantity and unit."""
    name: str = Field(..., description="Name of the ingredient")
    quantity: str = Field(default="", description="Amount of the ingredient (e.g., '2', '1/2', '3-4', or empty if not specified)")
    unit: str = Field(default="", description="Unit of measurement (e.g., 'cups', 'tablespoons', 'grams', 'whole', 'to taste', 'handful', or empty if not specified)")

class RecipeStep(BaseModel):
    """A single step in a recipe with associated cooking techniques."""
    step_number: float = Field(..., description="The sequential number of this step (supports decimals like 1.1, 1.2 for sub-steps)")
    instruction: str = Field(..., description="The instruction text for this step")
    techniques: list[TechniqueInfo] = Field(
        default_factory=list,
        description="List of cooking techniques used in this step with relevance and importance ratings"
    )

class TechniqueExtractionResponse(BaseModel):
    """Response schema for technique extraction."""
    recipe_name: str = Field(..., description="Name of the recipe")
    ingredients: list[Ingredient] = Field(..., description="List of ingredients needed for the recipe")
    steps: list[RecipeStep] = Field(..., description="List of recipe steps with techniques")
    status: str = Field(default="success", description="Status of the extraction")
