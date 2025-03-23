"""
Contract management service for document classification and matching.

This module provides the ContractManager class, which is responsible for managing
contracts and document processing in the Doculens application. It serves as a central
component that coordinates various document-related operations.

Key functionalities:
1. Document Classification: Uses AI models to determine the type of uploaded documents
2. Contract Matching: Matches documents against predefined and user-defined contracts
3. Data Extraction: Extracts structured data from documents based on contract schemas
4. Schema Management: Validates and processes contract schemas for data extraction
5. Contract Operations: Manages predefined contracts and user-defined contracts

The ContractManager integrates with several other services:
- DatabaseManager: For database operations related to contracts and documents
- DocumentClassifier: For classifying documents using AI models
- DocumentParser: For parsing document content
- DocumentExtractor: For extracting data from documents based on schemas

This module centralizes document processing logic and provides a consistent interface
for the rest of the application to interact with document-related functionality.
"""

# Standard library imports
import json
import os
import tempfile
import uuid
import random
import re
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Tuple, Union, Optional

# Third-party imports
from dotenv import load_dotenv
from fastapi import UploadFile
from supabase import Client
from pydantic import BaseModel, create_model, Field
import google.generativeai as genai
from llama_parse import LlamaParse
from supabase.lib.client_options import ClientOptions

# Local imports
from ..core.logging import logger
from ..core.config import get_settings
from ..utils.ai_config import GEMINI_GENERATION_CONFIG, GEMINI_SAFETY_SETTINGS
from ..utils.string_utils import normalize_document_type, generate_case_variations
from .database_manager import DatabaseManager
from .llama_parser import DocumentParser
from .llama_extractor import DocumentExtractor
from .gemini_classifier import DocumentClassifier

# Load environment variables
load_dotenv()
settings = get_settings()

