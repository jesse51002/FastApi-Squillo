import httpx
import json
from typing import Optional, Any
from enum import Enum

import logging
from src.core.config import settings
from .base import BaseLLMService
from .schemas import (
    ClaudeMessage,
    ClaudeRequest,
    ClaudeHeaders,
    ClaudeResponse,
    ClaudeTool,
    ClaudeToolChoice,
    ClaudeToolInputSchema
)

logger = logging.getLogger(__name__)

COMPLETIONS_API_URL = 'https://api.anthropic.com/v1/messages'


class ClaudeModels(Enum):
    """Available Claude model versions."""
    haiku = 'claude-haiku-4-5'
    sonnet = 'claude-sonnet-4-5'
    opus = 'claude-opus-4-1'


class ClaudeService(BaseLLMService):
    """Service for processing prompts using Claude's API."""

    def __init__(self):
        self.api_key = settings.claude_api_key

    def get_model_enum(self) -> type[Enum]:
        """Return the ClaudeModels enum class.

        Returns:
            ClaudeModels enum class
        """
        return ClaudeModels

    async def call_llm_api(
        self,
        input_prompt: str,
        json_schema: Optional[dict[str, Any]] = None
    ) -> Optional[str]:
        """Make the API call to the Claude API service.

        Args:
            input_prompt: The text prompt to send to Claude
            json_schema: Optional JSON schema for structured output using tool calling.
                        If provided, Claude will use a tool to ensure JSON output.

        Returns:
            The Claude response content as a string, or None if no response.
            If json_schema is provided, returns the JSON output from tool use.

        Raises:
            Exception: If the API call fails or times out
        """

        logger.debug(f"Input prompt:\\n\\n {input_prompt}")

        # Build base request
        request_data = {
            'model': ClaudeModels.sonnet.value,
            'max_tokens': 10000,
            'temperature': 0,
            'messages': [
                ClaudeMessage(
                    role='user',
                    content=input_prompt
                )
            ]
        }

        # If JSON schema is provided, use tool calling for structured output
        if json_schema:
            tool = ClaudeTool(
                name='provide_json_response',
                description='Provide a structured JSON response matching the required schema',
                input_schema=ClaudeToolInputSchema(
                    type='object',
                    properties=json_schema.get('properties', {}),
                    required=json_schema.get('required', [])
                )
            )
            request_data['tools'] = [tool]
            request_data['tool_choice'] = ClaudeToolChoice(
                type='tool',
                name='provide_json_response'
            )

        # Build request using Pydantic models
        request = ClaudeRequest(**request_data)

        # Build headers using Pydantic model
        headers_model = ClaudeHeaders(
            x_api_key=self.api_key
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    COMPLETIONS_API_URL,
                    headers=headers_model.model_dump(by_alias=True),
                    json=request.model_dump(by_alias=True, exclude_none=True),
                )

                if response.status_code == 200:
                    # Parse response with Pydantic
                    claude_response = ClaudeResponse(**response.json())
                    if claude_response.content:
                        # If we used tool calling, extract JSON from tool use
                        if json_schema and claude_response.content[0].type == 'tool_use':
                            tool_input = claude_response.content[0].input
                            return json.dumps(tool_input)
                        # Otherwise return text content
                        elif claude_response.content[0].text:
                            output = claude_response.content[0].text
                            return output
                    return None
                else:
                    print(f"LLM API Error: {response.status_code} - {response.text}")
                    raise Exception(f"LLM call failed with status {response.status_code}: {response.text}")

            except httpx.TimeoutException:
                raise Exception("LLM API request timed out")
            except Exception as e:
                raise Exception(f"LLM call failed with exception: {str(e)}")
