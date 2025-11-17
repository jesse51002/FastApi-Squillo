"""Database utility functions for ID generation and other common operations."""

import re
import uuid
from datetime import datetime


def generate_recipe_id() -> str:
    """Generate a unique recipe ID with embedded timestamp.

    Creates a recipe ID in the format: recipe_YYYYMMDD_uuid4
    This allows for chronological sorting while maintaining uniqueness.

    Returns:
        A unique recipe ID string with date prefix

    Example:
        "recipe_20250116_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    date_str = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())
    return f"recipe_{date_str}_{unique_id}"


def generate_user_id() -> str:
    """Generate a unique user ID with embedded timestamp.

    Creates a user ID in the format: user_YYYYMMDD_uuid4
    This allows for chronological sorting while maintaining uniqueness.

    Returns:
        A unique user ID string with date prefix

    Example:
        "user_20250116_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    date_str = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())
    return f"user_{date_str}_{unique_id}"


def validate_recipe_id(recipe_id: str) -> str:
    """Validate that recipe_id follows the expected format.

    Expected format: recipe_YYYYMMDD_<uuid>
    Example: recipe_20250116_a1b2c3d4-e5f6-7890-abcd-ef1234567890

    Args:
        recipe_id: The recipe_id to validate

    Returns:
        The validated recipe_id

    Raises:
        ValueError: If the recipe_id doesn't match the expected format
    """
    pattern = (
        r"^recipe_\d{8}_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    )
    if not re.match(pattern, recipe_id):
        raise ValueError(
            f"Invalid recipe_id format: '{recipe_id}'. "
            "Expected format: recipe_YYYYMMDD_<uuid> "
            "(e.g., 'recipe_20250116_a1b2c3d4-e5f6-7890-abcd-ef1234567890')"
        )
    return recipe_id


def validate_user_id(user_id: str) -> str:
    """Validate that user_id follows the expected format.

    Expected format: user_YYYYMMDD_<uuid>
    Example: user_20250116_a1b2c3d4-e5f6-7890-abcd-ef1234567890

    Args:
        user_id: The user_id to validate

    Returns:
        The validated user_id

    Raises:
        ValueError: If the user_id doesn't match the expected format
    """
    pattern = (
        r"^user_\d{8}_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    )
    if not re.match(pattern, user_id):
        raise ValueError(
            f"Invalid user_id format: '{user_id}'. "
            "Expected format: user_YYYYMMDD_<uuid> "
            "(e.g., 'user_20250116_a1b2c3d4-e5f6-7890-abcd-ef1234567890')"
        )
    return user_id
