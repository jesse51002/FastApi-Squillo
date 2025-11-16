import httpx
import base64
from typing import Optional, Any
from enum import Enum
from pathlib import Path

import logging
from src.core.config import settings
from .base import BaseLLMService
from .schemas import (
    MistralTextMessageContent,
    MistralVoiceMessageContent,
    Message,
    ResponseFormat,
    MistralRequest,
    MistralHeaders,
    MistralResponse
)

logger = logging.getLogger(__name__)

COMPLETIONS_API_URL = 'https://api.mistral.ai/v1/chat/completions'


class MistralModels(Enum):
    small = 'mistral-small-latest'
    medium = 'mistral-medium-latest'
    large = 'mistral-large-latest'
    reasoning_medium = 'magistral-medium-latest'
    reasoning_small = 'magistral-small-latest'
    voxtral_small = 'voxtral-small-latest'
    voxtral_mini = 'voxtral-mini-latest'


class MistralService(BaseLLMService):
    """Service for processing voice recordings and converting them to structured recipes using LLM."""

    def __init__(self):
        self.api_key = settings.mistral_api_key

    def get_model_enum(self) -> type[Enum]:
        """Return the MistralModels enum class.

        Returns:
            MistralModels enum class
        """
        return MistralModels

    async def call_llm_api(
        self,
        input_prompt: str,
        json_schema: Optional[dict[str, Any]] = None,
        model: MistralModels = MistralModels.medium
    ) -> Optional[str]:
        """Make the API call to the LLM service.

        Args:
            input_prompt: The text prompt to send to the LLM
            json_schema: Optional JSON schema for structured output.
                        Mistral always uses json_object response format.
                        This parameter is included for interface compatibility.

        Returns:
            The LLM response content as a string, or None if no response

        Raises:
            Exception: If the API call fails or times out
        """

        # Build request using Pydantic models
        # Mistral always uses json_object format, json_schema parameter not used
        request = MistralRequest(
            model=model,
            max_tokens=10000,
            temperature=0.1,
            safe_prompt=True,
            response_format=ResponseFormat(type='json_object'),
            messages=[
                Message(
                    role='user',
                    content=[
                        MistralTextMessageContent(
                            text=input_prompt
                        )
                    ]
                )
            ]
        )

        # Build headers using Pydantic model
        headers_model = MistralHeaders(
            authorization=f'Bearer {self.api_key}'
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    COMPLETIONS_API_URL,
                    headers=headers_model.model_dump(by_alias=True),
                    json=request.model_dump(by_alias=True),
                )

                if response.status_code == 200:
                    # Parse response with Pydantic
                    mistral_response = MistralResponse(**response.json())
                    if mistral_response.choices:
                        output = mistral_response.choices[0].message.content
                        return output
                    return None
                else:
                    # print(f"LLM API Error: {response.status_code} - {response.text}")
                    raise Exception(f"LLM call failed with status {response.status_code}")

            except httpx.TimeoutException:
                raise Exception("LLM API request timed out")
            except Exception as e:
                raise Exception(f"LLM call failed with exception: {str(e)}")

    async def call_voxtral_api(
        self,
        audio_file_path: Path,
        text_prompt: str,
        model: MistralModels = MistralModels.voxtral_small,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """Make the API call to Voxtral for audio + text processing.

        Args:
            audio_file_path: Path to the audio file to process
            text_prompt: The text prompt containing instructions and optional description
            model: Voxtral model to use (voxtral_small or voxtral_mini)
            json_schema: Optional JSON schema for structured output.
                        Mistral always uses json_object response format.
                        This parameter is included for interface compatibility.

        Returns:
            The LLM response content as a string, or None if no response

        Raises:
            Exception: If the API call fails, times out, or audio file not found
        """
        # Validate audio file exists
        if not audio_file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # Read and encode audio file to base64
        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # Build multimodal request with audio and text
        request = MistralRequest(
            model=model,
            max_tokens=10000,
            temperature=0.1,
            safe_prompt=True,
            response_format=ResponseFormat(type='json_object') if json_schema else None,
            messages=[
                Message(
                    role='user',
                    content=[
                        MistralVoiceMessageContent(
                            input_audio=audio_base64
                        ),
                        MistralTextMessageContent(
                            text=text_prompt
                        )
                    ]
                )
            ]
        )

        # Build headers using Pydantic model
        headers_model = MistralHeaders(
            authorization=f'Bearer {self.api_key}'
        )

        async with httpx.AsyncClient(timeout=180.0) as client:  # Longer timeout for audio
            try:
                response = await client.post(
                    COMPLETIONS_API_URL,
                    headers=headers_model.model_dump(by_alias=True),
                    json=request.model_dump(by_alias=True, exclude_none=True),
                )

                if response.status_code == 200:
                    # Parse response with Pydantic
                    mistral_response = MistralResponse(**response.json())
                    if mistral_response.choices:
                        output = mistral_response.choices[0].message.content
                        return output
                    return None
                else:
                    logger.error(f"Voxtral API Error: {response.status_code}")
                    raise Exception(f"Voxtral call failed with status {response.status_code}")

            except httpx.TimeoutException:
                raise Exception("Voxtral API request timed out")
            except Exception as e:
                raise Exception(f"Voxtral call failed with exception: {str(e)}")