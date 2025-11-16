from pydantic import BaseModel, Field
from typing import List


class EnsembleApiParams(BaseModel):
    """Parameters for Ensemble Data API request."""

    url: str = Field(..., description="TikTok video URL")
    token: str = Field(..., description="API token for authentication")
    new_version: bool = Field(default=True, description="Use new API version")
    download_video: bool = Field(
        default=True, description="Include video download URL in response"
    )


class VideoMetadata(BaseModel):
    """Model for video metadata."""

    video_id: str = Field(..., description="TikTok video ID")
    download_addr: str = Field(..., description="Direct download URL for the video")
    cookie_download: str = Field(..., description="Authentication cookies for download")
    duration: int = Field(..., description="Video duration in seconds")
    cover: str = Field(..., description="Link to video thumbnail")

    class Config:
        extra = "ignore"  # Ignore all other fields


class TikTokVideoData(BaseModel):
    """Pydantic model for TikTok scraped video data."""

    video: VideoMetadata
    desc: str

    class Config:
        extra = "ignore"  # Ignore all other fields in the main object


class TikTokScrapeResponse(BaseModel):
    """Full TikTok scrape response with data array."""

    data: List[TikTokVideoData]

    class Config:
        extra = "ignore"  # Ignore all other fields
