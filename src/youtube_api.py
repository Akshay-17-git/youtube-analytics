"""
YouTube Data API Module.
Handles fetching video data from YouTube API.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

from config.settings import settings


class YouTubeAPI:
    """YouTube Data API client."""
    
    def __init__(self, api_key: str = None):
        """Initialize YouTube API client."""
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YouTube API key is required")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def get_channel_info(self, channel_id: str) -> Dict:
        """Get channel information."""
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            )
            response = request.execute()
            
            if response['items']:
                item = response['items'][0]
                return {
                    'channel_id': item['id'],
                    'channel_name': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'total_subscribers': int(item['statistics'].get('subscriberCount', 0)),
                    'total_views': int(item['statistics'].get('viewCount', 0)),
                    'total_videos': int(item['statistics'].get('videoCount', 0)),
                    'uploads_playlist_id': item['contentDetails']['relatedPlaylists']['uploads']
                }
            return None
        except HttpError as e:
            print(f"HTTP Error: {e}")
            return None
    
    def get_uploaded_videos(self, playlist_id: str, max_results: int = 50) -> List[Dict]:
        """Get all videos from uploads playlist."""
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            request = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=min(50, max_results - len(videos)),
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response['items']:
                videos.append({
                    'video_id': item['contentDetails']['videoId'],
                    'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', '')
                })
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return videos[:max_results]
    
    def get_video_statistics(self, video_id: str) -> dict:
        """Get statistics for a single video."""
        try:
            request = self.youtube.videos().list(
                part='statistics',
                id=video_id
            )
            response = request.execute()
            
            if response.get('items'):
                stats = response['items'][0]['statistics']
                return {
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                    'subscribers_gained': 0,  # Not available per video
                    'impressions': 0,  # Requires different API
                }
            return None
        except Exception as e:
            print(f"Error getting video statistics: {e}")
            return None
    
    def get_video_details(self, video_ids: List[str]) -> pd.DataFrame:
        """Get detailed statistics for videos."""
        if not video_ids:
            return pd.DataFrame()
        
        all_stats = []
        
        # YouTube API allows max 50 video IDs per request
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(batch)
            )
            response = request.execute()
            
            for item in response['items']:
                stats = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt'],
                    'duration': item['contentDetails'].get('duration', 'PT0M0S'),
                    'views': int(item['statistics'].get('viewCount', 0)),
                    'likes': int(item['statistics'].get('likeCount', 0)),
                    'comments': int(item['statistics'].get('commentCount', 0)),
                    'favorites': int(item['statistics'].get('favoriteCount', 0)),
                }
                all_stats.append(stats)
        
        df = pd.DataFrame(all_stats)
        
        # Parse duration
        if not df.empty:
            df['duration_seconds'] = df['duration'].apply(self._parse_duration)
            df['published_at'] = pd.to_datetime(df['published_at'])
        
        return df
    
    def _parse_duration(self, duration: str) -> int:
        """Parse YouTube duration format (PT1H30M45S) to seconds."""
        import re
        hours = 0
        minutes = 0
        seconds = 0
        
        hour_match = re.search(r'(\d+)H', duration)
        min_match = re.search(r'(\d+)M', duration)
        sec_match = re.search(r'(\d+)S', duration)
        
        if hour_match:
            hours = int(hour_match.group(1))
        if min_match:
            minutes = int(min_match.group(1))
        if sec_match:
            seconds = int(sec_match.group(1))
        
        return hours * 3600 + minutes * 60 + seconds
    
    def get_channel_videos(self, channel_id: str, max_results: int = None) -> pd.DataFrame:
        """Get all videos from a channel with statistics."""
        max_results = max_results or settings.MAX_VIDEOS  # Default is now 150
        
        # Ensure we get at least 100 videos for analysis
        if max_results < 100:
            max_results = 100
        
        # Get channel info
        channel_info = self.get_channel_info(channel_id)
        if not channel_info:
            print(f"Could not find channel with ID: {channel_id}")
            return pd.DataFrame()
        
        print(f"Channel: {channel_info['channel_name']}")
        print(f"Total videos: {channel_info['total_videos']}")
        
        # Get uploaded videos
        videos = self.get_uploaded_videos(channel_info['uploads_playlist_id'], max_results)
        print(f"Fetched {len(videos)} video IDs")
        
        if not videos:
            return pd.DataFrame()
        
        # Get detailed statistics
        video_ids = [v['video_id'] for v in videos]
        df = self.get_video_details(video_ids)
        
        return df
    
    def search_videos(self, channel_id: str, query: str, max_results: int = 50) -> pd.DataFrame:
        """Search videos in a channel."""
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                q=query,
                type='video',
                maxResults=min(50, max_results - len(videos)),
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response['items']:
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_id': item['snippet']['channelId'],
                    'description': item['snippet'].get('description', '')
                })
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return pd.DataFrame(videos[:max_results])


def fetch_youtube_data(channel_id: str = None) -> pd.DataFrame:
    """Main function to fetch YouTube data."""
    channel_id = channel_id or settings.DEFAULT_CHANNEL_ID
    
    if not channel_id:
        print("Please provide a channel ID")
        return pd.DataFrame()
    
    try:
        yt = YouTubeAPI()
        df = yt.get_channel_videos(channel_id)
        print(f"\nFetched {len(df)} videos successfully!")
        return df
    except Exception as e:
        print(f"Error fetching YouTube data: {e}")
        return pd.DataFrame()


# Test function
if __name__ == "__main__":
    print("Testing YouTube API...")
    
    # Test with a sample channel
    # You can use any public YouTube channel ID
    test_channel_id = settings.DEFAULT_CHANNEL_ID or "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # Google Developers
    
    if test_channel_id:
        df = fetch_youtube_data(test_channel_id)
        if not df.empty:
            print("\nSample data:")
            print(df.head())
    else:
        print("Please set DEFAULT_CHANNEL_ID in .env file")
