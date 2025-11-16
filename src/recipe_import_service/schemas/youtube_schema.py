"""YouTube-specific schemas for Ensemble API responses."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class YouTubeEnsembleParams(BaseModel):
    """Parameters for Ensemble Data YouTube API request."""
    id: str = Field(..., description="YouTube video ID")
    token: str = Field(..., description="API token for authentication")
    alternative_method: bool = Field(default=True, description="Use alternative method for fetching data")


class CaptionTrack(BaseModel):
    """YouTube caption track information."""
    baseUrl: str = Field(..., description="URL to fetch the caption XML")
    name: Dict[str, str] = Field(..., description="Caption track name")
    vssId: str = Field(..., description="Caption track VSS ID")
    languageCode: str = Field(..., description="Language code (e.g., 'en')")
    kind: str = Field(default="", description="Caption kind (e.g., 'asr' for auto-generated)")
    isTranslatable: bool = Field(default=True, description="Whether caption can be translated")

    class Config:
        extra = "ignore"


class CaptionTrackList(BaseModel):
    """YouTube captions tracklist renderer."""
    captionTracks: List[CaptionTrack] = Field(..., description="Available caption tracks")

    class Config:
        extra = "ignore"


class CaptionsData(BaseModel):
    """YouTube captions data."""
    playerCaptionsTracklistRenderer: CaptionTrackList = Field(..., description="Caption tracks renderer")

    class Config:
        extra = "ignore"


class ThumbnailItem(BaseModel):
    """YouTube thumbnail item."""
    url: str = Field(..., description="Thumbnail URL")
    width: int = Field(..., description="Thumbnail width")
    height: int = Field(..., description="Thumbnail height")

    class Config:
        extra = "ignore"


class ThumbnailData(BaseModel):
    """YouTube thumbnail data."""
    thumbnails: List[ThumbnailItem] = Field(..., description="Available thumbnails")

    class Config:
        extra = "ignore"


class VideoDetails(BaseModel):
    """YouTube video details from Ensemble API."""
    videoId: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    lengthSeconds: str = Field(..., description="Video duration in seconds")
    shortDescription: str = Field(..., description="Video description")
    thumbnail: ThumbnailData = Field(..., description="Video thumbnails")

    class Config:
        extra = "ignore"


class VideoFormat(BaseModel):
    """YouTube video format information."""
    itag: int = Field(..., description="Format tag")
    mimeType: str = Field(..., description="MIME type of the format")
    url: str = Field(default="", description="Direct download URL")
    signatureCipher: str = Field(default="", description="Signature cipher for protected videos")
    quality: str = Field(..., description="Quality label (e.g., 'medium', 'hd720')")
    audioQuality: str = Field(default="", description="Audio quality")

    class Config:
        extra = "ignore"


class StreamingData(BaseModel):
    """YouTube streaming data containing video formats."""
    formats: List[VideoFormat] = Field(..., description="Available video formats")

    class Config:
        extra = "ignore"


class YouTubeData(BaseModel):
    """Main YouTube data container (handles both regular videos and Shorts)."""
    videoDetails: VideoDetails = Field(..., description="Video metadata")
    captions: Optional[CaptionsData] = Field(None, description="Caption/transcript data (optional)")
    streamingData: Optional[StreamingData] = Field(None, description="Streaming/download data (optional)")

    class Config:
        extra = "ignore"


class YouTubeEnsembleResponse(BaseModel):
    """Full response from Ensemble YouTube API."""
    data: YouTubeData = Field(..., description="YouTube video data")

    class Config:
        extra = "ignore"
