import json
from typing import Optional
from pathlib import Path
from typing import Tuple
import logging
import httpx

from src.shared.llm_service.mistral import MistralService, MistralModels
from src.recipe_import_service.schemas.tiktok_schema import TikTokScrapeResponse, EnsembleApiParams
from src.recipe_import_service.services.base_import_service import BaseImportService
from src.recipe_import_service.services.media_utils import extract_audio_from_video, download_video
from src.core.config import settings


logger = logging.getLogger(__name__)

class TiktokImportService(BaseImportService):

    MODEL = MistralModels.voxtral_small
    TEMPLATE_PATH = Path(__file__).parent.parent / 'templates' / 'audio_recipe_template.md'
    ENSEMBLE_API_URL = "https://ensembledata.com/apis/tt/post/info"

    def __init__(self, mistral_service: MistralService):
        self.mistral_service = mistral_service

    async def url_to_text_recipe(self, url: str, mock: bool = False) -> Optional[str]:
        """Extract and create a recipe from a TikTok video URL.

        This orchestrates the full pipeline:
        1. Download TikTok video and get description from Ensemble API
        2. Extract audio from video
        3. Process audio + description with Voxtral to create recipe

        Args:
            url: TikTok video URL
            mock: If True, uses mock data instead of real API calls

        Returns:
            Recipe in markdown format, or empty string if no recipe found

        Raises:
            Exception: If any step in the pipeline fails
        """
        # Step 1: Download video and get description
        if mock:
            description, video_file = await self._download_tiktok_mock(url)
        else:
            description, video_file = await self._download_tiktok(url)

        # Step 2: Extract audio from video
        audio_file = extract_audio_from_video(video_file)

        try:
            # Step 3: Create recipe from audio and description
            recipe = await self._create_text_recipe_with_audio(audio_file, description)

            logger.debug(f"Final Recipe: \n {recipe}")

            return recipe
        finally:
            # Clean up temporary audio file
            if audio_file.exists():
                audio_file.unlink()
        

    async def _download_tiktok(self, url: str) -> Tuple[str, Path]:
        """Download TikTok video and extract description using Ensemble API.

        Args:
            url: TikTok video URL

        Returns:
            Tuple of (description text, video file path)

        Raises:
            Exception: If API call or download fails
        """
        # Build API parameters using schema
        params = EnsembleApiParams(
            url=url,
            token=settings.ensemble_data_api_key
        )

        # Fetch TikTok data from Ensemble API
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.ENSEMBLE_API_URL,
                params=params.model_dump()
            )

        if response.status_code != 200:
            raise Exception(f"Ensemble API request failed with status {response.status_code}")

        data = response.json()
        tiktok_response = TikTokScrapeResponse(**data)

        # Extract description and video download info
        video_data = tiktok_response.data[0]
        description = video_data.desc
        download_url = video_data.video.download_addr
        cookie_string = video_data.video.cookie_download
        video_id = video_data.video.video_id

        # Parse cookies from string
        cookies = {}
        if cookie_string:
            for cookie_part in cookie_string.split('; '):
                if '=' in cookie_part:
                    key, value = cookie_part.split('=', 1)
                    cookies[key.strip()] = value.strip()

        # Download video using utility function
        video_file = await download_video(
            download_url=download_url,
            video_id=video_id,
            cookies=cookies,
            referer='https://www.tiktok.com/'
        )

        return description, video_file

    async def _download_tiktok_mock(self, url: str) -> Tuple[str, Path]:
        """Download TikTok video and extract description (using mock data).

        Args:
            url: TikTok video URL (currently ignored, uses mock data)

        Returns:
            Tuple of (description text, video file path)

        Raises:
            Exception: If mock data cannot be loaded
        """
        temp_mock_json = Path('resources/tiktok/ingredient_desc.json')
        temp_video_file = Path('resources/tiktok/ingredient_desc.mp4')

        # Load mock TikTok data
        with open(temp_mock_json, "r") as f:
            response = TikTokScrapeResponse(**json.load(f))

        description = response.data[0].desc

        return description, temp_video_file
