"""
YouTube Playlist Tool - Fetch videos from a YouTube playlist for scanning.

Supports:
- Playlist URL
- Playlist name (searches user's playlists)
- Video URL extraction
"""
import os
import re
from typing import Type, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Try to import YouTube API
try:
    from googleapiclient.discovery import build
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False


class YouTubePlaylistInput(BaseModel):
    """Input schema for YouTube Playlist Tool"""
    playlist_identifier: str = Field(
        ...,
        description="Playlist URL, playlist ID, or playlist name to search for"
    )
    max_videos: int = Field(
        default=20,
        description="Maximum number of videos to fetch"
    )


class YouTubePlaylistTool(BaseTool):
    """
    Fetch videos from a YouTube playlist for gear review scanning.

    Can accept:
    - Full playlist URL (https://youtube.com/playlist?list=...)
    - Playlist ID (PLxxxxxxx)
    - Playlist name (searches your playlists)
    """
    name: str = "YouTube Playlist Scanner"
    description: str = """Fetch videos from a YouTube playlist.

    Input a playlist URL, ID, or name to get a list of video URLs for scanning.
    Returns video titles and URLs ready for the YouTube Scanner agent."""

    args_schema: Type[BaseModel] = YouTubePlaylistInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._youtube = None

    def _get_youtube_client(self):
        """Get or create YouTube API client"""
        if self._youtube is None and YOUTUBE_API_AVAILABLE:
            api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if api_key:
                self._youtube = build('youtube', 'v3', developerKey=api_key)
        return self._youtube

    def _extract_playlist_id(self, identifier: str) -> Optional[str]:
        """Extract playlist ID from URL or return as-is if already an ID"""
        # Full URL pattern
        url_match = re.search(r'[?&]list=([^&]+)', identifier)
        if url_match:
            return url_match.group(1)

        # Already a playlist ID (starts with PL usually)
        if identifier.startswith('PL') or identifier.startswith('UU'):
            return identifier

        return None

    def _run(self, playlist_identifier: str, max_videos: int = 20) -> str:
        """Fetch videos from the playlist"""

        youtube = self._get_youtube_client()

        if not youtube:
            return self._fallback_response(playlist_identifier, max_videos)

        playlist_id = self._extract_playlist_id(playlist_identifier)

        if not playlist_id:
            # Try to search for playlist by name
            return self._search_playlist_by_name(playlist_identifier, max_videos)

        try:
            videos = []
            next_page_token = None

            while len(videos) < max_videos:
                request = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=min(50, max_videos - len(videos)),
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response.get('items', []):
                    video_id = item['snippet']['resourceId']['videoId']
                    title = item['snippet']['title']
                    videos.append({
                        'title': title,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'video_id': video_id
                    })

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            return self._format_response(videos, playlist_identifier)

        except Exception as e:
            return f"Error fetching playlist: {str(e)}\n\n" + self._fallback_response(playlist_identifier, max_videos)

    def _search_playlist_by_name(self, name: str, max_videos: int) -> str:
        """Search for playlist by name"""
        youtube = self._get_youtube_client()

        if not youtube:
            return self._fallback_response(name, max_videos)

        try:
            request = youtube.search().list(
                part="snippet",
                q=name,
                type="playlist",
                maxResults=5
            )
            response = request.execute()

            if response.get('items'):
                # Found playlists, use first match
                first = response['items'][0]
                playlist_id = first['id']['playlistId']
                return self._run(playlist_id, max_videos)
            else:
                return f"No playlist found with name '{name}'"

        except Exception as e:
            return f"Error searching playlists: {str(e)}"

    def _format_response(self, videos: List[dict], source: str) -> str:
        """Format video list for agent consumption"""
        response = f"Found {len(videos)} videos from playlist '{source}':\n\n"

        for i, video in enumerate(videos, 1):
            response += f"{i}. {video['title']}\n"
            response += f"   URL: {video['url']}\n\n"

        response += "\nReady for scanning by YouTube Scanner agent."
        return response

    def _fallback_response(self, identifier: str, max_videos: int) -> str:
        """Provide manual instructions if API unavailable"""
        return f"""
YouTube API not available or configured.

To scan playlist '{identifier}' manually:

1. Go to the playlist on YouTube
2. Copy video URLs you want to scan
3. Provide them to the YouTube Scanner agent

Or configure YouTube API:
1. Get API key from Google Cloud Console
2. Set YOUTUBE_API_KEY environment variable
3. Run again

Example videos to scan from gear review playlists:
- https://youtube.com/watch?v=... (video 1)
- https://youtube.com/watch?v=... (video 2)

Alternatively, provide individual video URLs directly.
"""


# Convenience function
def get_playlist_videos(playlist_identifier: str, max_videos: int = 20) -> List[dict]:
    """Standalone function to get playlist videos"""
    tool = YouTubePlaylistTool()
    result = tool._run(playlist_identifier, max_videos)
    return result
