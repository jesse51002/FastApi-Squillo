"""Shared schemas for recipe import services across all platforms."""

from pydantic import BaseModel, Field
from typing import Optional


class ImportRequest(BaseModel):
    """Request model for recipe import (used by all platforms)."""
    url: str = Field(..., description="URL from any supported platform (TikTok, YouTube, Instagram, or recipe website)")
    user_id: Optional[str] = Field(default=None, description="User ID for saving the recipe (if provided, recipe will be saved)")
    mock: bool = Field(default=False, description="If True, uses mock data instead of real API calls")


class ImportResponse(BaseModel):
    """Response model for recipe import (used by all platforms)."""
    recipe: str = Field(..., description="Extracted recipe in markdown format")
    no_recipe_found: bool = Field(..., description="Whether or not a recipe was found in the video")


class LlmOutputFormat(BaseModel):
    """Expected LLM output format for recipe extraction."""
    recipe: Optional[str] = Field(None, description="Recipe in markdown format, or null if no recipe content found")
