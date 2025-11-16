"""Base class for recipe import services across all platforms."""

import json
import logging
from pathlib import Path
from typing import Optional

from src.shared.llm_service.mistral import MistralService
from src.recipe_import_service.schemas.import_schema import LlmOutputFormat
from src.util.template_formatter import TemplateFormatter


logger = logging.getLogger(__name__)


class BaseImportService:
    """Base class for recipe import services (TikTok, YouTube, Instagram, etc.)."""

    # Subclasses should define these
    MODEL = None
    TEMPLATE_PATH = None

    def __init__(self, mistral_service: MistralService):
        """Initialize base import service.

        Args:
            mistral_service: Mistral LLM service for recipe extraction
        """
        self.mistral_service = mistral_service

    async def url_to_text_recipe(self, url: str, mock: bool = False) -> Optional[str]:
        """Extract and create a recipe from a video URL.

        This method should be overridden by subclasses.

        Args:
            url: Video URL from the platform
            mock: If True, uses mock data instead of real API calls

        Returns:
            Recipe in markdown format, or None if no recipe found

        Raises:
            Exception: If any step in the pipeline fails
        """
        raise NotImplementedError("Subclasses must implement url_to_text_recipe")

    async def _create_text_recipe_with_audio(
        self,
        audio_file: Path,
        description: str
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
            self.TEMPLATE_PATH,
            description=description,
            schema=str_json_schema
        )

        # Call Voxtral API with audio and prompt
        response = await self.mistral_service.call_voxtral_api(
            audio_file_path=audio_file,
            text_prompt=prompt,
            model=self.MODEL,
            json_schema=json_schema
        )

        if not response:
            raise Exception("No response received from Mistral Voxtral API")

        # Parse and validate the JSON response using Pydantic
        try:
            llm_output = LlmOutputFormat.model_validate_json(response)
            return llm_output.recipe

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to validate LLM response: {e}")
            raise Exception(f"LLM response validation failed: {str(e)}")

    async def _create_text_recipe_with_transcript(
        self,
        transcript: str = "",
        description: str = ""
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
            raise ValueError("At least one of transcript or description must be provided")

        # Get JSON schema from LlmOutputFormat
        json_schema = LlmOutputFormat.model_json_schema()
        str_json_schema = json.dumps(json_schema, indent=2)

        # Format the template with transcript, description, and schema
        prompt = TemplateFormatter.format_template(
            self.TEMPLATE_PATH,
            transcript=transcript or "",
            description=description or "",
            schema=str_json_schema
        )

        # Call Mistral API with text prompt
        response = await self.mistral_service.call_llm_api(
            input_prompt=prompt,
            model=self.MODEL,
            json_schema=json_schema
        )

        if not response:
            raise Exception("No response received from Mistral API")

        # Parse and validate the JSON response using Pydantic
        try:
            llm_output = LlmOutputFormat.model_validate_json(response)
            return llm_output.recipe

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to validate LLM response: {e}")
            raise Exception(f"LLM response validation failed: {str(e)}")
