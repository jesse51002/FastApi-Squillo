"""Mock database service for storing users and recipes in-memory."""

import asyncio
from typing import Optional
from datetime import datetime
import uuid

from src.database.schemas.user_schema import User, UserCreate
from src.database.schemas.recipe_schema import StoredRecipe, RecipeDisplayData


class DatabaseService:
    """Singleton service for managing in-memory user and recipe storage.

    This service provides thread-safe CRUD operations for users and recipes
    using in-memory dictionaries. All instances share the same storage.

    Attributes:
        _users: Dictionary mapping user_id to User objects
        _recipes: Dictionary mapping recipe_id to StoredRecipe objects
        _lock: Async lock for thread-safe operations
    """

    _users: dict[str, User] = {}
    _recipes: dict[str, StoredRecipe] = {}
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        """Initialize the database service.

        Note: Storage is class-level, so all instances share the same data.
        """
        pass

    async def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID.

        Args:
            user_id: The unique identifier of the user

        Returns:
            User object if found, None otherwise
        """
        async with self._lock:
            return self._users.get(user_id)

    async def save_user(self, user_create: UserCreate) -> User:
        """Create and save a new user.

        Args:
            user_create: User creation request with user_id and username

        Returns:
            The created User object

        Raises:
            ValueError: If a user with the given user_id already exists
        """
        async with self._lock:
            if user_create.user_id in self._users:
                raise ValueError(f"User with ID '{user_create.user_id}' already exists")

            user = User(
                user_id=user_create.user_id,
                username=user_create.username,
                email=user_create.email,
                recipes=[],
                created_at=datetime.now(),
            )
            self._users[user_create.user_id] = user
            return user

    async def add_recipe_to_user(
        self, user_id: str, recipe: StoredRecipe
    ) -> RecipeDisplayData:
        """Add a recipe to a user's collection.

        Args:
            user_id: The ID of the user to add the recipe to
            recipe: The recipe to add (must have recipe_id set)

        Returns:
            The stored recipe object

        Raises:
            ValueError: If the user doesn't exist or recipe_id is missing
        """
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User with ID '{user_id}' not found")

            if not recipe.recipe_id:
                raise ValueError("Recipe must have a recipe_id")

            # Store the full recipe
            self._recipes[recipe.recipe_id] = recipe

            # Add recipe display data to user's list if not already present
            if any(r.recipe_id == recipe.recipe_id for r in user.recipes):
                raise ValueError(f"Recipe id {recipe.recipe_id} already exists")

            recipe_display = self.create_recipe_display(recipe)
            user.recipes.append(recipe_display)

            return recipe_display

    def create_recipe_display(self, recipe: StoredRecipe):
        technique_ids = set()
        for step in recipe.steps:
            for technique in step.techniques:
                technique_ids.add(technique.id)

        # Create RecipeDisplayData for the user's list
        return RecipeDisplayData(
            recipe_id=recipe.recipe_id,
            recipe_name=recipe.recipe_name,
            thumbnail_url=recipe.thumbnail_url,
            difficulty=recipe.difficulty,
            technique_ids=list(technique_ids),
        )

    async def get_all_recipes_from_user(self, user_id: str) -> list[RecipeDisplayData]:
        """Retrieve all recipes belonging to a user.

        Args:
            user_id: The ID of the user

        Returns:
            List of StoredRecipe objects owned by the user

        Raises:
            ValueError: If the user doesn't exist
        """
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User with ID '{user_id}' not found")
            return user.recipes

    async def get_recipe(self, recipe_id: str) -> Optional[StoredRecipe]:
        """Retrieve a specific recipe by its ID.

        Args:
            recipe_id: The unique identifier of the recipe

        Returns:
            StoredRecipe object if found, None otherwise
        """
        async with self._lock:
            return self._recipes.get(recipe_id)

    @staticmethod
    def generate_recipe_id() -> str:
        """Generate a unique recipe ID.

        Returns:
            A UUID4 string to use as a recipe ID
        """
        return str(uuid.uuid4())
