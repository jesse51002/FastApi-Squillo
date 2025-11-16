"""Pydantic schemas for LLM API requests and responses (Mistral and Claude)."""

from pydantic import BaseModel, Field
from typing import Literal, Union, Optional


class MistralVoiceMessageContent(BaseModel):
    """Content item in a message (supports text)."""
    type: Literal['input_audio'] = Field('input_audio')
    input_audio: str  = Field(..., description="Base64 encoded audio for Voxtral")

class MistralTextMessageContent(BaseModel):
    """Content item in a message (supports text and audio for Voxtral)."""
    type: Literal['text']  = Field('text')
    text: str = Field(..., description="Input text")


class Message(BaseModel):
    """Chat message structure."""
    role: str
    content: list[Union[MistralVoiceMessageContent, MistralTextMessageContent]]

 
class ResponseFormat(BaseModel):
    """Response format configuration."""
    type: str = 'json_object'


class MistralRequest(BaseModel):
    """Mistral API request payload."""
    model: str
    max_tokens: int = Field(default=2000, gt=0)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    safe_prompt: bool = True
    response_format: Optional[ResponseFormat]
    messages: list[Message]

    class Config:
        use_enum_values = True


class MistralHeaders(BaseModel):
    """Headers for Mistral API requests."""
    content_type: str = Field(default='application/json', alias='Content-Type')
    authorization: str = Field(alias='Authorization')
    accept: str = Field(default='application/json', alias='Accept')

    class Config:
        populate_by_name = True


class MessageResponse(BaseModel):
    """Message in the API response."""
    content: str


class Choice(BaseModel):
    """Choice in the API response."""
    message: MessageResponse


class MistralResponse(BaseModel):
    """Mistral API response structure."""
    choices: list[Choice]


# Claude API Schemas

class ClaudeMessageContent(BaseModel):
    """Content item in a Claude message."""
    type: Literal['text'] = 'text'
    text: str


class ClaudeMessage(BaseModel):
    """Claude message structure."""
    role: Literal['user', 'assistant']
    content: str | list[ClaudeMessageContent]


class ClaudeToolInputSchema(BaseModel):
    """Schema definition for tool input."""
    type: Literal['object'] = 'object'
    properties: dict
    required: Optional[list[str]] = None


class ClaudeTool(BaseModel):
    """Tool definition for Claude API."""
    name: str
    description: str
    input_schema: ClaudeToolInputSchema


class ClaudeToolChoice(BaseModel):
    """Tool choice configuration."""
    type: Literal['tool'] = 'tool'
    name: str


class ClaudeRequest(BaseModel):
    """Claude API request payload."""
    model: str
    max_tokens: int = Field(default=2000, gt=0)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    messages: list[ClaudeMessage]
    system: Optional[str] = None
    tools: Optional[list[ClaudeTool]] = None
    tool_choice: Optional[ClaudeToolChoice] = None

    class Config:
        use_enum_values = True


class ClaudeHeaders(BaseModel):
    """Headers for Claude API requests."""
    content_type: str = Field(default='application/json', alias='Content-Type')
    x_api_key: str = Field(alias='x-api-key')
    anthropic_version: str = Field(default='2023-06-01', alias='anthropic-version')

    class Config:
        populate_by_name = True


class ClaudeContentBlock(BaseModel):
    """Content block in Claude response."""
    type: str
    text: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[dict] = None


class ClaudeResponseContent(BaseModel):
    """Claude API response message content."""
    id: str
    type: str
    role: str
    content: list[ClaudeContentBlock]
    model: str
    stop_reason: Optional[str] = None
    usage: Optional[dict] = None


class ClaudeResponse(BaseModel):
    """Claude API response structure."""
    id: str
    type: str
    role: str
    content: list[ClaudeContentBlock]
    model: str
    stop_reason: Optional[str] = None


# Gemini API Schemas

class GeminiPart(BaseModel):
    """Part of content in Gemini message."""
    text: str


class GeminiContent(BaseModel):
    """Content structure for Gemini messages."""
    parts: list[GeminiPart]
    role: Optional[str] = None


class GeminiGenerationConfig(BaseModel):
    """Generation configuration for Gemini."""
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    maxOutputTokens: int = Field(default=2000, gt=0, alias='max_output_tokens')
    responseMimeType: Optional[str] = Field(default=None, alias='response_mime_type')
    responseSchema: Optional[dict] = Field(default=None, alias='response_schema')

    class Config:
        populate_by_name = True


class GeminiRequest(BaseModel):
    """Gemini API request payload."""
    contents: list[GeminiContent]
    generationConfig: Optional[GeminiGenerationConfig] = Field(default=None, alias='generation_config')

    class Config:
        use_enum_values = True
        populate_by_name = True


class GeminiHeaders(BaseModel):
    """Headers for Gemini API requests."""
    content_type: str = Field(default='application/json', alias='Content-Type')

    class Config:
        populate_by_name = True


class GeminiCandidate(BaseModel):
    """Candidate response from Gemini."""
    content: GeminiContent
    finishReason: Optional[str] = Field(default=None, alias='finish_reason')

    class Config:
        populate_by_name = True


class GeminiUsageMetadata(BaseModel):
    """Usage metadata from Gemini response."""
    promptTokenCount: Optional[int] = Field(default=None, alias='prompt_token_count')
    candidatesTokenCount: Optional[int] = Field(default=None, alias='candidates_token_count')
    totalTokenCount: Optional[int] = Field(default=None, alias='total_token_count')

    class Config:
        populate_by_name = True


class GeminiResponse(BaseModel):
    """Gemini API response structure."""
    candidates: list[GeminiCandidate]
    usageMetadata: Optional[GeminiUsageMetadata] = Field(default=None, alias='usage_metadata')

    class Config:
        populate_by_name = True