class ContractManager:
    """
    A class for managing contracts and document processing.
    
    This class provides methods to classify documents, match them against contracts,
    extract data from documents, and manage contract schemas in the database.
    
    Attributes:
        supabase (Client): The Supabase client for database operations.
        org_id (str): The organization ID for filtering contracts.
        db_manager (DatabaseManager): Manager for database operations.
        admin_client (Client): Admin client for database operations.
        parser (DocumentParser): Parser for document content extraction.
        extractor (DocumentExtractor): Extractor for structured data extraction.
        classifier (DocumentClassifier): Classifier for document classification.
        user_contracts (Dict[str, Any]): User contracts stored in an instance variable.
    """
    def __init__(self, supabase_client: Client, org_id: str = None):
        """
        Initialize ContractManager with Supabase client.
        
        Args:
            supabase_client (Client): Supabase client for database operations.
            org_id (str, optional): Organization ID for filtering contracts.
            
        Raises:
            Exception: If initialization of any component fails.
        """
        try:
            self.org_id = org_id
            self.supabase = supabase_client
            
            # Initialize database manager
            self.db_manager = DatabaseManager(supabase_client)
            
            # Use the admin_client from database_manager instead of creating a new one
            self.admin_client = self.db_manager.admin_client
            
            # Initialize document parser with API key
            try:
                self.parser = DocumentParser()
            except Exception as e:
                logger.error(f"Failed to initialize DocumentParser: {str(e)}")
                raise
            
            # Initialize document extractor
            try:
                self.extractor = DocumentExtractor()
            except Exception as e:
                logger.error(f"Failed to initialize DocumentExtractor: {str(e)}")
                raise
            
            # Initialize document classifier
            try:
                self.classifier = DocumentClassifier()
            except Exception as e:
                logger.error(f"Failed to initialize DocumentClassifier: {str(e)}")
                raise

            # Store user contracts once
            self.user_contracts = self.db_manager.get_user_contracts(self.org_id)

        except Exception as e:
            logger.error(f"Error initializing ContractManager: {str(e)}")
            raise

    def load_contracts(self):
        """
        Load contracts from user_contracts table only.
        
        This method is used to preload contracts for faster access during document processing.
        
        Returns:
            Dict[str, Any]: Dictionary of loaded contracts.
        """
        try:
            # Clear existing contracts
            self.user_contracts = self.db_manager.get_user_contracts(self.org_id)
            
            logger.info(f"Loaded {len(self.user_contracts)} user contracts")
            return self.user_contracts
        except Exception as e:
            logger.error(f"Error loading contracts: {str(e)}")
            return {}

    async def classify_document(self, file: Union[str, UploadFile]) -> Tuple[str, float, Any]:
        """
        Classify the document using Gemini model dynamically.
        
        Args:
            file (Union[str, UploadFile]): Either a file path (str) or an UploadFile object
            
        Returns:
            Tuple containing:
            - document_type (str): Type of document
            - confidence (float): Classification confidence score
            - parsed_document (Any): Parsed document content
        """
        try:
            # Handle both file path and UploadFile
            if isinstance(file, str):
                # For file paths, create a mock UploadFile
                filename = os.path.basename(file)
                documents = await self.parser.parse_document(file)
            else:
                # For UploadFile objects
                filename = file.filename
                documents = await self.parser.parse_document(file)
            
            if not documents or len(documents) == 0:
                logger.warning(f"No content extracted from document: {filename}")
                return "unknown", 0.0, None

            # Combine text from all pages
            document_text = "\n\n".join(doc.text for doc in documents if doc.text)
            if not document_text:
                logger.warning("Empty document content")
                return "unknown", 0.0, None

            # Get user contract types for classification
            classifications = list(self.user_contracts.keys())
            
            if not classifications:
                logger.warning("No contract types available for classification")
                # Use the classifier without specific classifications
                doc_type, confidence, _ = await self.classifier.classify_document(document_text, [])
            else:
                # Use the classifier with available classifications
                doc_type, confidence, _ = await self.classifier.classify_document(document_text, classifications)
            
            # Check if document type is recognized
            if doc_type == "unknown" or doc_type not in classifications:
                logger.info(f"Document type '{doc_type}' not found in available contracts")
                return doc_type, confidence, documents
            
            logger.info(f"Successfully classified document as {doc_type} with confidence {confidence}")
            return doc_type, confidence, documents

        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            return "unknown", 0.0, None

    async def create_or_get_agent(self, document_type: str, model_class) -> Any:
        """
        Create or get an existing extraction agent for a document type.
        
        Args:
            document_type (str): Type of document to create agent for.
            model_class: The model class to use for extraction.
            
        Returns:
            Any: The extraction agent.
        """
        try:
            # Generate a unique agent name using timestamp and random suffix
            agent_name = f"{document_type}-{int(time.time())}-{random.randint(1000, 9999)}"
            
            # Create extraction configuration
            config = {
                "extraction_mode": "ACCURATE",
                "extraction_target": "PER_DOC",
                "handle_missing": True,
                "system_prompt": (
                    "You are an expert at extracting information from resumes and documents. "
                    "Your task is to carefully analyze the document and extract all relevant information "
                    "according to the provided schema. Pay special attention to contact information, "
                    "work experience, education, and skills. Format lists as arrays and ensure all "
                    "extracted data matches the schema requirements."
                )
            }
            
            # Create a new agent with configuration
            agent = self.extractor.create_agent(
                name=agent_name,
                data_schema=model_class,
                config=config
            )
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise

    async def extract_data(self, parsed_documents, document_type: str) -> Dict[str, Any]:
        """
        Extract data from document using document extractor.
        
        Args:
            parsed_documents: The parsed document content.
            document_type (str): Type of document for extraction.
            
        Returns:
            Dict[str, Any]: Extracted data from the document.
        """
        try:
            # Get the contract for the document type
            contract = await self.get_document_contract(document_type)
            if not contract:
                logger.error(f"No contract found for document type: {document_type}")
                return {"error": "unknown document, please create your contract first"}

            # Extract data using the contract
            try:
                # Combine text from all pages if parsed_documents is a list
                if isinstance(parsed_documents, list):
                    document_text = "\n\n".join(doc.text for doc in parsed_documents if hasattr(doc, 'text') and doc.text)
                else:
                    document_text = parsed_documents.text if hasattr(parsed_documents, 'text') else str(parsed_documents)

                if not document_text.strip():
                    logger.error("Empty document text")
                    return {"error": "Empty document content"}

                extracted_data = await self.extractor.extract_data(document_text, contract)
                if not extracted_data:
                    logger.warning("No data extracted from document")
                    return {"error": "Failed to extract data from document"}
                    
                return extracted_data

            except Exception as e:
                logger.error(f"Error during data extraction: {str(e)}")
                return {"error": f"Error during data extraction: {str(e)}"}

        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            return {"error": f"Error extracting data: {str(e)}"}

    async def get_document_contract(self, document_type: str, org_id: str = None) -> Dict[str, Any]:
        """
        Get contract for a document type from user_contracts table only.
        
        If the document type is not found in user_contracts, return an empty dictionary.
        
        Args:
            document_type (str): Type of document to get contract for.
            org_id (str, optional): Organization ID to filter contracts by.
            
        Returns:
            Dict[str, Any]: Document contract if found, empty dict otherwise.
        """
        try:
            # Use stored user contracts instead of calling get_user_contracts multiple times
            if document_type in self.user_contracts:
                contract = self.user_contracts[document_type]
                # Ensure contract is properly formatted
                if isinstance(contract, list):
                    contract = self._convert_contract_list_to_dict(contract, document_type)
                return contract

            # Try case-insensitive match
            for contract_type in self.user_contracts:
                if document_type.lower() == contract_type.lower():
                    contract = self.user_contracts[contract_type]
                    # Ensure contract is properly formatted
                    if isinstance(contract, list):
                        contract = self._convert_contract_list_to_dict(contract, contract_type)
                    return contract

            # If exact match not found, try normalized variations
            normalized_doc_type = normalize_document_type(document_type)

            # Try the standard normalization approach
            for contract_type in self.user_contracts:
                normalized_contract_type = normalize_document_type(contract_type)
                if normalized_doc_type == normalized_contract_type:
                    contract = self.user_contracts[contract_type]
                    # Ensure contract is properly formatted
                    if isinstance(contract, list):
                        contract = self._convert_contract_list_to_dict(contract, contract_type)
                    return contract

            # If no contract is found, return an empty dictionary
            logger.warning(f"No contract found for document type: {document_type} in user_contracts")
            return {}
        
        except Exception as e:
            logger.error(f"Error getting document contract: {str(e)}")
            return {}

    def validate_contract(self, contract_data: Dict[str, Any], document_type: str = None) -> Tuple[bool, str]:
        """
        Validate contract data structure.
        
        Ensures that the contract data has the required structure and fields.
        
        Args:
            contract_data (Dict[str, Any]): Contract data to validate.
            document_type (str, optional): Document type for context in error messages.
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            if not contract_data:
                return False, "Contract data is empty"
                
            # Handle both array and object formats
            schema_data = contract_data

            # Convert array format to object format
            if isinstance(schema_data, list):
                schema_data = self._convert_contract_list_to_dict(schema_data, document_type)

            # Validate required schema structure
            if not isinstance(schema_data, dict):
                return False, "Contract data must be a dictionary or a list of field definitions"
                
            if "properties" not in schema_data and not document_type:
                return False, "Contract must have a 'properties' field defining the data structure"
                
            # For object format, validate properties
            if "properties" in schema_data:
                properties = schema_data["properties"]
                if not isinstance(properties, dict):
                    return False, "Contract properties must be a dictionary"
                    
                # Validate each property
                for field_name, field_def in properties.items():
                    if not isinstance(field_def, dict):
                        return False, f"Field definition for '{field_name}' must be a dictionary"
                        
                    if "type" not in field_def:
                        return False, f"Field '{field_name}' must have a 'type' property"
                        
            return True, ""
        except Exception as e:
            return False, f"Error validating contract: {str(e)}"

    def _convert_contract_list_to_dict(self, contract_list, document_type):
        """
        Convert a contract from list format to dictionary format.
        
        Args:
            contract_list (List): Contract in list format.
            document_type (str): Document type for logging.
            
        Returns:
            Dict[str, Any]: Contract in dictionary format.
        """
        contract_dict = {
            "type": "object",
            "properties": {}
        }
        
        for field in contract_list:
            if isinstance(field, dict) and 'name' in field:
                field_name = field['name']
                field_type = field.get('type', 'string')
                field_desc = field.get('description', f"Extract the {field_name}")
                
                contract_dict["properties"][field_name] = {
                    "type": field_type,
                    "description": field_desc
                }
        
        return contract_dict

    def list_contract_templates(self) -> List[Dict[str, Any]]:
        """
        List all available contract templates from the system_contracts table.
        
        These templates serve as predefined contract structures that can be used
        as a basis for creating custom contracts.
        
        Returns:
            List[Dict[str, Any]]: A list of contract templates with their metadata.
            
        Raises:
            Exception: If there is an error retrieving the templates.
        """
        try:
            # Get system contracts from database manager
            system_contracts = self.db_manager.get_system_contracts()
            
            # Format the response
            contracts = []
            for contract_id, contract_data in system_contracts.items():
                contracts.append({
                    "id": contract_id,
                    "contract_data": contract_data,
                    "created_at": datetime.now().isoformat()  # Using current time as creation time is not stored
                })
            
            return contracts
        except Exception as e:
            logger.error(f"Error listing contract templates: {str(e)}")
            raise

    def get_active_contract_template(self) -> Dict[str, Any]:
        """
        Get the currently active contract template for the system.
        
        The active contract template is used as the default for document processing.
        
        Returns:
            Dict[str, Any]: The active contract template data if found, None otherwise.
            
        Raises:
            Exception: If there is an error retrieving the active contract template.
        """
        try:
            # Query the active_contract table
            response = self.supabase.table('active_contract').select('*').execute()
            
            if not response.data:
                return None
                
            active_contract = response.data[0]
            contract_id = active_contract.get('contract_id')
            
            if not contract_id:
                return None
                
            # Get the contract details
            contract_response = self.supabase.table('system_contracts').select('*').eq('id', contract_id).execute()
            
            if not contract_response.data:
                return None
                
            return {
                "id": contract_id,
                "contract_data": contract_response.data[0],
                "created_at": active_contract.get('created_at', datetime.now().isoformat())
            }
        except Exception as e:
            logger.error(f"Error getting active contract template: {str(e)}")
            raise

    def select_contract_template(self, contract_id: str) -> Dict[str, Any]:
        """
        Select a contract template as the active contract.
        
        This method sets a specified template from the system_contracts table
        as the active contract for the system. The active contract will be used
        as the default for document processing.
        
        Args:
            contract_id (str): The ID of the contract template to set as active.
            
        Returns:
            Dict[str, Any]: The newly activated contract template data if successful, None otherwise.
            
        Raises:
            Exception: If there is an error setting the active contract template.
        """
        try:
            # Check if the contract template exists
            contract_response = self.supabase.table('system_contracts').select('*').eq('id', contract_id).execute()
            
            if not contract_response.data:
                return None
                
            # Update or insert the active contract
            active_response = self.supabase.table('active_contract').select('*').execute()
            
            if active_response.data:
                # Update existing record
                self.supabase.table('active_contract').update({
                    'contract_id': contract_id,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', active_response.data[0]['id']).execute()
            else:
                # Insert new record
                self.supabase.table('active_contract').insert({
                    'contract_id': contract_id,
                    'created_at': datetime.now().isoformat()
                }).execute()
                
            return {
                "id": contract_id,
                "contract_data": contract_response.data[0],
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error selecting contract template: {str(e)}")
            raise