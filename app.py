"""
YouTube Analytics Dashboard - Streamlit Application
Main entry point for the YouTube Growth Analytics Assistant.

Enhancements include:
- Sample data generation for demo
- Information buttons on all charts
- Kid-friendly explanations
- Improved visualizations
- Enhanced chatbot capabilities
"""
import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from src.database import get_all_video_metrics, init_database, test_connection, save_video_metrics
from src.metrics import AnalyticsMetrics
from src.forecasting import TrendForecasting
from src.calendar_optimizer import CalendarOptimizer
from src.pattern_detection import PatternDetection
from src.ab_testing import ABTestSimulator
from src.chatbot import YouTubeAnalyticsChatbot
from src.etl import ETLPipeline
from src.youtube_api import YouTubeAPI
from src.sample_data import SampleDataGenerator
from src.analytics_explanations import AnalyticsExplainer


# Page configuration
st.set_page_config(
    page_title="YouTube Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS - Colorful and Engaging
st.markdown("""
<style>
    .main {
        background-color: #0e1117
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
    }
    .metric-label {
        color: #9ca3af;
    }
    .metric-value {
        color: #ffffff;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .stDataFrame {
        background-color: #1e2130;
    }
    div[data-testid="stExpander"] {
        background-color: #1e2130;
    }
    .stTextInput > div > div > input {
        background-color: #1e2130;
        color: white;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
    }
    /* Custom info boxes */
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
    }
    .tip-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    /* Chart container */
    .chart-container {
        background-color: #1e2130;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1e2130;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load data from database."""
    try:
        df = get_all_video_metrics()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def fetch_and_analyze_channel(channel_input: str):
    """Fetch channel data and return analyzed metrics."""
    try:
        yt = YouTubeAPI()
        
        # Try to search for channel if it's a name
        if not channel_input.startswith('UC'):
            results = yt.youtube.search().list(
                part='snippet',
                q=channel_input,
                type='channel',
                maxResults=1
            ).execute()
            
            if results.get('items'):
                channel_id = results['items'][0]['id']['channelId']
            else:
                st.error("Channel not found. Please check the channel name.")
                return None
        else:
            channel_id = channel_input
        
        # Get channel info
        channel_info = yt.get_channel_info(channel_id)
        if not channel_info:
            st.error("Could not fetch channel information.")
            return None
        
        # Get videos with stats (now fetches 150 videos)
        videos = yt.get_uploaded_videos(channel_info['uploads_playlist_id'], max_results=150)
        
        if not videos:
            st.error("No videos found for this channel.")
            return None
        
        # Get video IDs
        video_ids = [v['video_id'] for v in videos]
        
        # Fetch all video statistics in batch
        video_details = yt.get_video_details(video_ids)
        
        if video_details.empty:
            st.error("Could not fetch video statistics.")
            return None
        
        # Prepare data with all required columns
        data = []
        for _, row in video_details.iterrows():
            views = row['views']
            likes = row['likes']
            comments = row['comments']
            
            engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0
            
            data.append({
                'video_id': row['video_id'],
                'title': row['title'],
                'published_at': row['published_at'],
                'views': views,
                'likes': likes,
                'comments': comments,
                'engagement_rate': engagement_rate,
                'subscribers': 0,
                'day_of_week': pd.to_datetime(row['published_at']).day_name(),
                'hour': pd.to_datetime(row['published_at']).hour,
            })
        
        df = pd.DataFrame(data)
        
        # Save to database
        try:
            save_video_metrics(df)
        except Exception as e:
            st.warning(f"Could not save to database: {e}")
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None


def main():
    """Main application."""
    st.title("📊 YouTube Analytics Dashboard")
    st.caption("Use these metrics to see what works and improve your channel growth—post when it counts, double down on what performs, and test titles and thumbnails.")
    
    # Initialize database
    try:
        init_database()
    except Exception as e:
        st.warning(f"Database not available: {e}")
    
    # Sidebar - Data Source Selection
    st.sidebar.title("⚙️ Settings")
    
    # Data source options - only live YouTube
    data_source = st.sidebar.radio(
        "📥 Data Source",
        ["🔗 Fetch from YouTube"]
    )
    
    # Future import option placeholder
    with st.sidebar.expander("📥 Import from YouTube Studio (Coming Soon)"):
        st.info("🎯 Coming soon!")
    
    # Clear data button
    if st.sidebar.button("🗑️ Clear Data"):
        keys_to_remove = [key for key in st.session_state.keys()]
        for key in keys_to_remove:
            del st.session_state[key]
        st.rerun()
    
    # Display current channel if loaded
    if 'channel_info' in st.session_state:
        info = st.session_state['channel_info']
        st.sidebar.success(f"📺 {info.get('channel_name', 'Channel')} loaded")
    
    # Check session state first for existing data
    if 'df' in st.session_state and not st.session_state['df'].empty:
        df = st.session_state['df']
    else:
        df = pd.DataFrame()
    
    # Get channel info from session state
    channel_info = st.session_state.get('channel_info', {})
    
    if data_source == "🔗 Fetch from YouTube":
        channel_input = st.sidebar.text_input(
            "🎬 YouTube Channel",
            placeholder="Channel name, URL, or ID",
            value=channel_info.get('channel_name', '')
        )
        
        if st.sidebar.button("📥 Fetch Channel Data"):
            if not channel_input:
                st.error("Please enter a channel name!")
            else:
                with st.spinner("Fetching channel data..."):
                    # Get channel info first
                    yt = YouTubeAPI()
                    
                    # Search for channel if needed
                    if not channel_input.startswith('UC'):
                        results = yt.youtube.search().list(
                            part='snippet',
                            q=channel_input,
                            type='channel',
                            maxResults=1
                        ).execute()
                        
                        if results.get('items'):
                            channel_id = results['items'][0]['id']['channelId']
                            channel_name = results['items'][0]['snippet']['title']
                        else:
                            st.error("Channel not found. Please check the channel name.")
                            channel_id = None
                            channel_name = None
                    else:
                        channel_id = channel_input
                        channel_name = None
                    
                    if channel_id:
                        # Get full channel info
                        info = yt.get_channel_info(channel_id)
                        if info:
                            channel_name = info.get('channel_name', channel_name)
                            st.session_state['channel_info'] = info
                        
                        df = fetch_and_analyze_channel(channel_input)
                        if df is not None:
                            st.session_state['df'] = df
                            st.success(f"✅ Loaded {len(df)} videos from {channel_name or channel_input}!")
                        else:
                            st.error("Failed to fetch data. Check the channel name and try again.")

    # If no data, show message
    if df.empty:
        st.info("👈 Enter a YouTube channel in the sidebar to get started!")
        return
    
    # Prepare current_df with required columns
    current_df = df.copy()
    
    # Add required columns if missing
    if 'published_at' in current_df.columns:
        if 'day_of_week' not in current_df.columns:
            current_df['day_of_week'] = pd.to_datetime(current_df['published_at']).dt.day_name()
        if 'hour' not in current_df.columns:
            current_df['hour'] = pd.to_datetime(current_df['published_at']).dt.hour
    
    # Calculate engagement rate if missing
    if 'engagement_rate' not in current_df.columns:
        if 'likes' in current_df.columns and 'comments' in current_df.columns and 'views' in current_df.columns:
            current_df['engagement_rate'] = ((current_df['likes'] + current_df['comments']) / current_df['views'] * 100).fillna(0)
    
    # Sidebar - Page Selection
    st.sidebar.title("📑 Pages")
    page = st.sidebar.radio(
        "Go to",
        ["📊 Dashboard", "🔮 Forecasting", "📅 Calendar Optimizer", "🔍 Pattern Detection", "🧪 A/B Testing", "🤖 AI Chatbot"]
    )
    
    # Page content
    if page == "📊 Dashboard":
        render_dashboard(current_df)
    elif page == "🔮 Forecasting":
        render_forecasting(current_df)
    elif page == "📅 Calendar Optimizer":
        render_calendar_optimizer(current_df)
    elif page == "🔍 Pattern Detection":
        render_pattern_detection(current_df)
    elif page == "🧪 A/B Testing":
        render_ab_testing(current_df)
    elif page == "🤖 AI Chatbot":
        render_chatbot(current_df)


def render_dashboard(df):
    """Render dashboard page with improved charts."""
    
    # Get channel info from session state
    channel_info = st.session_state.get('channel_info', {})
    channel_name = channel_info.get('channel_name', 'Your Channel')
    
    st.header(f"📊 {channel_name} - Channel Overview")
    
    # Calculate metrics
    metrics = AnalyticsMetrics(df)
    summary = metrics.get_summary_stats()
    
    # Key metrics - Using Streamlit native columns with abbreviations
    st.markdown("### 📊 Channel Performance Summary")
    st.caption("Quick snapshot of your overall channel performance and growth.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_videos = summary.get('total_videos', 0)
    total_views = summary.get('total_views', 0)
    total_likes = summary.get('total_likes', 0)
    avg_engagement = summary.get('avg_engagement_rate', 0)
    
    # Format large numbers with K/M suffixes
    def format_number(num):
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:,.0f}"
    
    with col1:
        st.metric("🎬 Videos", f"{total_videos}")
        st.caption("Total videos analyzed")
    with col2:
        st.metric("👀 Views", format_number(total_views))
        st.caption("Total video views")
    with col3:
        st.metric("👍 Likes", format_number(total_likes))
        st.caption("Total thumbs up")
    with col4:
        st.metric("❤️ Engagement", f"{avg_engagement:.1f}%")
        st.caption("(Likes+Comments)/Views × 100")
    
    # Improved Charts Section
    st.markdown("---")
    
    # Create two columns for charts
    chart_col1, chart_col2 = st.columns(2)
    
    # Prepare data for charts
    df_sorted = df.sort_values('published_at').tail(20)  # Last 20 videos
    
    with chart_col1:
        st.markdown("**📈 Views Trend (Last 20 Videos)**")
        fig_views = go.Figure()
        fig_views.add_trace(go.Scatter(
            x=list(range(len(df_sorted))),
            y=df_sorted['views'].values,
            mode='lines+markers',
            name='Views',
            fill='tozeroy',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=8, color='#4CAF50', symbol='circle')
        ))
        fig_views.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,33,48,1)',
            font_color='white',
            xaxis_title="Video #",
            yaxis_title="Views",
            hovermode='x unified',
            height=300,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        fig_views.update_yaxes(tickformat=',')
        st.plotly_chart(fig_views, use_container_width=True)
    
    with chart_col2:
        st.markdown("**❤️ Engagement Trend (Last 20 Videos)**")
        fig_eng = go.Figure()
        fig_eng.add_trace(go.Scatter(
            x=list(range(len(df_sorted))),
            y=df_sorted['engagement_rate'].values,
            mode='lines+markers',
            name='Engagement',
            fill='tozeroy',
            line=dict(color='#FF9800', width=3),
            marker=dict(size=8, color='#FF9800', symbol='circle')
        ))
        fig_eng.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,33,48,1)',
            font_color='white',
            xaxis_title="Video #",
            yaxis_title="Engagement %",
            hovermode='x unified',
            height=300,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        fig_eng.update_yaxes(tickformat='.1f')
        st.plotly_chart(fig_eng, use_container_width=True)
    
    # Additional charts row
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        st.markdown("**📅 Performance by Day of Week**")
        day_perf = metrics.get_performance_by_day()
        if not day_perf.empty:
            # Order days correctly
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_perf['day_of_week'] = pd.Categorical(day_perf['day_of_week'], categories=day_order, ordered=True)
            day_perf = day_perf.sort_values('day_of_week')
            
            fig_day = px.bar(
                day_perf, 
                x='day_of_week', 
                y='views',
                color='views',
                color_continuous_scale='Viridis'
            )
            fig_day.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30,33,48,1)',
                font_color='white',
                xaxis_title="Day",
                yaxis_title="Avg Views",
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                coloraxis_showscale=False
            )
            fig_day.update_yaxes(tickformat=',')
            st.plotly_chart(fig_day, use_container_width=True)
    
    with chart_col4:
        st.markdown("**🏆 Views vs Likes Scatter**")
        fig_scatter = px.scatter(
            df, 
            x='views', 
            y='likes',
            size='engagement_rate',
            hover_name='title',
            color='engagement_rate',
            color_continuous_scale='RdYlGn',
            size_max=30
        )
        fig_scatter.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,33,48,1)',
            font_color='white',
            xaxis_title="Views",
            yaxis_title="Likes",
            height=300,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        fig_scatter.update_xaxes(tickformat=',')
        fig_scatter.update_yaxes(tickformat=',')
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Top 5 Videos with conditional formatting
    st.markdown("---")
    st.subheader("🏆 Top 5 Videos")
    st.caption("Your best-performing videos based on views and engagement.")
    
    top_videos = metrics.get_top_videos(5)
    if not top_videos.empty:
        st.dataframe(
            top_videos[['title', 'views', 'likes', 'engagement_rate']].head(5)
            .style.background_gradient(subset=['views', 'likes'], cmap='Greens'),
            use_container_width=True
        )

