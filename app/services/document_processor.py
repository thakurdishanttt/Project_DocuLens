"""
Document processing service for classification and data extraction.

This module provides functionality to process documents, classify their types,
extract data based on contract schemas, and track processing status.
It integrates with the ContractManager for document classification and data extraction.
"""

from typing import Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException
import asyncio
from ..core.logging import logger
from ..models.document import DocumentCreate, DocumentInDB, DocumentResponse
from .contract_manager import ContractManager
from .database_manager import DatabaseManager
import tempfile
import os
from datetime import datetime
import uuid

class DocumentProcessor:
    """
    A class for processing documents, classifying them, and extracting data.
    
    This class provides methods to process documents, track their processing status,
    and retrieve extracted data. It uses the ContractManager for document classification
    and data extraction.
    
    Attributes:
        contract_manager (ContractManager): Manager for contract operations and document classification.
        db_manager (DatabaseManager): Manager for database operations.
        _processing_documents (Dict[str, DocumentInDB]): Dictionary of documents being processed.
    """
    def __init__(self, contract_manager: ContractManager):
        """
        Initialize the DocumentProcessor with a ContractManager instance.
        
        Args:
            contract_manager (ContractManager): ContractManager instance for processing documents.
        """
        self.contract_manager = contract_manager
        self.db_manager = contract_manager.db_manager
        self._processing_documents: Dict[str, DocumentInDB] = {}

    async def process_document(self, file: UploadFile, user_id: str = None, org_id: str = None) -> Dict[str, Any]:
        """
        Process a document and return extracted data immediately.
        
        Args:
            file (UploadFile): The document file to process.
            user_id (str, optional): User ID to associate with the document.
            org_id (str, optional): Organization ID to associate with the document.
            
        Returns:
            Dict[str, Any]: Extracted data and metadata.
            
        Raises:
            HTTPException: If there is an error processing the document.
        """
        try:
            content = await file.read()
            
            if not content:
                raise HTTPException(status_code=400, detail="Empty file provided")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                temp_file.write(content)
                temp_file.flush()  # Ensure all data is written
                temp_path = temp_file.name
            
            try:
                document_type, confidence, parsed_document = await self.contract_manager.classify_document(temp_path)
                
                if document_type == "unknown":
                    document_id = str(uuid.uuid4())
                    return {
                        "filename": file.filename,
                        "document_type": "Unknown",
                        "confidence": 0.0,
                        "error": "Could not classify document",
                        "document_id": document_id
                    }

                if parsed_document is None:
                    logger.error("Parsed document is None, cannot extract data.")
                    document_id = str(uuid.uuid4())
                    return {
                        "filename": file.filename,
                        "document_type": document_type,
                        "confidence": 0.0,
                        "error": "Failed to parse document",
                        "document_id": document_id
                    }
                
                extracted_result = await self.contract_manager.extract_data(parsed_document, document_type)
                
                # Check if extraction failed
                if "error" in extracted_result:
                    document_id = str(uuid.uuid4())
                    return {
                        "filename": file.filename,
                        "document_type": document_type,
                        "confidence": confidence,
                        "error": extracted_result["error"],
                        "document_id": document_id
                    }
                
                # Generate document ID
                document_id = str(uuid.uuid4())
                
                # Create final extracted data with document_id
                extracted_data = {
                    **extracted_result,
                    "document_id": document_id,
                    "filename": file.filename,
                    "file_url": temp_path,
                    "document_type": document_type,
                    "confidence": confidence
                }
                
                # Save the extracted data
                try:
                    await self.db_manager.save_extracted_data(
                        document_id=document_id,
                        extracted_data=extracted_data,
                        user_id=user_id,
                        org_id=org_id
                    )
                except Exception as save_error:
                    logger.error(f"Error saving extracted data: {str(save_error)}")
                    return {
                        "filename": file.filename,
                        "document_type": document_type,
                        "confidence": confidence,
                        "error": f"Failed to save extracted data: {str(save_error)}",
                        "document_id": document_id
                    }
                
                return {
                    "filename": file.filename,
                    "document_type": document_type,
                    "confidence": confidence,
                    "extracted_data": extracted_data,
                    "document_id": document_id
                }
                
            finally:
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temporary file: {str(cleanup_error)}")
                    
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_status(self, document_id: str) -> str:
        """
        Get the current processing status of a document.
        
        Args:
            document_id (str): The ID of the document to check status for.
        
        Returns:
            str: The current processing status of the document.
        
        Raises:
            HTTPException: If the document is not found.
        """
        try:
            # Try memory first
            document = self._processing_documents.get(document_id)
            
            # If not in memory, try database
            if not document:
                response = await self.db_manager.get_document_by_id(document_id)
                if not response:
                    logger.error(f"Document ID not found in database: {document_id}")
                    raise HTTPException(status_code=404, detail=f"Document ID {document_id} not found")
                
                # Map database fields to DocumentInDB fields
                document_data = {
                    "id": response.get("id"),
                    "document_id": response.get("id"),  # Use id as document_id
                    "status": response.get("status", "unknown"),
                    "document_type": response.get("document_type", "unknown"),
                    "confidence": response.get("confidence", 0.0),
                    "extracted_data": response.get("extracted_data", {}),
                    "error": response.get("error"),
                    "filename": response.get("filename") or response.get("file_name", "unknown"),  # Try both filename and file_name
                    "created_at": response.get("created_at", datetime.utcnow()),
                    "updated_at": response.get("updated_at", datetime.utcnow()),
                    "email_id": response.get("email_id"),
                    "file_type": response.get("file_type"),
                    "classification_confidence": response.get("classification_confidence"),
                    "storage_path": response.get("storage_path"),
                    "processed_status": response.get("processed_status", "pending")
                }
                document = DocumentInDB(**document_data)
            
            return document.status
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting document status: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error while getting document status: {str(e)}")

    async def get_extracted_data(self, document_id: str) -> Dict[str, Any]:
        """
        Get the extracted data for a processed document.
        
        Args:
            document_id (str): The ID of the document to retrieve extracted data for.
        
        Returns:
            Dict[str, Any]: The extracted data for the document.
        
        Raises:
            HTTPException: If the document is not fully processed or not found.
        """
        try:
            # Try memory first
            document = self._processing_documents.get(document_id)
            
            # If not in memory, try database
            if not document:
                response = await self.db_manager.get_document_by_id(document_id)
                if not response:
                    logger.error(f"Document ID not found in database: {document_id}")
                    raise HTTPException(status_code=404, detail=f"Document ID {document_id} not found")
                
                # Map database fields to DocumentInDB fields
                document_data = {
                    "id": response.get("id"),
                    "document_id": response.get("id"),  # Use id as document_id
                    "status": response.get("status", "unknown"),
                    "document_type": response.get("document_type", "unknown"),
                    "confidence": response.get("confidence", 0.0),
                    "extracted_data": response.get("extracted_data", {}),
                    "error": response.get("error"),
                    "filename": response.get("filename") or response.get("file_name", "unknown"),  # Try both filename and file_name
                    "created_at": response.get("created_at", datetime.utcnow()),
                    "updated_at": response.get("updated_at", datetime.utcnow()),
                    "email_id": response.get("email_id"),
                    "file_type": response.get("file_type"),
                    "classification_confidence": response.get("classification_confidence"),
                    "storage_path": response.get("storage_path"),
                    "processed_status": response.get("processed_status", "pending")
                }
                document = DocumentInDB(**document_data)
            
            # Only allow extraction for completed or processed documents
            if document.status not in ["completed", "processed"]:
                logger.error(f"Document not fully processed. Current status: {document.status}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Document not fully processed. Current status: {document.status}"
                )
            
            return {
                "document_id": document.document_id,
                "extracted_data": document.extracted_data,
                "confidence": document.confidence,
                "error": document.error
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting extracted data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error while getting extracted data: {str(e)}")

    async def _save_uploaded_file(self, file: UploadFile) -> str:
        """
        Save uploaded file to temporary storage and return processing ID.
        
        Args:
            file (UploadFile): The uploaded document file.
        
        Returns:
            str: The processing ID (temporary file name).
        
        Description:
            This method saves the uploaded file to a temporary location
            and returns the processing ID for tracking.
        """
        try:
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file.flush()  # Ensure all data is written
                return os.path.basename(temp_file.name)
        except Exception as e:
            logger.error(f"Error saving uploaded file: {str(e)}")
            raise HTTPException(status_code=500, detail="Could not save uploaded file")

    async def _process_document_async(self, processing_id: str, document: DocumentInDB):
        """
        Process document asynchronously and update results.
        
        Args:
            processing_id (str): The processing ID of the document.
            document (DocumentInDB): The document record to process.
        
        Description:
            This method processes the document asynchronously, updating its status
            and saving the results back to database.
        """
        try:
            temp_path = os.path.join(tempfile.gettempdir(), processing_id)
            
            # Ensure the file exists
            if not os.path.exists(temp_path):
                logger.error(f"Temporary file not found: {temp_path}")
                raise ValueError(f"Temporary file not found: {temp_path}")
                
            # Perform document classification and extraction
            document_type, confidence, parsed_document = await self.contract_manager.classify_document(temp_path)
            
            # If document could not be classified
            if document_type == "unknown" or parsed_document is None:
                document.status = "failed"
                document.error = "Could not classify document or parsing failed"
                await self.db_manager.save_document(document)
                return
            
            # Extract data based on document type
            extracted_data = await self.contract_manager.extract_data(parsed_document, document_type)
            
            # Check if extraction failed
            if isinstance(extracted_data, dict) and "error" in extracted_data:
                logger.warning(f"Extraction failed: {extracted_data['error']}")
                document.status = "failed"
                document.error = extracted_data["error"]
                await self.db_manager.save_document(document)
                return
            
            # Add processing metadata
            extracted_data["processed_at"] = datetime.now().isoformat()
            
            # Update document record
            document.document_type = document_type
            document.confidence = confidence
            document.extracted_data = extracted_data
            document.status = "completed"
            
            # Save updated document to database
            await self.db_manager.save_document(document)
            logger.info(f"Document processing completed and saved for ID: {processing_id}")
        except Exception as e:
            logger.error(f"Error in async processing: {str(e)}")
            document.status = "failed"
            document.error = str(e)
            await self.db_manager.save_document(document)
        finally:
            # Clean up temporary file
            self._cleanup_temp_file(processing_id)

    def _cleanup_temp_file(self, processing_id: str):
        """
        Clean up temporary file after processing.
        
        Args:
            processing_id (str): The processing ID of the document.
        
        Description:
            This method removes the temporary file associated with the processing ID
            to free up resources.
        """
        try:
            temp_file_path = os.path.join(tempfile.gettempdir(), processing_id)
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        except Exception as e:
            logger.error(f"Error cleaning up temp file: {str(e)}")
