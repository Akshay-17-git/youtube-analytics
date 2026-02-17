"""
Analytics Explanations Module.
Provides easy-to-understand explanations for all metrics and charts.
Designed to be understandable by a 10-year-old.
"""
import streamlit as st
from typing import Dict, List


class AnalyticsExplainer:
    """Provides simple explanations for YouTube analytics."""
    
    # Simple explanations for kids and beginners
    METRIC_EXPLANATIONS = {
        'views': {
            'simple': "👀 Views are like counting how many people watched your video! It's like counting raise hands in a classroom - each hand raised is one person who watched.",
            'detailed': "Views represent the total number of times your video was watched. Each time someone starts watching your video, it counts as a view. YouTube counts a view after a few seconds of watching.",
            'emoji': '👀'
        },
        'likes': {
            'simple': "👍 Likes are when people click the thumbs up button because they liked your video! It's like giving a high-five to someone who did something good.",
            'detailed': "Likes are user interactions showing approval of your content. The like ratio (likes/views) helps understand how much viewers enjoyed your content relative to how many people watched it.",
            'emoji': '👍'
        },
        'comments': {
            'simple': "💬 Comments are messages people write to talk about your video! It's like passing notes in class, but everyone can see them.",
            'detailed': "Comments are viewer feedback and engagement. High comment counts indicate strong audience connection and community building. Comments provide valuable insights into what viewers think.",
            'emoji': '💬'
        },
        'engagement_rate': {
            'simple': "❤️ Engagement rate is like measuring how much people really like your video! It's the percentage of people who did something more than just watch - they liked, commented, or shared.",
            'detailed': "Engagement rate measures viewer interaction beyond passive watching. It's calculated as ((likes + comments) / views) × 100. Higher engagement means your content resonates with viewers.",
            'emoji': '❤️'
        },
        'impressions': {
            'simple': "📺 Impressions are how many times your video thumbnail was shown to people! It's like how many times a poster is shown on a billboard.",
            'detailed': "Impressions count how many times your video thumbnail was displayed on YouTube (search results, home page, suggested videos, etc.). This shows how often YouTube is showing your content to potential viewers.",
            'emoji': '📺'
        },
        'ctr': {
            'simple': "🖱️ CTR (Click-Through Rate) is like measuring how many people clicked on your video after seeing it! If 10 people saw your video thumbnail and 1 clicked, that's 10% CTR.",
            'detailed': "CTR measures the percentage of people who clicked on your video after seeing its thumbnail. It's calculated as (clicks/impressions) × 100. A good CTR indicates compelling thumbnails and titles.",
            'emoji': '🖱️'
        },
        'subscribers': {
            'simple': "⭐ Subscribers are people who follow your channel! It's like having fans who want to see every video you make.",
            'detailed': "Subscribers are viewers who choose to follow your channel to see new content. Subscriber count indicates channel growth and audience size. New subscribers gained per video shows content appeal.",
            'emoji': '⭐'
        },
        'watch_time': {
            'simple': "⏰ Watch time is how long people spend watching your videos! YouTube likes videos that keep people watching longer.",
            'detailed': "Watch time measures total minutes/hours viewers spent watching your content. It's a key ranking factor because YouTube wants to keep viewers on the platform. Longer watch sessions indicate engaging content.",
            'emoji': '⏰'
        },
        'avg_views': {
            'simple': "📊 Average views is the typical number of views per video! It helps you understand how well your videos do on average.",
            'detailed': "Average views per video helps understand typical video performance. Compare this to individual videos to see which perform above or below average.",
            'emoji': '📊'
        }
    }
    
    # Chart explanations
    CHART_EXPLANATIONS = {
        'views_over_time': {
            'title': '📈 Views Over Time',
            'simple': "This chart shows how your views have changed over time! Look for going UP - that means more people are watching!",
            'detailed': 'This line chart shows view counts across your video publication history. It helps identify growth trends, seasonal patterns, and the impact of content strategy changes.',
            'how_to_read': 'Look for upward trends (going up), downward trends (going down), and spikes (sudden jumps). Compare different time periods to understand growth.',
            'tip': 'If the line goes up, your channel is growing! 🎉'
        },
        'engagement_over_time': {
            'title': '❤️ Engagement Over Time',
            'simple': "This shows how much people interact with your videos! Higher is better!",
            'detailed': 'This chart tracks engagement rate (likes + comments as percentage of views) over time. It shows how well your content connects with viewers.',
            'how_to_read': 'Higher values mean more viewer interaction. Compare this to views to see if more views = more engagement.',
            'tip': 'Great engagement means people really like your content!'
        },
        'performance_by_day': {
            'title': '📅 Performance by Day',
            'simple': "This tells you which day of the week is best for posting! The taller the bar, the better!",
            'detailed': 'This bar chart shows average video performance for each day of the week. It helps identify optimal posting days based on historical data.',
            'how_to_read': 'The tallest bar shows the best day. Consider posting more content on those days!',
            'tip': 'Try posting on the best days for more views! 🚀'
        },
        'performance_by_hour': {
            'title': '⏰ Performance by Hour',
            'simple': "This shows what time of day people watch your videos most!",
            'detailed': 'This chart shows average performance by hour of publication. It helps identify when your target audience is most active.',
            'how_to_read': 'Find the hour with highest average views and try to publish around that time.',
            'tip': 'Post when your audience is awake and scrolling! 🌙'
        },
        'top_videos': {
            'title': '🏆 Top Videos',
            'simple': "These are your best videos! Learn from what made them successful!",
            'detailed': 'This table shows your highest-performing videos by various metrics. Study these to understand what works.',
            'how_to_read': 'Look at titles, topics, and timing of top performers. Try to identify patterns!',
            'tip': 'Try making more videos similar to your top performers! ✨'
        },
        'content_themes': {
            'title': '🎨 Content Themes',
            'simple': "This shows what types of videos do best! Like which flavor of ice cream is most popular!",
            'detailed': 'This analysis groups your videos by content type (tutorial, review, entertainment, etc.) and shows performance.',
            'how_to_read': 'Find the theme with highest views and consider making more of that type!',
            'tip': 'Focus on content types that your audience loves! 🎯'
        },
        'title_length': {
            'title': '📝 Title Length',
            'simple': "This shows if short or long video titles work better!",
            'detailed': 'This analyzes how video title length correlates with performance. It helps optimize titles.',
            'how_to_read': 'Find the title length category with best performance and use similar lengths.',
            'tip': 'Try different title lengths to see what works! 📏'
        },
        'duration_patterns': {
            'title': '⏱️ Video Duration',
            'simple': "This shows if short or long videos get more views!",
            'detailed': 'This analyzes how video length affects performance. Different lengths work for different content types.',
            'how_to_read': 'Find the duration range with best views and aim for that length.',
            'tip': 'The best video length depends on your content type! ⏰'
        }
    }
    
    # General tips for each page
    PAGE_TIPS = {
        'dashboard': [
            "📈 Keep an eye on your views - if they're going up, you're doing great!",
            "❤️ Higher engagement means people really love your content!",
            "📊 Compare your videos to find what works best!",
            "👀 Look for patterns in your best videos!"
        ],
        'forecasting': [
            "🔮 Forecasting is like predicting the weather - it's a guess, not certainty!",
            "📈 If the trend goes up, your channel is growing!",
            "🎯 Use forecasts to plan your content strategy!",
            "📊 Remember: past performance doesn't guarantee future results!"
        ],
        'calendar': [
            "📅 Posting at the right time helps more people see your video!",
            "⏰ Find when your audience is most active!",
            "🎯 Consistency is key - keep uploading regularly!",
            "📆 A content calendar helps you stay organized!"
        ],
        'patterns': [
            "🔍 Patterns help you understand what works!",
            "🎨 Some types of videos just do better!",
            "📝 Your video titles matter a lot!",
            "⏱️ Video length affects how many people watch!"
        ],
        'chatbot': [
            "🤖 Ask me anything about your channel!",
            "💡 The more specific your question, the better the answer!",
            "📊 I can help you understand your data!",
            "❓ Try asking 'What's my best video about?'"
        ]
    }
    
    @staticmethod
    def render_info_button(key: str, expanded: bool = False, use_expander: bool = True) -> None:
        """
        Render an information button with tooltip.
        
        Args:
            key: The metric or chart key
            expanded: Whether to show detailed explanation by default
            use_expander: Whether to use expander (set to False if inside another expander)
        """
        if key in AnalyticsExplainer.METRIC_EXPLANATIONS:
            exp = AnalyticsExplainer.METRIC_EXPLANATIONS[key]
            
            if use_expander:
                with st.expander(f"{exp['emoji']} What is {key.replace('_', ' ').title()}?", expanded=expanded):
                    st.markdown(f"**🌟 Simple Explanation:**")
                    st.markdown(exp['simple'])
                    st.markdown("---")
                    st.markdown(f"**📖 Detailed Explanation:**")
                    st.markdown(exp['detailed'])
            else:
                st.markdown(f"**{exp['emoji']} {key.replace('_', ' ').title()}**")
                st.markdown(f"*Simple: {exp['simple']}*")
                st.markdown(f"_Detailed: {exp['detailed']}_")
        
        elif key in AnalyticsExplainer.CHART_EXPLANATIONS:
            exp = AnalyticsExplainer.CHART_EXPLANATIONS[key]
            
            if use_expander:
                with st.expander(f"{exp['title']} - What does this chart mean?", expanded=expanded):
                    st.markdown(f"**🌟 Simple Explanation:**")
                    st.markdown(exp['simple'])
                    st.markdown("---")
                    st.markdown(f"**📖 How to Read This Chart:**")
                    st.markdown(exp['how_to_read'])
                    st.markdown("---")
                    st.markdown(f"**💡 Pro Tip:**")
                    st.markdown(exp['tip'])
            else:
                st.markdown(f"**{exp['title']}**")
                st.markdown(f"*Simple: {exp['simple']}*")
                st.markdown(f"_Tip: {exp['tip']}_")
    
    @staticmethod
    def render_metric_tooltip(metric: str) -> str:
        """Get tooltip text for a metric."""
        if metric in AnalyticsExplainer.METRIC_EXPLANATIONS:
            return AnalyticsExplainer.METRIC_EXPLANATIONS[metric]['simple']
        return ""
    
    @staticmethod
    def get_page_tips(page: str) -> List[str]:
        """Get tips for a specific page."""
        return AnalyticsExplainer.PAGE_TIPS.get(page, [])
    
    @staticmethod
    def render_kid_friendly_metric(metric_name: str, value: any, explanation: str = None) -> None:
        """Render a metric with kid-friendly explanation."""
        if explanation is None:
            explanation = AnalyticsExplainer.render_metric_tooltip(metric_name)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric(metric_name.replace('_', ' ').title(), value)
        with col2:
            if explanation:
                st.markdown(f"💡 {explanation[:50]}...")
    
    @staticmethod
    def render_simple_tip() -> None:
        """Render a random tip for beginners."""
        import random
        all_tips = []
        for tips in AnalyticsExplainer.PAGE_TIPS.values():
            all_tips.extend(tips)
        
        tip = random.choice(all_tips)
        st.info(tip)


def create_info_button(key: str, expanded: bool = False):
    """Convenience function to create info button."""
    AnalyticsExplainer.render_info_button(key, expanded)


def get_metric_explanation(metric: str) -> str:
    """Get simple explanation for a metric."""
    return AnalyticsExplainer.METRIC_EXPLANATIONS.get(metric, {}).get('simple', '')


# Test
if __name__ == "__main__":
    print("Analytics Explainer Test")
    print("=" * 50)
    
    print("\n📊 Metric Explanations:")
    for metric, exp in AnalyticsExplainer.METRIC_EXPLANATIONS.items():
        print(f"\n{exp['emoji']} {metric.upper()}")
        print(f"   Simple: {exp['simple'][:80]}...")
    
    print("\n\n📈 Chart Explanations:")
    for key, exp in AnalyticsExplainer.CHART_EXPLANATIONS.items():
        print(f"\n{exp['title']}")
        print(f"   Simple: {exp['simple'][:80]}...")
    
    print("\n\n💡 Page Tips:")
    for page, tips in AnalyticsExplainer.PAGE_TIPS.items():
        print(f"\n{page.upper()}:")
        for tip in tips[:2]:
            print(f"   - {tip}")
