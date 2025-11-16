"""Instagram-specific schemas for scraped data responses."""

from pydantic import BaseModel, Field
from typing import List


class InstagramEnsembleParams(BaseModel):
    """Parameters for Ensemble Data Instagram API request."""

    code: str = Field(..., description="Instagram post shortcode")
    token: str = Field(..., description="API token for authentication")


class CaptionEdgeNode(BaseModel):
    """Instagram caption node."""

    text: str = Field(..., description="Caption text")

    class Config:
        extra = "ignore"


class CaptionEdge(BaseModel):
    """Instagram caption edge."""

    node: CaptionEdgeNode = Field(..., description="Caption node")

    class Config:
        extra = "ignore"


class MediaToCaption(BaseModel):
    """Instagram media to caption relationship."""

    edges: List[CaptionEdge] = Field(default_factory=list, description="Caption edges")

    class Config:
        extra = "ignore"


class InstagramVideoData(BaseModel):
    """Instagram video data container."""

    video_url: str = Field(..., description="Direct video download URL")
    video_duration: float = Field(..., description="Video duration in seconds")
    has_audio: bool = Field(default=True, description="Whether video has audio")
    edge_media_to_caption: MediaToCaption = Field(
        ..., description="Video captions/description"
    )

    class Config:
        extra = "ignore"


class InstagramResponse(BaseModel):
    """Full response from Instagram scraper."""

    data: InstagramVideoData = Field(..., description="Instagram video data")

    class Config:
        extra = "ignore"
