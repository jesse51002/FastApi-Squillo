"""Web recipe-specific schemas for scraped data."""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class WebRecipeData(BaseModel):
    """Structured recipe data extracted from web pages."""
    title: str = Field(..., description="Recipe name/title")
    ingredients: List[str] = Field(..., description="List of ingredient strings")
    instructions: str = Field(..., description="Step-by-step cooking instructions")
    total_time: Optional[int] = Field(None, description="Total time in minutes")
    prep_time: Optional[int] = Field(None, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(None, description="Cooking time in minutes")
    yields: Optional[str] = Field(None, description="Serving size/yield (e.g., '4 servings')")
    image: Optional[str] = Field(None, description="Recipe image URL")
    description: Optional[str] = Field(None, description="Recipe description/summary")

    class Config:
        extra = "ignore"
