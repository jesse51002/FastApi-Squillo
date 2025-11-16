"""User schema for database storage."""

from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

from src.database.schemas.recipe_schema import RecipeDisplayData


class UserCreate(BaseModel):
    """Request schema for creating a new user."""

    user_id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., min_length=1, description="Username for the user")
    email: EmailStr = Field(..., description="Email address for the user")


class User(BaseModel):
    """User schema stored in the database."""

    user_id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username for the user")
    email: EmailStr = Field(..., description="Email address for the user")
    recipes: list[RecipeDisplayData] = Field(
        default_factory=list,
        description="List of recipe display data owned by this user",
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp when the user was created"
    )


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
