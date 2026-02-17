"""
Sample Data Generator Module.
Generates realistic YouTube video data for testing and demo purposes.
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np


class SampleDataGenerator:
    """Generate realistic sample YouTube video data."""
    
    # Sample video titles by category
    VIDEO_TITLES = {
        'Tutorial': [
            'How to Grow Your YouTube Channel in 2024',
            'Complete Guide to Video Editing',
            'Beginner Tutorial: Getting Started',
            'How to Make Professional Videos',
            'Step by Step Guide to Content Creation',
            'Learn Video Editing in 10 Minutes',
            'Mastering YouTube SEO Tips',
            'How to Edit Like a Pro',
            'Complete Tutorial for Beginners',
            'Advanced Editing Techniques'
        ],
        'Review': [
            'iPhone 15 Pro Honest Review',
            'Best Camera for YouTube - Honest Review',
            'Mic Review: Is It Worth It?',
            'Sony vs Canon - Which is Better?',
            'After 1 Month Using - True Review',
            'AirPods Pro 2 Review',
            'MacBook Pro M3 Review',
            'Honest Thoughts After 6 Months',
            'Product Review: Worth the Money?',
            'Detailed Analysis and Thoughts'
        ],
        'List': [
            'Top 10 Gadgets of 2024',
            'Best YouTube Tips You Need to Know',
            'Top 5 Cameras for Creators',
            'Worst Tech Mistakes to Avoid',
            'Top 10 Video Ideas for Growth',
            'Best Editing Software Ranked',
            'Top 7 Tips for Beginners',
            'Most Important Tips for Success',
            'Top 5 Mistakes to Avoid',
            'Best Strategies for Growth'
        ],
        'Entertainment': [
            '24 Hour Challenge Gone Wrong',
            'I Tried Everything for 30 Days',
            'Fun Challenge - Watch Until End',
            'Epic Fail Compilation',
            'Day in My Life Vlog',
            'Reacting to My Old Videos',
            'Storytime: How I Started',
            'My Morning Routine 2024',
            'Q&A - Answering Your Questions',
            'Gaming Session with Fans'
        ],
        'News': [
            'YouTube Algorithm Changes Explained',
            'New Feature Announcement',
            'Big News for Creators',
            'Platform Update - What Changed',
            'Important Announcement for Everyone',
            'Breaking: New YouTube Rules',
            'What Happened to My Channel',
            'Channel Update and News',
            'Exciting News!',
            'Everything You Need to Know'
        ],
        'Educational': [
            'Why Your Videos Are Not Growing',
            'What is the YouTube Algorithm?',
            'The Science Behind Engagement',
            'Why Consistency Matters',
            'Understanding YouTube Analytics',
            'How the Algorithm Works',
            'The Truth About Growing Fast',
            'Key Factors for Success',
            'Everything About Watch Time',
            'Learning About CTR'
        ],
        'Gaming': [
            'Gaming Setup Tour 2024',
            'First Impressions - New Game',
            'Let\'s Play: Adventure Game',
            'Gaming Challenge Day 1',
            'Ultimate Gaming Setup Build',
            'Best Gaming Gear Review',
            'Playing With Subscribers',
            'New Gameplay - Full Walkthrough',
            'Gaming Session Highlights',
            'Stream Highlights Compilation'
        ],
        'Tech': [
            'New Phone Unboxing',
            'Tech Review: Latest Gadgets',
            'Computer Setup Tour',
            'Tech Tips and Tricks',
            'Latest Tech News 2024',
            'Smartphone Comparison',
            'Best Laptop for Creators',
            'Tech Unboxing and First Look',
            'Device Review and Setup',
            'Technology Explained Simply'
        ]
    }
    
    # Days of week for realistic distribution
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Peak hours for YouTube
    PEAK_HOURS = [12, 14, 16, 18, 19, 20, 21]
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducibility."""
        random.seed(seed)
        np.random.seed(seed)
    
    def generate_sample_data(self, num_videos: int = 100, channel_name: str = "Demo Channel") -> pd.DataFrame:
        """
        Generate realistic sample YouTube video data.
        
        Args:
            num_videos: Number of videos to generate (default 100)
            channel_name: Name of the channel
            
        Returns:
            DataFrame with video data
        """
        videos = []
        start_date = datetime.now() - timedelta(days=num_videos)
        
        # Channel stats (realistic for a growing channel)
        base_views = random.randint(5000, 50000)
        
        for i in range(num_videos):
            # Choose a random category
            category = random.choice(list(self.VIDEO_TITLES.keys()))
            title = random.choice(self.VIDEO_TITLES[category])
            
            # Add some variation to titles
            if random.random() > 0.7:
                title = f"{title} - Part {random.randint(1, 5)}"
            
            # Publish date - more recent videos have higher views (channel growth)
            days_ago = num_videos - i - 1
            publish_date = start_date + timedelta(days=random.randint(0, num_videos))
            
            # Day and hour
            day_of_week = publish_date.strftime('%A')
            hour = random.choice(self.PEAK_HOURS) if random.random() > 0.3 else random.randint(8, 23)
            
            # Views - more recent videos tend to have more views (channel growth pattern)
            # But older videos may have accumulated more views
            base_view_count = base_views * (1 + (days_ago / num_videos) * 0.5)  # Growth trend
            view_count = int(base_view_count * random.uniform(0.2, 3.0))
            
            # Add some viral outliers
            if random.random() > 0.95:
                view_count = int(view_count * random.uniform(3, 10))
            
            # Engagement metrics (realistic ratios)
            like_ratio = random.uniform(0.02, 0.08)  # 2-8% of views
            comment_ratio = random.uniform(0.002, 0.02)  # 0.2-2% of views
            
            likes = int(view_count * like_ratio)
            comments = int(view_count * comment_ratio)
            
            # Engagement rate
            engagement_rate = ((likes + comments) / view_count * 100) if view_count > 0 else 0
            
            # Impressions (estimated)
            impressions = int(view_count * random.uniform(2, 5))
            
            # CTR
            ctr = (view_count / impressions * 100) if impressions > 0 else 0
            
            # Duration (in seconds)
            if category in ['Tutorial', 'Educational']:
                duration = random.randint(300, 1800)  # 5-30 minutes
            elif category in ['List', 'Entertainment']:
                duration = random.randint(180, 900)  # 3-15 minutes
            else:
                duration = random.randint(120, 600)  # 2-10 minutes
            
            # Subscribers gained (correlated with views)
            subs_gained = int(view_count * random.uniform(0.01, 0.05))
            
            videos.append({
                'video_id': f'video_{i+1:04d}',
                'title': title,
                'published_at': publish_date.isoformat(),
                'views': view_count,
                'likes': likes,
                'comments': comments,
                'engagement_rate': round(engagement_rate, 2),
                'impressions': impressions,
                'ctr': round(ctr, 2),
                'subscribers_gained': subs_gained,
                'duration_seconds': duration,
                'day_of_week': day_of_week,
                'hour': hour,
                'category': category
            })
        
        df = pd.DataFrame(videos)
        
        # Sort by publish date
        df = df.sort_values('published_at').reset_index(drop=True)
        
        return df
    
    def generate_small_sample(self) -> pd.DataFrame:
        """Generate a small sample (50 videos) for quick testing."""
        return self.generate_sample_data(50)
    
    def generate_medium_sample(self) -> pd.DataFrame:
        """Generate a medium sample (100 videos)."""
        return self.generate_sample_data(100)
    
    def generate_large_sample(self) -> pd.DataFrame:
        """Generate a large sample (150 videos)."""
        return self.generate_sample_data(150)
    
    def generate_viral_channel(self, num_videos: int = 100) -> pd.DataFrame:
        """Generate data for a viral/successful channel."""
        df = self.generate_sample_data(num_videos)
        
        # Boost all metrics for viral channel
        df['views'] = (df['views'] * random.uniform(3, 10)).astype(int)
        df['likes'] = (df['likes'] * random.uniform(2, 5)).astype(int)
        df['comments'] = (df['comments'] * random.uniform(2, 5)).astype(int)
        df['engagement_rate'] = df.apply(
            lambda x: ((x['likes'] + x['comments']) / x['views'] * 100) if x['views'] > 0 else 0, 
            axis=1
        )
        
        return df
    
    def generate_struggling_channel(self, num_videos: int = 100) -> pd.DataFrame:
        """Generate data for a struggling channel."""
        df = self.generate_sample_data(num_videos)
        
        # Reduce metrics for struggling channel
        df['views'] = (df['views'] * random.uniform(0.1, 0.5)).astype(int)
        df['likes'] = (df['likes'] * random.uniform(0.1, 0.3)).astype(int)
        df['comments'] = (df['comments'] * random.uniform(0.1, 0.3)).astype(int)
        
        return df


def generate_sample_data(num_videos: int = 100) -> pd.DataFrame:
    """Quick function to generate sample data."""
    generator = SampleDataGenerator()
    return generator.generate_sample_data(num_videos)


# Test the generator
if __name__ == "__main__":
    print("Testing Sample Data Generator...")
    
    # Generate sample data
    generator = SampleDataGenerator()
    df = generator.generate_sample_data(100)
    
    print(f"\nGenerated {len(df)} videos")
    print(f"Total Views: {df['views'].sum():,}")
    print(f"Total Likes: {df['likes'].sum():,}")
    print(f"Average Engagement Rate: {df['engagement_rate'].mean():.2f}%")
    
    print("\n📊 Sample Data Preview:")
    print(df[['title', 'views', 'likes', 'engagement_rate', 'category']].head(10))
    
    print("\n📅 Performance by Day:")
    day_perf = df.groupby('day_of_week')['views'].mean()
    print(day_perf)
    
    print("\n⏰ Performance by Hour:")
    hour_perf = df.groupby('hour')['views'].mean()
    print(hour_perf)
