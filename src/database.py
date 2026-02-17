"""
Database module for YouTube Analytics.
Handles MySQL/SQLite database operations using SQLAlchemy.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pandas as pd

# Try to import SQLAlchemy, but make it optional
try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Index, text
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None

from config.settings import settings

# Global flag for database availability
_db_available = None


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
    if not SQLALCHEMY_AVAILABLE:
        return None
    
    # Use SQLite as fallback for cloud deployment
    db_url = settings.get_database_url()
    
    # If MySQL connection fails, fallback to SQLite
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        # Fallback to SQLite
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'youtube_analytics.db')
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        sqlite_url = f"sqlite:///{sqlite_path}"
        engine = create_engine(sqlite_url, echo=False)
        return engine


def get_session():
    """Create and return a new database session."""
    engine = get_engine()
    if engine is None:
        return None
    Session = sessionmaker(bind=engine)
    return Session()


def init_database():
    """Initialize database: create tables if they don't exist."""
    if not SQLALCHEMY_AVAILABLE:
        print("SQLAlchemy not available, skipping database initialization")
        return
    
    print("Initializing database...")
    
    try:
        engine = get_engine()
        if engine is None:
            print("Could not create database engine")
            return
            
        # Check if it's SQLite (no need to create database)
        db_url = str(engine.url)
        if 'sqlite' in db_url:
            # SQLite - just create tables
            Base.metadata.create_all(engine)
            engine.dispose()
            print(f"SQLite database initialized successfully!")
            return
        
        # MySQL - need to create database first
        temp_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}"
        temp_engine = create_engine(temp_url, pool_pre_ping=True)
        
        # Create database if not exists
        with temp_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}"))
            conn.commit()
        temp_engine.dispose()
        
        # Now create tables
        Base.metadata.create_all(engine)
        engine.dispose()
        
        print(f"Database '{settings.DB_NAME}' initialized successfully!")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        # Try SQLite fallback
        try:
            sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'youtube_analytics.db')
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
            sqlite_url = f"sqlite:///{sqlite_path}"
            engine = create_engine(sqlite_url, echo=False)
            Base.metadata.create_all(engine)
            engine.dispose()
            print(f"SQLite fallback database initialized successfully!")
        except Exception as e2:
            print(f"SQLite fallback also failed: {e2}")


def test_connection():
    """Test database connection."""
    if not SQLALCHEMY_AVAILABLE:
        print("SQLAlchemy not available")
        return False
    
    try:
        engine = get_engine()
        if engine is None:
            return False
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def save_video_metrics(data: pd.DataFrame):
    """Save video metrics to database."""
    if not SQLALCHEMY_AVAILABLE:
        print("SQLAlchemy not available, skipping save")
        return
    
    session = get_session()
    if session is None:
        print("Could not create database session")
        return
    
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
        # Don't raise - just log the error
    finally:
        session.close()


def get_all_video_metrics() -> pd.DataFrame:
    """Get all video metrics from database."""
    if not SQLALCHEMY_AVAILABLE:
        return pd.DataFrame()
    
    session = get_session()
    if session is None:
        return pd.DataFrame()
    
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
    except Exception as e:
        print(f"Error getting video metrics: {e}")
        return pd.DataFrame()
    finally:
        session.close()


def get_video_metrics_by_date_range(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Get video metrics within a date range."""
    if not SQLALCHEMY_AVAILABLE:
        return pd.DataFrame()
    
    session = get_session()
    if session is None:
        return pd.DataFrame()
    
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
    except Exception as e:
        print(f"Error getting video metrics by date range: {e}")
        return pd.DataFrame()
    finally:
        session.close()


def delete_video_metrics(video_id: str):
    """Delete a video metric record."""
    if not SQLALCHEMY_AVAILABLE:
        return
    
    session = get_session()
    if session is None:
        return
    
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
