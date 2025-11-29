"""Mock database service for storing users and recipes in-memory."""

import asyncio
import logging
from datetime import datetime, timezone

import yaml

from src.core.constants import LOADING_RECIPE_TIMEOUT_SECONDS, MOCK_DATA_PATH
from src.database.schemas.recipe_schema import (
    LoadingRecipe,
    LoadingStatus,
    RecipeDisplayData,
    StoredRecipe,
    UserRecipesResponse,
)
from src.database.schemas.user_schema import (
    User,
    UserCreate,
)

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

    async def get_user(self, user_id: str) -> User:
        """Retrieve a user by their ID.

        Args:
            user_id: The unique identifier of the user

        Returns:
            User object if found, None otherwise
        """

        if user_id not in self._users:
            logger.error(f"User {user_id} not found")
            raise ValueError(f"User with ID '{user_id}' not found")

        async with self._lock:
            return self._users[user_id]

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

        if user.user_id not in self._users:
            raise ValueError(f"User with ID '{user.user_id}' not found")

        async with self._lock:
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
            created_at=recipe.created_at,
        )

    async def get_all_recipes_from_user(self, user_id: str) -> UserRecipesResponse:
        """Retrieve all recipes and loading recipes belonging to a user.

        Args:
            user_id: The ID of the user

        Returns:
            UserRecipesResponse containing completed recipes and loading recipes

        Raises:
            ValueError: If the user doesn't exist
        """
        # Check for timeouts before retrieving
        await self._check_loading_recipe_timeouts(user_id)

        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User with ID '{user_id}' not found")

            # Convert loading_recipes dict to list
            loading_recipes_list = list(user.loading_recipes.values())

            response = UserRecipesResponse(
                recipes=user.recipes,
                loading_recipes=loading_recipes_list,
            )

            # Remove all recipes in ERROR state after preparing response
            error_recipe_ids = [
                lr.recipe_id
                for lr in loading_recipes_list
                if lr.status == LoadingStatus.ERROR
            ]
            for recipe_id in error_recipe_ids:
                user.loading_recipes.pop(recipe_id, None)
                logger.info(f"Removed error recipe {recipe_id} from loading_recipes")

            return response

    async def get_recipe(self, recipe_id: str) -> StoredRecipe:
        """Retrieve a specific recipe by its ID.

        Args:
            recipe_id: The unique identifier of the recipe

        Returns:
            StoredRecipe object if found, None otherwise
        """

        if recipe_id not in self._recipes:
            logger.error(f"Recipe {recipe_id} not found")
            raise ValueError(f"Recipe with ID '{recipe_id}' not found")

        async with self._lock:
            return self._recipes[recipe_id]

    async def update_ingredient_checked(
        self, recipe_id: str, user_id: str, ingredient_name: str, checked: bool
    ) -> StoredRecipe:
        """Update the checked status of an ingredient in a recipe.

        Args:
            recipe_id: The unique identifier of the recipe
            user_id: The ID of the user who owns the recipe
            ingredient_name: The name of the ingredient to update
            checked: The new checked status

        Returns:
            The updated StoredRecipe object

        Raises:
            ValueError: If recipe not found, user doesn't own recipe, or ingredient not found
        """
        async with self._lock:
            # Verify recipe exists
            if recipe_id not in self._recipes:
                raise ValueError(f"Recipe with ID '{recipe_id}' not found")

            recipe = self._recipes[recipe_id]

            # Verify user owns the recipe
            if recipe.user_id != user_id:
                raise ValueError(
                    f"Recipe '{recipe_id}' does not belong to user '{user_id}'"
                )

            # Find and update the ingredient
            ingredient_found = False
            for ingredient in recipe.ingredients:
                if ingredient.name.lower() == ingredient_name.lower():
                    ingredient.checked = checked
                    ingredient_found = True
                    break

            if not ingredient_found:
                raise ValueError(
                    f"Ingredient '{ingredient_name}' not found in recipe '{recipe_id}'"
                )

            return recipe

    async def add_loading_recipe(
        self, user_id: str, loading_recipe: LoadingRecipe
    ) -> None:
        """Add a recipe to user's loading_recipes dict.

        Args:
            user_id: The ID of the user
            loading_recipe: The LoadingRecipe object to add

        Raises:
            ValueError: If the user doesn't exist
        """
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User with ID '{user_id}' not found")

            if loading_recipe.recipe_id in user.loading_recipes:
                raise ValueError(
                    f"Recipe with ID '{loading_recipe.recipe_id}' already exists in user's loading_recipes"
                )

            user.loading_recipes[loading_recipe.recipe_id] = loading_recipe

    async def remove_loading_recipe(self, user_id: str, recipe_id: str) -> None:
        """Remove a recipe from user's loading_recipes dict.

        Args:
            user_id: The ID of the user
            recipe_id: The ID of the recipe to remove

        Raises:
            ValueError: If the user doesn't exist
        """
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User with ID '{user_id}' not found")

            user.loading_recipes.pop(recipe_id, None)

    async def update_loading_recipe_status(
        self, user_id: str, recipe_id: str, status: LoadingStatus
    ) -> None:
        """Update the status of a loading recipe.

        Args:
            user_id: The ID of the user
            recipe_id: The ID of the recipe to update
            status: The new status value

        Raises:
            ValueError: If the user or loading recipe doesn't exist
        """
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User with ID '{user_id}' not found")

            loading_recipe = user.loading_recipes.get(recipe_id)
            if not loading_recipe:
                raise ValueError(
                    f"Loading recipe with ID '{recipe_id}' not found for user '{user_id}'"
                )

            loading_recipe.status = status

    async def get_loading_recipes(self, user_id: str) -> dict[str, LoadingRecipe]:
        """Get all loading recipes for a user.

        Args:
            user_id: The ID of the user

        Returns:
            Dictionary of loading recipes keyed by recipe_id

        Raises:
            ValueError: If the user doesn't exist
        """
        # Check for timeouts before retrieving
        await self._check_loading_recipe_timeouts(user_id)

        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User with ID '{user_id}' not found")

            return user.loading_recipes.copy()

    async def _check_loading_recipe_timeouts(self, user_id: str) -> None:
        """Check for loading recipes that have exceeded the timeout and mark them as ERROR.

        This method goes through all loading recipes for a user and marks any that have been
        processing for longer than LOADING_RECIPE_TIMEOUT_SECONDS as ERROR state.

        Args:
            user_id: The ID of the user whose loading recipes to check

        Raises:
            ValueError: If the user doesn't exist
        """
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User with ID '{user_id}' not found")

            now = datetime.now(timezone.utc)
            timed_out_recipes = []

            # Find all recipes that have timed out
            for recipe_id, loading_recipe in user.loading_recipes.items():
                elapsed_seconds = (now - loading_recipe.time_started).total_seconds()
                if elapsed_seconds > LOADING_RECIPE_TIMEOUT_SECONDS:
                    timed_out_recipes.append(recipe_id)

            # Mark timed out recipes as ERROR
            for recipe_id in timed_out_recipes:
                loading_recipe = user.loading_recipes[recipe_id]
                loading_recipe.status = LoadingStatus.ERROR
                logger.error(
                    f"Recipe {recipe_id} timed out after {LOADING_RECIPE_TIMEOUT_SECONDS} seconds"
                )
