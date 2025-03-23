"""
AI configuration utilities.

This module provides centralized configuration for AI services used throughout the application,
including Google's Generative AI (Gemini) and LlamaParse settings.
"""

import google.generativeai as genai
from ..core.logging import logger
from ..core.config import get_settings

settings = get_settings()

# Set up the model configuration for Gemini
GEMINI_GENERATION_CONFIG = {
    "temperature": 0.0,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

GEMINI_SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

def configure_gemini():
    """
    Configure Google's Generative AI with API key and safety settings.
    
    Returns:
        bool: True if configuration was successful, False otherwise.
    
    Raises:
        Exception: If configuration fails and raise_exception is True.
    """
    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        logger.info("Google Generative AI configured successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to configure Google Generative AI: {str(e)}")
        raise

# Initialize Gemini on module import
configure_gemini()

def get_gemini_config():
    """
    Get the Gemini AI configuration settings.
    
    Returns:
        tuple: A tuple containing (GEMINI_GENERATION_CONFIG, GEMINI_SAFETY_SETTINGS)
    """
    return GEMINI_GENERATION_CONFIG, GEMINI_SAFETY_SETTINGS
