"""
Document parsing service using LlamaParse.

This module provides functionality to parse documents using the LlamaParse API.
It extracts text content from various document formats and returns it in markdown format.
"""

from llama_parse import LlamaParse
from ..core.logging import logger
from ..core.config import get_settings
from fastapi import UploadFile
from typing import Union, Any, List
import os

settings = get_settings()

class DocumentParser:
    """
    A class for parsing documents using LlamaParse API.
    
    This class provides methods to parse documents from file paths or UploadFile objects
    and extract their text content in markdown format.
    
    Attributes:
        parser (LlamaParse): The LlamaParse instance used for document parsing.
    """
    def __init__(self):
        """
        Initialize the DocumentParser with LlamaParse API.
        
        Raises:
            Exception: If initialization of LlamaParse fails.
        """
        try:
            self.parser = LlamaParse(
                api_key=settings.LLAMA_PARSE_API_KEY,
                result_type="markdown",
                verbose=True,
            )
        except Exception as e:
            logger.error(f"Failed to initialize LlamaParse: {str(e)}")
            raise

    async def parse_document(self, file: Union[str, UploadFile]) -> List[Any]:
        """
        Parse document using LlamaParse to get text.
        
        Args:
            file: Either a file path (str) or an UploadFile object
            
        Returns:
            List[Any]: List of parsed document objects
        """
        try:
            if isinstance(file, str):
                # For file paths
                if not os.path.exists(file):
                    logger.error(f"File not found: {file}")
                    return []
                    
                documents = await self.parser.aload_data(file)
                return documents
                
            else:
                # For UploadFile objects
                content = await file.read()
                if not content:
                    logger.error("Empty file content")
                    return []
                    
                documents = await self.parser.aload_data(content)
                await file.seek(0)  # Reset file pointer for future reads
                return documents
                
        except Exception as e:
            logger.error(f"Error parsing document: {str(e)}")
            return []
