"""
Analytics and Metrics Module.
Calculates various analytics metrics from YouTube data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple


class AnalyticsMetrics:
    """Calculate analytics metrics from video data."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with video data."""
        self.df = df
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics."""
        if self.df.empty:
            return {}
        
        # Safely get column values with defaults
        likes = self.df['likes'].sum() if 'likes' in self.df.columns else 0
        comments = self.df['comments'].sum() if 'comments' in self.df.columns else 0
        views_sum = self.df['views'].sum()
        
        return {
            'total_videos': len(self.df),
            'total_views': int(views_sum),
            'total_likes': int(likes),
            'total_comments': int(comments),
            'avg_views': float(self.df['views'].mean()),
            'avg_likes': float(self.df['likes'].mean()) if 'likes' in self.df.columns else 0,
            'avg_comments': float(self.df['comments'].mean()) if 'comments' in self.df.columns else 0,
            'avg_engagement_rate': float(self.df['engagement_rate'].mean()) if 'engagement_rate' in self.df.columns else (likes + comments) / views_sum * 100 if views_sum > 0 else 0,
            'total_watch_time_hours': float(self.df['watch_time_hours'].sum()) if 'watch_time_hours' in self.df.columns else 0,
            'avg_ctr': float(self.df['ctr'].mean()) if 'ctr' in self.df.columns else 0,
            'total_impressions': int(self.df['impressions'].sum()) if 'impressions' in self.df.columns else 0,
            'total_subscribers': int(self.df['subscribers_gained'].sum()) if 'subscribers_gained' in self.df.columns else 0,
            'avg_subscribers': float(self.df['subscribers_gained'].mean()) if 'subscribers_gained' in self.df.columns else 0,
        }
    
    def get_top_videos(self, n: int = 10, sort_by: str = 'views') -> pd.DataFrame:
        """Get top N videos by specified metric."""
        if self.df.empty:
            return pd.DataFrame()
        
        return self.df.nlargest(n, sort_by)[['video_id', 'title', 'published_at', 
                                              'views', 'likes', 'comments', 'engagement_rate']]
    
    def get_worst_videos(self, n: int = 10, sort_by: str = 'views') -> pd.DataFrame:
        """Get worst N videos by specified metric."""
        if self.df.empty:
            return pd.DataFrame()
        
        return self.df.nsmallest(n, sort_by)[['video_id', 'title', 'published_at', 
                                               'views', 'likes', 'comments', 'engagement_rate']]
    
    def get_performance_by_day(self) -> pd.DataFrame:
        """Get average performance by day of week."""
        if self.df.empty:
            return pd.DataFrame()
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Group by day of week
        by_day = self.df.groupby('day_of_week').agg({
            'views': 'mean',
            'likes': 'mean',
            'comments': 'mean',
            'engagement_rate': 'mean',
            'video_id': 'count'
        }).rename(columns={'video_id': 'video_count'})
        
        # Reorder by day of week
        by_day = by_day.reindex(day_order)
        
        return by_day.reset_index()
    
    def get_performance_by_hour(self) -> pd.DataFrame:
        """Get average performance by hour of day."""
        if self.df.empty or 'hour' not in self.df.columns:
            return pd.DataFrame()
        
        by_hour = self.df.groupby('hour').agg({
            'views': 'mean',
            'likes': 'mean',
            'comments': 'mean',
            'engagement_rate': 'mean',
            'video_id': 'count'
        }).rename(columns={'video_id': 'video_count'})
        
        return by_hour.reset_index()
    
    def get_growth_trends(self, days: int = 30) -> pd.DataFrame:
        """Get growth trends over time."""
        if self.df.empty:
            return pd.DataFrame()
        
        # Convert to datetime with UTC
        self.df["published_at"] = pd.to_datetime(self.df["published_at"], utc=True)

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        df_filtered = self.df[self.df["published_at"] >= cutoff_date]
        return df_filtered
    
    def get_monthly_stats(self) -> pd.DataFrame:
        """Get monthly statistics."""
        if self.df.empty:
            return pd.DataFrame()
        
        # Ensure published_at is datetime
        self.df['published_at'] = pd.to_datetime(self.df['published_at'])
        
        # Group by month
        self.df['month'] = self.df['published_at'].dt.to_period('M')
        
        by_month = self.df.groupby('month').agg({
            'views': ['sum', 'mean'],
            'likes': ['sum', 'mean'],
            'comments': ['sum', 'mean'],
            'engagement_rate': 'mean',
            'video_id': 'count'
        })
        
        by_month.columns = ['_'.join(col).strip() for col in by_month.columns.values]
        by_month = by_month.rename(columns={'video_id_count': 'video_count'})
        
        return by_month.reset_index()
    
    def calculate_video_velocity(self) -> pd.DataFrame:
        """Calculate views velocity (views per day since publish)."""
        if self.df.empty:
            return pd.DataFrame()
        
        df = self.df.copy()
        # Ensure published_at is datetime
        df['published_at'] = pd.to_datetime(df['published_at'])
        df['days_since_published'] = (datetime.now(timezone.utc) - df['published_at']).dt.days
        
        df['views_per_day'] = df.apply(
            lambda x: x['views'] / max(x['days_since_published'], 1), 
            axis=1
        )
        
        return df[['video_id', 'title', 'days_since_published', 'views', 'views_per_day']]
    
    def get_engagement_distribution(self) -> Dict:
        """Get engagement rate distribution."""
        if self.df.empty:
            return {}
        
        engagement = self.df['engagement_rate']
        
        return {
            'min': float(engagement.min()),
            'max': float(engagement.max()),
            'mean': float(engagement.mean()),
            'median': float(engagement.median()),
            'std': float(engagement.std()),
            'q25': float(engagement.quantile(0.25)),
            'q75': float(engagement.quantile(0.75))
        }
    
    def get_content_gaps(self) -> List[Dict]:
        """Identify content gaps."""
        gaps = []
        
        # Check for low-performing days
        by_day = self.get_performance_by_day()
        if not by_day.empty:
            worst_day = by_day.loc[by_day['views'].idxmin()]
            gaps.append({
                'type': 'day',
                'description': f"Lowest views on {worst_day['day_of_week']}",
                'recommendation': f"Consider posting more content on {worst_day['day_of_week']}"
            })
        
        # Check for low engagement content
        if not self.df.empty:
            low_engagement = self.df[self.df['engagement_rate'] < self.df['engagement_rate'].quantile(0.25)]
            if len(low_engagement) > 0:
                gaps.append({
                    'type': 'engagement',
                    'description': f"{len(low_engagement)} videos have below-average engagement",
                    'recommendation': 'Review low-engagement videos for content improvement'
                })
        
        return gaps
    
    def get_performance_tiers(self) -> Dict:
        """Categorize videos into performance tiers."""
        if self.df.empty:
            return {}
        
        views_75 = self.df['views'].quantile(0.75)
        views_50 = self.df['views'].quantile(0.50)
        views_25 = self.df['views'].quantile(0.25)
        
        return {
            'viral': {
                'min_views': int(views_75),
                'count': len(self.df[self.df['views'] >= views_75]),
                'description': 'Top 25% by views'
            },
            'good': {
                'min_views': int(views_50),
                'count': len(self.df[(self.df['views'] >= views_50) & (self.df['views'] < views_75)]),
                'description': '50-75% by views'
            },
            'average': {
                'min_views': int(views_25),
                'count': len(self.df[(self.df['views'] >= views_25) & (self.df['views'] < views_50)]),
                'description': '25-50% by views'
            },
            'low': {
                'min_views': 0,
                'count': len(self.df[self.df['views'] < views_25]),
                'description': 'Bottom 25% by views'
            }
        }


def calculate_metrics(df: pd.DataFrame) -> AnalyticsMetrics:
    """Create AnalyticsMetrics instance."""
    return AnalyticsMetrics(df)


# Test metrics
if __name__ == "__main__":
    # Create sample data
    sample_data = pd.DataFrame({
        'video_id': [f'video_{i}' for i in range(1, 11)],
        'title': [f'Video {i}' for i in range(1, 11)],
        'published_at': pd.date_range('2024-01-01', periods=10, freq='D'),
        'views': [1000, 5000, 2000, 8000, 15000, 3000, 7000, 4000, 6000, 2500],
        'likes': [50, 250, 100, 400, 750, 150, 350, 200, 300, 125],
        'comments': [10, 50, 20, 80, 150, 30, 70, 40, 60, 25],
        'engagement_rate': [6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0],
        'day_of_week': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
                        'Monday', 'Tuesday', 'Wednesday'],
        'hour': [10, 12, 14, 16, 18, 20, 22, 8, 10, 12],
        'subscribers_gained': [100, 500, 200, 800, 1500, 300, 700, 400, 600, 250],
        'ctr': [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        'watch_time_hours': [10.0, 50.0, 20.0, 80.0, 150.0, 30.0, 70.0, 40.0, 60.0, 25.0]
    })
    
    metrics = AnalyticsMetrics(sample_data)
    
    print("Summary Stats:")
    print(metrics.get_summary_stats())
    
    print("\nTop 5 Videos:")
    print(metrics.get_top_videos(5))
    
    print("\nPerformance by Day:")
    print(metrics.get_performance_by_day())
    
    print("\nEngagement Distribution:")
    print(metrics.get_engagement_distribution())