def render_forecasting(df):
    """Render forecasting page with explanations."""
    channel_info = st.session_state.get('channel_info', {})
    channel_name = channel_info.get('channel_name', 'Your Channel')
    
    st.header(f"🔮 {channel_name} - Growth Forecasting")
    
    # Check if we have enough data
    if df is None or df.empty:
        st.error("No data available for forecasting. Please fetch channel data first.")
        return
    
    if len(df) < 5:
        st.warning("⚠️ Not enough data for accurate forecasting. Need at least 5 videos.")
        return
    
    # Explanation
    with st.expander("📖 What is Forecasting?", expanded=False):
        st.markdown("""
        **Forecasting is like predicting the weather!**
        
        Just like meteorologists use past weather data to predict tomorrow's weather, 
        we use your past video performance to guess how your channel might grow.
        
        ⚠️ **Important:** These are predictions based on trends, not guarantees! 
        External factors like trending topics can change results.
        """)
    
    try:
        forecast = TrendForecasting(df)
    except Exception as e:
        st.error(f"Error initializing forecasting: {str(e)}")
        return
    
    # View forecast
    st.subheader("📈 View Forecast")
    
    days = st.slider("Forecast Days", 7, 90, 30)
    
    try:
        view_forecast = forecast.forecast_views(days)
        if 'error' in view_forecast:
            st.warning(f"⚠️ {view_forecast['error']}")
            return
    except Exception as e:
        st.error(f"Error generating view forecast: {str(e)}")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🎯 Projected Total Views", f"{view_forecast.get('total_forecasted_views', 0):,}")
    with col2:
        st.metric("📊 Avg Daily Views", f"{view_forecast.get('average_daily_views', 0):,}")
    
    # Brief model quality info
    model_info = view_forecast.get("model", {})
    r2 = model_info.get("r_squared", 0.0)
    model_type = model_info.get("type", "linear").title()
    st.caption(f"Model: {model_type} regression (R² = {r2:.2f}). Shorter horizons are usually more reliable.")
    
    # Subscriber forecast
    st.subheader("👥 Subscriber Forecast")
    
    try:
        sub_forecast = forecast.forecast_subscribers(days)
        if 'error' not in sub_forecast:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🎯 Projected New Subscribers", f"{sub_forecast.get('total_forecasted_subscribers', 0):,}")
            with col2:
                st.metric("📊 Avg Daily Subscribers", f"{sub_forecast.get('average_daily_subscribers', 0):,}")
    except Exception as e:
        st.caption("Subscriber data not available")
    
    # Growth trajectory
    st.subheader("📈 Growth Trajectory")
    
    try:
        trajectory = forecast.get_growth_trajectory()
        
        col1, col2 = st.columns(2)
        with col1:
            trend_emoji = "📈" if trajectory.get('trend') == 'Growing' else "📉"
            st.metric("Current Trend", f"{trend_emoji} {trajectory.get('trend', 'Unknown')}")
        with col2:
            st.metric("Views Growth", f"{trajectory.get('views_growth_percentage', 0):.1f}%")
        
        st.success(f"💡 {trajectory.get('recommendation', '')}")
    except Exception as e:
        st.warning("Could not calculate growth trajectory")
    
    # Visualization
    st.subheader("📊 Forecast Visualization")
    
    try:
        forecast_df = forecast.get_forecast_dataframe(days)
        if forecast_df.empty:
            st.warning("Not enough data to visualize forecast.")
        else:
            fig = go.Figure()
            
            # Historical data
            if 'historical' in forecast_df.columns:
                hist_data = forecast_df['historical'].dropna()
                if not hist_data.empty:
                    fig.add_trace(go.Scatter(
                        x=hist_data.index,
                        y=hist_data.values,
                        mode='lines+markers',
                        name='Historical',
                        line=dict(color='#4CAF50'),
                        marker=dict(size=4)
                    ))
            
            # Forecast
            if 'forecast' in forecast_df.columns:
                forecast_data = forecast_df['forecast'].dropna()
                if not forecast_data.empty:
                    fig.add_trace(go.Scatter(
                        x=forecast_data.index,
                        y=forecast_data.values,
                        mode='lines+markers',
                        name='Forecast',
                        line=dict(color='#FF9800', dash='dash'),
                        marker=dict(size=4)
                    ))
            
            fig.update_layout(
                title='Views Forecast 📈',
                paper_bgcolor='#1e2130',
                plot_bgcolor='#1e2130',
                font_color='white',
                xaxis_title='Date',
                yaxis_title='Views',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Explanation of the chart
            with st.expander("📖 How to read this chart?", expanded=False):
                st.markdown("""
                - **Green line:** Your actual views in the past
                - **Orange dashed line:** Predicted views for the future
                
                The further into the future, the less certain the prediction!
                """)
    except Exception as e:
        st.error(f"Error creating forecast visualization: {str(e)}")


def render_calendar_optimizer(df):
    """Render calendar optimizer page with explanations."""
    channel_info = st.session_state.get('channel_info', {})
    channel_name = channel_info.get('channel_name', 'Your Channel')
    
    st.header(f"📅 {channel_name} - Content Calendar Optimizer")
    
    # Check if we have enough data
    if df is None or df.empty:
        st.error("No data available. Please fetch channel data first.")
        return
    
    if len(df) < 5:
        st.warning("⚠️ Not enough data for calendar optimization. Need at least 5 videos.")
        return
    
    # Explanation
    with st.expander("📖 What is the Calendar Optimizer?", expanded=False):
        st.markdown("""
        **This tool helps you find the best time to post your videos!**
        
        Just like the best time to post on social media matters, 
        this analyzes when your audience is most active.
        
        💡 **Tip:** Posting at the right time means more people see your video!
        """)
    
    try:
        optimizer = CalendarOptimizer(df)
    except Exception as e:
        st.error(f"Error initializing calendar optimizer: {str(e)}")
        return
    
    # Best days analysis
    st.subheader("📊 Day & Time Analysis")
    
    try:
        # Get all analyses
        best_days = optimizer.analyze_best_days()
        best_hours = optimizer.analyze_best_hours()
        
        # Show days as table
        if 'error' not in best_days:
            daily_stats = best_days.get('daily_stats', {})
            if daily_stats:
                days_data = []
                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                    if day in daily_stats.get('avg_views', {}):
                        days_data.append({
                            'Day': day,
                            'Avg Views': f"{daily_stats['avg_views'].get(day, 0):,.0f}",
                            'Total Views': f"{daily_stats['total_views'].get(day, 0):,}",
                            'Videos': daily_stats['video_count'].get(day, 0),
                            'Avg Engagement': f"{daily_stats['avg_engagement'].get(day, 0):.1f}%"
                        })
                days_df = pd.DataFrame(days_data)
                st.markdown("**📅 Performance by Day**")
                st.dataframe(days_df, use_container_width=True, hide_index=True)
                AnalyticsExplainer.render_info_button("performance_by_day", expanded=False)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏆 Best Day for Views", best_days.get('best_day_for_views', 'N/A'))
                with col2:
                    st.metric("❤️ Best Day for Engagement", best_days.get('best_day_for_engagement', 'N/A'))
        
        # Show hours as table
        if 'error' not in best_hours:
            hourly_stats = best_hours.get('hourly_stats', {})
            timezone_display = best_hours.get('timezone_display', 'UTC (Local Time)')
            
            if hourly_stats:
                hours_data = []
                for hour in sorted(hourly_stats.get('avg_views', {}).keys()):
                    hours_data.append({
                        'Hour': f"{hour}:00",
                        'Avg Views': f"{hourly_stats['avg_views'].get(hour, 0):,.0f}",
                        'Videos': hourly_stats['video_count'].get(hour, 0),
                        'Avg Engagement': f"{hourly_stats['avg_engagement'].get(hour, 0):.1f}%"
                    })
                hours_df = pd.DataFrame(hours_data)
                st.markdown("**⏰ Performance by Hour**")
                st.caption(f"🌍 Timezone: {timezone_display}")
                st.dataframe(hours_df, use_container_width=True, hide_index=True)
                AnalyticsExplainer.render_info_button("performance_by_hour", expanded=False)
                
                # Timezone info box
                st.info("📍 **Timezone Note:** These times are based on your channel's upload history. If you have a global audience, consider your target viewers' local time when scheduling.")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏆 Best Hour for Views", f"{best_hours.get('best_hour_for_views', 'N/A')}:00")
                with col2:
                    st.metric("❤️ Best Hour for Engagement", f"{best_hours.get('best_hour_for_engagement', 'N/A')}:00")
                    
    except Exception as e:
        st.warning("Could not analyze best days/hours")
    
    # Generate calendar
    st.subheader("📆 Recommended Content Calendar")
    
    weeks = st.slider("Weeks", 1, 4, 1)
    videos_per_week = st.slider("Videos per Week", 1, 7, 3)
    
    try:
        calendar = optimizer.generate_calendar(weeks=weeks, videos_per_week=videos_per_week)
        
        if not calendar:
            st.warning("Could not generate calendar. Not enough data.")
        else:
            # Display calendar
            calendar_data = []
            for item in calendar:
                calendar_data.append({
                    "Date": item['date'],
                    "Day": item['day'],
                    "Time": f"{item.get('time_24h', 14)}:00",
                    "Content Type": item['content_type'],
                    "Title Suggestion": item.get('title_suggestion', '')[:50]
                })
            
            calendar_df = pd.DataFrame(calendar_data)
            st.dataframe(calendar_df, use_container_width=True)
            
            # Content recommendations
            st.subheader("💡 Content Recommendations")
            
            recommendations = optimizer.get_complete_recommendations()
            
            # Upload frequency insight
            upload_freq = recommendations.get("upload_frequency", {})
            if upload_freq and "error" not in upload_freq:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "📅 Current Avg Uploads / Week",
                        upload_freq.get("current_avg_frequency", 0),
                    )
                with col2:
                    st.metric(
                        "🎯 Recommended Uploads / Week",
                        upload_freq.get("recommended_frequency", 0),
                    )
                st.caption(upload_freq.get("recommendation", ""))
            
            # Seasonal patterns insight
            seasonal = recommendations.get("seasonal_patterns", {})
            if seasonal and "error" not in seasonal:
                best_month = seasonal.get("best_month", "N/A")
                st.metric("🌟 Best Month Historically", best_month)
            
            # Title pattern highlight
            title_patterns = recommendations.get("title_patterns", {})
            if title_patterns and "error" not in title_patterns:
                patterns_list = title_patterns.get("best_patterns", [])[:3]
                if patterns_list:
                    st.markdown(
                        f"**📝 Title Patterns:** These work well on your channel: "
                        f"`{patterns_list[0]}`"
                        + (f", `{patterns_list[1]}`" if len(patterns_list) > 1 else "")
                        + (f", `{patterns_list[2]}`" if len(patterns_list) > 2 else "")
                    )
    except Exception as e:
        st.error(f"Error generating calendar: {str(e)}")


