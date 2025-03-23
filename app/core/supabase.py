"""
Supabase client singleton provider.

This module provides a cached Supabase client instance for database operations.
It ensures that only one client is created per application instance, improving
performance and resource utilization.
"""

from supabase import create_client, Client
import os
import logging
from functools import lru_cache

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

@lru_cache()
def get_supabase_client() -> Client:
    """
    Get a cached Supabase client instance.
    
    This function creates a Supabase client using environment variables
    and caches it for reuse. It ensures that only one client is created
    per application instance.
    
    Returns:
        Client: A configured Supabase client instance.
        
    Raises:
        ValueError: If Supabase credentials are missing from environment variables.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    
    _logger.info(f"Creating Supabase client with URL: {supabase_url}")
    return create_client(supabase_url, supabase_key)
