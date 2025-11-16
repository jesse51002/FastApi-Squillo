"""Base abstract class for LLM services."""

from abc import ABC, abstractmethod
from typing import Optional, Any
from enum import Enum


class BaseLLMService(ABC):
    """Abstract base class for LLM service implementations.

    All LLM services (Mistral, Claude, etc.) should inherit from this class
    and implement the required abstract methods.
    """

    @abstractmethod
    def __init__(self):
        """Initialize the LLM service with necessary credentials."""
        pass

    @abstractmethod
    async def call_llm_api(
        self, input_prompt: str, json_schema: Optional[dict[str, Any]] = None
    ) -> Optional[str]:
        """Make the API call to the LLM service.

        Args:
            input_prompt: The text prompt to send to the LLM
            json_schema: Optional JSON schema for structured output.
                        Implementation varies by service:
                        - Claude uses tool calling
                        - Mistral uses response_format

        Returns:
            The LLM response content as a string, or None if no response

        Raises:
            Exception: If the API call fails or times out
        """
        pass

    @abstractmethod
    def get_model_enum(self) -> type[Enum]:
        """Return the Enum class containing available models for this service.

        Returns:
            Enum class with model definitions
        """
        pass
