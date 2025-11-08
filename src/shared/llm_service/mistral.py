import httpx
from typing import Optional
from enum import Enum

import logging
from src.core.config import settings
from .schemas import (
    MessageContent,
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


class MistralService:
    """Service for processing voice recordings and converting them to structured recipes using LLM."""

    def __init__(self):
        self.api_key = settings.mistral_api_key

    async def call_llm_api(self, input_prompt: str) -> Optional[str]:
        """Make the API call to the LLM service.

        Args:
            input_prompt: The text prompt to send to the LLM

        Returns:
            The LLM response content as a string, or None if no response

        Raises:
            Exception: If the API call fails or times out
        """

        logger.debug(f"Input promt:\n\n {input_prompt}")

        # Build request using Pydantic models
        request = MistralRequest(
            model=MistralModels.medium.value,
            max_tokens=5000,
            temperature=0.2,
            safe_prompt=True,
            response_format=ResponseFormat(type='json_object'),
            messages=[
                Message(
                    role='user',
                    content=[
                        MessageContent(
                            type='text',
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

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    COMPLETIONS_API_URL,
                    headers=headers_model.model_dump(by_alias=True),
                    json=request.model_dump(by_alias=True)
                )

                if response.status_code == 200:
                    # Parse response with Pydantic
                    mistral_response = MistralResponse(**response.json())
                    if mistral_response.choices:
                        output = mistral_response.choices[0].message.content
                        return output
                    return None
                else:
                    print(f"LLM API Error: {response.status_code} - {response.text}")
                    raise Exception(f"LLM call failed with status {response.status_code}: {response.text}")

            except httpx.TimeoutException:
                raise Exception("LLM API request timed out")
            except Exception as e:
                raise Exception(f"LLM call failed with exception: {str(e)}")