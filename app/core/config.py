"""
Application configuration settings.

This module defines the configuration settings for the application using Pydantic's BaseSettings.
It loads environment variables from .env files and provides a centralized location for accessing
configuration values throughout the application.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from .logging import logger

def load_env():
    """
    Load environment variables from .env files.
    
    This function attempts to load environment variables from a .env file in the project root directory.
    If not found, it tries to find a .env file in parent directories.
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # Try to find .env file in parent directories
        env_file = find_dotenv()
        if env_file:
            load_dotenv(env_file)

load_env()

class Settings(BaseSettings):
    """
    Application settings class.
    
    This class defines all the configuration settings for the application,
    with default values and environment variable overrides.
    
    Attributes:
        APP_NAME (str): The name of the application.
        API_V1_STR (str): The API version prefix.
        PROJECT_NAME (str): The project name.
        VERSION (str): The application version.
        SUPABASE_URL (str): The URL of the Supabase instance.
        SUPABASE_KEY (str): The public/anon key for Supabase.
        SUPABASE_SERVICE_ROLE_KEY (str): The service role key for Supabase.
        SUPABASE_SERVICE_ROLE_EMAIL (str | None): Optional service role email.
        SUPABASE_SERVICE_ROLE_PASSWORD (str | None): Optional service role password.
        TESSERACT_PATH (str): Path to Tesseract OCR executable.
        OPENAI_API_KEY (str): OpenAI API key.
        GOOGLE_API_KEY (str): Google API key.
        LLAMA_PARSE_API_KEY (str): LlamaParse API key.
        LLAMA_PARSE_BASE_URL (str): Base URL for LlamaParse API.
        LLAMAPARSE_API_KEY (str): Alternative LlamaParse API key.
        LLAMAEXTRACT_API_KEY (str): LlamaExtract API key.
        GEMINI_API_KEY (str): Gemini API key.
    """
    APP_NAME: str = "Docu-Lens"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Doculens"
    VERSION: str = "1.0.0"
    
    # Supabase settings with default empty strings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # anon/public key
    SUPABASE_SERVICE_ROLE_KEY: str = ""  # service role key
    
    # Optional Supabase service role credentials
    SUPABASE_SERVICE_ROLE_EMAIL: str | None = None
    SUPABASE_SERVICE_ROLE_PASSWORD: str | None = None
    
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    LLAMA_PARSE_API_KEY: str = os.getenv("LLAMA_PARSE_API_KEY", "")
    LLAMA_PARSE_BASE_URL: str = os.getenv("LLAMA_PARSE_BASE_URL", "https://api.llamaparse.com")
    
    # LlamaParse and LlamaExtract settings
    LLAMAPARSE_API_KEY: str = os.getenv("LLAMAPARSE_API_KEY", "")
    LLAMAEXTRACT_API_KEY: str = os.getenv("LLAMAEXTRACT_API_KEY", "")
    
    # Gemini settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    class Config:
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in .env file

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load environment variables after initialization
        self.SUPABASE_URL = os.getenv("SUPABASE_URL", self.SUPABASE_URL)
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY", self.SUPABASE_KEY)
        self.SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", self.SUPABASE_SERVICE_ROLE_KEY)
        
        # Validate required settings
        if not self.SUPABASE_URL:
            logger.error("SUPABASE_URL is missing")
            raise ValueError("SUPABASE_URL is required")
        if not self.SUPABASE_KEY:
            logger.error("SUPABASE_KEY is missing")
            raise ValueError("SUPABASE_KEY is required")
        if not self.SUPABASE_SERVICE_ROLE_KEY:
            logger.error("SUPABASE_SERVICE_ROLE_KEY is missing")
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")

@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings.
    
    This function returns a cached instance of the Settings class,
    ensuring that settings are only loaded once.
    
    Returns:
        Settings: The application settings.
    """
    return Settings()

# Create settings instance
settings = get_settings()
