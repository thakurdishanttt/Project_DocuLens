"""
Document data extraction service using LlamaExtract.

This module provides functionality to extract structured data from document text
using the LlamaExtract API. It handles the creation of extraction agents based on
provided schemas and manages the extraction process.
"""

from llama_extract import LlamaExtract
from ..core.logging import logger
from ..core.config import get_settings
from typing import Dict, Any

settings = get_settings()

class DocumentExtractor:
    """
    Document data extractor using LlamaExtract.
    
    This class provides methods to extract structured data from document text
    based on provided schemas using the LlamaExtract API.
    
    Attributes:
        extractor (LlamaExtract): Initialized LlamaExtract instance.
    """
    
    def __init__(self):
        """
        Initialize the DocumentExtractor with a LlamaExtract instance.
        
        Raises:
            Exception: If there is an error initializing LlamaExtract.
        """
        try:
            self.extractor = LlamaExtract(api_key=settings.LLAMA_PARSE_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize LlamaExtract: {str(e)}")
            raise

    async def extract_data(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from text using LlamaExtract.
        
        Args:
            text (str): The document text to extract data from.
            schema (Dict[str, Any]): Schema defining the structure of data to extract.
                Can be either a dictionary with properties or a list of field definitions.
                
        Returns:
            Dict[str, Any]: Extracted data as a dictionary. Returns an empty dictionary
            if extraction fails or no data is found.
            
        Notes:
            This method creates a temporary file containing the text for processing
            and cleans it up after extraction is complete.
        """
        try:
            # Ensure schema is a dictionary
            if isinstance(schema, list):
                schema_dict = {"type": "object", "properties": {}}
                for item in schema:
                    if isinstance(item, dict) and 'name' in item and 'type' in item:
                        schema_dict["properties"][item['name']] = {
                            "type": item['type'],
                            "description": item.get('description', '')
                        }
                schema = schema_dict
            
            # Create extraction schema
            extraction_schema = {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
            
            # Create an extraction agent with the schema
            schema_hash = hash(str(extraction_schema))
            agent_name = f"extraction-agent-{schema_hash}"
            
            try:
                # Try to get existing agent first
                agent = self.extractor.get_agent(agent_name)
                logger.info(f"Using existing extraction agent: {agent_name}")
            except Exception:
                import time
                unique_name = f"extraction-agent-{int(time.time() * 1000)}"
                try:
                    agent = self.extractor.create_agent(
                        name=unique_name,
                        data_schema=extraction_schema
                    )
                    logger.info(f"Created new extraction agent: {unique_name}")
                except Exception as e:
                    logger.error(f"Failed to create extraction agent: {str(e)}")
                    return {}
            
            # Use the agent to extract data from the text
            # Create a temporary file with the text
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(text)
                temp_path = temp_file.name
            
            # Extract data from the temporary file
            result = agent.extract(temp_path)
            
            # Clean up the temporary file
            import os
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")
            
            if not result or not hasattr(result, 'data'):
                logger.warning("No data extracted from document")
                return {}
                
            logger.info("Successfully extracted data")
            return result.data
            
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            return {}
