"""
Database connection utilities.

This module provides functions to create and manage database connections using Supabase.
It centralizes the creation of Supabase clients to ensure consistent configuration
throughout the application.
"""

from supabase import create_client
from app.core.config import settings

def get_supabase_client():
    """
    Create and return a Supabase client instance.
    
    This function creates a new Supabase client using the URL and API key
    from the application settings.
    
    Returns:
        Client: A configured Supabase client instance.
    """
    client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    return client
