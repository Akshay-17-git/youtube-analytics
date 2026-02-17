"""
ETL Pipeline Module.
Handles data extraction, transformation, and loading.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Tuple

from src.youtube_api import YouTubeAPI
from src.database import save_video_metrics, get_all_video_metrics


class ETLPipeline:
    """ETL Pipeline for YouTube Analytics data."""
    
    def __init__(self):
        """Initialize ETL pipeline."""
        self.youtube_api = None
    
    def extract_from_api(self, channel_id: str) -> pd.DataFrame:
        """Extract data from YouTube API."""
        print("Extracting data from YouTube API...")
        
        if not self.youtube_api:
            self.youtube_api = YouTubeAPI()
        
        df = self.youtube_api.get_channel_videos(channel_id)
        print(f"Extracted {len(df)} videos from API")
        return df
    
    def extract_from_csv(self, file_path: str) -> pd.DataFrame:
        """Extract data from CSV file (YouTube Studio export)."""
        print(f"Extracting data from CSV: {file_path}")
        
        df = pd.read_csv(file_path)
        print(f"Extracted {len(df)} rows from CSV")
        return df
    
    def transform_api_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data from YouTube API."""
        print("Transforming API data...")
        
        if df.empty:
            return df
        
        # Ensure required columns exist
        required_cols = ['video_id', 'title', 'published_at', 'views', 'likes', 'comments']
        
        # Add missing columns with default values
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0 if col in ['views', 'likes', 'comments'] else ''
        
        # Add calculated metrics
        df['impressions'] = df.get('impressions', 0)
        df['ctr'] = df.get('ctr', 0.0)
        df['watch_time_hours'] = df.get('watch_time_hours', 0.0)
        df['subscribers_gained'] = df.get('subscribers_gained', 0)
        
        # If impressions are 0, estimate based on views (typical CTR ~30-50%)
        if df['impressions'].sum() == 0:
            # Estimate impressions: assume each view came from an impression
            # Typical click-through rate is around 30-50% for popular videos
            df['impressions'] = (df['views'] * 3).astype(int)  # 3x views as impressions
        
        # Calculate Views per Impression (Proxy CTR)
        # Note: True CTR = Clicks / Impressions. Since YouTube Data API doesn't provide
        # click data per video, we use views/impressions as a proxy (Views per Impression %)
        if df['impressions'].sum() > 0:
            df['views_per_impression'] = (df['views'] / df['impressions'] * 100).replace([float('inf'), -float('inf')], 0)
            # Keep 'ctr' for backwards compatibility but it's actually views_per_impression
        
        # Estimate subscribers gained based on engagement (typical conversion rate)
        if df['subscribers_gained'].sum() == 0:
            # Typical subscriber conversion: ~1-3% of engaged users
            df['subscribers_gained'] = ((df['likes'] + df['comments']) * 0.1).astype(int)
        
        # Calculate engagement rate
        df['engagement_rate'] = df.apply(
            lambda x: ((x['likes'] + x['comments']) / x['views'] * 100) 
            if x['views'] > 0 else 0, 
            axis=1
        )
        
        # Calculate subs per 1k views
        df['subs_per_1k_views'] = df.apply(
            lambda x: (x['subscribers_gained'] / x['views'] * 1000) 
            if x['views'] > 0 else 0, 
            axis=1
        )
        
        # Calculate subscriber conversion rate (%)
        df['sub_conversion_rate'] = df.apply(
            lambda x: (x['subscribers_gained'] / x['views'] * 100)
            if x['views'] > 0 else 0,
            axis=1
        )
        
        # Convert published_at to datetime
        df['published_at'] = pd.to_datetime(df['published_at'])
        
        # Add day of week
        df['day_of_week'] = df['published_at'].dt.day_name()
        
        # Add hour
        df['hour'] = df['published_at'].dt.hour
        
        print(f"Transformed {len(df)} records")
        return df
    
    def transform_csv_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data from YouTube Studio CSV export."""
        print("Transforming CSV data...")
        
        if df.empty:
            return df
        
        # Map CSV columns to standard schema
        column_mapping = {
            'Video title': 'title',
            'Video ID': 'video_id',
            'Publish date': 'published_at',
            'Views': 'views',
            'Likes': 'likes',
            'Comments': 'comments',
            'Impressions': 'impressions',
            'Click-through rate (CTR)': 'ctr',
            'Watch time (hours)': 'watch_time_hours',
            'Subscribers': 'subscribers_gained'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Calculate engagement rate
        df['engagement_rate'] = df.apply(
            lambda x: ((x.get('likes', 0) + x.get('comments', 0)) / x.get('views', 1) * 100) 
            if x.get('views', 0) > 0 else 0, 
            axis=1
        )
        
        # Calculate subs per 1k views
        df['subs_per_1k_views'] = df.apply(
            lambda x: (x.get('subscribers_gained', 0) / x.get('views', 1) * 1000) 
            if x.get('views', 0) > 0 else 0, 
            axis=1
        )
        
        # Convert published_at to datetime
        df['published_at'] = pd.to_datetime(df['published_at'])
        
        # Add day of week
        df['day_of_week'] = df['published_at'].dt.day_name()
        
        print(f"Transformed {len(df)} CSV records")
        return df
    
    def merge_data(self, api_df: pd.DataFrame, csv_df: pd.DataFrame) -> pd.DataFrame:
        """Merge API data with CSV data."""
        print("Merging API and CSV data...")
        
        if api_df.empty:
            return csv_df
        if csv_df.empty:
            return api_df
        
        # Merge on video_id
        merged = pd.merge(
            api_df, 
            csv_df[['video_id', 'impressions', 'ctr', 'watch_time_hours', 'subscribers_gained']],
            on='video_id',
            how='left',
            suffixes=('_api', '_csv')
        )
        
        # Use CSV values if available, otherwise use API values
        merged['impressions'] = merged['impressions_csv'].fillna(merged.get('impressions_api', 0))
        merged['ctr'] = merged['ctr_csv'].fillna(merged.get('ctr_api', 0))
        merged['watch_time_hours'] = merged['watch_time_hours_csv'].fillna(merged.get('watch_time_hours_api', 0))
        merged['subscribers_gained'] = merged['subscribers_gained_csv'].fillna(merged.get('subscribers_gained_api', 0))
        
        # Recalculate metrics
        merged['engagement_rate'] = merged.apply(
            lambda x: ((x.get('likes', 0) + x.get('comments', 0)) / x.get('views', 1) * 100) 
            if x.get('views', 0) > 0 else 0, 
            axis=1
        )
        
        merged['subs_per_1k_views'] = merged.apply(
            lambda x: (x.get('subscribers_gained', 0) / x.get('views', 1) * 1000) 
            if x.get('views', 0) > 0 else 0, 
            axis=1
        )
        
        print(f"Merged data: {len(merged)} records")
        return merged
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate data."""
        print("Cleaning data...")
        
        if df.empty:
            return df
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['video_id'], keep='last')
        
        # Remove rows with missing video_id
        df = df.dropna(subset=['video_id'])
        
        # Fill missing values - ensure columns exist first
        df['views'] = df['views'].fillna(0).astype(int)
        df['likes'] = df['likes'].fillna(0).astype(int)
        df['comments'] = df['comments'].fillna(0).astype(int)
        
        # Add missing columns with defaults if they don't exist
        if 'impressions' not in df.columns:
            df['impressions'] = 0
        df['impressions'] = df['impressions'].fillna(0).astype(int)
        
        if 'ctr' not in df.columns:
            df['ctr'] = 0.0
        df['ctr'] = df['ctr'].fillna(0.0)
        
        if 'watch_time_hours' not in df.columns:
            df['watch_time_hours'] = 0.0
        df['watch_time_hours'] = df['watch_time_hours'].fillna(0.0)
        
        if 'subscribers_gained' not in df.columns:
            df['subscribers_gained'] = 0
        df['subscribers_gained'] = df['subscribers_gained'].fillna(0).astype(int)
        
        if 'engagement_rate' not in df.columns:
            df['engagement_rate'] = 0.0
        df['engagement_rate'] = df['engagement_rate'].fillna(0.0)
        
        if 'subs_per_1k_views' not in df.columns:
            df['subs_per_1k_views'] = 0.0
        df['subs_per_1k_views'] = df['subs_per_1k_views'].fillna(0.0)
        
        # Handle infinite values
        df = df.replace([np.inf, -np.inf], 0)
        
        print(f"Cleaned data: {len(df)} records")
        return df
    
    def load_to_database(self, df: pd.DataFrame):
        """Load data to database."""
        print("Loading data to database...")
        
        save_video_metrics(df)
        print("Data loaded successfully!")
    
    def run_pipeline(self, channel_id: str = None, csv_path: str = None) -> pd.DataFrame:
        """Run complete ETL pipeline."""
        print("=" * 50)
        print("Starting ETL Pipeline")
        print("=" * 50)
        
        # Extract
        api_df = pd.DataFrame()
        csv_df = pd.DataFrame()
        
        if channel_id:
            api_df = self.extract_from_api(channel_id)
            api_df = self.transform_api_data(api_df)
        
        if csv_path:
            csv_df = self.extract_from_csv(csv_path)
            csv_df = self.transform_csv_data(csv_df)
        
        # Merge
        if not api_df.empty and not csv_df.empty:
            final_df = self.merge_data(api_df, csv_df)
        elif not api_df.empty:
            final_df = api_df
        else:
            final_df = csv_df
        
        # Clean
        final_df = self.clean_data(final_df)
        
        # Load
        if not final_df.empty:
            self.load_to_database(final_df)
        
        print("=" * 50)
        print("ETL Pipeline Complete!")
        print(f"Total records: {len(final_df)}")
        print("=" * 50)
        
        return final_df