def render_pattern_detection(df):
    """Render pattern detection page with explanations."""
    channel_info = st.session_state.get('channel_info', {})
    channel_name = channel_info.get('channel_name', 'Your Channel')
    
    st.header(f"🔍 {channel_name} - Content Pattern Detection")
    
    # Check if we have enough data
    if df is None or df.empty:
        st.error("No data available. Please fetch channel data first.")
        return
    
    if len(df) < 5:
        st.warning("⚠️ Not enough data for pattern detection. Need at least 5 videos.")
        return
    
    # Explanation
    with st.expander("📖 What is Pattern Detection?", expanded=False):
        st.markdown("""
        **Pattern Detection finds what makes your videos successful!**
        
        It looks at your videos and finds patterns, like:
        - What types of videos get the most views
        - How long your titles should be
        - How long your videos should be
        - When you should upload
        
        🎯 **Use this to make more videos like your best ones!**
        """)
    
    try:
        detector = PatternDetection(df)
    except Exception as e:
        st.error(f"Error initializing pattern detection: {str(e)}")
        return
    
    # Content themes - Channel based
    st.subheader("🎨 Content Themes (Your Channel)")
    st.caption("Themes detected from your specific video titles - based on recurring keywords")
    
    try:
        themes = detector.detect_content_themes()
        if themes:
            theme_data = []
            for theme in themes:
                theme_data.append({
                    'Theme': theme.get('theme', 'Unknown'),
                    'Videos': theme.get('count', 0),
                    'Avg Views': theme.get('avg_views', 0),
                    'Example': theme.get('example_title', '')[:40] + '...',
                    'Performance': theme.get('performance', 'N/A')
                })
            
            theme_df = pd.DataFrame(theme_data)
            st.dataframe(theme_df, use_container_width=True)
            AnalyticsExplainer.render_info_button("content_themes", expanded=False)
        else:
            st.info("Not enough data to detect content themes.")
    except Exception as e:
        st.warning("Could not analyze content themes")
    
    # Title patterns
    st.subheader("📝 Title Patterns")
    st.caption("How title length affects video performance")
    
    try:
        title_patterns = detector.detect_title_length_patterns()
        if title_patterns and 'error' not in title_patterns:
            title_data = []
            for bucket, stats in title_patterns.items():
                title_data.append({
                    'Title Length': bucket,
                    'Avg Views': stats.get('avg_views', 0),
                    'Video Count': stats.get('count', 0)
                })
            
            title_df = pd.DataFrame(title_data)
            
            fig = px.bar(title_df, x='Title Length', y='Avg Views',
                        title='Average Views by Title Length 📝',
                        color='Avg Views', color_continuous_scale='Greens')
            fig.update_layout(paper_bgcolor='#1e2130', plot_bgcolor='#1e2130', font_color='white')
            st.plotly_chart(fig, use_container_width=True)
            AnalyticsExplainer.render_info_button("title_length", expanded=False)
        else:
            st.info("Title pattern data not available")
    except Exception as e:
        st.warning("Could not analyze title patterns")
    
    # Upload consistency
    st.subheader("📅 Upload Consistency")
    
    try:
        consistency = detector.detect_upload_consistency()
        if consistency and 'error' not in consistency:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Consistency", consistency.get('consistency', 'Unknown'))
            with col2:
                st.metric("📅 Avg Days Between Videos", f"{consistency.get('avg_days_between_uploads', 0):.1f}")
            
            st.success(f"💡 {consistency.get('recommendation', '')}")
        else:
            st.info("Not enough data to analyze upload consistency")
    except Exception as e:
        st.warning("Could not analyze upload consistency")


