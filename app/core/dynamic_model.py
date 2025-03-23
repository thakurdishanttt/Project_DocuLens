"""
Dynamic model generation utilities.

This module provides functionality to dynamically create Pydantic models from JSON schemas.
It allows for flexible model creation at runtime based on schema definitions, which is
particularly useful for handling varying document structures and contract schemas.
"""

from typing import Dict, Any
from pydantic import BaseModel, create_model

class DynamicModelFactory:
    """
    Factory class for dynamically creating Pydantic model classes from JSON schemas.
    
    This class provides static methods to generate Pydantic model classes at runtime
    based on JSON schema definitions, allowing for flexible data validation and
    serialization of dynamically structured data.
    """
    
    @staticmethod
    def create_model_class(model_name: str, schema: Dict[str, Any]) -> type[BaseModel]:
        """
        Create a Pydantic model class dynamically from a JSON schema.
        
        Args:
            model_name (str): Name of the model class to create
            schema (Dict[str, Any]): JSON schema definition
            
        Returns:
            type[BaseModel]: Generated Pydantic model class
            
        Raises:
            ValueError: If the schema is invalid or missing required properties
        """
        if not schema or "properties" not in schema:
            raise ValueError("Invalid schema - must contain 'properties'")
            
        # Extract required fields
        required_fields = schema.get("required", [])
        
        # Build field definitions
        fields = {}
        for field_name, field_schema in schema["properties"].items():
            field_type = DynamicModelFactory._get_field_type(field_schema["type"])
            is_required = field_name in required_fields
            
            # If field is required, use the type directly
            # If optional, wrap in Optional
            if is_required:
                fields[field_name] = (field_type, ...)
            else:
                fields[field_name] = (field_type, None)
                
        # Create and return the model class
        return create_model(model_name, **fields)
    
    @staticmethod
    def _get_field_type(json_type: str) -> type:
        """
        Map JSON schema types to Python types.
        
        Args:
            json_type (str): JSON schema type name
            
        Returns:
            type: Corresponding Python type
        """
        type_mapping = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        return type_mapping.get(json_type, str)  # Default to str if type unknown
