"""YouTube import service for extracting recipes from YouTube videos."""

import json
import re
from typing import Optional
from pathlib import Path
import logging
import httpx
from xml.etree import ElementTree as ET

from src.shared.llm_service.mistral import MistralService, MistralModels
from src.recipe_import_service.schemas.youtube_schema import (
    YouTubeEnsembleResponse,
    YouTubeEnsembleParams,
)
from src.recipe_import_service.services.base_import_service import BaseImportService
from src.core.config import settings


logger = logging.getLogger(__name__)


class YouTubeImportService(BaseImportService):
    """Service for importing recipes from YouTube videos."""

    MODEL = MistralModels.small
    TEMPLATE_PATH = (
        Path(__file__).parent.parent / "templates" / "youtube_recipe_template.md"
    )
    ENSEMBLE_API_URL = "https://ensembledata.com/apis/youtube/channel/get-short-stats"

    def __init__(self, mistral_service: MistralService):
        """Initialize YouTube import service.

        Args:
            mistral_service: Mistral LLM service for recipe extraction
        """
        self.mistral_service = mistral_service

    async def url_to_text_recipe(self, url: str, mock: bool = False) -> Optional[str]:
        """Extract and create a recipe from a YouTube video URL.

        This orchestrates the full pipeline:
        1. Extract video ID from URL
        2. Fetch video metadata from Ensemble API
        3. If captions available: fetch transcript and use with description
        4. If no captions (Shorts): use title + description only
        5. Process with LLM to create recipe

        Args:
            url: YouTube video URL or video ID
            mock: If True, uses mock data instead of real API calls

        Returns:
            Recipe in markdown format, or None if no recipe found

        Raises:
            Exception: If any step in the pipeline fails
        """
        # Step 1: Extract video ID
        video_id = self._extract_video_id(url)

        # Step 2: Fetch metadata and check for captions
        if mock:
            description, title, transcript_url = await self._fetch_youtube_data_mock(
                video_id
            )
        else:
            description, title, transcript_url = await self._fetch_youtube_data(
                video_id
            )

        # Step 3 & 4: Create recipe based on available data
        transcript = None
        if transcript_url:
            # Has captions - try to fetch transcript
            try:
                transcript = await self._fetch_transcript(transcript_url)
            except Exception as e:
                # If transcript fetch fails, fall back to title + description
                logger.warning(
                    f"Failed to fetch transcript, will use title + description: {e}"
                )
                transcript = None

        combined_text = f"{title}\n\n{description}"

        # Create recipe with available data (transcript and/or description)
        if transcript:

            logger.info(f"Text Data: {combined_text}\n\n Transcript: {transcript}")

            recipe = await self._create_text_recipe_with_transcript(
                transcript=transcript, description=combined_text
            )

        else:
            # No transcript - use title + description

            logger.info(f"Text Data: {combined_text}")

            recipe = await self._create_text_recipe_with_transcript(
                transcript=combined_text, description=""
            )

        logger.debug(f"Final Recipe: \n {recipe}")

        return recipe

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL or return as-is if already an ID.

        Handles various YouTube URL formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID

        Args:
            url: YouTube URL or video ID

        Returns:
            Extracted video ID

        Raises:
            ValueError: If URL format is invalid
        """
        # If it's already a video ID (11 characters, alphanumeric + - and _)
        if re.match(r"^[A-Za-z0-9_-]{11}$", url):
            return url

        # Try various URL patterns
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})",
            r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
            r"youtube\.com/v/([A-Za-z0-9_-]{11})",
            r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise ValueError(f"Invalid YouTube URL or video ID: {url}")

    async def _fetch_youtube_data(
        self, video_id: str
    ) -> tuple[str, str, Optional[str]]:
        """Fetch YouTube video metadata and transcript URL from Ensemble API.

        Args:
            video_id: YouTube video ID

        Returns:
            Tuple of (description text, title, transcript URL or None)

        Raises:
            Exception: If API call fails
        """
        # Build API parameters
        params = YouTubeEnsembleParams(
            id=video_id, token=settings.ensemble_data_api_key, alternative_method=True
        )

        # Fetch data from Ensemble API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.ENSEMBLE_API_URL, params=params.model_dump()
            )

        if response.status_code != 200:
            raise Exception(
                f"Ensemble API request failed with status {response.status_code}"
            )

        data = response.json()

        # Parse response
        youtube_response = YouTubeEnsembleResponse(**data)

        # Extract video details
        description = youtube_response.data.videoDetails.shortDescription
        title = youtube_response.data.videoDetails.title

        logger.info(f"Loading YouTube video ({video_id})")

        # Check if captions are available
        transcript_url = None
        if youtube_response.data.captions:
            caption_tracks = (
                youtube_response.data.captions.playerCaptionsTracklistRenderer.captionTracks
            )
            if caption_tracks:
                transcript_url = caption_tracks[0].baseUrl

        return description, title, transcript_url

    async def _fetch_youtube_data_mock(
        self, video_id: str
    ) -> tuple[str, str, Optional[str]]:
        """Fetch YouTube video metadata and transcript URL (using mock data).

        Args:
            video_id: YouTube video ID (currently ignored, uses mock data)

        Returns:
            Tuple of (description text, title, transcript URL or None)

        Raises:
            Exception: If mock data cannot be loaded
        """
        temp_mock_json = Path("resources/youtube/recipe_short.json")

        # Load mock YouTube data
        with open(temp_mock_json, "r") as f:
            data = json.load(f)

        # Parse response
        youtube_response = YouTubeEnsembleResponse(**data)

        # Extract video details
        description = youtube_response.data.videoDetails.shortDescription
        title = youtube_response.data.videoDetails.title

        logger.info(f"Loading YouTube video ({video_id})")
        logger.info(f"Description: {description}\n\nTitle: {title}")

        # Check if captions are available
        transcript_url = None
        if youtube_response.data.captions:
            caption_tracks = (
                youtube_response.data.captions.playerCaptionsTracklistRenderer.captionTracks
            )
            if caption_tracks:
                transcript_url = caption_tracks[0].baseUrl

        return description, title, transcript_url

    async def _fetch_transcript(self, transcript_url: str) -> str:
        """Fetch and parse YouTube transcript XML.

        Args:
            transcript_url: URL to YouTube caption/transcript XML

        Returns:
            Plain text transcript

        Raises:
            Exception: If fetching or parsing fails
        """
        try:
            # Fetch the XML transcript
            async with httpx.AsyncClient() as client:
                response = await client.get(transcript_url)

            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch transcript with status {response.status_code}"
                )

            xml_content = response.text

            # Parse XML and extract text
            root = ET.fromstring(xml_content)
            texts = []

            # Extract all text elements from the XML
            for text_elem in root.findall(".//text"):
                if text_elem.text:
                    texts.append(text_elem.text)

            transcript = " ".join(texts)

            # Clean up common HTML entities
            transcript = transcript.replace("&quot;", '"')
            transcript = transcript.replace("&amp;", "&")
            transcript = transcript.replace("&#39;", "'")
            transcript = transcript.replace("&lt;", "<")
            transcript = transcript.replace("&gt;", ">")

            logger.debug(f"Transcript extracted: {len(transcript)} characters")

            return transcript

        except Exception as e:
            raise Exception(f"Transcript extraction failed: {str(e)}")
