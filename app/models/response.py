"""
API response models for the application.

This module defines Pydantic models for various API responses used throughout the application.
It includes models for health checks, error responses, processing status, and data extraction results,
providing a consistent structure for API responses across different endpoints.
"""

from pydantic import BaseModel
from typing import Optional, Any, Dict

class HealthResponse(BaseModel):
    """
    Model representing the health check response.
    
    Attributes:
        status (str): The health status of the application (e.g., healthy).
        version (str): The version of the application.
    """
    status: str
    version: str
    
class ErrorResponse(BaseModel):
    """
    Model representing an error response.
    
    Attributes:
        detail (str): A description of the error that occurred.
    """
    detail: str
    
class ProcessingResponse(BaseModel):
    """
    Model representing the response for document processing tasks.
    
    Attributes:
        processing_id (str): The ID associated with the processing task.
        status (str): The current status of the processing task.
        message (str): A message providing additional information about the processing task.
    """
    processing_id: str
    status: str
    message: str
    
class ExtractedDataResponse(BaseModel):
    """
    Model representing the response containing extracted data from a document.
    
    Attributes:
        document_id (str): The ID of the document from which data was extracted.
        extracted_data (Dict[str, Any]): The data extracted from the document.
        confidence (float): The confidence score of the extraction.
        error (Optional[str]): An optional error message if extraction failed.
    """
    document_id: str
    extracted_data: Dict[str, Any]
    confidence: float
    error: Optional[str] = None
