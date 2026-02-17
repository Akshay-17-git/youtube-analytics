"""
Database module for YouTube Analytics.
Handles MySQL database operations using SQLAlchemy.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pandas as pd

from config.settings import settings

# Create declarative base
Base = declarative_base()


class VideoMetrics(Base):
    """Video metrics table model."""
    __tablename__ = 'video_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500))
    published_at = Column(DateTime)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    watch_time_hours = Column(Float, default=0.0)
    subscribers_gained = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    subs_per_1k_views = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define indexes for faster queries
    __table_args__ = (
        Index('idx_published_at', 'published_at'),
        Index('idx_views', 'views'),
        Index('idx_engagement_rate', 'engagement_rate'),
    )


class ChannelStats(Base):
    """Channel statistics table model."""
    __tablename__ = 'channel_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(50), unique=True, nullable=False, index=True)
    channel_name = Column(String(500))
    total_subscribers = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_videos = Column(Integer, default=0)
    fetched_at = Column(DateTime, default=datetime.utcnow)


def get_engine():
    """Create and return SQLAlchemy engine."""
    engine = create_engine(
        settings.get_database_url(),
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
    return engine


def get_session():
    """Create and return a new database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_database():
    """Initialize database: create tables if they don't exist."""
    print("Initializing database...")
    
    # First, connect without database to create it if needed
    temp_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}"
    temp_engine = create_engine(temp_url, pool_pre_ping=True)
    
    # Create database if not exists
    with temp_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}"))
        conn.commit()
    temp_engine.dispose()
    
    # Now create tables
    engine = get_engine()
    Base.metadata.create_all(engine)
    engine.dispose()
    
    print(f"Database '{settings.DB_NAME}' initialized successfully!")


def test_connection():
    """Test database connection."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def save_video_metrics(data: pd.DataFrame):
    """Save video metrics to database."""
    session = get_session()
    try:
        for _, row in data.iterrows():
            # Check if video already exists
            existing = session.query(VideoMetrics).filter_by(video_id=row.get('video_id', '')).first()
            
            if existing:
                # Update existing record
                for key, value in row.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # Create new record
                video = VideoMetrics(
                    video_id=row.get('video_id', ''),
                    title=row.get('title', ''),
                    published_at=row.get('published_at'),
                    views=row.get('views', 0),
                    likes=row.get('likes', 0),
                    comments=row.get('comments', 0),
                    impressions=row.get('impressions', 0),
                    ctr=row.get('ctr', 0.0),
                    watch_time_hours=row.get('watch_time_hours', 0.0),
                    subscribers_gained=row.get('subscribers_gained', 0),
                    engagement_rate=row.get('engagement_rate', 0.0),
                    subs_per_1k_views=row.get('subs_per_1k_views', 0.0)
                )
                session.add(video)
        
        session.commit()
        print(f"Saved {len(data)} video metrics to database!")
    except Exception as e:
        session.rollback()
        print(f"Error saving video metrics: {e}")
        raise
    finally:
        session.close()


def get_all_video_metrics() -> pd.DataFrame:
    """Get all video metrics from database."""
    session = get_session()
    try:
        videos = session.query(VideoMetrics).order_by(VideoMetrics.published_at.desc()).all()
        
        data = []
        for video in videos:
            data.append({
                'video_id': video.video_id,
                'title': video.title,
                'published_at': video.published_at,
                'views': video.views,
                'likes': video.likes,
                'comments': video.comments,
                'impressions': video.impressions,
                'ctr': video.ctr,
                'watch_time_hours': video.watch_time_hours,
                'subscribers_gained': video.subscribers_gained,
                'engagement_rate': video.engagement_rate,
                'subs_per_1k_views': video.subs_per_1k_views
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def get_video_metrics_by_date_range(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Get video metrics within a date range."""
    session = get_session()
    try:
        videos = session.query(VideoMetrics).filter(
            VideoMetrics.published_at >= start_date,
            VideoMetrics.published_at <= end_date
        ).order_by(VideoMetrics.published_at.desc()).all()
        
        data = []
        for video in videos:
            data.append({
                'video_id': video.video_id,
                'title': video.title,
                'published_at': video.published_at,
                'views': video.views,
                'likes': video.likes,
                'comments': video.comments,
                'impressions': video.impressions,
                'ctr': video.ctr,
                'watch_time_hours': video.watch_time_hours,
                'subscribers_gained': video.subscribers_gained,
                'engagement_rate': video.engagement_rate,
                'subs_per_1k_views': video.subs_per_1k_views
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def delete_video_metrics(video_id: str):
    """Delete a video metric record."""
    session = get_session()
    try:
        video = session.query(VideoMetrics).filter_by(video_id=video_id).first()
        if video:
            session.delete(video)
            session.commit()
            print(f"Deleted video {video_id}")
    except Exception as e:
        session.rollback()
        print(f"Error deleting video: {e}")
    finally:
        session.close()


# Main function to initialize database
if __name__ == "__main__":
    print("Testing database connection...")
    if test_connection():
        print("\nInitializing database...")
        init_database()
        print("\nDatabase setup complete!")
    else:
        print("\nPlease check your database settings in .env file")
