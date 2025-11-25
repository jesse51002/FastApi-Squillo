"""Mock database service for storing users and recipes in-memory."""

import asyncio
import logging
from typing import Optional

import yaml

from src.core.constants import MOCK_DATA_PATH
from src.database.schemas.recipe_schema import RecipeDisplayData, StoredRecipe
from src.database.schemas.user_schema import User, UserCreate

logger = logging.getLogger(__name__)


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
    _lock: asyncio.Lock

    def __init__(self) -> None:
        """Initialize the database service.

        Note: Storage is class-level, so all instances share the same data.
        """
        if self._lock is None:
            self.__class__._lock = asyncio.Lock()
        self._load_mock_data()

    def _load_mock_data(self) -> None:
        """Load mock data from YAML file into the database.

        Loads users and recipes from the mock_data.yaml file in the resources
        directory. Only loads data if the file exists and databases are empty.
        """
        if not MOCK_DATA_PATH.exists():
            logger.warning("No mock data file found, starting with empty database")
            return

        if self._users or self._recipes:
            logger.info("Database already populated, skipping mock data load")
            return

        try:
            with open(MOCK_DATA_PATH, "r", encoding="utf-8") as file:
                mock_data = yaml.safe_load(file)

            if not mock_data:
                logger.warning("Mock data file is empty")
                return

            users_data = mock_data.get("users", [])
            recipes_data = mock_data.get("recipes", [])

            for user_data in users_data:
                user = User(**user_data)
                self._users[user.user_id] = user

            for recipe_data in recipes_data:
                recipe = StoredRecipe(**recipe_data)
                self._recipes[recipe.recipe_id] = recipe

                user = self._users.get(recipe.user_id)
                if user:
                    recipe_display = self.create_recipe_display(recipe)
                    user.recipes.append(recipe_display)
                else:
                    logger.warning(
                        f"Recipe {recipe.recipe_id} references "
                        f"non-existent user {recipe.user_id}"
                    )

            logger.info(
                f"Loaded {len(self._users)} users and "
                f"{len(self._recipes)} recipes from mock data"
            )

        except Exception as e:
            logger.error(f"Failed to load mock data: {e}", exc_info=True)
            raise

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
            )
            self._users[user_create.user_id] = user
            return user

    async def update_user(self, user: User) -> User:
        """Update an existing user's data.

        Args:
            user: User object with updated data

        Returns:
            The updated User object

        Raises:
            ValueError: If the user doesn't exist
        """
        async with self._lock:
            if user.user_id not in self._users:
                raise ValueError(f"User with ID '{user.user_id}' not found")

            self._users[user.user_id] = user
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

            if recipe.recipe_id in self._recipes:
                raise ValueError(f"Recipe with id {recipe.recipe_id} already exists")

            # Store the full recipe
            self._recipes[recipe.recipe_id] = recipe

            # Add recipe display data to user's list if not already present
            if any(r.recipe_id == recipe.recipe_id for r in user.recipes):
                raise ValueError(f"Recipe id {recipe.recipe_id} already exists")

            recipe_display = self.create_recipe_display(recipe)
            user.recipes.append(recipe_display)

            return recipe_display

    def create_recipe_display(self, recipe: StoredRecipe) -> RecipeDisplayData:
        """Create RecipeDisplayData from a StoredRecipe.

        Extracts technique IDs and calculates time metrics for display.

        Args:
            recipe: The full recipe to create display data from

        Returns:
            RecipeDisplayData with all calculated fields
        """
        # Extract unique technique IDs
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
