import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration class"""
    
    # Discord Bot Token
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    # Bot Settings
    PREFIX = os.getenv('PREFIX', '!')
    OWNER_ID = int(os.getenv('OWNER_ID', '0'))
    
    # Database Settings (if needed later)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
    
    # API Keys (if needed for external services)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    
    # Bot Status
    STATUS_MESSAGE = os.getenv('STATUS_MESSAGE', '!help for commands')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required!")
        return True
