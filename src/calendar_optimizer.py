"""
Content Calendar Optimizer Module.
Recommends optimal posting schedule for maximum views and subscriber growth.
"""
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class CalendarOptimizer:
    """Optimize content calendar based on historical performance."""
    
    def __init__(self, df: pd.DataFrame, timezone: str = 'UTC'):
        """Initialize with video data and timezone."""
        self.df = df.copy()
        self.timezone = timezone
        self._detect_timezone()
    
    def _detect_timezone(self):
        """Detect timezone from data or use default."""
        # Try to get timezone from published_at if available
        if 'published_at' in self.df.columns and len(self.df) > 0:
            try:
                # Check if timezone info exists in the data
                sample_dt = pd.to_datetime(self.df['published_at'].iloc[0])
                if sample_dt.tzinfo is not None:
                    self.timezone = str(sample_dt.tzinfo)
                else:
                    # Default to UTC if no timezone info
                    self.timezone = 'UTC'
            except:
                self.timezone = 'UTC'
    
    def get_timezone_display(self) -> str:
        """Get formatted timezone display string."""
        timezone_map = {
            'UTC': 'UTC (Coordinated Universal Time)',
            'US/Eastern': 'ET (Eastern Time - US)',
            'US/Central': 'CT (Central Time - US)',
            'US/Mountain': 'MT (Mountain Time - US)',
            'US/Pacific': 'PT (Pacific Time - US)',
            'Europe/London': 'GMT/BST (UK Time)',
            'Europe/Paris': 'CET/CEST (Central European Time)',
            'Asia/Tokyo': 'JST (Japan Standard Time)',
            'Asia/Singapore': 'SGT (Singapore Time)',
            'Asia/Dubai': 'GST (Gulf Standard Time)',
            'Australia/Sydney': 'AEST (Australian Eastern Time)',
            'Asia/Kolkata': 'IST (India Standard Time)',
            'Asia/Manila': 'PHT (Philippine Time)',
            'America/Sao_Paulo': 'BRT (Brasília Time)',
        }
        return timezone_map.get(self.timezone, f'{self.timezone} (Local Time)')
    
    def analyze_best_days(self) -> Dict:
        """Analyze best days of the week for posting."""
        if self.df.empty:
            return {'error': 'No data available'}
        
        # Add day_of_week if not present
        if 'day_of_week' not in self.df.columns:
            if 'published_at' in self.df.columns:
                self.df['day_of_week'] = pd.to_datetime(self.df['published_at']).dt.day_name()
            else:
                return {'error': 'No date data available to analyze days'}
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Calculate average metrics by day
        by_day = self.df.groupby('day_of_week').agg({
            'views': ['mean', 'sum', 'count'],
            'engagement_rate': 'mean',
            'likes': 'mean',
            'comments': 'mean'
        })
        
        by_day.columns = ['avg_views', 'total_views', 'video_count', 'avg_engagement', 'avg_likes', 'avg_comments']
        by_day = by_day.reindex(day_order)
        
        # Find best days
        best_day_views = by_day['avg_views'].idxmax()
        best_day_engagement = by_day['avg_engagement'].idxmax()
        
        return {
            'daily_stats': by_day.to_dict(),
            'best_day_for_views': best_day_views,
            'best_day_for_engagement': best_day_engagement,
            'recommendation': self._get_day_recommendation(by_day)
        }
    
    def analyze_best_hours(self) -> Dict:
        """Analyze best hours for posting with timezone awareness."""
        if self.df.empty:
            return {'error': 'No data available'}
        
        # Add hour if not present
        if 'hour' not in self.df.columns:
            if 'published_at' in self.df.columns:
                self.df['hour'] = pd.to_datetime(self.df['published_at']).dt.hour
            else:
                return {'error': 'No time data available to analyze hours'}
        
        by_hour = self.df.groupby('hour').agg({
            'views': ['mean', 'sum', 'count'],
            'engagement_rate': 'mean'
        })
        
        by_hour.columns = ['avg_views', 'total_views', 'video_count', 'avg_engagement']
        
        # Find best hours
        best_hour_views = by_hour['avg_views'].idxmax()
        best_hour_engagement = by_hour['avg_engagement'].idxmax()
        
        # Get top 3 hours
        top_hours = by_hour.nlargest(3, 'avg_views').index.tolist()
        
        return {
            'hourly_stats': by_hour.to_dict(),
            'best_hour_for_views': best_hour_views,
            'best_hour_for_engagement': best_hour_engagement,
            'top_3_hours': top_hours,
            'timezone': self.timezone,
            'timezone_display': self.get_timezone_display(),
            'recommendation': self._get_hour_recommendation(best_hour_views, top_hours)
        }
    
    def _format_hour_ampm(self, hour: int) -> str:
        """Convert hour to AM/PM format with context."""
        if hour == 0:
            return "12:00 AM (Midnight)"
        elif hour == 12:
            return "12:00 PM (Noon)"
        elif hour < 12:
            return f"{hour}:00 AM"
        else:
            return f"{hour-12}:00 PM"
    
    def _get_hour_recommendation(self, best_hour: int, top_hours: List[int]) -> str:
        """Get hour recommendation with AM/PM format and timezone."""
        best_formatted = self._format_hour_ampm(best_hour)
        top_formatted = [self._format_hour_ampm(h) for h in top_hours]
        timezone_display = self.get_timezone_display()
        
        return f"Best time: {best_formatted} ({timezone_display}). Top 3 times: {', '.join(top_formatted)}"
    
    def _get_day_recommendation(self, by_day: pd.DataFrame) -> str:
        """Get day recommendation based on analysis."""
        best_day = by_day['avg_views'].idxmax()
        weekend_avg = by_day.loc[['Saturday', 'Sunday'], 'avg_views'].mean()
        weekday_avg = by_day.loc[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'avg_views'].mean()
        
        if weekend_avg > weekday_avg:
            return f"Best day: {best_day}. Weekends perform better than weekdays."
        else:
            return f"Best day: {best_day}. Weekdays perform better than weekends."
    
    def _get_frequency_recommendation(self, avg_frequency: float) -> str:
        """Get frequency recommendation."""
        if avg_frequency >= 5:
            return "High upload frequency. Focus on consistency and quality."
        elif avg_frequency >= 3:
            return "Moderate frequency. Good balance for growth."
        elif avg_frequency >= 1:
            return "Lower frequency. Focus on video quality over quantity."
        else:
            return "Consider increasing upload frequency for better growth."
    
    def _get_best_title_patterns(self) -> Dict:
        """Analyze title patterns from top-performing videos."""
        if self.df.empty or 'title' not in self.df.columns:
            return {'error': 'Title data not available'}
        
        # Get top 20% performers
        threshold = self.df['views'].quantile(0.80)
        top_videos = self.df[self.df['views'] >= threshold]
        
        if len(top_videos) < 3:
            # Not enough data, return defaults
            return {
                'best_patterns': ['How to', 'Top', 'Best', 'Review', 'Tutorial'],
                'avg_title_length': 50,
                'use_numbers': True,
                'use_questions': True
            }
        
        # Analyze patterns
        patterns_found = {
            'how_to': 0,
            'top_list': 0,
            'best': 0,
            'review': 0,
            'tutorial': 0,
            'vs': 0,
            'secret': 0,
            'why': 0,
            'numbers': 0,
            'questions': 0
        }
        
        for title in top_videos['title']:
            title_lower = str(title).lower()
            if 'how to' in title_lower or 'how-to' in title_lower:
                patterns_found['how_to'] += 1
            if 'top' in title_lower or 'ranking' in title_lower:
                patterns_found['top_list'] += 1
            if 'best' in title_lower:
                patterns_found['best'] += 1
            if 'review' in title_lower:
                patterns_found['review'] += 1
            if 'tutorial' in title_lower or 'guide' in title_lower:
                patterns_found['tutorial'] += 1
            if ' vs ' in title_lower or 'versus' in title_lower:
                patterns_found['vs'] += 1
            if 'secret' in title_lower:
                patterns_found['secret'] += 1
            if 'why' in title_lower:
                patterns_found['why'] += 1
            if re.search(r'\d+', title_lower):
                patterns_found['numbers'] += 1
            if '?' in title:
                patterns_found['questions'] += 1
        
        # Get most common patterns
        best_patterns = sorted(patterns_found.items(), key=lambda x: x[1], reverse=True)[:5]
        best_patterns = [p[0].replace('_', ' ').title() for p in best_patterns if p[1] > 0]
        
        avg_length = int(top_videos['title'].str.len().mean())
        
        return {
            'best_patterns': best_patterns if best_patterns else ['How to', 'Top', 'Best'],
            'avg_title_length': avg_length,
            'use_numbers': patterns_found['numbers'] > len(top_videos) * 0.3,
            'use_questions': patterns_found['questions'] > len(top_videos) * 0.2,
            'pattern_details': patterns_found
        }
    
    def _generate_title_suggestion(self, content_type: str, patterns: Dict) -> str:
        """Generate a title suggestion based on content type and patterns."""
        best_patterns = patterns.get('best_patterns', [])
        
        title_templates = {
            'Educational': [
                f"How to [Achieve Result] - {best_patterns[0] if best_patterns else 'Step by Step'}",
                f"Why [Audience] [Struggle] - Complete Guide",
                f"[Number] Things [Audience] Should Know About [Topic]"
            ],
            'Tutorial': [
                f"Complete Tutorial: [Topic] from Start to Finish",
                f"Beginner's Guide to [Topic] in [Number] Minutes",
                f"How to Master [Skill] - Full Tutorial"
            ],
            'Entertainment': [
                f"[Challenge/Event] Gone Wrong - [Reaction]",
                f"I Tried [Trend] for [Time] - Here's What Happened",
                f"[Number] [Things/Moments] That [Shock Audience]"
            ],
            'Review': [
                f"Honest Review: [Product/Topic] - Is It Worth It?",
                f"[Product] vs [Competitor] - Which is Better?",
                f"After [Time] Using [Product] - My True Thoughts"
            ],
            'List': [
                f"Top [Number] [Topic] You Need to See",
                f"Best [Topic] of [Year] - Ultimate Ranking",
                f"[Number] [Secrets/Tips] Nobody Tells You About [Topic]"
            ],
            'Q&A': [
                f"Answering Your Questions About [Topic]",
                f"You Asked, I Answered - [Number] Questions",
                f"[Common Question] - My Answer After [Time]"
            ]
        }
        
        # Get templates for content type
        templates = title_templates.get(content_type.split('/')[0], title_templates['Educational'])
        
        # Return first template with placeholders
        return templates[0]
    
    def _suggest_content_type(self, day: str, day_idx: int) -> Dict:
        """Suggest content type based on day with detailed info."""
        content_types = {
            'Monday': {
                'type': 'Educational',
                'description': 'Start the week with value - teach something useful',
                'reason': 'Audiences are in work mode and looking to learn',
                'example': 'How-to videos, tutorials, educational content'
            },
            'Tuesday': {
                'type': 'Tutorial',
                'description': 'Step-by-step guides and how-tos',
                'reason': 'Tutorials perform well early in the week',
                'example': 'Complete guides, step-by-step tutorials'
            },
            'Wednesday': {
                'type': 'List',
                'description': 'Top lists, rankings, or compilations',
                'reason': 'Mid-week engagement peaks with list content',
                'example': 'Top 10, rankings, best of lists'
            },
            'Thursday': {
                'type': 'Reaction',
                'description': 'React to trends, share opinions',
                'reason': 'Builds anticipation for the weekend',
                'example': 'React to news, trending topics, opinions'
            },
            'Friday': {
                'type': 'Behind the Scenes',
                'description': 'Vlogs, BTS, personal content',
                'reason': 'Weekend vibes start, more casual content works',
                'example': 'Day in life, vlogs, behind the scenes'
            },
            'Saturday': {
                'type': 'Entertainment',
                'description': 'Fun content, challenges, lifestyle',
                'reason': 'Highest engagement - people have free time',
                'example': 'Challenges, lifestyle, fun content'
            },
            'Sunday': {
                'type': 'Q&A',
                'description': 'Answer fan questions, community content',
                'reason': 'End of week - connect with your audience',
                'example': 'Q&A, community requests, fan interactions'
            }
        }
        
        return content_types.get(day, {
            'type': 'Regular',
            'description': 'Standard content',
            'reason': 'Consistent uploading builds audience habits',
            'example': 'Regular uploads'
        })
    
    def generate_enhanced_calendar(self, weeks: int = 4, videos_per_week: int = 3) -> List[Dict]:
        """Generate an enhanced content calendar with full recommendations."""
        day_analysis = self.analyze_best_days()
        hour_analysis = self.analyze_best_hours()
        title_patterns = self._get_best_title_patterns()
        
        if 'error' in day_analysis:
            return []
        
        # Get best days
        daily_stats = pd.DataFrame(day_analysis['daily_stats'])
        best_days = daily_stats.nlargest(videos_per_week, 'avg_views').index.tolist()
        
        # Get best hours
        best_hour = hour_analysis.get('best_hour_for_views', 14) if 'error' not in hour_analysis else 14
        
        # Generate calendar
        calendar = []
        start_date = datetime.now().date()
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for week in range(weeks):
            for day_idx, day in enumerate(days_order):
                if day in best_days:
                    # Find the next occurrence of this day
                    current_date = start_date + timedelta(weeks=week)
                    while current_date.strftime('%A') != day:
                        current_date += timedelta(days=1)
                    
                    content_info = self._suggest_content_type(day, day_idx)
                    
                    calendar.append({
                        'week': week + 1,
                        'date': current_date.isoformat(),
                        'date_formatted': current_date.strftime('%B %d, %Y'),
                        'day': day,
                        'time': self._format_hour_ampm(best_hour),
                        'time_24h': best_hour,
                        'timezone': self.timezone,
                        'timezone_display': self.get_timezone_display(),
                        'content_type': content_info['type'],
                        'content_description': content_info['description'],
                        'content_reason': content_info['reason'],
                        'content_example': content_info['example'],
                        'title_suggestion': self._generate_title_suggestion(content_info['type'], title_patterns),
                        'title_patterns': title_patterns.get('best_patterns', [])[:3]
                    })
        
        return calendar
    
    def generate_calendar(self, weeks: int = 4, videos_per_week: int = 3) -> List[Dict]:
        """Generate optimized content calendar for the next N weeks."""
        return self.generate_enhanced_calendar(weeks, videos_per_week)
    
    def get_upload_frequency_analysis(self) -> Dict:
        """Analyze optimal upload frequency."""
        if self.df.empty:
            return {'error': 'No data available'}
        
        # Calculate videos per week
        self.df['week'] = self.df['published_at'].dt.isocalendar().week
        videos_per_week = self.df.groupby('week').size()
        
        # Calculate correlation with views
        views_by_week = self.df.groupby('week')['views'].mean()
        
        # Analyze performance at different frequencies
        if len(videos_per_week) > 1:
            avg_videos_per_week = videos_per_week.mean()
            optimal_frequency = int(round(avg_videos_per_week))
            
            return {
                'current_avg_frequency': round(avg_videos_per_week, 2),
                'recommended_frequency': optimal_frequency,
                'views_correlation': float(views_by_week.corr(videos_per_week)) if len(videos_per_week) > 2 else 0,
                'recommendation': self._get_frequency_recommendation(avg_videos_per_week)
            }
        
        return {'error': 'Not enough data for frequency analysis'}
    
    def analyze_seasonal_patterns(self) -> Dict:
        """Analyze seasonal performance patterns."""
        if self.df.empty:
            return {'error': 'No data available'}
        
        # Group by month
        self.df['month'] = self.df['published_at'].dt.month
        by_month = self.df.groupby('month').agg({
            'views': 'mean',
            'video_id': 'count'
        }).rename(columns={'video_id': 'video_count'})
        
        # Find best months
        best_month = by_month['views'].idxmax()
        
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        return {
            'monthly_stats': by_month.to_dict(),
            'best_month': month_names.get(best_month, 'Unknown'),
            'best_month_num': int(best_month)
        }
    
    def get_complete_recommendations(self) -> Dict:
        """Get complete scheduling recommendations."""
        return {
            'best_days': self.analyze_best_days(),
            'best_hours': self.analyze_best_hours(),
            'title_patterns': self._get_best_title_patterns(),
            'upload_frequency': self.get_upload_frequency_analysis(),
            'seasonal_patterns': self.analyze_seasonal_patterns(),
            'timezone': self.timezone,
            'timezone_display': self.get_timezone_display()
        }


