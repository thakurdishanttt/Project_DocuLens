"""
API endpoints for document processing and data extraction.

This module provides endpoints for uploading, processing, and extracting data from documents.
It handles various document formats, including PDF and multiple image formats, and provides
status tracking for document processing.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Header
from ...models.document import DocumentResponse
from ...services.document_processor import DocumentProcessor
from ...core.logging import logger
from typing import Dict, Any, Optional
from functools import lru_cache
import tempfile
import os
import mimetypes
from PIL import Image
import io
import uuid
from uuid import UUID
from datetime import datetime

router = APIRouter()

# Initialize mimetypes
mimetypes.init()

# Supported image formats and their MIME types
SUPPORTED_FORMATS = {
    'application/pdf': '.pdf',
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/tiff': '.tiff',
    'image/bmp': '.bmp',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/x-portable-anymap': '.pnm',
    'image/x-portable-bitmap': '.pbm',
    'image/x-portable-graymap': '.pgm',
    'image/x-portable-pixmap': '.ppm',
    'image/x-dcx': '.dcx',
    'image/x-pcx': '.pcx',
    'image/vnd.djvu': '.djvu',
    'image/heic': '.heic',
    'image/heif': '.heif'
}

# Get document processor instance
@lru_cache()
def get_document_processor():
    """
    Get the document processor instance.
    
    Returns:
        DocumentProcessor: The document processor instance.
    """
    from ...main import contract_manager
    return DocumentProcessor(contract_manager)

def detect_mime_type(file_name: str, content: bytes) -> str:
    """
    Detect the MIME type of a file using its filename and content.
    
    Args:
        file_name (str): The name of the file.
        content (bytes): The content of the file.
    
    Returns:
        str: The detected MIME type of the file.
    """
    # First try to detect from filename
    mime_type, _ = mimetypes.guess_type(file_name)
    
    if mime_type:
        return mime_type
        
    # If that fails, try to detect from content using PIL
    try:
        with io.BytesIO(content) as buf:
            img = Image.open(buf)
            return f"image/{img.format.lower()}"
    except:
        # If PIL can't open it and it has a .pdf extension, assume it's a PDF
        if file_name.lower().endswith('.pdf'):
            return 'application/pdf'
    
    return 'application/octet-stream'

def convert_to_processable_format(content: bytes, original_mime: str) -> tuple[bytes, str]:
    """
    Convert an image to a processable format if needed.
    
    Args:
        content (bytes): The content of the image.
        original_mime (str): The original MIME type of the image.
    
    Returns:
        tuple[bytes, str]: The converted image content in a processable format and its MIME type.
    """
    try:
        # If it's PDF or already in a supported format, return as is
        if original_mime == 'application/pdf' or original_mime in {
            'image/jpeg', 'image/png', 'image/tiff', 'image/bmp'
        }:
            return content, original_mime

        # For other formats, convert to PNG
        image = Image.open(io.BytesIO(content))
        
        # Convert RGBA to RGB if needed
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        elif image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Save as PNG
        output = io.BytesIO()
        image.save(output, format='PNG', optimize=True)
        return output.getvalue(), 'image/png'

    except Exception as e:
        logger.error(f"Error converting image: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Error converting image format: {str(e)}"
        )

@router.post("/process", response_model=DocumentResponse)
async def process_document(
    file: UploadFile = File(...),
    email: str = None,
    org_name: Optional[str] = None,
    doc_processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Process a document and extract data.
    
    Args:
        file (UploadFile): The document file to process
        email (str, optional): User email
        org_name (str, optional): Organization name
        doc_processor (DocumentProcessor): Document processor dependency
        
    Returns:
        Dict[str, Any]: Extracted data and metadata
    """
    try:
        user_id, org_id = await doc_processor.contract_manager.db_manager.handle_user_organization(email, org_name)
        
        # Process the document
        result = await doc_processor.process_document(file, user_id, org_id)
        
        # Add user and organization IDs to the result
        result["user_id"] = user_id
        result["org_id"] = org_id
        
        return result
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/status/{document_id}")
async def get_status(
    document_id: str,
    doc_processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Get the status of a document processing request.
    
    Args:
        document_id (str): The ID of the document to check the status for.
        doc_processor (DocumentProcessor): The document processor instance.
    
    Returns:
        str: The status of the document processing request.
    
    Raises:
        HTTPException: If there is an error retrieving the status.
    """
    return await doc_processor.get_status(document_id)

@router.get("/data/{document_id}")
async def get_extracted_data(
    document_id: str,
    doc_processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Get the extracted data for a processed document.
    
    Args:
        document_id (str): The ID of the processed document.
        doc_processor (DocumentProcessor): The document processor instance.
    
    Returns:
        Dict[str, Any]: The extracted data from the document.
    
    Raises:
        HTTPException: If there is an error retrieving the extracted data.
    """
    return await doc_processor.get_extracted_data(document_id)
