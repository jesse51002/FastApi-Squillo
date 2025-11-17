"""Base class for recipe import services across all platforms."""

import json
import logging
from pathlib import Path
from typing import Optional

from src.shared.llm_service.mistral import MistralService
from src.ai_recipe_engine.ai_recipe_service import TechniqueExtractionService
from src.database.database_service import DatabaseService
from src.recipe_import_service.schemas.import_schema import (
    LlmOutputFormat,
    ImportResponse,
)
from src.util.template_formatter import TemplateFormatter
from src.database.schemas.recipe_schema import RecipeDisplayData, StoredRecipe
from src.database.database_utils import generate_recipe_id


logger = logging.getLogger(__name__)


class BaseImportService:
    """Base class for recipe import services (TikTok, YouTube, Instagram, etc.)."""

    # Subclasses should define these
    MODEL: Optional[str] = None
    TEMPLATE_PATH: Optional[Path] = None

    def __init__(self, mistral_service: MistralService) -> None:
        """Initialize base import service.

        Args:
            mistral_service: Mistral LLM service for recipe extraction
        """
        self.mistral_service = mistral_service

    async def import_recipe(
        self,
        url: str,
        user_id: Optional[str],
        technique_extraction_service: TechniqueExtractionService,
        db_service: DatabaseService,
        mock: bool = False,
    ) -> ImportResponse:
        """Import recipe from URL with validation and optional database storage.

        Args:
            url: URL from any supported platform
            user_id: Optional user ID for saving the recipe
            technique_extraction_service: Service for extracting techniques from recipe text
            db_service: Database service instance for saving recipes
            mock: If True, uses mock data instead of real API calls

        Returns:
            ImportResponse with recipe data or no_recipe_found flag

        Raises:
            ValueError: If URL is empty or invalid
            Exception: If recipe extraction or database operation fails
        """
        if not url.strip():
            raise ValueError("URL cannot be empty")

        # Extract recipe and thumbnail from platform
        recipe, thumbnail_url = await self._url_to_text_recipe(url, mock=mock)

        # Return early if no recipe found
        if recipe is None:
            return ImportResponse(recipe=None, no_recipe_found=True)

        # Extract techniques from the recipe text
        extraction_result = await technique_extraction_service.extract_techniques(
            recipe
        )

        # Save recipe to database if user_id is provided
        if user_id:
            stored_recipe = StoredRecipe(
                **extraction_result.model_dump(),
                recipe_id=generate_recipe_id(),
                user_id=user_id,
                source_url=url,
                thumbnail_url=thumbnail_url,
            )

            recipe_display = await db_service.add_recipe_to_user(user_id, stored_recipe)
            logger.info(
                f"Recipe '{stored_recipe.recipe_name}' saved for user {user_id}"
            )
            return ImportResponse(
                recipe=recipe_display,
                no_recipe_found=False,
            )

        # Return recipe without saving to database
        return ImportResponse(
            recipe=RecipeDisplayData(
                recipe_id=generate_recipe_id(),
                recipe_name=extraction_result.recipe_name,
                thumbnail_url=thumbnail_url,
                difficulty=extraction_result.difficulty,
                technique_ids=list(
                    {
                        technique.id
                        for step in extraction_result.steps
                        for technique in step.techniques
                    }
                ),
            ),
            no_recipe_found=False,
        )

    async def _url_to_text_recipe(
        self, url: str, mock: bool = False
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract and create a recipe from a video URL.

        This method should be overridden by subclasses.

        Args:
            url: Video URL from the platform
            mock: If True, uses mock data instead of real API calls

        Returns:
            Tuple of (recipe in markdown format, thumbnail URL) or (None, None) if no recipe found

        Raises:
            Exception: If any step in the pipeline fails
        """
        raise NotImplementedError("Subclasses must implement _url_to_text_recipe")

    async def _create_text_recipe_with_audio(
        self, audio_file: Path, description: str
    ) -> Optional[str]:
        """Create recipe from audio and description using Voxtral (shared method).

        Args:
            audio_file: Path to extracted audio file
            description: Video description text

        Returns:
            Recipe in markdown format, or None if no recipe found

        Raises:
            Exception: If LLM processing fails or validation fails
        """
        # Get JSON schema from LlmOutputFormat
        json_schema = LlmOutputFormat.model_json_schema()
        str_json_schema = json.dumps(json_schema, indent=2)

        # Format the template with description and schema
        prompt = TemplateFormatter.format_template(
            self.TEMPLATE_PATH, description=description, schema=str_json_schema
        )

        # Call Voxtral API with audio and prompt
        response = await self.mistral_service.call_voxtral_api(
            audio_file_path=audio_file,
            text_prompt=prompt,
            model=self.MODEL,
            json_schema=json_schema,
        )

        if not response:
            raise Exception("No response received from Mistral Voxtral API")

        # Parse and validate the JSON response using Pydantic
        try:
            llm_output = LlmOutputFormat.model_validate_json(response)
            return llm_output.recipe

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            raise Exception(f"LLM response validation failed: {str(e)}")

    async def _create_text_recipe_with_transcript(
        self, transcript: str = "", description: str = ""
    ) -> Optional[str]:
        """Create recipe from transcript and/or description using Mistral (shared method).

        Args:
            transcript: Extracted transcript text (optional)
            description: Video description text (optional)

        Returns:
            Recipe in markdown format, or None if no recipe found

        Raises:
            ValueError: If both transcript and description are None
            Exception: If LLM processing fails or validation fails
        """
        # Ensure at least one of transcript or description is provided
        if transcript == "" and description == "":
            raise ValueError(
                "At least one of transcript or description must be provided"
            )

        # Get JSON schema from LlmOutputFormat
        json_schema = LlmOutputFormat.model_json_schema()
        str_json_schema = json.dumps(json_schema, indent=2)

        # Format the template with transcript, description, and schema
        prompt = TemplateFormatter.format_template(
            self.TEMPLATE_PATH,
            transcript=transcript or "",
            description=description or "",
            schema=str_json_schema,
        )

        # Call Mistral API with text prompt
        response = await self.mistral_service.call_llm_api(
            input_prompt=prompt, model=self.MODEL, json_schema=json_schema
        )

        if not response:
            raise Exception("No response received from Mistral API")

        # Parse and validate the JSON response using Pydantic
        try:
            llm_output = LlmOutputFormat.model_validate_json(response)
            return llm_output.recipe

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            raise Exception(f"LLM response validation failed: {str(e)}")
