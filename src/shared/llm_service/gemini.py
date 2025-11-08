from google import genai
from google.genai import types

from pydantic import BaseModel, Field, create_model
from typing import Optional, Any
from enum import Enum

import logging
from src.core.config import settings
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class GeminiModels(Enum):
    """Available Gemini model versions."""
    flash = 'gemini-2.5-flash'
    pro = 'gemini-1.5-pro-latest'
    flash_lite = 'gemini-2.5-flash-lite'


class GeminiService(BaseLLMService):
    """Service for processing prompts using Google's Gemini API via official SDK."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.client = genai.Client(api_key=self.api_key)

    def get_model_enum(self) -> type[Enum]:
        """Return the GeminiModels enum class.

        Returns:
            GeminiModels enum class
        """
        return GeminiModels

    async def call_llm_api(
        self,
        input_prompt: str,
        json_schema: Optional[dict[str, Any]] = None
    ) -> Optional[str]:
        """Make the API call to the Gemini API service using official SDK.

        Args:
            input_prompt: The text prompt to send to Gemini
            json_schema: Optional JSON schema for structured output.
                        If provided, Gemini will use response_json_schema to ensure JSON output.

        Returns:
            The Gemini response content as a string, or None if no response.
            If json_schema is provided, returns the JSON output.

        Raises:
            Exception: If the API call fails or times out
        """

        logger.debug(f"Input prompt:\\n\\n {input_prompt}")

        try:
            # Build base config
            config = {
                "temperature": 0,
            }

            # If JSON schema is provided, use Gemini's native JSON mode with Pydantic model
            if json_schema:
                # Create a Pydantic model from the schema
                # response_model = self._create_pydantic_model_from_schema(json_schema)

                config["response_mime_type"] = "application/json"
                config["response_json_schema"] = json_schema

                logger.debug(f"Using JSON schema with Gemini")

            # Make the API call using the official SDK
            response = self.client.models.generate_content(
                model=GeminiModels.flash.value,
                contents=input_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget= 2500),
                    response_json_schema=json_schema,
                    response_mime_type="application/json" if json_schema else None
                ),
            )

            # Extract and return the text response
            if response.text:
                return response.text
            
            raise Exception("No response from gemini")

        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            raise e
