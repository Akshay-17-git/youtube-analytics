"""
Pattern Detection Module.
Automatically identifies content patterns in YouTube videos.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple
from collections import defaultdict, Counter


class PatternDetection:
    """Detect patterns in video content and performance."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with video data."""
        self.df = df.copy()
    
    def detect_content_themes(self) -> List[Dict]:
        """Detect common content themes based on YOUR channel's video titles."""
        if self.df.empty:
            return []
        
        # First, extract all meaningful keywords from the channel's video titles
        all_words = []
        for _, row in self.df.iterrows():
            title = str(row.get('title', '')).lower()
            # Extract words (filter out common stop words)
            words = re.findall(r'\b\w{4,}\b', title)
            all_words.extend(words)
        
        # Count word frequency
        word_counts = Counter(all_words)
        
        # Filter to get top recurring themes (words appearing 2+ times)
        common_words = {word: count for word, count in word_counts.items() if count >= 2}
        
        # If we don't have enough recurring words, use top individual keywords
        if len(common_words) < 3:
            # Fall back to top individual keywords
            common_words = dict(word_counts.most_common(10))
        
        # Group videos by their main keywords
        theme_videos = defaultdict(lambda: {'views': [], 'titles': [], 'count': 0})
        
        for _, row in self.df.iterrows():
            title = str(row.get('title', '')).lower()
            
            # Find which theme keywords this video contains
            matched_themes = []
            for word in common_words:
                if word in title:
                    matched_themes.append(word)
            
            if matched_themes:
                # Use the most specific (longest) matching keyword as the theme
                primary_theme = max(matched_themes, key=len)
                theme_videos[primary_theme]['views'].append(row.get('views', 0))
                theme_videos[primary_theme]['titles'].append(row.get('title', '')[:50])
                theme_videos[primary_theme]['count'] += 1
        
        # Calculate stats for each channel-specific theme
        themes = []
        for theme, stats in theme_videos.items():
            if stats['count'] >= 1:  # At least 1 video
                avg_views = int(np.mean(stats['views'])) if stats['views'] else 0
                themes.append({
                    'theme': theme.title(),  # Capitalize
                    'count': stats['count'],
                    'avg_views': avg_views,
                    'example_title': stats['titles'][0] if stats['titles'] else '',
                    'performance': self._rate_performance(avg_views)
                })
        
        # Sort by average views
        themes.sort(key=lambda x: x['avg_views'], reverse=True)
        
        return themes[:10]  # Return top 10 themes
    
    def detect_duration_patterns(self) -> Dict:
        """Analyze video duration patterns."""
        if self.df.empty or 'duration_seconds' not in self.df.columns:
            return {'error': 'Duration data not available'}
        
        # Define duration buckets
        duration_buckets = {
            'Short (< 5 min)': (0, 300),
            'Medium (5-15 min)': (300, 900),
            'Long (15-30 min)': (900, 1800),
            'Very Long (> 30 min)': (1800, float('inf'))
        }
        
        bucket_stats = {}
        
        for bucket_name, (min_dur, max_dur) in duration_buckets.items():
            bucket_data = self.df[
                (self.df['duration_seconds'] >= min_dur) & 
                (self.df['duration_seconds'] < max_dur)
            ]
            
            if len(bucket_data) > 0:
                bucket_stats[bucket_name] = {
                    'count': len(bucket_data),
                    'avg_views': int(bucket_data['views'].mean()),
                    'avg_engagement': round(bucket_data['engagement_rate'].mean(), 2)
                }
        
        return bucket_stats
    
    def detect_title_length_patterns(self) -> Dict:
        """Analyze title length patterns."""
        if self.df.empty:
            return {'error': 'No data available'}
        
        # Calculate title length
        self.df['title_length'] = self.df['title'].str.len()
        
        # Define buckets
        length_buckets = {
            'Very Short (< 30)': (0, 30),
            'Short (30-50)': (30, 50),
            'Medium (50-70)': (50, 70),
            'Long (70-90)': (70, 90),
            'Very Long (> 90)': (90, float('inf'))
        }
        
        bucket_stats = {}
        
        for bucket_name, (min_len, max_len) in length_buckets.items():
            bucket_data = self.df[
                (self.df['title_length'] >= min_len) & 
                (self.df['title_length'] < max_len)
            ]
            
            if len(bucket_data) > 0:
                bucket_stats[bucket_name] = {
                    'count': len(bucket_data),
                    'avg_views': int(bucket_data['views'].mean()),
                    'avg_ctr': round(bucket_data['ctr'].mean(), 2) if 'ctr' in bucket_data.columns else 0
                }
        
        return bucket_stats
    
    def detect_engagement_patterns(self) -> Dict:
        """Detect engagement patterns."""
        if self.df.empty:
            return {'error': 'No data available'}
        
        # High vs low engagement videos
        median_engagement = self.df['engagement_rate'].median()
        
        high_eng = self.df[self.df['engagement_rate'] >= median_engagement]
        low_eng = self.df[self.df['engagement_rate'] < median_engagement]
        
        low_avg = low_eng['views'].mean() if len(low_eng) > 0 else 1
        high_avg = high_eng['views'].mean() if len(high_eng) > 0 else 0
        
        return {
            'high_engagement': {
                'count': len(high_eng),
                'avg_views': int(high_avg),
                'avg_likes': int(high_eng['likes'].mean()) if len(high_eng) > 0 else 0,
                'avg_comments': int(high_eng['comments'].mean()) if len(high_eng) > 0 else 0
            },
            'low_engagement': {
                'count': len(low_eng),
                'avg_views': int(low_avg) if not pd.isna(low_avg) else 0,
                'avg_likes': int(low_eng['likes'].mean()) if len(low_eng) > 0 else 0,
                'avg_comments': int(low_eng['comments'].mean()) if len(low_eng) > 0 else 0
            },
            'insight': f"High engagement videos get {round((high_avg / max(low_avg, 1)) - 1, 2) * 100}% more views on average"
        }
    
    def detect_upload_consistency(self) -> Dict:
        """Analyze upload consistency patterns."""
        if self.df.empty:
            return {'error': 'No data available'}
        
        # Calculate days between uploads
        sorted_df = self.df.sort_values('published_at')
        dates = pd.to_datetime(sorted_df['published_at']).dt.date
        
        if len(dates) < 2:
            return {'error': 'Not enough data'}
        
        day_diffs = []
        for i in range(1, len(dates)):
            diff = (dates.iloc[i] - dates.iloc[i-1]).days
            day_diffs.append(diff)
        
        avg_gap = np.mean(day_diffs)
        
        # Consistency score
        std_gap = np.std(day_diffs)
        
        if std_gap < 2:
            consistency = "Very Consistent"
        elif std_gap < 5:
            consistency = "Moderately Consistent"
        else:
            consistency = "Inconsistent"
        
        return {
            'avg_days_between_uploads': round(avg_gap, 2),
            'std_days_between_uploads': round(std_gap, 2),
            'consistency': consistency,
            'recommendation': self._get_consistency_recommendation(avg_gap, std_gap)
        }
    
    def detect_winning_patterns(self) -> List[Dict]:
        """Detect patterns in top-performing videos."""
        if self.df.empty:
            return []
        
        # Get top 20% performers
        threshold = self.df['views'].quantile(0.80)
        top_performers = self.df[self.df['views'] >= threshold]
        
        patterns = []
        
        # Analyze common patterns
        title_lengths = top_performers['title'].str.len()
        
        patterns.append({
            'pattern': 'Average title length',
            'value': int(title_lengths.mean()),
            'description': 'Top performers average title length'
        })
        
        # Check for common words
        all_titles = ' '.join(top_performers['title'].str.lower())
        words = re.findall(r'\b\w{4,}\b', all_titles)
        word_counts = defaultdict(int)
        
        for word in words:
            word_counts[word] += 1
        
        common_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        patterns.append({
            'pattern': 'Common words in titles',
            'value': [w[0] for w in common_words],
            'description': 'Most common words in top performing video titles'
        })
        
        return patterns
    
    def get_all_patterns(self) -> Dict:
        """Get all detected patterns."""
        return {
            'content_themes': self.detect_content_themes(),
            'duration_patterns': self.detect_duration_patterns(),
            'title_length_patterns': self.detect_title_length_patterns(),
            'engagement_patterns': self.detect_engagement_patterns(),
            'upload_consistency': self.detect_upload_consistency(),
            'winning_patterns': self.detect_winning_patterns()
        }
    
    def _rate_performance(self, avg_views: float) -> str:
        """Rate performance based on average views."""
        overall_avg = self.df['views'].mean()
        
        if avg_views >= overall_avg * 1.5:
            return "Excellent"
        elif avg_views >= overall_avg:
            return "Good"
        elif avg_views >= overall_avg * 0.5:
            return "Average"
        else:
            return "Below Average"
    
    def _get_consistency_recommendation(self, avg_gap: float, std_gap: float) -> str:
        """Get recommendation based on consistency."""
        if avg_gap <= 3:
            return "Excellent consistency! Keep up the regular upload schedule."
        elif avg_gap <= 7:
            return "Good consistency. Try to maintain a more regular schedule."
        else:
            return "Inconsistent uploads. Consider creating a content calendar."


