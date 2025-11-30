"""Recipe schema for database storage."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.ai_recipe_engine.schema import (
    ExtractionIngredient,
    RecipeDifficulty,
    TechniqueExtractionResponse,
)
from src.database.database_utils import validate_recipe_id, validate_user_id


class LoadingStatus(str, Enum):
    """Status values for recipes being imported and polled."""

    LOADING = "loading"
    PROCESSING = "processing"
    EXTRACTING_TECHNIQUES = "extracting_techniques"
    COMPLETED = "completed"
    ERROR = "error"


class LoadingRecipe(BaseModel):
    """Schema for tracking recipes currently being imported."""

    recipe_id: str = Field(..., description="Unique identifier for the recipe")
    original_link: str = Field(
        ..., description="Original URL from which the recipe is being imported"
    )
    time_started: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the import started",
    )
    status: LoadingStatus = Field(
        default=LoadingStatus.PROCESSING,
        description="Current status of the import",
    )


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
        ...,
        description="Overall recipe difficulty based on the most difficult technique used",
    )
    technique_ids: list[str] = Field(
        default_factory=list,
        description="List of technique IDs used in this recipe",
    )
    created_at: datetime = Field(
        ...,
        description="Recipe creation time",
    )

    @field_validator("recipe_id")
    @classmethod
    def _validate_recipe_id(cls, v: str) -> str:
        """Validate recipe_id format using shared validator."""
        return validate_recipe_id(v)


class StoreIngredient(ExtractionIngredient):
    checked: bool = Field(
        default=False, description="Whether the ingredient has been checked"
    )


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
        default="https://plus.unsplash.com/premium_photo-1694547926001-f2151e4a476b?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8Zm9vZCUyMHBob3RvZ3JhcGh5fGVufDB8fDB8fHww",
        description="URL to the recipe thumbnail image",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Recipe creation time",
    )
    ingredients: list[StoreIngredient] = Field(  # pyright: ignore
        ..., description="List of ingredients needed for the recipe"
    )

    @field_validator("recipe_id")
    @classmethod
    def _validate_recipe_id(cls, v: str) -> str:
        """Validate recipe_id format using shared validator."""
        return validate_recipe_id(v)


class UserRecipesResponse(BaseModel):
    """Response schema for getting all recipes for a user.

    Contains both completed recipes and recipes currently being loaded.
    """

    recipes: list[RecipeDisplayData] = Field(
        default_factory=list,
        description="List of completed recipes owned by the user",
    )
    loading_recipes: list[LoadingRecipe] = Field(
        default_factory=list,
        description="List of recipes currently being imported",
    )


class UpdateIngredientCheckedRequest(BaseModel):
    """Request schema for updating ingredient checked status."""

    recipe_id: str = Field(..., description="Unique identifier for the recipe")
    user_id: str = Field(..., description="ID of the user who owns the recipe")
    ingredient_name: str = Field(..., description="Name of the ingredient to update")
    checked: bool = Field(..., description="New checked status for the ingredient")

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


class UpdateIngredientCheckedResponse(BaseModel):
    """Response schema for updating ingredient checked status."""

    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Success or error message")
    ingredient_name: str = Field(..., description="Name of the updated ingredient")
    checked: bool = Field(..., description="New checked status")
