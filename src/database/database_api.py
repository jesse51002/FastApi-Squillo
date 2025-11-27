"""API router for database operations (users and recipes)."""

import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.dependencies import DependencyManager
from src.database.database_service import DatabaseService
from src.database.schemas.recipe_schema import RecipeDisplayData, StoredRecipe
from src.database.schemas.user_schema import (
    UserCreate,
    UserCreateResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/database",
    tags=["database"],
)


@router.post(
    "/create-user",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a new user in the database",
)
@inject
async def create_user(
    user_create: UserCreate,
    db_service: DatabaseService = Depends(Provide[DependencyManager.database_service]),
) -> UserCreateResponse:
    """Create a new user.

    Args:
        user_create: User creation request with user_id and username
        db_service: Injected database service

    Returns:
        UserCreateResponse with success flag and optional error message

    Raises:
        HTTPException: Never raised - errors are returned in response
    """
    try:
        await db_service.save_user(user_create)
        return UserCreateResponse(success=True)
    except ValueError as e:
        return UserCreateResponse(success=False, error=str(e))
    except Exception:
        logger.error("Failed to create user", exc_info=True)
        return UserCreateResponse(success=False, error="Failed to create user")


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Retrieves a user's information by their ID",
)
@inject
async def get_user(
    user_id: str,
    db_service: DatabaseService = Depends(Provide[DependencyManager.database_service]),
) -> UserResponse:
    """Retrieve a user by ID.

    Args:
        user_id: The unique identifier of the user
        db_service: Injected database service

    Returns:
        UserResponse with user details

    Raises:
        HTTPException: If user not found or retrieval fails
    """
    try:
        user = await db_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found",
            )

        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to retrieve user", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )


@router.get(
    "/users/{user_id}/recipes",
    response_model=list[RecipeDisplayData],
    status_code=status.HTTP_200_OK,
    summary="Get all recipes for user",
    description="Retrieves all recipes belonging to a user",
)
@inject
async def get_user_recipes(
    user_id: str,
    db_service: DatabaseService = Depends(Provide[DependencyManager.database_service]),
) -> list[RecipeDisplayData]:
    """Get all recipes for a user.

    Args:
        user_id: The ID of the user
        db_service: Injected database service

    Returns:
        List of recipes owned by the user

    Raises:
        HTTPException: If user not found or retrieval fails
    """
    try:
        recipes = await db_service.get_all_recipes_from_user(user_id)
        return recipes
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:
        logger.error("Failed to retrieve user recipes", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipes",
        )


@router.get(
    "/recipes/{recipe_id}",
    response_model=StoredRecipe,
    status_code=status.HTTP_200_OK,
    summary="Get recipe by ID",
    description="Retrieves a specific recipe's full details by its ID",
)
@inject
async def get_recipe(
    recipe_id: str,
    db_service: DatabaseService = Depends(Provide[DependencyManager.database_service]),
) -> StoredRecipe:
    """Retrieve a recipe by ID.

    Args:
        recipe_id: The unique identifier of the recipe
        db_service: Injected database service

    Returns:
        StoredRecipe with full recipe details including ingredients and steps

    Raises:
        HTTPException: If recipe not found or retrieval fails
    """
    try:
        recipe = await db_service.get_recipe(recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID '{recipe_id}' not found",
            )
        return recipe
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to retrieve recipe", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipe",
        )