def detect_patterns(df: pd.DataFrame) -> PatternDetection:
    """Create PatternDetection instance."""
    return PatternDetection(df)


# Test Pattern Detection
if __name__ == "__main__":
    import random
    
    # Create sample data
    sample_data = pd.DataFrame({
        'video_id': [f'video_{i}' for i in range(1, 31)],
        'title': [
            'How to Edit Videos Like a Pro',
            'iPhone 15 Pro Review',
            'Top 10 Gadgets of 2024',
            'Funny Challenge Video',
            'Complete Tutorial: Python',
            'MacBook vs Windows Laptop',
            'Best Gaming Setup Tour',
            'My Morning Routine',
            'What is Artificial Intelligence?',
            'New iOS Update News',
            '5 Tips for Better Videos',
            'Unboxing the New Phone',
            'Worst Tech Mistakes',
            'Gaming Challenge: 24 Hours',
            'Learn Coding in 10 Minutes',
            'Honest Review: AirPods',
            'Top 5 Educational Apps',
            'Vlog: A Day in My Life',
            'Science Facts You Didnt Know',
            'Update: Channel News',
            'Tutorial: Photo Editing',
            'Phone Comparison 2024',
            'Best Apps for Students',
            'Prank Gone Wrong',
            'Beginner Guide to YouTube',
            'Tech News This Week',
            'Top 10 Movies List',
            'Gaming: First Impressions',
            'Story: How I Started',
            'Facts About Space'
        ],
        'published_at': pd.date_range('2024-01-01', periods=30, freq='D'),
        'views': [random.randint(5000, 20000) for _ in range(30)],
        'likes': [random.randint(100, 1000) for _ in range(30)],
        'comments': [random.randint(20, 200) for _ in range(30)],
        'engagement_rate': [random.uniform(3.0, 12.0) for _ in range(30)],
        'duration_seconds': [random.randint(180, 3600) for _ in range(30)],
        'ctr': [random.uniform(3.0, 10.0) for _ in range(30)]
    })
    
    detector = PatternDetection(sample_data)
    
    print("Content Theme Analysis:")
    themes = detector.detect_content_themes()
    for theme in themes[:3]:
        print(f"  {theme['theme']}: {theme['avg_views']} avg views ({theme['performance']})")
    
    print("\nEngagement Patterns:")
    eng_patterns = detector.detect_engagement_patterns()
    print(f"  Insight: {eng_patterns.get('insight')}")
    
    print("\nUpload Consistency:")
    consistency = detector.detect_upload_consistency()
    print(f"  Consistency: {consistency.get('consistency')}")