def render_ab_testing(df):
    """Render A/B testing page."""
    channel_info = st.session_state.get('channel_info', {})
    channel_name = channel_info.get('channel_name', 'Your Channel')
    
    st.header(f"🧪 {channel_name} - A/B Testing Simulator")
    
    # Context about the analysis
    st.info("""
    📊 **How this works:** This tool analyzes your channel's video history to identify patterns in titles 
    that perform well. It compares videos with certain patterns (like numbers, questions, "tips", etc.) 
    against videos without those patterns to estimate potential impact.
    """)
    
    simulator = ABTestSimulator(df)
    
    # Test scenarios
    st.subheader("📋 Test Scenarios")
    
    # Title A/B Test
    st.subheader("📝 Title A/B Test")
    st.caption("Compare two video titles and our AI will predict which one should perform better based on your channel's history.")
    
    title_col1, title_col2 = st.columns(2)
    with title_col1:
        title_a = st.text_input("Title A", "How to grow your channel", key="title_a_input")
    with title_col2:
        title_b = st.text_input("Title B", "10 tips to grow your YouTube channel", key="title_b_input")
    
    if st.button("🔍 Analyze Titles", key="analyze_titles"):
        with st.spinner("Analyzing titles..."):
            result = simulator.simulate_title_change(title_a, title_b)
            
            st.markdown("---")
            st.subheader("🏆 Title Analysis Results")
            
            # Show sample info
            sample_info = result.get('sample_info', {})
            st.caption(f"📊 {sample_info.get('message', 'Analyzing your video data...')}")
            
            # Determine winner based on expected improvement
            expected_change = result.get('expected_improvement', 0)
            
            if expected_change > 5:
                winner = "B"
                st.success(f"### 🥇 Title B Wins! (+{expected_change:.1f}% expected improvement)")
            elif expected_change < -5:
                winner = "A"
                improvement = abs(expected_change)
                st.success(f"### 🥇 Title A Wins! (+{improvement:.1f}% expected improvement)")
            else:
                st.info(f"### 🤝 Similar Performance (±{abs(expected_change):.1f}% difference)")
            
            # Metrics display
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Expected Change", f"{expected_change:+.1f}%")
            with col2:
                confidence = result.get('confidence', 'N/A')
                st.metric("Confidence Level", confidence)
            with col3:
                pattern_count = len(result.get('pattern_details', []))
                st.metric("Patterns Detected", pattern_count)
            
            # Detailed analysis
            st.markdown("---")
            st.subheader("📋 Detailed Analysis")
            
            # Show pattern details if available
            pattern_details = result.get('pattern_details', [])
            if pattern_details:
                st.markdown("**Title Pattern Changes Detected:**")
                
                for detail in pattern_details:
                    change_icon = "➕" if detail['change'] == 'Added' else "➖"
                    impact_color = "green" if detail['expected_impact'] > 0 else "red"
                    impact_sign = "+" if detail['expected_impact'] > 0 else ""
                    
                    st.markdown(
                        f"{change_icon} **{detail['change']}** '{detail['pattern']}' — "
                        f"Expected impact: :{impact_color}[{impact_sign}{detail['expected_impact']:.1f}%] "
                        f"(Confidence: {detail['confidence']})"
                    )
            else:
                st.info("ℹ️ No significant title pattern differences detected between these titles. Try making more distinct changes (e.g., add numbers, questions, or power words).")
            
            # Title comparison
            st.markdown("---")
            st.subheader("📝 Title Comparison")
            
            comp_col1, comp_col2 = st.columns(2)
            with comp_col1:
                st.markdown("**Title A:**")
                st.code(title_a, language='text')
            with comp_col2:
                st.markdown("**Title B:**")
                st.code(title_b, language='text')
            
            # Recommendation
            st.markdown("---")
            st.subheader("💡 Recommendation")
            recommendation = result.get('recommendation', '')
            if expected_change > 5:
                st.success(f"✅ **Use Title B** — {recommendation}")
            elif expected_change < -5:
                st.success(f"✅ **Use Title A** — {recommendation}")
            else:
                st.warning(f"⚠️ **Either title could work** — {recommendation}")
            
            # Title improvement tips
            st.markdown("---")
            st.subheader("🎯 Title Improvement Tips")
            
            tips = []
            title_lower = title_b.lower()
            
            # Check for best practices
            if not any(c.isdigit() for c in title_b):
                tips.append("🔢 Add numbers to your title (e.g., '5 Tips', '10 Ways') — numbers increase CTR by 15-20%")
            
            if '?' not in title_b:
                tips.append("❓ Consider using a question to spark curiosity")
            
            if len(title_b) < 30:
                tips.append("📝 Title B is quite short. Aim for 50-70 characters for optimal display")
            elif len(title_b) > 80:
                tips.append("✂️ Title B is long. Consider shortening to 50-70 characters so it doesn't get cut off")
            
            power_words = ['secret', 'best', 'ultimate', 'proven', 'exclusive', 'free', 'new', 'instant']
            has_power_word = any(word in title_lower for word in power_words)
            if not has_power_word:
                tips.append("⚡ Add power words like 'Secret', 'Best', 'Proven', or 'Ultimate' to increase emotional response")
            
            if 'how to' not in title_lower and 'tutorial' not in title_lower and 'guide' not in title_lower:
                tips.append("📚 For educational content, include 'How to' or 'Guide' to signal value")
            
            if not tips:
                tips.append("✅ Title B follows good practices! Test it and see how it performs.")
            
            for tip in tips:
                st.markdown(f"- {tip}")
    
    # Thumbnail A/B Test with upload
    st.markdown("---")
    st.subheader("🖼️ Thumbnail A/B Test")
    st.caption("Upload two thumbnail options and our AI will analyze which one should perform better based on visual features.")
    
    col1, col2 = st.columns(2)
    with col1:
        thumb_a = st.file_uploader("Thumbnail A", type=["png", "jpg", "jpeg"], key="thumb_a")
        if thumb_a is not None:
            st.image(thumb_a, use_column_width=True)
    with col2:
        thumb_b = st.file_uploader("Thumbnail B", type=["png", "jpg", "jpeg"], key="thumb_b")
        if thumb_b is not None:
            st.image(thumb_b, use_column_width=True)
    
    # Analyze thumbnails button
    if thumb_a is not None and thumb_b is not None:
        if st.button("🔍 Analyze Thumbnails", key="analyze_thumbs"):
            with st.spinner("Analyzing thumbnails..."):
                try:
                    # Read thumbnail data
                    thumb_a_data = thumb_a.getvalue()
                    thumb_b_data = thumb_b.getvalue()
                    
                    # Compare thumbnails
                    result = simulator.compare_thumbnails(thumb_a_data, thumb_b_data)
                    
                    if 'error' in result:
                        st.error(f"Analysis error: {result['error']}")
                    else:
                        # Display winner
                        winner = result.get('winner')
                        score_a = result.get('score_a', 0)
                        score_b = result.get('score_b', 0)
                        
                        st.markdown("---")
                        st.subheader("🏆 Analysis Results")
                        
                        # Winner announcement
                        if winner == 'A':
                            st.success(f"### 🥇 Thumbnail A Wins! (Score: {score_a} vs {score_b})")
                        elif winner == 'B':
                            st.success(f"### 🥇 Thumbnail B Wins! (Score: {score_b} vs {score_a})")
                        else:
                            st.info(f"### 🤝 It's a Tie! (Score: {score_a} each)")
                        
                        # Recommendation
                        st.markdown(f"**{result.get('recommendation', '')}**")
                        
                        # Detailed comparison
                        st.markdown("---")
                        st.subheader("📊 Detailed Comparison")
                        
                        comp_col1, comp_col2 = st.columns(2)
                        
                        with comp_col1:
                            st.markdown("**Thumbnail A Analysis:**")
                            reasons_a = result.get('reasons_a', [])
                            for reason in reasons_a:
                                st.markdown(f"✅ {reason}")
                            
                            analysis_a = result.get('analysis_a', {})
                            with st.expander("Technical Details"):
                                st.write(f"Brightness: {analysis_a.get('brightness', 0):.1f}")
                                st.write(f"Contrast: {analysis_a.get('contrast', 0):.1f}")
                                st.write(f"Colorfulness: {analysis_a.get('colorfulness', 0):.1f}")
                                st.write(f"Has face-like features: {analysis_a.get('has_face_like_features', False)}")
                                st.write(f"Has text-like features: {analysis_a.get('has_text_like_features', False)}")
                                st.write(f"Aspect ratio: {analysis_a.get('aspect_ratio', 0):.2f}")
                        
                        with comp_col2:
                            st.markdown("**Thumbnail B Analysis:**")
                            reasons_b = result.get('reasons_b', [])
                            for reason in reasons_b:
                                st.markdown(f"✅ {reason}")
                            
                            analysis_b = result.get('analysis_b', {})
                            with st.expander("Technical Details"):
                                st.write(f"Brightness: {analysis_b.get('brightness', 0):.1f}")
                                st.write(f"Contrast: {analysis_b.get('contrast', 0):.1f}")
                                st.write(f"Colorfulness: {analysis_b.get('colorfulness', 0):.1f}")
                                st.write(f"Has face-like features: {analysis_b.get('has_face_like_features', False)}")
                                st.write(f"Has text-like features: {analysis_b.get('has_text_like_features', False)}")
                                st.write(f"Aspect ratio: {analysis_b.get('aspect_ratio', 0):.2f}")
                        
                        # Improvement tips
                        st.markdown("---")
                        st.subheader("💡 Improvement Tips")
                        tips = result.get('improvement_tips', [])
                        for tip in tips:
                            st.markdown(f"- {tip}")
                        
                except Exception as e:
                    st.error(f"Failed to analyze thumbnails: {str(e)}")
                    st.info("Make sure you have Pillow installed: pip install Pillow")
    
    st.info("""
    **How to test these thumbnails on YouTube:**
    
    1. **Use YouTube's native experiments** (if available) to A/B test the two thumbnails.
    2. Or run a **manual test**: change the thumbnail after a set period and compare CTR and views.
    3. You can also use **community polls** or social media to ask which thumbnail people prefer.
    
    💡 Tip: Test one thing at a time – either change the title OR the thumbnail, not both together.
    """)


