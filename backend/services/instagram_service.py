import os
import requests
from typing import Dict

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
GRAPH_API_VERSION = "v18.0"

async def upload_to_instagram(video_path: str, caption: str) -> Dict:
    """
    Upload video to Instagram using Graph API.
    Returns response dict.
    """
    # Step 1: Create media container
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "media_type": "VIDEO",
        "video_url": video_path,  # Assuming video is already uploaded to accessible URL
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }

    response = requests.post(url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to create media container: {response.text}")

    container_id = response.json()["id"]

    # Step 2: Publish the media
    publish_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }

    publish_response = requests.post(publish_url, data=publish_payload)
    if publish_response.status_code != 200:
        raise Exception(f"Failed to publish media: {publish_response.text}")

    return publish_response.json()

async def get_instagram_analytics(post_id: str) -> Dict:
    """
    Get analytics for an Instagram post.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{post_id}/insights"
    params = {
        "metric": "impressions,reach,engagement",
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get analytics: {response.text}")

    return response.json()
