"""
String utility functions for text processing.

This module provides utility functions for string processing and normalization
that can be used across different components of the application.
"""

from typing import List


def normalize_document_type(document_type: str) -> str:
    """
    Normalize document type to handle variations in naming.
    
    Removes spaces, underscores, and converts to lowercase.
    
    Args:
        document_type (str): Document type to normalize.
        
    Returns:
        str: Normalized document type.
    """
    if not document_type:
        return ""
    
    # Remove spaces, underscores, and convert to lowercase
    normalized = document_type.lower().replace(" ", "").replace("_", "").replace("-", "")
    
    # Handle common misspellings or variations
    if "employment" in normalized:
        normalized = normalized.replace("employement", "employment")
    
    return normalized


def generate_case_variations(text: str) -> List[str]:
    """
    Generate different case variations of a string for matching.
    
    Args:
        text (str): The text to generate variations for.
        
    Returns:
        List[str]: List of case variations of the input text.
    """
    variations = [
        text.lower(),           # lowercase
        text.upper(),           # UPPERCASE
        text.title(),           # Title Case
        ''.join(text.split()),  # remove spaces
        '_'.join(text.split()).lower(),  # snake_case
        ''.join(word.capitalize() for word in text.split()),  # camelCase
    ]
    return list(set(variations))  # Remove duplicates
