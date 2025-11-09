import requests
import json
import os
from pathlib import Path


def load_tiktok_data(json_path: str) -> dict:
    """Load TikTok scraped data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def extract_video_info(data: dict) -> dict:
    """Extract video download information from TikTok data."""
    video_data = data['data'][0]['video']

    return {
        'download_url': video_data.get('download_addr'),
        'play_url': video_data.get('play_addr'),
        'cookie': video_data.get('cookie_download'),
        'video_id': video_data.get('video_id'),
        'file_size': video_data.get('size'),
        'duration': video_data.get('duration'),
        'definition': video_data.get('definition'),
    }


def download_video(video_info: dict, output_path: str = None) -> bool:
    """
    Download TikTok video using download_addr and cookie_download.

    Args:
        video_info: Dictionary containing video download details
        output_path: Path to save the video (default: current directory)

    Returns:
        bool: True if download successful, False otherwise
    """
    download_url = video_info.get('download_url')
    cookie_string = video_info.get('cookie')
    video_id = video_info.get('video_id')

    if not download_url:
        print("Error: No download URL found in video data")
        return False

    if not cookie_string:
        print("Warning: No cookies found. Download may fail due to authentication.")

    # Set default output path
    if output_path is None:
        output_path = f"tiktok_video_{video_id}.mp4"

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

    try:
        print(f"Downloading video from: {download_url[:80]}...")
        response = requests.get(
            download_url,
            cookies=cookies,
            headers=headers,
            stream=True,
            timeout=30
        )

        if response.status_code == 200:
            # Get file size from headers if available
            total_size = int(response.headers.get('content-length', 0))

            # Create parent directories if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Download with progress
            downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            progress = (downloaded / total_size) * 100
                            print(f"Progress: {progress:.1f}% ({downloaded}/{total_size} bytes)", end='\r')

            print(f"\n✓ Video downloaded successfully to: {output_path}")
            return True
        else:
            print(f"Error: Failed to download. HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("Error: Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False


def download_from_json(json_path: str, output_path: str = None) -> bool:
    """
    Main function to download video from TikTok JSON data.

    Args:
        json_path: Path to the TikTok scraped data JSON file
        output_path: Path to save the video

    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        print(f"Loading TikTok data from: {json_path}")
        data = load_tiktok_data(json_path)

        print("Extracting video information...")
        video_info = extract_video_info(data)

        print(f"Video ID: {video_info['video_id']}")
        print(f"Duration: {video_info['duration']}s")
        print(f"Definition: {video_info['definition']}")
        print(f"File size: {video_info['file_size']:,} bytes")
        print()

        return download_video(video_info, output_path)

    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_path}")
        return False
    except KeyError as e:
        print(f"Error: Missing required field in JSON: {e}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    import sys

    # Example usage
    json_file = "resources/no_recipe_long.json"

    if len(sys.argv) > 1:
        json_file = sys.argv[1]

    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    success = download_from_json(json_file, output_file)
    sys.exit(0 if success else 1)
