"""Pydantic schemas for Mistral API requests and responses."""

from pydantic import BaseModel, Field


class MessageContent(BaseModel):
    """Content item in a message."""
    type: str = 'text'
    text: str


class Message(BaseModel):
    """Chat message structure."""
    role: str
    content: list[MessageContent]


class ResponseFormat(BaseModel):
    """Response format configuration."""
    type: str = 'json_object'


class MistralRequest(BaseModel):
    """Mistral API request payload."""
    model: str
    max_tokens: int = Field(default=2000, gt=0)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    safe_prompt: bool = True
    response_format: ResponseFormat
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
