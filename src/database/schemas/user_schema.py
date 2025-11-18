"""User schema for database storage."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr, field_validator

from src.database.schemas.recipe_schema import RecipeDisplayData
from src.database.database_utils import validate_user_id


class TechniqueWatchSession(BaseModel):
    """Individual watch session for a technique video."""

    watched_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of the video watched in this session (0-100)",
    )
    watch_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when this watch session occurred",
    )


class TechniqueViewingInfo(BaseModel):
    """Detailed viewing information for a technique video."""

    technique_id: str = Field(..., description="Unique identifier for the technique")
    watch_history: list[TechniqueWatchSession] = Field(
        default_factory=list,
        description="List of watch sessions with percentage and timestamp",
    )
    skipped: bool = Field(False, description="Whether the technique video was skipped")


class UserCreate(BaseModel):
    """Request schema for creating a new user."""

    user_id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., min_length=1, description="Username for the user")
    email: EmailStr = Field(..., description="Email address for the user")

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v: str) -> str:
        """Validate user_id format using shared validator."""
        return validate_user_id(v)


class User(BaseModel):
    """User schema stored in the database."""

    user_id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username for the user")
    email: EmailStr = Field(..., description="Email address for the user")
    recipes: list[RecipeDisplayData] = Field(
        default_factory=list,
        description="List of recipe display data owned by this user",
    )
    techniques_watched: list[TechniqueViewingInfo] = Field(
        default_factory=list,
        description="Detailed viewing information for technique videos",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Recipe creation time",
    )

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v: str) -> str:
        """Validate user_id format using shared validator."""
        return validate_user_id(v)


class UserResponse(BaseModel):
    """Response schema for user operations."""

    user_id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username for the user")
    email: EmailStr = Field(..., description="Email address for the user")
    recipes: list[RecipeDisplayData] = Field(
        default_factory=list,
        description="List of recipe display data owned by this user",
    )
    created_at: datetime = Field(..., description="Timestamp when the user was created")

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v: str) -> str:
        """Validate user_id format using shared validator."""
        return validate_user_id(v)
