"""Instagram import service for extracting recipes from Instagram videos."""

import re
import json
from typing import Optional
from pathlib import Path
from typing import Tuple
import logging
import httpx

from src.shared.llm_service.mistral import MistralService, MistralModels
from src.recipe_import_service.schemas.instagram_schema import (
    InstagramResponse,
    InstagramEnsembleParams,
)
from src.recipe_import_service.services.base_import_service import BaseImportService
from src.recipe_import_service.services.media_utils import (
    extract_audio_from_video,
    download_video,
)
from src.core.config import settings


logger = logging.getLogger(__name__)


class InstagramImportService(BaseImportService):
    """Service for importing recipes from Instagram videos."""

    MODEL = MistralModels.voxtral_small
    TEMPLATE_PATH = (
        Path(__file__).parent.parent / "templates" / "audio_recipe_template.md"
    )
    ENSEMBLE_API_URL = "https://ensembledata.com/apis/instagram/post/details"

    def __init__(self, mistral_service: MistralService):
        """Initialize Instagram import service.

        Args:
            mistral_service: Mistral LLM service for recipe extraction
        """
        self.mistral_service = mistral_service

    async def url_to_text_recipe(self, url: str, mock: bool = False) -> Optional[str]:
        """Extract and create a recipe from an Instagram video URL.

        This orchestrates the full pipeline:
        1. Download Instagram video and get description
        2. Extract audio from video
        3. Process audio + description with Voxtral to create recipe

        Args:
            url: Instagram video URL
            mock: If True, uses mock data instead of real API calls

        Returns:
            Recipe in markdown format, or None if no recipe found

        Raises:
            Exception: If any step in the pipeline fails
        """
        # Step 1: Download video and get description
        if mock:
            description, video_file = await self._download_instagram_mock(url)
        else:
            description, video_file = await self._download_instagram(url)

        # Step 2: Extract audio from video
        audio_file = extract_audio_from_video(video_file)

        try:
            # Step 3: Create recipe from audio and description
            recipe = await self._create_text_recipe_with_audio(audio_file, description)
            return recipe
        finally:
            # Clean up temporary audio file
            if audio_file.exists():
                audio_file.unlink()

    def _extract_shortcode(self, url: str) -> str:
        """Extract shortcode from Instagram URL or return as-is if already a shortcode.

        Handles various Instagram URL formats:
        - https://www.instagram.com/p/SHORTCODE/
        - https://www.instagram.com/reel/SHORTCODE/
        - https://instagram.com/p/SHORTCODE/

        Args:
            url: Instagram URL or shortcode

        Returns:
            Extracted shortcode

        Raises:
            ValueError: If URL format is invalid
        """
        # If it's already a shortcode (alphanumeric + - and _)
        if re.match(r"^[A-Za-z0-9_-]+$", url) and "/" not in url:
            return url

        # Try various URL patterns
        patterns = [
            r"instagram\.com/(?:p|reel)/([A-Za-z0-9_-]+)",
            r"instagram\.com/(?:tv)/([A-Za-z0-9_-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise ValueError(f"Invalid Instagram URL or shortcode: {url}")

    async def _download_instagram(self, url: str) -> Tuple[str, Path]:
        """Download Instagram video and extract description using Ensemble API.

        Args:
            url: Instagram video URL or shortcode

        Returns:
            Tuple of (description text, video file path)

        Raises:
            Exception: If API call or download fails
        """
        # Extract shortcode from URL
        shortcode = self._extract_shortcode(url)

        # Build API parameters
        params = InstagramEnsembleParams(
            code=shortcode, token=settings.ensemble_data_api_key
        )

        # Fetch Instagram data from Ensemble API
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.ENSEMBLE_API_URL, params=params.model_dump()
            )

        if response.status_code != 200:
            raise Exception(
                f"Ensemble API request failed with status {response.status_code}"
            )

        data = response.json()

        # Parse response
        instagram_response = InstagramResponse(**data)

        # Extract description from caption
        description = ""
        if instagram_response.data.edge_media_to_caption.edges:
            description = instagram_response.data.edge_media_to_caption.edges[
                0
            ].node.text

        # Extract video URL
        video_url = instagram_response.data.video_url

        logger.info(f"Loading Instagram video (shortcode: {shortcode})")

        # Download the video using utility function
        video_file = await download_video(
            download_url=video_url,
            video_id=shortcode,
            cookies=None,
            referer="https://www.instagram.com/",
        )

        return description, video_file

    async def _download_instagram_mock(self, url: str) -> Tuple[str, Path]:
        """Download Instagram video and extract description (using mock data).

        Args:
            url: Instagram video URL (currently ignored, uses mock data)

        Returns:
            Tuple of (description text, video file path)

        Raises:
            Exception: If mock data cannot be loaded
        """
        temp_mock_json = Path("resources/insta/recipe.json")
        temp_video_file = Path("resources/insta/recipe.mp4")

        # Load mock Instagram data
        with open(temp_mock_json, "r") as f:
            data = json.load(f)

        # Parse response
        instagram_response = InstagramResponse(**data)

        # Extract description from caption
        description = ""
        if instagram_response.data.edge_media_to_caption.edges:
            description = instagram_response.data.edge_media_to_caption.edges[
                0
            ].node.text

        return description, temp_video_file
