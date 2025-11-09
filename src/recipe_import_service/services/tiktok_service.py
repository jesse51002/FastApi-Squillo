import json
from typing import Optional
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple
import logging
import httpx

from src.shared.llm_service.mistral import MistralService, MistralModels
from src.recipe_import_service.schemas.tiktok_schema import TikTokScrapeResponse, LlmOutputFormat, EnsembleApiParams
from src.util.template_formatter import TemplateFormatter
from src.core.config import settings


logger = logging.getLogger(__name__)

class TiktokImportService:

    MODEL = MistralModels.voxtral_small
    TEMPLATE_PATH = Path(__file__).parent.parent / 'templates' / 'audio_recipe_template.md'
    ENSEMBLE_API_URL = "https://ensembledata.com/apis/tt/post/info"

    def __init__(self, mistral_service: MistralService):
        self.mistral_service = mistral_service

    async def url_to_text_recipe(self, url: str) -> Optional[str]:
        """Extract and create a recipe from a TikTok video URL.

        This orchestrates the full pipeline:
        1. Download TikTok video and get description from Ensemble API
        2. Extract audio from video
        3. Process audio + description with Voxtral to create recipe

        Args:
            url: TikTok video URL

        Returns:
            Recipe in markdown format, or empty string if no recipe found

        Raises:
            Exception: If any step in the pipeline fails
        """
        # Step 1: Download video and get description
        description, video_file = await self._download_tiktok_mock(url)

        # Step 2: Extract audio from video
        audio_file = self._extract_audio_from_video(video_file)

        try:
            # Step 3: Create recipe from audio and description
            recipe = await self._create_text_recipe(audio_file, description)

            logger.debug(f"Final Recipe: \n {recipe}")

            return recipe
        finally:
            # Clean up temporary audio file
            if audio_file.exists():
                audio_file.unlink()


    async def _create_text_recipe(self, audio_file: Path, description: str) -> str:
        """Create recipe from audio and description using Voxtral.

        Args:
            audio_file: Path to extracted audio file
            description: TikTok video description text

        Returns:
            Recipe in markdown format, or empty string if no recipe found

        Raises:
            Exception: If LLM processing fails or validation fails
        """
        # Get JSON schema from LlmOutputFormat
        json_schema = LlmOutputFormat.model_json_schema()
        str_json_schema = json.dumps(json_schema, indent=2)

        # Format the template with description and schema using TemplateFormatter
        prompt = TemplateFormatter.format_template(
            self.TEMPLATE_PATH,
            description=description,
            schema=str_json_schema
        )

        # Call Voxtral API with audio and prompt
        response = await self.mistral_service.call_voxtral_api(
            audio_file_path=audio_file,
            text_prompt=prompt,
            model=self.MODEL,
            json_schema=json_schema
        )

        if not response:
            raise Exception("No response received from Mistral Voxtral API")

        # Parse and validate the JSON response using Pydantic
        try:
            llm_output = LlmOutputFormat.model_validate_json(response)
            return llm_output.recipe

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to validate LLM response: {e}")
            raise Exception(f"LLM response validation failed: {str(e)}")
        

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
        async with httpx.AsyncClient() as client:
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

        # Download video
        video_file = await self._download_video(
            download_url=download_url,
            cookie_string=cookie_string,
            video_id=video_id
        )

        return description, video_file

    async def _download_video(
        self,
        download_url: str,
        cookie_string: str,
        video_id: str
    ) -> Path:
        """Download TikTok video using httpx.

        Args:
            download_url: Direct download URL for the video
            cookie_string: Authentication cookies for download
            video_id: TikTok video ID

        Returns:
            Path to downloaded video file

        Raises:
            Exception: If download fails
        """
        # Parse cookies from string
        cookies = {}
        if cookie_string:
            for cookie_part in cookie_string.split('; '):
                if '=' in cookie_part:
                    key, value = cookie_part.split('=', 1)
                    cookies[key.strip()] = value.strip()

        # Download headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.tiktok.com/',
        }

        # Create temporary video file
        temp_video_fd, temp_video_path = tempfile.mkstemp(suffix='.mp4')
        temp_video = Path(temp_video_path)
        os.close(temp_video_fd)

        try:
            logger.debug(f"Downloading video {video_id} from Ensemble API")

            async with httpx.AsyncClient() as client:
                async with client.stream('GET', download_url, cookies=cookies, headers=headers) as response:
                    if response.status_code != 200:
                        raise Exception(f"Video download failed with status {response.status_code}")

                    # Download video in chunks
                    with open(temp_video, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)

            logger.debug(f"Video downloaded successfully to {temp_video}")
            return temp_video

        except Exception as e:
            # Clean up temp file if download failed
            if temp_video.exists():
                temp_video.unlink()
            raise Exception(f"Video download failed: {str(e)}")

    async def _download_tiktok_mock(self, url: str) -> Tuple[str, Path]:
        """Download TikTok video and extract description (using mock data).

        Args:
            url: TikTok video URL (currently ignored, uses mock data)

        Returns:
            Tuple of (description text, video file path)

        Raises:
            Exception: If mock data cannot be loaded
        """
        temp_mock_json = Path('resources/no_recipe_long.json')
        temp_video_file = Path('resources/no_recipe_long.mp4')

        # Load mock TikTok data
        with open(temp_mock_json, "r") as f:
            response = TikTokScrapeResponse(**json.load(f))

        description = response.data[0].desc

        return description, temp_video_file
    
    def _extract_audio_from_video(self, video_file_path: Path) -> Path:
        """Extract audio from video file using ffmpeg.

        Args:
            video_file_path: Path to the video file

        Returns:
            Path to the extracted audio file

        Raises:
            FileNotFoundError: If video file doesn't exist
            Exception: If ffmpeg processing fails
        """
        if not video_file_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_file_path}")

        # Create temporary audio file
        temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix='.mp3')
        temp_audio = Path(temp_audio_path)

        # Close the file descriptor as ffmpeg will handle the file
        os.close(temp_audio_fd)

        try:
            # Extract audio using ffmpeg
            # -i: input file
            # -vn: disable video
            # -acodec: audio codec (libmp3lame for MP3)
            # -ar: audio sample rate (44100 Hz)
            # -ac: audio channels (2 for stereo)
            # -ab: audio bitrate (192k)
            # -y: overwrite output file without asking
            result = subprocess.run([
                'ffmpeg',
                '-i', str(video_file_path),
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-ar', '44100',
                '-ac', '2',
                '-ab', '192k',
                '-y',
                str(temp_audio)
            ], capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr}")

            return temp_audio

        except FileNotFoundError:
            raise Exception("ffmpeg not found. Please install ffmpeg: sudo apt install ffmpeg")
        except Exception as e:
            # Clean up temp file if extraction failed
            if temp_audio.exists():
                temp_audio.unlink()
            raise Exception(f"Audio extraction failed: {str(e)}")

