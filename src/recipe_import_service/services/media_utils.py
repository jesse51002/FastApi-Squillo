"""Media processing utilities for recipe import services."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict
from enum import Enum
import logging
import httpx


logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Supported platforms for recipe import."""

    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    WEB = "web"


def detect_platform(url: str) -> Platform:
    """Detect the platform from the URL.

    Args:
        url: URL to analyze

    Returns:
        Platform enum value
    """
    url_lower = url.lower()

    # TikTok detection
    if "tiktok.com" in url_lower:
        return Platform.TIKTOK

    # YouTube detection
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return Platform.YOUTUBE

    # Instagram detection
    if "instagram.com" in url_lower or "instagr.am" in url_lower:
        return Platform.INSTAGRAM

    # Everything else is treated as a web recipe URL
    return Platform.WEB


def extract_audio_from_video(video_file_path: Path) -> Path:
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
    temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix=".mp3")
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
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(video_file_path),
                "-vn",  # No video
                "-acodec",
                "libmp3lame",
                "-ar",
                "44100",
                "-ac",
                "2",
                "-ab",
                "192k",
                "-y",
                str(temp_audio),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise Exception(f"ffmpeg failed: {result.stderr}")

        logger.debug(f"Audio extracted successfully to {temp_audio}")
        return temp_audio

    except FileNotFoundError:
        # Clean up temp file
        if temp_audio.exists():
            temp_audio.unlink()
        raise Exception(
            "ffmpeg not found. Please install ffmpeg: sudo apt install ffmpeg"
        )
    except Exception as e:
        # Clean up temp file if extraction failed
        if temp_audio.exists():
            temp_audio.unlink()
        raise Exception(f"Audio extraction failed: {str(e)}")


async def download_video(
    download_url: str,
    video_id: str,
    cookies: Optional[Dict[str, str]] = None,
    referer: Optional[str] = None,
) -> Path:
    """Download video from URL using httpx.

    Args:
        download_url: Direct download URL for the video
        video_id: Video ID (for logging/debugging)
        cookies: Optional cookies dict for authentication
        referer: Optional referer URL (e.g., 'https://www.tiktok.com/')

    Returns:
        Path to downloaded video file

    Raises:
        Exception: If download fails
    """
    # Build headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }
    if referer:
        headers["Referer"] = referer

    # Create temporary video file
    temp_video_fd, temp_video_path = tempfile.mkstemp(suffix=".mp4")
    temp_video = Path(temp_video_path)
    os.close(temp_video_fd)

    try:
        logger.debug(f"Downloading video {video_id}")

        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream(
                "GET", download_url, cookies=cookies, headers=headers
            ) as response:
                if response.status_code != 200:
                    raise Exception(
                        f"Video download failed with status {response.status_code}"
                    )

                # Download video in chunks
                with open(temp_video, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

        logger.debug(f"Video downloaded successfully to {temp_video}")
        return temp_video

    except Exception as e:
        # Clean up temp file if download failed
        if temp_video.exists():
            temp_video.unlink()
        raise Exception(f"Video download failed: {str(e)}")
