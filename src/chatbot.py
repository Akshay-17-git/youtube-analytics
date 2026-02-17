"""
AI Chatbot with Memory Module.
Natural language interface powered by LangChain for YouTube analytics.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import io

from config.settings import settings
from src.database import get_all_video_metrics, get_video_metrics_by_date_range
from src.metrics import AnalyticsMetrics
from src.forecasting import TrendForecasting
from src.calendar_optimizer import CalendarOptimizer
from src.pattern_detection import PatternDetection


class YouTubeAnalyticsChatbot:
    """AI Chatbot for YouTube Analytics with conversational memory."""
    
    def __init__(self, df: pd.DataFrame = None):
        """Initialize chatbot with video data."""
        self.df = df
        self.conversation_history = []
        self.openai_client = None
        
        # Initialize OpenAI if API key is available
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != 'your_openai_api_key_here':
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                print(f"OpenAI initialization error: {e}")
        
        # Load data from database if not provided
        if self.df is None or self.df.empty:
            try:
                self.df = get_all_video_metrics()
            except:
                self.df = pd.DataFrame()
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_data_summary(self) -> str:
        """Get summary of available data."""
        if self.df is None or self.df.empty:
            return "No data available. Please fetch YouTube data first."
        
        metrics = AnalyticsMetrics(self.df)
        summary = metrics.get_summary_stats()
        
        # Get additional stats
        day_perf = metrics.get_performance_by_day()
        hour_perf = metrics.get_performance_by_hour()
        
        day_str = ""
        if not day_perf.empty:
            best_day = day_perf.loc[day_perf['views'].idxmax()]
            day_str = f"\n📅 Best day to post: {best_day['day_of_week']}"
        
        hour_str = ""
        if not hour_perf.empty:
            best_hour = hour_perf.loc[hour_perf['views'].idxmax()]
            hour_str = f"\n⏰ Best hour to post: {int(best_hour['hour'])}:00"
        
        # Calculate estimated proxy CTR based on views performance
        # Since we don't have real impressions data from YouTube Data API,
        # we estimate based on views relative to channel average
        avg_views = summary.get('avg_views', 0)
        if avg_views > 0:
            # Estimate: videos performing above average have better "CTR"
            # This is a proxy metric since real CTR requires YouTube Analytics API
            high_performers = len(self.df[self.df['views'] > avg_views * 1.5])
            estimated_ctr = (high_performers / len(self.df)) * 10  # Scale to 0-10% range
            ctr_display = f"{estimated_ctr:.1f}% (estimated)"
        else:
            ctr_display = "N/A (requires Analytics API)"
        
        return f"""📊 Channel Summary:

📹 Total Videos: {summary.get('total_videos', 0)}
👀 Total Views: {summary.get('total_views', 0):,}
👍 Total Likes: {summary.get('total_likes', 0):,}
💬 Total Comments: {summary.get('total_comments', 0):,}
🎯 Estimated CTR: {ctr_display}
❤️ Average Engagement Rate: {summary.get('avg_engagement_rate', 0):.2f}%
⭐ Subscribers Gained: {summary.get('total_subscribers', 0):,}
📈 Average Views per Video: {summary.get('avg_views', 0):,.0f}{day_str}{hour_str}