def optimize_calendar(df: pd.DataFrame, timezone: str = 'UTC') -> CalendarOptimizer:
    """Create CalendarOptimizer instance with timezone support."""
    return CalendarOptimizer(df, timezone)


# Test Calendar Optimizer
if __name__ == "__main__":
    # Create sample data
    import random
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hours = list(range(8, 22))
    
    sample_data = pd.DataFrame({
        'video_id': [f'video_{i}' for i in range(1, 51)],
        'title': [
            '5 Tips for Better YouTube Videos',
            'How to Grow Your Channel Fast',
            '10 Secrets Nobody Tells You',
            'Complete Guide to Video Editing',
            'iPhone vs Android - Which is Better',
            'Top 10 List of 2024',
            'Honest Review: New Camera',
            'Why YouTube Algorithm Changed',
            'Beginner Tutorial: Getting Started',
            'Advanced Tips for Pros'
        ] * 5,
        'published_at': pd.date_range('2024-01-01', periods=50, freq='D'),
        'views': [random.randint(1000, 15000) for _ in range(50)],
        'likes': [random.randint(50, 750) for _ in range(50)],
        'comments': [random.randint(10, 150) for _ in range(50)],
        'engagement_rate': [random.uniform(4.0, 10.0) for _ in range(50)],
        'day_of_week': [days[random.randint(0, 6)] for _ in range(50)],
        'hour': [hours[random.randint(0, len(hours)-1)] for _ in range(50)]
    })
    
    optimizer = CalendarOptimizer(sample_data, timezone='US/Eastern')
    
    print("=" * 60)
    print("ENHANCED CALENDAR OPTIMIZER TEST")
    print("=" * 60)
    
    print(f"\n🌍 Timezone: {optimizer.get_timezone_display()}")
    
    print("\n📅 Best Days Analysis:")
    day_analysis = optimizer.analyze_best_days()
    print(f"  Best day for views: {day_analysis.get('best_day_for_views')}")
    print(f"  Recommendation: {day_analysis.get('recommendation')}")
    
    print("\n⏰ Best Hours Analysis:")
    hour_analysis = optimizer.analyze_best_hours()
    print(f"  Timezone: {hour_analysis.get('timezone_display')}")
    print(f"  {hour_analysis.get('recommendation')}")
    
    print("\n📝 Title Patterns:")
    patterns = optimizer._get_best_title_patterns()
    print(f"  Best patterns: {patterns.get('best_patterns')}")
    print(f"  Average title length: {patterns.get('avg_title_length')} characters")
    
    print("\n📅 Generated Enhanced Calendar (1 week, 3 videos):")
    calendar = optimizer.generate_enhanced_calendar(weeks=1, videos_per_week=3)
    for item in calendar:
        print(f"\n  📆 {item['date_formatted']} ({item['day']})")
        print(f"     ⏰ Time: {item['time']} ({item['timezone_display']})")
        print(f"     🎬 Content: {item['content_type']}")
        print(f"     📝 Description: {item['content_description']}")
        print(f"     💡 Example: {item['content_example']}")
        print(f"     ✏️ Title: {item['title_suggestion']}")

