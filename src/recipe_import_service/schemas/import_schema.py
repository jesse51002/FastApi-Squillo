"""Shared schemas for recipe import services across all platforms."""

from typing import Optional

from pydantic import BaseModel, Field

from src.database.schemas.recipe_schema import RecipeDisplayData
from src.database.schemas.user_schema import LoadingStatus


class ImportRequest(BaseModel):
    """Request model for recipe import (used by all platforms)."""

    url: str = Field(
        ...,
        description="URL from any supported platform (TikTok, YouTube, Instagram, or recipe website)",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for saving the recipe (if provided, recipe will be saved)",
    )
    mock: bool = Field(
        default=False, description="If True, uses mock data instead of real API calls"
    )
    polling: bool = Field(
        default=False,
        description="If True, return recipe_id immediately for polling instead of waiting for completion",
    )


class ImportResponse(BaseModel):
    """Response model for recipe import (used by all platforms)."""

    recipe: Optional[RecipeDisplayData] = Field(
        None, description="Extracted recipe display data"
    )
    no_recipe_found: bool = Field(
        default=False, description="Whether or not a recipe was found in the video"
    )
    recipe_id: str = Field(..., description="Recipe ID for the imported recipe")


class LlmOutputFormat(BaseModel):
    """Expected LLM output format for recipe extraction."""

    recipe: Optional[str] = Field(
        None,
        description="Recipe in markdown format, or null if no recipe content found",
    )


class PollingRequest(BaseModel):
    """Request model for polling recipe import status."""

    recipe_ids: list[str] = Field(
        ..., description="List of recipe IDs to check status for"
    )
    user_id: str = Field(..., description="User ID who owns the recipes")


class RecipeStatus(BaseModel):
    """Status of a single recipe in polling response."""

    status: LoadingStatus = Field(..., description="Current status of the recipe")
    recipe: Optional[RecipeDisplayData] = Field(
        default=None,
        description="Recipe display data (only present when status is 'completed')",
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if status is 'error'"
    )


class PollingResponse(BaseModel):
    """Response model for polling recipe import status."""

    statuses: dict[str, RecipeStatus] = Field(
        ..., description="Dictionary mapping recipe_id to its status"
    )