def run_etl(channel_id: str = None, csv_path: str = None) -> pd.DataFrame:
    """Run ETL pipeline."""
    pipeline = ETLPipeline()
    return pipeline.run_pipeline(channel_id, csv_path)


# Test ETL pipeline
if __name__ == "__main__":
    import config.settings as settings
    
    print("Testing ETL Pipeline...")
    
    # Initialize database first
    from src.database import init_database, test_connection
    
    if test_connection():
        init_database()
        
        # Test with sample data
        pipeline = ETLPipeline()
        
        # Create sample data for testing
        sample_data = pd.DataFrame({
            'video_id': ['test1', 'test2', 'test3'],
            'title': ['Test Video 1', 'Test Video 2', 'Test Video 3'],
            'published_at': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
            'views': [1000, 2000, 3000],
            'likes': [50, 100, 150],
            'comments': [10, 20, 30],
            'impressions': [5000, 10000, 15000],
            'ctr': [20.0, 20.0, 20.0],
            'watch_time_hours': [10.5, 21.0, 31.5],
            'subscribers_gained': [100, 200, 300]
        })
        
        # Transform and clean
        transformed = pipeline.transform_api_data(sample_data)
        cleaned = pipeline.clean_data(transformed)
        
        print("\nSample transformed data:")
        print(cleaned)
        
        # Save to database
        pipeline.load_to_database(cleaned)
        print("\nETL Pipeline test complete!")
    else:
        print("Please check your database configuration")
