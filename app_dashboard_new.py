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
            x=range(len(df_sorted)),
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
            x=range(len(df_sorted)),
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
