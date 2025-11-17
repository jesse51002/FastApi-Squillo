"""Recipe schema for database storage."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from src.ai_recipe_engine.schema import TechniqueExtractionResponse
from src.ai_recipe_engine.schema import RecipeDifficulty
from src.database.database_utils import validate_recipe_id, validate_user_id


class StoredRecipe(TechniqueExtractionResponse):
    """Recipe schema that extends TechniqueExtractionResponse with storage metadata.

    This schema inherits all fields from TechniqueExtractionResponse:
    - recipe_name: str
    - ingredients: list[ExtractionIngredient]
    - steps: list[ExtractionRecipeStep]
    - status: str

    And adds storage-specific fields for tracking and user association.
    """

    recipe_id: str = Field(..., description="Unique identifier for the recipe")
    user_id: str = Field(..., description="ID of the user who owns this recipe")
    source_url: Optional[str] = Field(
        default=None, description="Original URL where the recipe was imported from"
    )
    thumbnail_url: Optional[str] = Field(
        default=None, description="URL to the recipe thumbnail image"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the recipe was saved",
    )
    active_time: float = Field(..., description="Active time in a recipe")
    total_time: float = Field(..., description="Total time in a recipe")
    creation_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Recipe creation time",
    )

    @field_validator("recipe_id")
    @classmethod
    def _validate_recipe_id(cls, v: str) -> str:
        """Validate recipe_id format using shared validator."""
        return validate_recipe_id(v)

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v: str) -> str:
        """Validate user_id format using shared validator."""
        return validate_user_id(v)


class RecipeDisplayData(BaseModel):
    """Lightweight recipe schema for displaying recipe summaries in lists.

    Contains only the essential information needed to display a recipe card
    or list item, without the full recipe details.
    """

    recipe_id: str = Field(..., description="Unique identifier for the recipe")
    recipe_name: str = Field(..., description="Name of the recipe")
    thumbnail_url: Optional[str] = Field(
        default=None, description="URL to the recipe thumbnail image"
    )
    difficulty: RecipeDifficulty = Field(
        default=None,
        description="Overall recipe difficulty based on the most difficult technique used",
    )
    technique_ids: list[str] = Field(
        default_factory=list,
        description="List of technique IDs used in this recipe",
    )

    @field_validator("recipe_id")
    @classmethod
    def _validate_recipe_id(cls, v: str) -> str:
        """Validate recipe_id format using shared validator."""
        return validate_recipe_id(v)
