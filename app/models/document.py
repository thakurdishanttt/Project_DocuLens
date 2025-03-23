"""
Document data models for the application.

This module defines Pydantic models for document-related data structures used throughout the application.
It includes models for document creation, database storage, and API responses, providing a consistent
interface for document data across different components of the system.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class DocumentBase(BaseModel):
    """
    Base model for document-related data.
    
    Attributes:
        filename (str): The name of the document file.
        document_type (str): The type of the document (e.g., PDF, DOCX).
        confidence (float): The confidence score for the document classification, ranging from 0.0 to 1.0.
    """
    filename: str
    document_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    
class DocumentCreate(DocumentBase):
    """
    Model for creating a new document entry.
    
    Inherits from DocumentBase and adds additional attributes specific to document creation.
    
    Attributes:
        content (bytes): The raw content of the document.
        mime_type (str): The MIME type of the document (e.g., application/pdf).
    """
    content: bytes
    mime_type: str
    
class DocumentInDB(DocumentBase):
    """
    Model representing a document stored in the database.
    
    Inherits from DocumentBase and includes additional fields for database management.
    
    Attributes:
        document_id (uuid.UUID): Unique identifier for the document.
        created_at (datetime): Timestamp of when the document was created.
        updated_at (datetime): Timestamp of the last update to the document.
        extracted_data (Dict[str, Any]): Data extracted from the document.
        status (str): Current processing status of the document (e.g., pending, completed).
        error (Optional[str]): Error message if processing failed.
        email_id (Optional[str]): Associated email ID if applicable.
        file_name (Optional[str]): Original file name of the document.
        file_type (Optional[str]): Type of the file.
        classification_confidence (Optional[float]): Confidence score for the classification.
        storage_path (Optional[str]): Path where the document is stored.
        processed_status (str): Status of the document processing, defaults to pending.
    """
    document_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    error: Optional[str] = None
    email_id: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    document_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    storage_path: Optional[str] = None
    processed_status: str = "pending"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
        
class DocumentResponse(DocumentBase):
    """
    Model for returning document data in API responses.
    
    Inherits from DocumentBase and includes additional fields for response purposes.
    
    Attributes:
        document_id (uuid.UUID): Unique identifier for the document.
        extracted_data (Optional[Dict[str, Any]]): The extracted data from the document, if available.
        error (Optional[str]): Error message if there was an issue processing the document.
        processing_id (Optional[str]): The processing ID associated with the document.
    """
    document_id: uuid.UUID
    filename: str
    extracted_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_id: Optional[str] = None