def render_chatbot(df):
    """Render AI chatbot page with improved UI."""
    channel_info = st.session_state.get('channel_info', {})
    channel_name = channel_info.get('channel_name', 'Your Channel')
    
    st.header(f"🤖 {channel_name} - AI Analytics Assistant")
    st.caption("Get clear answers and actionable next steps so you can grow your channel.")
    
    # Welcome message
    st.markdown("""
    Ask me anything about your channel. Every answer includes **how to grow** so you know what to do next.
    """)
    
    # Example questions
    st.info("""
    **Example questions (each answer includes how to grow):**
    - "When should I post?" / "Best day to post?"
    - "What content works best?" / "Which videos performed best?"
    - "Give me recommendations" / "How can I improve?"
    - "What's my growth trend?" / "Compare to benchmarks"
    """)
    
    # Initialize chatbot with current data
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = YouTubeAnalyticsChatbot(df)
    else:
        # Update chatbot with fresh data
        st.session_state.chatbot.df = df
    
    chatbot = st.session_state.chatbot
    
    # Quick action buttons
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Total Views", key="btn_views"):
            result = chatbot.process_message("What is my total views?")
            st.session_state.last_response = result['response']
    
    with col2:
        if st.button("🏆 Top Videos", key="btn_top"):
            result = chatbot.process_message("Show me my top 5 videos")
            st.session_state.last_response = result['response']
    
    with col3:
        if st.button("📅 Best Time to Post", key="btn_time"):
            result = chatbot.process_message("When should I post?")
            st.session_state.last_response = result['response']
    
    with col4:
        if st.button("💡 Recommendations", key="btn_rec"):
            result = chatbot.process_message("Give me recommendations for my channel")
            st.session_state.last_response = result['response']
    
    # More quick actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📈 Growth Trend", key="btn_growth"):
            result = chatbot.process_message("What is my growth trend?")
            st.session_state.last_response = result['response']
    
    with col2:
        if st.button("🎨 Best Content", key="btn_content"):
            result = chatbot.process_message("What content works best?")
            st.session_state.last_response = result['response']
    
    with col3:
        if st.button("👥 Audience Info", key="btn_audience"):
            result = chatbot.process_message("Tell me about my audience")
            st.session_state.last_response = result['response']
    
    with col4:
        if st.button("🏆 Benchmark", key="btn_benchmark"):
            result = chatbot.process_message("Compare my performance to industry benchmarks")
            st.session_state.last_response = result['response']
    
    # Show last response
    if 'last_response' in st.session_state:
        st.markdown("---")
        st.markdown(f"**Answer:** {st.session_state.last_response}")
    
    st.markdown("---")
    
    # Chat input
    st.subheader("💬 Ask Your Own Question")
    user_input = st.text_input("Type your question:", key="chat_input", 
                               placeholder="e.g., What's my best performing content? How can I grow faster?")
    
    if user_input:
        with st.spinner("🤔 Thinking..."):
            result = chatbot.process_message(user_input)
            st.session_state.last_response = result['response']
            st.markdown(f"**Answer:** {result['response']}")
            
            if result.get('query_used'):
                st.code(result['query_used'], language='sql')
            
            # Check if PDF report was generated
            if result.get('pdf_report'):
                st.download_button(
                    label="📄 Download PDF Report",
                    data=result['pdf_report'],
                    file_name="youtube_analytics_report.pdf",
                    mime="application/pdf"
                )
    
    # Direct PDF download button
    st.markdown("---")
    st.subheader("📄 Generate PDF Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Generate Full Analytics Report", key="gen_pdf"):
            with st.spinner("Generating PDF report..."):
                try:
                    pdf_data = chatbot.generate_pdf_report()
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_data,
                        file_name="youtube_analytics_report.pdf",
                        mime="application/pdf",
                        key="pdf_download"
                    )
                    st.success("✅ PDF report ready for download!")
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
    
    with col2:
        if st.button("🗑️ Clear Chat History", key="clear_chat"):
            chatbot.clear_history()
            if 'last_response' in st.session_state:
                del st.session_state.last_response
            st.success("Chat cleared!")


# Run main function
if __name__ == "__main__":
    main()
