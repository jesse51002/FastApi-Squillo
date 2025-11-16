import requests
import json
import os
from pathlib import Path


def load_instagram_data(json_path: str) -> dict:
    """Load Instagram scraped data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def extract_video_info(data: dict) -> dict:
    """Extract video download information from Instagram data."""
    video_data = data['data']

    # Extract description from caption
    description = ""
    if video_data.get('edge_media_to_caption', {}).get('edges'):
        caption_edges = video_data['edge_media_to_caption']['edges']
        if caption_edges:
            description = caption_edges[0]['node']['text']

    return {
        'download_url': video_data.get('video_url'),
        'shortcode': video_data.get('shortcode'),
        'video_duration': video_data.get('video_duration'),
        'description': description,
        'has_audio': video_data.get('has_audio', True),
    }


def download_video(video_info: dict, output_path: str = None) -> bool:
    """
    Download Instagram video using video_url.

    Args:
        video_info: Dictionary containing video download details
        output_path: Path to save the video (default: current directory)

    Returns:
        bool: True if download successful, False otherwise
    """
    download_url = video_info.get('download_url')
    shortcode = video_info.get('shortcode')

    if not download_url:
        print("Error: No download URL found in video data")
        return False

    # Set default output path
    if output_path is None:
        output_path = f"instagram_video_{shortcode}.mp4"

    # Download headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.instagram.com/',
    }

    try:
        print(f"Downloading video from: {download_url[:80]}...")
        response = requests.get(
            download_url,
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
    Main function to download video from Instagram JSON data.

    Args:
        json_path: Path to the Instagram scraped data JSON file
        output_path: Path to save the video

    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        print(f"Loading Instagram data from: {json_path}")
        data = load_instagram_data(json_path)

        print("Extracting video information...")
        video_info = extract_video_info(data)

        print(f"Shortcode: {video_info['shortcode']}")
        print(f"Duration: {video_info['video_duration']}s")
        print(f"Has audio: {video_info['has_audio']}")
        if video_info['description']:
            desc_preview = video_info['description'][:100] + "..." if len(video_info['description']) > 100 else video_info['description']
            print(f"Description: {desc_preview}")
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
    json_file = "resources/insta/recipe.json"

    if len(sys.argv) > 1:
        json_file = sys.argv[1]

    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    success = download_from_json(json_file, output_file)
    sys.exit(0 if success else 1)
