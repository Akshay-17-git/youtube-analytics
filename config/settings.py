"""
Configuration settings for YouTube Analytics project.
Loads environment variables from .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Settings:
    """Application settings loaded from environment variables."""
    
    # YouTube API Configuration
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    
    # MySQL Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'youtube_analytics')
    
    # OpenAI API (for chatbot)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Optional: Gemini API (alternative)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Application Settings
    MAX_VIDEOS = int(os.getenv('MAX_VIDEOS', 150))
    DEFAULT_CHANNEL_ID = os.getenv('DEFAULT_CHANNEL_ID', '')
    
    @classmethod
    def get_database_url(cls):
        """Get SQLAlchemy database URL."""
        return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def get_mysql_connection_params(cls):
        """Get MySQL connection parameters for mysql-connector."""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME
        }
    
    @classmethod
    def validate(cls):
        """Validate required settings."""
        missing = []
        if not cls.YOUTUBE_API_KEY or cls.YOUTUBE_API_KEY == 'your_youtube_api_key_here':
            missing.append('YOUTUBE_API_KEY')
        if not cls.DB_PASSWORD or cls.DB_PASSWORD == 'your_mysql_root_password':
            missing.append('DB_PASSWORD')
        return missing


# Create settings instance
settings = Settings()