🎯 To grow: Post on your best day at your best hour, and make more videos like your top performers."""
    
    def answer_metric_question(self, question: str) -> str:
        """Answer questions about specific metrics."""
        if self.df is None or self.df.empty:
            return "No data available. Please analyze a channel first."
        
        metrics = AnalyticsMetrics(self.df)
        question_lower = question.lower()
        summary = metrics.get_summary_stats()
        
        # Handle "how many" questions
        if 'how many' in question_lower:
            if 'video' in question_lower:
                return f"Total videos: {summary.get('total_videos', 0)}. To grow: aim for at least 1–2 uploads per week and keep titles clear."
            elif 'view' in question_lower:
                return f"Total views: {summary.get('total_views', 0):,}. To grow: post when your audience is most active and improve thumbnails to boost CTR."
            elif 'like' in question_lower:
                return f"Total likes: {summary.get('total_likes', 0):,}. To grow: ask viewers to like and comment, and reply to comments to boost engagement."
            elif 'comment' in question_lower:
                return f"Total comments: {summary.get('total_comments', 0):,}. To grow: end videos with a question and reply to comments to build community."
        
        # Handle "how much" questions
        if 'how much' in question_lower:
            if 'view' in question_lower:
                return f"Total views: {summary.get('total_views', 0):,}. To grow: post consistently and double down on content types that get the most views."
        
        if 'top' in question_lower and 'video' in question_lower:
            n = 10
            if any(num in question_lower for num in ['5', 'five']):
                n = 5
            elif any(num in question_lower for num in ['3', 'three']):
                n = 3
            
            sort_by = 'views'
            if 'like' in question_lower:
                sort_by = 'likes'
            elif 'comment' in question_lower:
                sort_by = 'comments'
            elif 'engagement' in question_lower:
                sort_by = 'engagement_rate'
            
            top_videos = metrics.get_top_videos(n, sort_by)
            result = f"Top {n} videos by {sort_by}:\n"
            for i, row in top_videos.iterrows():
                result += f"- {row['title'][:50]}: {row[sort_by]:,}\n"
            result += "\nTo grow: make more videos like these—same topics, title style, and length."
            return result
        
        elif 'worst' in question_lower or 'lowest' in question_lower:
            n = 5
            sort_by = 'views'
            worst_videos = metrics.get_worst_videos(n, sort_by)
            result = f"Bottom {n} videos by {sort_by}:\n"
            for i, row in worst_videos.iterrows():
                result += f"- {row['title'][:50]}: {row[sort_by]:,}\n"
            result += "\nTo grow: avoid repeating what these did—try different titles, thumbnails, or posting times."
            return result
        
        elif 'average' in question_lower or 'mean' in question_lower:
            if 'view' in question_lower:
                return f"Average views per video: {summary.get('avg_views', 0):,.0f}"
            elif 'like' in question_lower:
                return f"Average likes per video: {summary.get('avg_likes', 0):,.0f}"
            elif 'comment' in question_lower:
                return f"Average comments per video: {summary.get('avg_comments', 0):,.0f}"
            elif 'engagement' in question_lower:
                return f"Average engagement rate: {summary.get('avg_engagement_rate', 0):.2f}%"
        
        elif 'total' in question_lower:
            if 'view' in question_lower:
                return f"Total views: {summary.get('total_views', 0):,}"
            elif 'video' in question_lower:
                return f"Total videos: {summary.get('total_videos', 0)}"
            elif 'like' in question_lower:
                return f"Total likes: {summary.get('total_likes', 0):,}"
            elif 'comment' in question_lower:
                return f"Total comments: {summary.get('total_comments', 0):,}"
        
        # Default - show full summary
        return self.get_data_summary()
    
    def answer_impressions_ctr_question(self, question: str) -> str:
        """Answer questions about impressions and CTR."""
        if self.df is None or self.df.empty:
            return "No data available."
        
        metrics = AnalyticsMetrics(self.df)
        summary = metrics.get_summary_stats()
        question_lower = question.lower()
        
        if 'impression' in question_lower:
            if 'total' in question_lower:
                return f"Total Impressions: {summary.get('total_impressions', 0):,}"
            elif 'average' in question_lower or 'avg' in question_lower:
                avg_impressions = self.df['impressions'].mean() if 'impressions' in self.df.columns else 0
                return f"Average Impressions per video: {avg_impressions:,.0f}"
        
        if 'ctr' in question_lower or 'click' in question_lower:
            return f"Average CTR (Click-Through Rate): {summary.get('avg_ctr', 0):.2f}%"
        
        if 'subscriber' in question_lower or 'sub' in question_lower:
            if 'total' in question_lower:
                return f"Total Subscribers Gained: {summary.get('total_subscribers', 0):,}"
            elif 'average' in question_lower or 'avg' in question_lower:
                return f"Average Subscribers per video: {summary.get('avg_subscribers', 0):,.0f}"
            else:
                return f"Subscribers Gained: {summary.get('total_subscribers', 0):,}"
        
        return "I can answer questions about impressions, CTR, and subscribers. Try asking about total impressions, average CTR, or subscribers gained."
    
    def answer_forecast_question(self, question: str) -> str:
        """Answer questions about forecasts."""
        if self.df is None or self.df.empty:
            return "No data available for forecasting."
        
        forecast = TrendForecasting(self.df)
        question_lower = question.lower()
        
        if 'view' in question_lower:
            fc = forecast.forecast_views(30)
            return f"30-day view forecast: ~{fc.get('total_forecasted_views', 0):,} views (avg {fc.get('average_daily_views', 0):,} daily). To grow: post on your best days and hours to beat this projection."
        
        elif 'subscriber' in question_lower or 'sub' in question_lower:
            fc = forecast.forecast_subscribers(30)
            return f"30-day subscriber forecast: ~{fc.get('total_forecasted_subscribers', 0):,} new subscribers. To grow: add clear subscribe CTAs and focus on content that gets the most engagement."
        
        elif 'growth' in question_lower or 'trend' in question_lower:
            trajectory = forecast.get_growth_trajectory()
            return f"Growth trend: {trajectory.get('trend', 'Unknown')}. {trajectory.get('recommendation', '')} To grow: follow the recommendation and keep uploads consistent."
        
        return "I can forecast views, subscribers, and growth trends. Ask 'What's my view forecast?' or 'What's my growth trend?'"
    
    def answer_schedule_question(self, question: str) -> str:
        """Answer questions about optimal scheduling."""
        if self.df is None or self.df.empty:
            return "No data available for scheduling analysis."
        
        optimizer = CalendarOptimizer(self.df)
        question_lower = question.lower()
        
        if 'best day' in question_lower or 'what day' in question_lower:
            analysis = optimizer.analyze_best_days()
            return f"Best day to post for views: {analysis.get('best_day_for_views', 'Unknown')}. {analysis.get('recommendation', '')} To grow: schedule your next uploads on this day."
        
        elif 'best hour' in question_lower or 'what time' in question_lower:
            analysis = optimizer.analyze_best_hours()
            return f"Best hour to post: {analysis.get('best_hour_for_views', 'Unknown')}:00. {analysis.get('recommendation', '')} To grow: publish at this time for more initial views."
        
        elif 'calendar' in question_lower or 'schedule' in question_lower:
            calendar = optimizer.generate_calendar(weeks=1, videos_per_week=3)
            result = "Recommended posting schedule for this week:\n"
            for item in calendar:
                result += f"- {item['date']} ({item['day']}) at {item.get('time_24h', 14)}:00 - {item['content_type']}\n"
            result += "\nTo grow: stick to this schedule so your audience knows when to expect new videos."
            return result
        
        return "Ask 'When should I post?' or 'Best day to post?' for actionable scheduling tips."
    
    def answer_pattern_question(self, question: str) -> str:
        """Answer questions about patterns."""
        if self.df is None or self.df.empty:
            return "No data available for pattern analysis."
        
        detector = PatternDetection(self.df)
        question_lower = question.lower()
        
        if 'theme' in question_lower or 'type' in question_lower or 'content' in question_lower:
            themes = detector.detect_content_themes()
            result = "Content themes by performance:\n"
            for theme in themes[:5]:
                result += f"- {theme['theme']}: {theme['avg_views']:,} avg views ({theme['performance']})\n"
            result += "\nTo grow: make more of your best-performing theme and fewer of the weaker ones."
            return result
        
        elif 'title' in question_lower:
            patterns = detector.detect_title_length_patterns()
            result = "Title length analysis:\n"
            for bucket, stats in patterns.items():
                result += f"- {bucket}: {stats['avg_views']:,} avg views\n"
            result += "\nTo grow: use title lengths that get the most views on your channel."
            return result
        
        elif 'duration' in question_lower or 'length' in question_lower:
            patterns = detector.detect_duration_patterns()
            if 'error' in patterns:
                return "Duration data not available. To grow: check Dashboard and Pattern Detection for what length works best."
            result = "Video duration analysis:\n"
            for bucket, stats in patterns.items():
                result += f"- {bucket}: {stats['avg_views']:,} avg views\n"
            result += "\nTo grow: aim for the duration range that gets the most views."
            return result
        
        return "Ask 'What content works best?' or 'Title length analysis?' for growth tips."
    
    def answer_performance_question(self, question: str) -> str:
        """Answer questions about why videos aren't performing well."""
        if self.df is None or self.df.empty:
            return "No data available. Please analyze a channel first."
        
        from src.metrics import AnalyticsMetrics
        from src.pattern_detection import PatternDetection
        
        metrics = AnalyticsMetrics(self.df)
        detector = PatternDetection(self.df)
        
        # Analyze the problem
        analysis = []
        
        # Get worst performing videos
        worst_videos = metrics.get_worst_videos(5)
        if not worst_videos.empty:
            analysis.append("📉 Your lowest performing videos:\n")
            for _, row in worst_videos.head(3).iterrows():
                title = row.get('title', 'Unknown')[:50]
                views = row.get('views', 0)
                engagement = row.get('engagement_rate', 0)
                analysis.append(f"   - '{title}...': {views:,} views, {engagement:.1f}% engagement")
        
        # Get content gaps
        gaps = metrics.get_content_gaps()
        if gaps:
            analysis.append("\n🔍 Content gaps identified:\n")
            for gap in gaps[:3]:
                analysis.append(f"   - {gap.get('description', '')}")
                analysis.append(f"     💡 {gap.get('recommendation', '')}\n")
        
        # Get engagement patterns
        eng_patterns = detector.detect_engagement_patterns()
        if 'error' not in eng_patterns:
            low_eng = eng_patterns.get('low_engagement', {})
            analysis.append(f"\n⚠️ Low engagement videos average:\n")
            analysis.append(f"   - Views: {low_eng.get('avg_views', 0):,}")
            analysis.append(f"   - Likes: {low_eng.get('avg_likes', 0):,}")
            analysis.append(f"   - Comments: {low_eng.get('avg_comments', 0):,}")
        
        # Get performance tiers
        tiers = metrics.get_performance_tiers()
        analysis.append(f"\n📊 Performance breakdown:\n")
        for tier, data in tiers.items():
            analysis.append(f"   - {tier.capitalize()}: {data.get('count', 0)} videos")
        
        # Get upload consistency
        consistency = detector.detect_upload_consistency()
        if 'error' not in consistency:
            analysis.append(f"\n📅 Upload consistency: {consistency.get('consistency', 'Unknown')}")
            analysis.append(f"   💡 {consistency.get('recommendation', '')}")
        
        analysis.append("\n🎯 To grow: Fix the gaps above, post on your best days, and make more content like your top performers.")
        return "\n".join(analysis)
    
    def generate_sql_query(self, question: str) -> str:
        """Generate and potentially execute SQL query from natural language."""
        question_lower = question.lower()
        
        # Simple query generation based on keywords
        if 'view' in question_lower and 'greater' in question_lower:
            # Extract number if present
            import re
            numbers = re.findall(r'\d+', question)
            if numbers:
                threshold = int(numbers[0])
                return f"SELECT * FROM video_metrics WHERE views > {threshold} ORDER BY views DESC"
        
        if 'limit' in question_lower:
            import re
            numbers = re.findall(r'\d+', question)
            if numbers:
                limit = int(numbers[0])
                return f"SELECT video_id, title, views, likes FROM video_metrics ORDER BY views DESC LIMIT {limit}"
        
        return None
    
    def answer_general_question(self, question: str) -> str:
        """Answer general questions about the channel that don't fit other categories."""
        if self.df is None or self.df.empty:
            return "No data available. Please fetch YouTube data first."
        
        metrics = AnalyticsMetrics(self.df)
        detector = PatternDetection(self.df)
        summary = metrics.get_summary_stats()
        
        question_lower = question.lower()
        
        # Questions about channel health/growth
        if any(kw in question_lower for kw in ['healthy', 'health', 'status', 'how am i doing']):
            tier = metrics.get_performance_tiers()
            if tier:
                viral = tier.get('viral', {}).get('count', 0)
                total = summary.get('total_videos', 0)
                pct = (viral / total * 100) if total > 0 else 0
                
                if pct >= 20:
                    health = "🌟 Excellent! Your channel is very healthy!"
                elif pct >= 10:
                    health = "👍 Good! Your channel is doing well."
                elif pct >= 5:
                    health = "📊 Average. Room for improvement."
                else:
                    health = "💪 Keep working! Growth takes time."
                
                return f"""{health}

📊 Channel Health:
- {viral} out of {total} videos are in the top 25% ({pct:.1f}%)
- Total views: {summary.get('total_views', 0):,}
- Average engagement: {summary.get('avg_engagement_rate', 0):.2f}%

💡 Tip: Focus on content similar to your top-performing videos!"""
        
        # Questions about what to do next / recommendations
        if any(kw in question_lower for kw in ['what should', 'should i', 'advice', 'recommend', 'suggestion', 'tip', 'help']):
            best_days = CalendarOptimizer(self.df).analyze_best_days()
            best_hours = CalendarOptimizer(self.df).analyze_best_hours()
            
            tips = [
                "📅 Post on " + best_days.get('best_day_for_views', 'Saturday') + " - that's when your audience is most active!",
                "⏰ Upload around " + str(best_hours.get('best_hour_for_views', 14)) + ":00 for best visibility!",
                "🎬 Look at your top videos and make more content similar to them!",
                "📝 Try adding numbers to your titles - they often get more clicks!",
                "❤️ Engage with commenters - it builds community!",
                "🎨 Stick to 2-3 content types that work well for your channel!"
            ]
            
            import random
            selected_tips = random.sample(tips, 3)
            
            return f"""🎯 Here are my recommendations:

{chr(10).join(f'{i+1}. {tip}' for i, tip in enumerate(selected_tips))}

💡 Remember: Consistency is key! Keep uploading!"""
        
        # Questions about recent performance
        if any(kw in question_lower for kw in ['recent', 'last', 'latest', 'new', 'trend']):
            sorted_df = self.df.sort_values('published_at', ascending=False)
            recent = sorted_df.head(10)
            older = sorted_df.tail(10)
            
            recent_avg = recent['views'].mean() if len(recent) > 0 else 0
            older_avg = older['views'].mean() if len(older) > 0 else 0
            
            if older_avg > 0:
                change = ((recent_avg - older_avg) / older_avg) * 100
                trend = "📈 Up" if change > 0 else "📉 Down"
                
                return f"""📊 Recent Performance (last 10 videos vs earlier 10):

- Recent average views: {recent_avg:,.0f}
- Earlier average views: {older_avg:,.0f}
- Change: {trend} {abs(change):.1f}%

{'To grow: keep doing what works and post on your best days.' if change > 0 else 'To grow: post more consistently and double down on content similar to your top videos.'}"""
            
        # Questions about worst performing videos
        if any(kw in question_lower for kw in ['worst', 'lowest', 'bad', 'poor', 'not working']):
            worst = metrics.get_worst_videos(5)
            if not worst.empty:
                result = "😔 Here are your lowest performing videos:\n\n"
                for _, row in worst.iterrows():
                    result += f"• {row['title'][:50]}... ({row['views']:,} views)\n"
                
                result += """
💡 Possible reasons they underperformed:
- Title might not be catchy enough
- Thumbnail might not stand out
- The topic might not interest your audience
- Posting time might not be optimal

To grow: compare these to your top videos—different title style, thumbnail, or topic? Fix that next time."""
                return result
        
        # Questions comparing metrics
        if any(kw in question_lower for kw in ['compare', 'vs', 'versus', 'difference']):
            # Views vs engagement
            if 'view' in question_lower and ('engagement' in question_lower or 'like' in question_lower):
                sorted_by_views = self.df.nlargest(10, 'views')
                sorted_by_eng = self.df.nlargest(10, 'engagement_rate')
                
                overlap = len(set(sorted_by_views.index) & set(sorted_by_eng.index))
                
                return f"""📊 Views vs Engagement Comparison:

- Top 10 by views: {sorted_by_views['views'].mean():,.0f} avg views
- Top 10 by engagement: {sorted_by_eng['engagement_rate'].mean():.2f}% avg engagement

📋 Overlap: {overlap}/10 videos appear in both top 10 lists

{'To grow: keep making content that gets both views and engagement.' if overlap >= 5 else 'To grow: improve hooks and thumbnails so high-engagement videos get more views.'}"""
        
        # Questions about specific numbers
        if any(kw in question_lower for kw in ['how much', 'how many', 'what is the']):
            # Just return summary with all key metrics
            return self.get_data_summary()
        
        # Default - try to give helpful response
        return f"""Here's a quick snapshot of your channel:

{self.get_data_summary()}

To grow: use the Dashboard, Calendar Optimizer, and A/B Testing pages. Ask me: "When should I post?", "What content works best?", or "Give me recommendations."""
    
    def answer_competitor_question(self, question: str) -> str:
        """Answer questions about competitor analysis (simulated)."""
        if self.df is None or self.df.empty:
            return "No data available."
        
        # Since we don't have competitor data, we'll provide benchmarks based on industry standards
        metrics = AnalyticsMetrics(self.df)
        summary = metrics.get_summary_stats()
        
        # Industry benchmarks (approximate)
        avg_ctr = summary.get('avg_ctr', 0)
        avg_eng = summary.get('avg_engagement_rate', 0)
        
        # CTR benchmarks
        ctr_benchmark = 4.0  # Good CTR is around 4-6%
        eng_benchmark = 4.0  # Good engagement is around 4%
        
        ctr_status = "🟢 Above average" if avg_ctr > ctr_benchmark else "🟡 Average" if avg_ctr > ctr_benchmark * 0.5 else "🔴 Below average"
        eng_status = "🟢 Above average" if avg_eng > eng_benchmark else "🟡 Average" if avg_eng > eng_benchmark * 0.5 else "🔴 Below average"
        
        return f"""📊 Industry Benchmark Comparison:

🎯 Click-Through Rate (CTR):
- Your average: {avg_ctr:.2f}%
- Industry benchmark: ~{ctr_benchmark}%
- Status: {ctr_status}

❤️ Engagement Rate:
- Your average: {avg_eng:.2f}%
- Industry benchmark: ~{eng_benchmark}%
- Status: {eng_status}

To grow:
- CTR: Use thumbnails with bold text and clear faces or emotions; test with A/B Thumbnails.
- Engagement: Ask one clear question per video and reply to comments in the first 24 hours."""
    
    def answer_content_strategy_question(self, question: str) -> str:
        """Answer questions about content strategy."""
        if self.df is None or self.df.empty:
            return "No data available."
        
        detector = PatternDetection(self.df)
        optimizer = CalendarOptimizer(self.df)
        
        question_lower = question.lower()
        
        # Get content themes
        themes = detector.detect_content_themes()
        
        # Get best days and hours
        best_days = optimizer.analyze_best_days()
        best_hours = optimizer.analyze_best_hours()
        
        # Get title patterns
        title_patterns = detector.detect_title_length_patterns()
        
        strategy = """🎯 Content Strategy Recommendations:

📅 POSTING SCHEDULE:"""
        
        if 'best' in question_lower and ('day' in question_lower or 'time' in question_lower):
            strategy += f"""
- Best day: {best_days.get('best_day_for_views', 'Saturday')}
- Best hour: {best_hours.get('best_hour_for_views', 14)}:00
- Post 3-4 times per week for optimal growth"""
        
        if themes and (('type' in question_lower) or ('theme' in question_lower) or ('kind' in question_lower)):
            top_theme = themes[0] if themes else None
            if top_theme:
                strategy += f"""

🎨 BEST CONTENT TYPE:
- {top_theme['theme']}: {top_theme['avg_views']:,} avg views
- This content type performs {top_theme['performance']} for your channel!"""
        
        if title_patterns and 'error' not in title_patterns and ('title' in question_lower or ('name' in question_lower and 'video' in question_lower)):
            best_title_bucket = max(title_patterns.items(), key=lambda x: x[1].get('avg_views', 0))
            strategy += f"""

📝 TITLE STRATEGY:
- Best performing length: {best_title_bucket[0]}
- Use {best_title_bucket[1].get('avg_views', 0):,} average views"""
        
        strategy += """

To grow (action plan):
1. Post on your best day at your best hour every week.
2. Make more of your top content type; cut or improve the weakest.
3. Use titles in your best-performing length; test with A/B Title tool.
4. Thumbnails: bold text, clear face or emotion; test with A/B Thumbnails.
5. End each video with one clear CTA (subscribe / comment / like)."""
        
        return strategy
    
    def answer_audience_question(self, question: str) -> str:
        """Answer questions about audience insights."""
        if self.df is None or self.df.empty:
            return "No data available."
        
        metrics = AnalyticsMetrics(self.df)
        summary = metrics.get_summary_stats()
        
        # Analyze when audience is most active
        hour_perf = metrics.get_performance_by_hour()
        day_perf = metrics.get_performance_by_day()
        
        audience = """👥 Audience Insights:

📊 WHEN YOUR AUDIENCE IS MOST ACTIVE:"""
        
        if not hour_perf.empty:
            best_hour = hour_perf.loc[hour_perf['views'].idxmax()]
            audience += f"""
- Most views around: {int(best_hour['hour'])}:00
- Peak engagement during: afternoon and evening hours"""
        
        if not day_perf.empty:
            best_day = day_perf.loc[day_perf['views'].idxmax()]
            audience += f"""
- Best day: {best_day['day_of_week']}
- Weekends vs weekdays: """
            
            weekend_avg = day_perf[day_perf['day_of_week'].isin(['Saturday', 'Sunday'])]['views'].mean()
            weekday_avg = day_perf[day_perf['day_of_week'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])]['views'].mean()
            
            if weekend_avg > weekday_avg:
                audience += "Weekends perform better!"
            else:
                audience += "Weekdays perform better!"
        
        audience += f"""

📈 AUDIENCE ENGAGEMENT:
- Average engagement rate: {summary.get('avg_engagement_rate', 0):.2f}%
- Average views per video: {summary.get('avg_views', 0):,.0f}

To grow: post when your audience is most active and make more of the content that gets the most engagement."""
        
        return audience
    
    def generate_pdf_report(self) -> bytes:
        """Generate a comprehensive PDF report of all analytics with charts."""
        from fpdf import FPDF
        import matplotlib.pyplot as plt
        import io
        import re
        
        def clean_text(text):
            """Remove emojis and non-Latin characters for PDF compatibility."""
            if not text:
                return ""
            # Convert to string if not already
            text = str(text)
            # Remove emojis and special characters
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                u"\U0001F1E0-\U0001F1FF"  # flags
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                u"\U0001F900-\U0001F9FF"  # supplemental symbols
                u"\U0001FA00-\U0001FA6F"  # chess symbols
                u"\U0001FA70-\U0001FAFF"  # more symbols
                "]+", flags=re.UNICODE)
            text = emoji_pattern.sub(r'', text)
            # Remove any remaining non-ASCII characters
            text = text.encode('ascii', 'replace').decode('ascii')
            return text
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 20)
        
        # Title with gradient effect (simulated with color)
        pdf.set_text_color(41, 128, 185)
        pdf.cell(0, 15, 'YouTube Analytics Report', ln=True, align='C')
        pdf.set_font('Arial', 'I', 12)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f'Generated on {datetime.now().strftime("%B %d, %Y")}', ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_text_color(0, 0, 0)
        
        # Executive Summary
        pdf.set_font('Arial', 'B', 16)
        pdf.set_fill_color(41, 128, 185)
        pdf.cell(0, 12, 'Executive Summary', ln=True, fill=True)
        pdf.set_font('Arial', '', 11)
        pdf.ln(5)
        
        metrics = AnalyticsMetrics(self.df)
        summary = metrics.get_summary_stats()
        
        # Key metrics
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Channel Performance Overview:', ln=True)
        pdf.set_font('Arial', '', 10)
        
        overview_data = [
            ('Total Videos', f"{summary.get('total_videos', 0)}"),
            ('Total Views', f"{summary.get('total_views', 0):,}"),
            ('Total Likes', f"{summary.get('total_likes', 0):,}"),
            ('Total Comments', f"{summary.get('total_comments', 0):,}"),
            ('Average Engagement Rate', f"{summary.get('avg_engagement_rate', 0):.2f}%"),
            ('Average CTR', f"{summary.get('avg_ctr', 0):.2f}%"),
            ('Average Views per Video', f"{summary.get('avg_views', 0):,.0f}"),
        ]
        
        for label, value in overview_data:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(60, 8, label, border=0)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 8, value, ln=True)
        
        pdf.ln(10)
        
        # Top Performing Videos
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 12, 'Top Performing Videos', ln=True, fill=True)
        pdf.set_font('Arial', '', 9)
        pdf.ln(5)
        
        top_videos = metrics.get_top_videos(10)
        if not top_videos.empty:
            # Header row
            pdf.set_font('Arial', 'B', 8)
            pdf.cell(90, 8, 'Title', border=1)
            pdf.cell(30, 8, 'Views', border=1, align='R')
            pdf.cell(25, 8, 'Likes', border=1, align='R')
            pdf.cell(25, 8, 'Comments', border=1, align='R')
            pdf.ln()
            
            # Data rows
            pdf.set_font('Arial', '', 7)
            for _, row in top_videos.head(10).iterrows():
                title = clean_text(row.get('title', 'Unknown'))[:40]
                pdf.cell(90, 7, title, border=1)
                pdf.cell(30, 7, f"{row.get('views', 0):,}", border=1, align='R')
                pdf.cell(25, 7, f"{row.get('likes', 0):,}", border=1, align='R')
                pdf.cell(25, 7, f"{row.get('comments', 0):,}", border=1, align='R')
                pdf.ln()
        
        pdf.ln(10)
        
        # Performance by Day
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 12, 'Performance by Day of Week', ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(5)
        
        day_perf = metrics.get_performance_by_day()
        if not day_perf.empty:
            pdf.cell(60, 8, 'Day', border=1)
            pdf.cell(50, 8, 'Avg Views', border=1, align='R')
            pdf.cell(50, 8, 'Videos', border=1, align='R')
            pdf.ln()
            
            for _, row in day_perf.iterrows():
                pdf.cell(60, 7, str(row.get('day_of_week', '')), border=1)
                pdf.cell(50, 7, f"{row.get('views', 0):,.0f}", border=1, align='R')
                pdf.cell(50, 7, str(int(row.get('video_count', 0))), border=1, align='R')
                pdf.ln()
        
        pdf.ln(10)
        
        # Forecasting
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 12, 'Growth Forecast (30-Day Projection)', ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(5)
        
        forecast = TrendForecasting(self.df)
        view_forecast = forecast.forecast_views(30)
        sub_forecast = forecast.forecast_subscribers(30)
        trajectory = forecast.get_growth_trajectory()
        
        pdf.cell(80, 8, 'Metric', border=0)
        pdf.cell(0, 8, 'Value', ln=True)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 8, '30-Day View Forecast:', border=0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f"~{view_forecast.get('total_forecasted_views', 0):,}", ln=True)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 8, '30-Day Subscriber Forecast:', border=0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f"~{sub_forecast.get('total_forecasted_subscribers', 0):,}", ln=True)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 8, 'Growth Trend:', border=0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, trajectory.get('trend', 'Unknown'), ln=True)
        
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, clean_text(f"Tip: {trajectory.get('recommendation', '')}"), ln=True)
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        
        # Best Posting Times
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 12, 'Optimal Posting Schedule', ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(5)
        
        optimizer = CalendarOptimizer(self.df)
        best_day = optimizer.analyze_best_days()
        best_hour = optimizer.analyze_best_hours()
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 8, 'Best Day to Post:', border=0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, clean_text(best_day.get('best_day_for_views', 'N/A')), ln=True)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 8, 'Best Hour to Post:', border=0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f"{clean_text(str(best_hour.get('best_hour_for_views', 'N/A')))}:00", ln=True)
        
        pdf.ln(10)
        
        # Content Performance Analysis
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 12, 'Content Performance Analysis', ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(5)
        
        detector = PatternDetection(self.df)
        themes = detector.detect_content_themes()
        
        if themes:
            pdf.cell(60, 8, 'Content Type', border=1)
            pdf.cell(40, 8, 'Avg Views', border=1, align='R')
            pdf.cell(40, 8, 'Performance', border=1, align='R')
            pdf.ln()
            
            for theme in themes[:5]:
                theme_name = clean_text(theme.get('theme', 'Unknown'))[:25]
                pdf.cell(60, 7, theme_name, border=1)
                pdf.cell(40, 7, f"{theme.get('avg_views', 0):,}", border=1, align='R')
                pdf.cell(40, 7, clean_text(theme.get('performance', 'N/A')), border=1, align='R')
                pdf.ln()
        
        pdf.ln(10)
        
        # Your Action Plan (growth-focused)
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 12, 'Your Action Plan to Grow', ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.ln(5)
        
        best_day_str = clean_text(str(best_day.get('best_day_for_views', 'weekdays')))
        best_hr = clean_text(str(best_hour.get('best_hour_for_views', 14)))
        top_theme = clean_text(themes[0]['theme'] if themes else 'educational')
        
        action_plan = [
            f"1. Post on {best_day_str} at {best_hr}:00 - your data shows best performance then.",
            f"2. Make more {top_theme} content; it performs best on your channel.",
            f"3. Aim for 3-4 uploads per week and stick to the same days/times.",
            f"4. Use thumbnails with bold text and clear faces; test with A/B Thumbnails.",
            f"5. End each video with one clear CTA: subscribe, like, or comment.",
        ]
        
        for rec in action_plan:
            pdf.cell(0, 8, rec, ln=True)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 8, 'Use the dashboard Calendar Optimizer and A/B Testing pages to refine further.', ln=True)
        pdf.set_text_color(0, 0, 0)
        
        # Footer
        pdf.ln(20)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, 'Report generated by YouTube Analytics Dashboard', ln=True, align='C')
        pdf.cell(0, 5, 'For educational purposes only. Actual results may vary.', ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1')
    
    def process_message(self, message: str) -> Dict:
        """Process user message and generate LLM-style response."""
        self.add_message('user', message)
        
        response = ""
        query_used = None
        
        # Always use LLM-style response (OpenAI if available, otherwise simulated)
        if self.openai_client and len(self.df) > 0:
            # Use OpenAI for true LLM response
            try:
                response = self._generate_openai_response(message)
            except Exception as e:
                # Fall back to simulated LLM response
                response = self._generate_simulated_llm_response(message)
        else:
            # No OpenAI available - use simulated LLM response
            if self.df is not None and not self.df.empty:
                response = self._generate_simulated_llm_response(message)
            else:
                response = """I need your channel data to provide insights! 

Please fetch your YouTube data first using the sidebar, then ask me anything about your analytics. I can help with:

• "How is my channel performing?" — overall health check
• "What are my best videos?" — top content analysis  
• "When should I post?" — optimal scheduling
• "Why are my views low?" — performance diagnostics
• "How can I grow faster?" — personalized recommendations

I'll analyze your data and give you specific, actionable advice!"""
        
        # Handle special cases that need additional processing
        message_lower = message.lower()
        
        # Check if asking for PDF report
        if any(kw in message_lower for kw in ['pdf', 'report', 'download', 'export', 'create report', 'generate report']):
            if self.df is not None and not self.df.empty:
                try:
                    pdf_data = self.generate_pdf_report()
                    response += "\n\n📄 I've also generated a comprehensive PDF report for you. Click the download button below to save it!"
                    self.last_pdf_report = pdf_data
                except Exception as e:
                    response += f"\n\n(Note: PDF generation failed: {str(e)})"
                    self.last_pdf_report = None
            else:
                response = "No data available to generate report. Please fetch YouTube data first."
                self.last_pdf_report = None
        
        # Check if asking to generate SQL
        elif 'sql' in message_lower or 'query' in message_lower:
            query = self.generate_sql_query(message)
            if query:
                response += f"\n\n💻 Here's the SQL query for your question:\n```sql\n{query}\n```"
                query_used = query
        
        # Add response to history
        self.add_message('assistant', response)
        
        return {
            'response': response,
            'query_used': query_used,
            'conversation_length': len(self.conversation_history),
            'pdf_report': getattr(self, 'last_pdf_report', None)
        }
    
    def _generate_openai_response(self, message: str) -> str:
        """Generate response using OpenAI API."""
        metrics = AnalyticsMetrics(self.df)
        summary = metrics.get_summary_stats()
        
        # Get comprehensive data for context
        top_videos = metrics.get_top_videos(5)
        worst_videos = metrics.get_worst_videos(5)
        day_perf = metrics.get_performance_by_day()
        hour_perf = metrics.get_performance_by_hour()
        
        # Build rich context
        # Calculate estimated proxy CTR
        avg_views = summary.get('avg_views', 0)
        if avg_views > 0:
            high_performers = len(self.df[self.df['views'] > avg_views * 1.5])
            estimated_ctr = (high_performers / len(self.df)) * 10
            ctr_display = f"{estimated_ctr:.1f}%"
        else:
            ctr_display = "N/A"
        
        context = f"""You are an expert YouTube Analytics Consultant and Growth Strategist. Analyze this channel data and answer the user's question in a natural, conversational way like a helpful AI assistant.

CHANNEL DATA:
• Videos: {summary.get('total_videos', 0)} | Views: {summary.get('total_views', 0):,} | Likes: {summary.get('total_likes', 0):,}
• Comments: {summary.get('total_comments', 0):,} | Subscribers: {summary.get('total_subscribers', 0):,}
• Estimated CTR: {ctr_display} | Engagement: {summary.get('avg_engagement_rate', 0):.2f}%
• Avg Views/Video: {summary.get('avg_views', 0):,.0f}

TOP 5 VIDEOS:"""
        
        for i, (_, row) in enumerate(top_videos.head(5).iterrows(), 1):
            context += f"\n{i}. {row.get('title', 'Unknown')[:50]}... ({row.get('views', 0):,} views)"
        
        context += "\n\nBOTTOM 5 VIDEOS:"
        for i, (_, row) in enumerate(worst_videos.head(5).iterrows(), 1):
            context += f"\n{i}. {row.get('title', 'Unknown')[:50]}... ({row.get('views', 0):,} views)"
        
        if not day_perf.empty:
            context += "\n\nBEST DAYS:"
            best_days = day_perf.nlargest(3, 'views')
            for _, row in best_days.iterrows():
                context += f"\n• {row.get('day_of_week', '')}: {row.get('views', 0):,.0f} avg views"
        
        if not hour_perf.empty:
            context += "\n\nBEST HOURS:"
            best_hours = hour_perf.nlargest(3, 'views')
            for _, row in best_hours.iterrows():
                context += f"\n• {int(row.get('hour', 0))}:00: {row.get('views', 0):,.0f} avg views"
        
        context += f"""

USER QUESTION: {message}

Provide a helpful, conversational response that:
1. Directly answers their specific question
2. References actual numbers from their data
3. Explains what the metrics mean in simple terms
4. Gives 1-2 specific, actionable recommendations
5. Uses a friendly, encouraging tone

Your response:"""
        
        completion = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a knowledgeable YouTube growth expert who explains analytics clearly and gives practical advice."},
                {"role": "user", "content": context}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        return completion.choices[0].message.content
    
    def _generate_simulated_llm_response(self, message: str) -> str:
        """Generate LLM-style response using rule-based logic with natural language."""
        if self.df is None or self.df.empty:
            return "I don't have any data to analyze yet. Please load your YouTube channel data first!"
        
        metrics = AnalyticsMetrics(self.df)
        summary = metrics.get_summary_stats()
        message_lower = message.lower()
        
        # Determine question type and generate appropriate LLM-style response
        if any(kw in message_lower for kw in ['summary', 'overview', 'how am i doing', 'channel health', 'performance']):
            return self._generate_overview_response(summary, metrics)
        
        elif any(kw in message_lower for kw in ['top', 'best', 'highest', 'most views']):
            return self._generate_top_videos_response(metrics)
        
        elif any(kw in message_lower for kw in ['worst', 'lowest', 'bad', 'underperforming']):
            return self._generate_worst_videos_response(metrics)
        
        # IMPORTANT: Check for "what to post" / content strategy BEFORE scheduling
        # "what to post", "what should i make", "content ideas" = content strategy
        elif any(kw in message_lower for kw in ['what to post', 'what should i make', 'what to make', 'content ideas', 'video ideas', 'topic', 'theme', 'content strategy', 'what content']):
            return self._generate_content_ideas_response(metrics)
        
        # "when to post", "best time", "schedule" = scheduling
        elif any(kw in message_lower for kw in ['when', 'schedule', 'best time', 'best day', 'what day', 'what time', 'upload time', 'posting time']):
            # Make sure it's not a "what to post" question
            if 'what' not in message_lower or 'post' not in message_lower:
                return self._generate_scheduling_response(metrics)
            # If it contains both "what" and "post", check if it's about content
            elif 'to post' in message_lower and 'what' in message_lower:
                # This is "what to post" - already handled above, but just in case
                return self._generate_content_ideas_response(metrics)
            else:
                return self._generate_scheduling_response(metrics)
        
        elif any(kw in message_lower for kw in ['why', 'not performing', 'low views', 'struggling', 'problem']):
            return self._generate_diagnostic_response(metrics)
        
        elif any(kw in message_lower for kw in ['grow', 'improve', 'recommendation', 'advice', 'tips', 'strategy']):
            return self._generate_growth_strategy_response(summary, metrics)
        
        elif any(kw in message_lower for kw in ['forecast', 'predict', 'future', 'trend', 'projection']):
            return self._generate_forecast_response()
        
        elif any(kw in message_lower for kw in ['engagement', 'likes', 'comments', 'interaction']):
            return self._generate_engagement_response(summary, metrics)
        
        elif any(kw in message_lower for kw in ['ctr', 'click', 'thumbnail', 'impression', 'views per impression']):
            return self._generate_ctr_response(summary)
        
        else:
            # General question - provide comprehensive overview
            return self._generate_general_response(message, summary, metrics)
    
    def _generate_overview_response(self, summary: Dict, metrics: AnalyticsMetrics) -> str:
        """Generate LLM-style channel overview."""
        total_videos = summary.get('total_videos', 0)
        total_views = summary.get('total_views', 0)
        avg_views = summary.get('avg_views', 0)
        engagement = summary.get('avg_engagement_rate', 0)
        
        # Determine channel health
        if avg_views > 10000:
            health = "strong"
            health_emoji = "🌟"
        elif avg_views > 5000:
            health = "solid"
            health_emoji = "📈"
        elif avg_views > 1000:
            health = "growing"
            health_emoji = "🌱"
        else:
            health = "early stage"
            health_emoji = "🌱"
        
        response = f"""{health_emoji} Your channel is looking {health}! Here's what I'm seeing:

**The Numbers:**
• You've published **{total_videos} videos** that have generated **{total_views:,} total views**
• That's an average of **{avg_views:,.0f} views per video** — """
        
        if avg_views > 5000:
            response += "that's well above typical for most channels!\n"
        elif avg_views > 1000:
            response += "a solid foundation to build on.\n"
        else:
            response += "room to grow as you find your audience.\n"
        
        response += f"""• Your engagement rate is **{engagement:.2f}%** — """
        
        if engagement > 5:
            response += "your audience is really connecting with your content! 🔥\n"
        elif engagement > 3:
            response += "decent engagement, there's potential to boost this further.\n"
        else:
            response += "you might want to focus on creating more interactive content.\n"
        
        response += f"""• Your Proxy CTR is **{summary.get('avg_ctr', 0):.2f}%** — this shows how many people who saw your thumbnail actually watched

**My Take:** """
        
        if total_videos < 20:
            response += "You're still in the early stages. Consistency is key right now — keep publishing regularly to build momentum!"
        elif avg_views < 2000:
            response += "Your content has potential, but your titles and thumbnails might need work. Try testing different styles and see what gets more clicks!"
        else:
            response += "You're on a good trajectory! Double down on what's working and consider posting more frequently."
        
        response += "\n\n**Quick Win:** Look at your top 3 videos — what do they have in common? Try creating more content in that style!"
        
        return response
    
    def _generate_top_videos_response(self, metrics: AnalyticsMetrics) -> str:
        """Generate LLM-style top videos analysis."""
        top_videos = metrics.get_top_videos(5)
        
        if top_videos.empty:
            return "I don't see any video data yet. Make sure your channel data is loaded!"
        
        response = "🏆 **Your Top Performers** — these are your golden videos!\n\n"
        
        total_top_views = top_videos['views'].sum()
        
        for i, (_, row) in enumerate(top_videos.iterrows(), 1):
            title = row.get('title', 'Unknown')[:45]
            views = row.get('views', 0)
            likes = row.get('likes', 0)
            engagement = row.get('engagement_rate', 0)
            
            response += f"{i}. **{title}**...\n"
            response += f"   📺 {views:,} views | 👍 {likes:,} likes | ❤️ {engagement:.1f}% engagement\n\n"
        
        response += f"These top 5 videos account for a significant portion of your total views. "
        response += "**What makes them work?** Look for patterns in:\n"
        response += "• Topics — what subject matter got the most interest?\n"
        response += "• Titles — do they use numbers, questions, or curiosity gaps?\n"
        response += "• Thumbnails — what visual style performed best?\n\n"
        response += "💡 **Action:** Create 2-3 more videos similar to your #1 performer. "
        response += "Don't copy it exactly, but capture what made it successful!"
        
        return response
    
    def _generate_worst_videos_response(self, metrics: AnalyticsMetrics) -> str:
        """Generate LLM-style underperforming videos analysis."""
        worst_videos = metrics.get_worst_videos(5)
        
        if worst_videos.empty:
            return "I need more video data to identify underperformers. Keep uploading!"
        
        response = "📉 **Let's Look at What Didn't Work** — this is just as valuable!\n\n"
        
        for i, (_, row) in enumerate(worst_videos.iterrows(), 1):
            title = row.get('title', 'Unknown')[:45]
            views = row.get('views', 0)
            
            response += f"{i}. **{title}**... ({views:,} views)\n"
        
        response += "\n**Why These Underperformed:**\n\n"
        response += "• **Timing:** Were these posted at odd hours or on low-traffic days?\n"
        response += "• **Titles:** Do they lack curiosity or clear value proposition?\n"
        response += "• **Thumbnails:** Would YOU click on these if you saw them in search?\n"
        response += "• **Topics:** Was the subject too niche or not aligned with your audience?\n\n"
        
        response += "🔍 **Learning Opportunity:** Compare these to your top videos. "
        response += "What's different? The gap between them shows you exactly what to improve!\n\n"
        response += "Don't delete these — they're valuable data points that teach you what your audience prefers."
        
        return response
    
    def _generate_scheduling_response(self, metrics: AnalyticsMetrics) -> str:
        """Generate LLM-style scheduling recommendations."""
        optimizer = CalendarOptimizer(self.df)
        
        best_day_analysis = optimizer.analyze_best_days()
        best_hour_analysis = optimizer.analyze_best_hours()
        
        best_day = best_day_analysis.get('best_day_for_views', 'Unknown')
        best_hour = best_hour_analysis.get('best_hour_for_views', 14)
        
        day_perf = metrics.get_performance_by_day()
        hour_perf = metrics.get_performance_by_hour()
        
        response = f"⏰ **Optimal Posting Strategy** — timing matters!\n\n"
        
        response += f"**Your Best Day:** {best_day}\n"
        if not day_perf.empty:
            best_day_data = day_perf[day_perf['day_of_week'] == best_day]
            if not best_day_data.empty:
                avg_views = best_day_data['views'].values[0]
                response += f"• Videos posted on {best_day} average **{avg_views:,.0f} views**\n"
        
        response += f"\n**Your Best Hour:** {best_hour}:00\n"
        if not hour_perf.empty:
            best_hour_data = hour_perf[hour_perf['hour'] == best_hour]
            if not best_hour_data.empty:
                avg_views = best_hour_data['views'].values[0]
                response += f"• Videos posted at {best_hour}:00 average **{avg_views:,.0f} views**\n"
        
        response += f"\n**The Science Behind This:**\n\n"
        response += f"Posting on {best_day} at {best_hour}:00 puts your content in front of viewers "
        response += f"when they're most active and likely to engage. This gives you a stronger "
        response += f"initial boost, which signals YouTube's algorithm to recommend your video more.\n\n"
        
        response += f"📅 **Your Action Plan:**\n"
        response += f"1. Schedule your next 3 videos for {best_day}s around {best_hour}:00\n"
        response += f"2. Be consistent — same day, same time builds audience expectations\n"
        response += f"3. Upload 30 minutes early so you're live at peak time\n\n"
        
        response += f"Consistency + Optimal Timing = Algorithm Love ❤️"
        
        return response
    
    def _generate_diagnostic_response(self, metrics: AnalyticsMetrics) -> str:
        """Generate LLM-style performance diagnosis."""
        worst_videos = metrics.get_worst_videos(3)
        summary_stats = metrics.get_summary_stats()
        
        response = "🔍 **Performance Diagnosis** — let's figure out what's happening\n\n"
        
        # Analyze patterns
        response += "**Common Issues I See:**\n\n"
        
        avg_views = summary_stats.get('avg_views', 0)
        if avg_views < 1000:
            response += "• **Low Average Views** — Your videos are struggling to get initial traction. "
            response += "This usually means your titles/thumbnails aren't compelling enough in search results.\n\n"
        
        response += "• **The First 24 Hours** — YouTube's algorithm heavily weights early performance. "
        response += "If a video doesn't get clicks and engagement quickly, it gets buried.\n\n"
        
        response += "**Specific Issues with Your Lowest Performers:**\n\n"
        
        for i, (_, row) in enumerate(worst_videos.iterrows(), 1):
            title = row.get('title', 'Unknown')
            views = row.get('views', 0)
            
            issues = []
            if len(title) < 20:
                issues.append("title too short")
            if len(title) > 80:
                issues.append("title too long")
            if views < 500:
                issues.append("very low initial reach")
            
            if issues:
                response += f"• '{title[:40]}...' — {', '.join(issues)}\n"
        
        response += f"\n**Your Recovery Plan:**\n\n"
        response += f"1. **Audit Your Thumbnails** — Are they readable at small sizes? Do they evoke emotion?\n"
        response += f"2. **Rewrite Titles** — Use the 'Curiosity Gap' technique: promise value but leave a question\n"
        response += f"3. **Check Your Hooks** — First 30 seconds must grab attention. No long intros!\n"
        response += f"4. **Post at Optimal Times** — Use the Calendar Optimizer to find your best slots\n\n"
        
        response += f"Remember: Every creator has videos that underperform. The key is learning from them!"
        
        return response
    
    def _generate_growth_strategy_response(self, summary: Dict, metrics: AnalyticsMetrics) -> str:
        """Generate LLM-style growth strategy."""
        total_videos = summary.get('total_videos', 0)
        avg_views = summary.get('avg_views', 0)
        
        response = "🚀 **Your Personalized Growth Strategy**\n\n"
        
        response += f"Based on your {total_videos} videos averaging {avg_views:,.0f} views, here's your roadmap:\n\n"
        
        response += "**Phase 1: Quick Wins (Next 2 Weeks)**\n"
        response += "• Post 2-3 videos on your best-performing day (check Calendar Optimizer)\n"
        response += "• Use titles similar to your top 3 videos — they've proven to work!\n"
        response += "• Add a clear call-to-action in every video: 'Subscribe for more [topic] content'\n\n"
        
        response += "**Phase 2: Content Optimization (Month 1-2)**\n"
        response += "• Analyze your top 5 videos — what topics, lengths, and styles do they share?\n"
        response += "• Create a content series around your best-performing topic\n"
        response += "• Test 2-3 different thumbnail styles and track which gets better CTR\n\n"
        
        response += "**Phase 3: Scale (Month 3+)**\n"
        response += "• Increase upload frequency to 2-3x per week if possible\n"
        response += "• Start collaborating with similar-sized creators\n"
        response += "• Use Community Tab to keep audience engaged between uploads\n\n"
        
        response += "**Key Metrics to Watch:**\n"
        response += f"• **Proxy CTR:** Currently {summary.get('avg_ctr', 0):.2f}% — aim for 4%+\n"
        response += f"• **Engagement Rate:** Currently {summary.get('avg_engagement_rate', 0):.2f}% — higher = more recommendations\n"
        response += f"• **Avg Views:** Track this weekly — your goal is consistent growth\n\n"
        
        response += "You've got this! 🎯"
        
        return response
    
    def _generate_forecast_response(self) -> str:
        """Generate LLM-style forecast response."""
        forecast = TrendForecasting(self.df)
        
        view_forecast = forecast.forecast_views(30)
        sub_forecast = forecast.forecast_subscribers(30)
        trajectory = forecast.get_growth_trajectory()
        
        trend = trajectory.get('trend', 'Unknown')
        recommendation = trajectory.get('recommendation', '')
        
        response = f"🔮 **30-Day Growth Forecast**\n\n"
        
        response += f"**Projected Numbers:**\n"
        response += f"• Views: ~{view_forecast.get('total_forecasted_views', 0):,} (avg {view_forecast.get('average_daily_views', 0):,}/day)\n"
        response += f"• New Subscribers: ~{sub_forecast.get('total_forecasted_subscribers', 0):,}\n\n"
        
        response += f"**Trend Analysis:** {trend}\n"
        
        if 'accelerating' in trend.lower():
            response += f"Great news! Your channel is gaining momentum. Keep doing exactly what you're doing!\n\n"
        elif 'stable' in trend.lower():
            response += f"You're maintaining steady growth. To break through, try experimenting with new content formats.\n\n"
        elif 'declining' in trend.lower():
            response += f"Your growth has slowed. Time to refresh your strategy — try new topics or posting times.\n\n"
        else:
            response += f"Your trajectory is {trend.lower()}. {recommendation}\n\n"
        
        response += f"**How to Beat the Forecast:**\n"
        response += f"• Post on your optimal days/times (see Calendar Optimizer)\n"
        response += f"• Create content similar to your top 20% of videos\n"
        response += f"• Improve your thumbnails to boost that Proxy CTR\n"
        response += f"• Engage with every comment in the first 2 hours\n\n"
        
        response += f"Forecasts are based on your historical data — but YOU can outperform them! 💪"
        
        return response
    
    def _generate_engagement_response(self, summary: Dict, metrics: AnalyticsMetrics) -> str:
        """Generate LLM-style engagement analysis."""
        engagement_rate = summary.get('avg_engagement_rate', 0)
        total_likes = summary.get('total_likes', 0)
        total_comments = summary.get('total_comments', 0)
        total_views = summary.get('total_views', 0)
        
        response = f"❤️ **Engagement Analysis** — How Connected Is Your Audience?\n\n"
        
        response += f"**Your Engagement Metrics:**\n"
        response += f"• Overall Engagement Rate: **{engagement_rate:.2f}%**\n"
        response += f"• Total Likes: **{total_likes:,}** ({total_likes/total_views*100:.1f}% of viewers)\n"
        response += f"• Total Comments: **{total_comments:,}** ({total_comments/total_views*100:.2f}% of viewers)\n\n"
        
        response += f"**What This Means:**\n\n"
        
        if engagement_rate > 5:
            response += f"Your engagement rate is **excellent**! Your audience is highly invested in your content. "
            response += f"This tells YouTube's algorithm that people love your videos, which leads to more recommendations.\n\n"
        elif engagement_rate > 3:
            response += f"Your engagement is **solid** — better than many channels! There's still room to grow though. "
            response += f"Focus on creating more interactive moments in your videos.\n\n"
        else:
            response += f"Your engagement could use a boost. Don't worry — this is fixable! "
            response += f"The key is giving viewers clear reasons to interact.\n\n"
        
        response += f"**Boost Your Engagement:**\n"
        response += f"• Ask ONE specific question in each video (not 'let me know what you think' — be specific!)\n"
        response += f"• Reply to comments within the first 2 hours — this builds community\n"
        response += f"• Use polls in Community Tab between uploads\n"
        response += f"• Create 'response videos' to popular comments\n"
        response += f"• End with a teaser for your next video\n\n"
        
        response += f"Remember: Engagement > Views. A smaller, engaged audience beats a large, passive one! 🎯"
        
        return response
    
    def _generate_ctr_response(self, summary: Dict) -> str:
        """Generate LLM-style CTR analysis."""
        ctr = summary.get('avg_ctr', 0)
        
        response = f"🎯 **Thumbnail & Click-Through Analysis**\n\n"
        
        # Calculate estimated proxy CTR
        avg_views = summary.get('avg_views', 0)
        if avg_views > 0:
            high_performers = len(self.df[self.df['views'] > avg_views * 1.5])
            estimated_ctr = (high_performers / len(self.df)) * 10
            ctr = estimated_ctr
            ctr_source = "estimated based on your video performance distribution"
        else:
            ctr = 0
            ctr_source = "unable to calculate - insufficient data"
        
        response += f"**Your Estimated CTR: {ctr:.1f}%** ({ctr_source})\n\n"
        
        if ctr > 0:
            response += f"This estimate is based on how many of your videos significantly outperform your average. "
            response += f"A higher percentage suggests your thumbnails and titles are effectively attracting clicks.\n\n"
            
            if ctr > 6:
                response += f"That's **outstanding**! Many of your videos are beating expectations. 🔥\n\n"
            elif ctr > 4:
                response += f"That's **solid** — you're on the right track with your thumbnails!\n\n"
            elif ctr > 2:
                response += f"There's **room for improvement**. Try testing different thumbnail styles.\n\n"
            else:
                response += f"Your thumbnails likely need work. Focus on making them more eye-catching!\n\n"
        else:
            response += f"Unable to calculate CTR estimate. Make sure you have video data loaded.\n\n"
        
        response += f"**Why CTR Matters:**\n"
        response += f"CTR (Click-Through Rate) shows how often people click after seeing your thumbnail. "
        response += f"Higher CTR = more views and better YouTube recommendations!\n\n"
        response += f"**Note:** True CTR requires YouTube Analytics API access. This is an estimate based on your performance data.\n\n"
        
        response += f"**Thumbnail Best Practices:**\n"
        response += f"• Use **bold, readable text** (3-4 words max)\n"
        response += f"• Include a **human face with emotion** — curiosity, surprise, or excitement\n"
        response += f"• **High contrast colors** that pop in the sidebar\n"
        response += f"• **Avoid** cluttered backgrounds — keep it simple\n"
        response += f"• Test different styles with the A/B Thumbnail tool\n\n"
        
        response += f"**Quick Win:** Look at your highest-viewed video. What does its thumbnail do right? "
        response += f"Apply those elements to your next 3 uploads!"
        
        return response
    
    def _generate_content_ideas_response(self, metrics: AnalyticsMetrics) -> str:
        """Generate smart content ideas based on what's working."""
        top_videos = metrics.get_top_videos(10)
        detector = PatternDetection(self.df)
        
        # Get content themes
        try:
            themes = detector.detect_content_themes()
        except:
            themes = []
        
        response = "🎬 **What You Should Post Next** — Based on Your Data\n\n"
        
        # Analyze top performers for patterns
        if not top_videos.empty:
            top_3 = top_videos.head(3)
            
            response += "**Your Winning Formula:**\n\n"
            response += "Looking at your top performers, I see these patterns:\n\n"
            
            for i, (_, row) in enumerate(top_3.iterrows(), 1):
                title = row.get('title', 'Unknown')
                views = row.get('views', 0)
                response += f"{i}. **'{title[:50]}'** ({views:,} views)\n"
            
            response += "\n**Common Success Elements:**\n"
            
            # Analyze titles for patterns
            titles = [row.get('title', '') for _, row in top_3.iterrows()]
            
            # Check for numbers in titles
            has_numbers = any(any(c.isdigit() for c in title) for title in titles)
            if has_numbers:
                response += "• Your top videos use **numbers in titles** (e.g., '5 Tips', '3 Ways') — this creates specific expectations\n"
            
            # Check for how-to/tutorial style
            how_to_count = sum(1 for t in titles if any(kw in t.lower() for kw in ['how', 'tutorial', 'guide', 'learn', 'beginner']))
            if how_to_count >= 2:
                response += "• **Educational content** performs well for you — tutorials and how-to guides\n"
            
            # Check for question style
            question_count = sum(1 for t in titles if '?' in t)
            if question_count >= 1:
                response += "• **Question-based titles** spark curiosity and get clicks\n"
            
            response += "• These topics clearly **resonate with your audience** — they found them valuable enough to watch\n\n"
        
        # Suggest specific content ideas
        response += "**🎯 Recommended Next Videos:**\n\n"
        
        if themes and len(themes) > 0:
            top_theme = themes[0]
            theme_name = top_theme['theme']
            
            response += f"1. **Double Down on '{theme_name}'**\n"
            response += f"   Your {theme_name} content averages {top_theme['avg_views']:,} views. "
            response += f"Create a sequel or related topic to your best {theme_name} video.\n\n"
            
            if len(themes) > 1:
                second_theme = themes[1]
                response += f"2. **Expand Your '{second_theme['theme']}' Series**\n"
                response += f"   This is your second-best performing theme. A 3-part series here could build momentum.\n\n"
        
        # Generic but data-informed suggestions
        response += f"3. **'The [Number] [Topic] Mistakes Beginners Make'**\n"
        response += f"   This format combines education with curiosity. Use your top theme as the topic.\n\n"
        
        response += f"4. **'I Tried [Popular Video Topic] for 30 Days'**\n"
        response += f"   Challenge-style content based on your proven topic. Document the journey!\n\n"
        
        response += "**💡 Pro Tips for Your Next Upload:**\n"
        response += f"• Use the title patterns from your top 3 videos\n"
        response += f"• Post on your best day (check Calendar Optimizer)\n"
        response += f"• Make the thumbnail show a clear transformation or result\n"
        response += f"• Hook viewers in the first 15 seconds with the outcome\n\n"
        
        response += "Your data shows you know what works — now scale it! 🚀"
        
        return response

    def _generate_general_response(self, message: str, summary: Dict, metrics: AnalyticsMetrics) -> str:
        """Generate general LLM-style response for any question."""
        total_videos = summary.get('total_videos', 0)
        total_views = summary.get('total_views', 0)
        avg_views = summary.get('avg_views', 0)
        
        response = f"Great question! Let me analyze your channel data to help.\n\n"
        
        response += f"**Your Channel at a Glance:**\n"
        response += f"• You've created **{total_videos} videos** with **{total_views:,} total views**\n"
        response += f"• Average of **{avg_views:,.0f} views per video**\n"
        response += f"• Proxy CTR: **{summary.get('avg_ctr', 0):.2f}%** | Engagement: **{summary.get('avg_engagement_rate', 0):.2f}%**\n\n"
        
        # Add specific insight based on their data
        top_videos = metrics.get_top_videos(3)
        if not top_videos.empty:
            response += f"**Your Top Video:** '{top_videos.iloc[0].get('title', 'Unknown')[:40]}...' "
            response += f"with **{top_videos.iloc[0].get('views', 0):,} views** — this is your blueprint for success!\n\n"
        
        response += f"**What I Recommend:**\n"
        response += f"• Study your highest-performing video and identify what made it work\n"
        response += f"• Post consistently on days when your audience is most active\n"
        response += f"• Focus on improving your Proxy CTR through better thumbnails\n\n"
        
        response += f"Want specific advice? Ask me about:\n"
        response += f"• 'What should I post?' — content ideas based on your top videos\n"
        response += f"• 'When should I post?' — optimal scheduling\n"
        response += f"• 'How do I grow faster?' — growth strategy\n"
        response += f"• 'Why are my views low?' — performance diagnosis"
        
        return response
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []


def create_chatbot(df: pd.DataFrame = None) -> YouTubeAnalyticsChatbot:
    """Create a chatbot instance."""
    return YouTubeAnalyticsChatbot(df)


# Test chatbot
if __name__ == "__main__":
    # Create sample data
    sample_data = pd.DataFrame({
        'video_id': [f'video_{i}' for i in range(1, 21)],
        'title': [f'Video {i}' for i in range(1, 21)],
        'published_at': pd.date_range('2024-01-01', periods=20, freq='D'),
        'views': [1000, 5000, 2000, 8000, 15000, 3000, 7000, 4000, 6000, 2500,
                 9000, 11000, 5500, 7500, 12000, 3500, 6500, 4500, 8500, 5000],
        'likes': [50, 250, 100, 400, 750, 150, 350, 200, 300, 125,
                 450, 550, 275, 375, 600, 175, 325, 225, 425, 250],
        'comments': [10, 50, 20, 80, 150, 30, 70, 40, 60, 25,
                    90, 110, 55, 75, 120, 35, 65, 45, 85, 50],
        'engagement_rate': [6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0,
                           6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0],
        'day_of_week': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
                        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
                        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        'hour': [10, 12, 14, 16, 18, 20, 22, 8, 10, 12, 14, 16, 18, 20, 22, 8, 10, 12, 14, 16],
        'subscribers_gained': [100, 500, 200, 800, 1500, 300, 700, 400, 600, 250,
                              900, 1100, 550, 750, 1200, 350, 650, 450, 850, 500]
    })
    
    # Create chatbot
    chatbot = create_chatbot(sample_data)
    
    # Test questions
    print("Testing Chatbot...")
    print("\n1. Summary:")
    result = chatbot.process_message("Give me a summary of my data")
    print(result['response'][:200])
    
    print("\n2. Top videos:")
    result = chatbot.process_message("What are my top 5 videos by views?")
    print(result['response'])
    
    print("\n3. Forecasting:")
    result = chatbot.process_message("What are my view forecasts?")
    print(result['response'])
