"""
API endpoints for managing contract templates.

This module provides endpoints for listing, creating, copying, and deleting contract templates.
It handles both system predefined contracts and user-defined contract templates, allowing users to
create custom contract templates based on predefined contracts or from scratch.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from ...core.config import get_settings
from ...core.logging import logger
from ...services.database_manager import DatabaseManager
from supabase import create_client, Client
from datetime import datetime
import os
import uuid
import re

# Get settings first
settings = get_settings()

# Create Supabase client
try:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # Create admin client with service role key that can bypass RLS
    admin_supabase: Client = create_client(
        settings.SUPABASE_URL, 
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
    
    # Initialize database manager
    db_manager = DatabaseManager(supabase)
except Exception as e:
    logger.error(f"Critical error initializing Supabase client: {e}")
    supabase = None
    admin_supabase = None
    db_manager = None

router = APIRouter(prefix="/contract-templates", tags=["contract_templates"])

class ContractField(BaseModel):
    """
    Contract field definition.
    
    Attributes:
        name (str): The name of the field.
        type (str): The data type of the field.
        description (Optional[str]): Optional description of the field.
    """
    name: str
    type: str
    description: Optional[str] = None

class ContractCopyRequest(BaseModel):
    """
    Request model for copying a system contract.
    
    Attributes:
        template_id (str): The ID of the template to copy.
        customize_fields (Optional[Dict[str, Any]]): Optional customizations for the fields.
        new_name (Optional[str]): Optional new name for the copied contract.
    """
    template_id: str
    customize_fields: Optional[Dict[str, Any]] = None
    new_name: Optional[str] = None

class ContractUploadRequest(BaseModel):
    """
    Request model for uploading a new contract.
    
    Attributes:
        name (str): The name of the new contract.
        document_type (str): The type of document this contract is for.
        fields (Dict[str, Any]): The fields that define the contract structure.
    """
    name: str
    document_type: str
    fields: Dict[str, Any]

def is_valid_email(email: str) -> bool:
    """
    Check if string is a valid email address.
    
    Args:
        email (str): The email address to validate.
        
    Returns:
        bool: True if the email is valid, False otherwise.
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))

async def get_or_create_user(email: str, org_name: Optional[str] = None) -> tuple[str, Optional[str]]:
    """
    Get or create a user and organization based on email.
    
    This function delegates to the DatabaseManager's handle_user_organization method
    to avoid code duplication.
    
    Args:
        email (str): The email address of the user.
        org_name (Optional[str]): Optional organization name.
        
    Returns:
        tuple[str, Optional[str]]: User and organization IDs.
        
    Raises:
        HTTPException: If there is an error creating or retrieving the user.
    """
    try:
        if not db_manager:
            raise Exception("Database manager not initialized")
        
        return await db_manager.handle_user_organization(email, org_name)
    except Exception as e:
        logger.error(f"Error in get_or_create_user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing user information: {str(e)}"
        )

@router.get("/templates")
async def list_templates():
    """
    List all available templates (system contracts) without their fields.
    Only returns basic information like name and ID.
    
    Returns:
        Dict[str, Any]: List of available templates.
        
    Raises:
        HTTPException: If there is an error retrieving the templates.
    """
    try:
        response = supabase.table('system_contracts').select('id,name,created_at').execute()
        return {"message": "Templates retrieved successfully", "data": response.data}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_id}")
async def get_template_details(template_id: str):
    """
    Get detailed information about a specific template, including its fields.
    
    Args:
        template_id (str): The ID of the template to retrieve.
        
    Returns:
        Dict[str, Any]: Detailed template information.
        
    Raises:
        HTTPException: If the template is not found or there is an error retrieving it.
    """
    try:
        response = supabase.table('system_contracts').select('*').eq('id', template_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template details retrieved successfully", "data": response.data[0]}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving template details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contracts")
async def list_user_contracts():
    """
    List all user contracts without their fields.
    Only returns basic information like name and type.
    
    Returns:
        Dict[str, Any]: List of user contracts.
        
    Raises:
        HTTPException: If there is an error retrieving the contracts.
    """
    try:
        response = supabase.table('user_contracts').select('id,name,document_type,created_at,system_contract_id').execute()
        return {"message": "User contracts retrieved successfully", "data": response.data}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving user contracts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contracts/{contract_id}")
async def get_contract_details(contract_id: str):
    """
    Get detailed information about a specific user contract, including its fields.
    
    Args:
        contract_id (str): The ID of the contract to retrieve.
        
    Returns:
        Dict[str, Any]: Detailed contract information.
        
    Raises:
        HTTPException: If the contract is not found or there is an error retrieving it.
    """
    try:
        response = supabase.table('user_contracts').select('*').eq('id', contract_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Contract not found")
        return {"message": "Contract details retrieved successfully", "data": response.data[0]}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving contract details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/contracts/copy-template")
async def copy_template(
    request: ContractCopyRequest,
    user_id: str,
    org_id: Optional[str] = None
):
    """
    Copy a system contract template to create a new user contract.
    Can be customized or copied as-is.
    
    Args:
        request (ContractCopyRequest): The request containing template ID and customizations.
        user_id (str): The ID of the user creating the contract.
        org_id (Optional[str]): Optional organization ID.
        
    Returns:
        Dict[str, Any]: The newly created contract.
        
    Raises:
        HTTPException: If the template is not found or there is an error creating the contract.
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Check if user_id is an email
        if is_valid_email(user_id):
            # Get or create user based on email
            user_id, org_id = await get_or_create_user(user_id, None)
        else:
            # Validate UUID format if not an email
            try:
                uuid.UUID(user_id)
                if org_id:
                    uuid.UUID(org_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid UUID format for user_id or org_id")
            
        # Get template
        template = supabase.table('system_contracts').select('*').eq('id', request.template_id).execute()
        if not template.data:
            raise HTTPException(status_code=404, detail="Template not found")
            
        template_data = template.data[0]
        current_time = datetime.utcnow().isoformat()
        
        # Prepare base fields from template
        fields_dict = template_data['fields'].copy()
        
        # Apply customizations if provided
        if request.customize_fields:
            for field_name, customization in request.customize_fields.items():
                if field_name in fields_dict['properties']:
                    fields_dict['properties'][field_name].update(customization)
        
        # Create new contract
        contract_data = {
            'id': str(uuid.uuid4()),
            'org_id': org_id,
            'user_id': user_id,
            'document_type': request.new_name.lower() if request.new_name else template_data['document_type'],
            'system_contract_id': template_data['id'],
            'name': request.new_name if request.new_name else template_data['name'],
            'fields': fields_dict,
            'version': 1,
            'created_at': current_time,
            'updated_at': current_time,
            'deleted_at': None
        }
        
        result = supabase.table('user_contracts').insert(contract_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create contract from template")
            
        return {
            "message": "Contract created successfully from template",
            "data": result.data[0]
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions with their original status code
        raise he
    except Exception as e:
        logger.error(f"Error creating contract from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/contracts/upload")
async def upload_contract(
    contract: ContractUploadRequest,
    user_id: str,
    org_id: Optional[str] = None
):
    """
    Create a new contract by uploading a custom JSON definition.
    
    Args:
        contract (ContractUploadRequest): The contract definition to upload.
        user_id (str): The ID of the user creating the contract.
        org_id (Optional[str]): Optional organization ID.
        
    Returns:
        Dict[str, Any]: The newly created contract.
        
    Raises:
        HTTPException: If there is an error creating the contract.
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
            
        # Check if user_id is an email
        if is_valid_email(user_id):
            # Get or create user based on email
            user_id, org_id = await get_or_create_user(user_id, None)
        else:
            # Validate UUID format if not an email
            try:
                uuid.UUID(user_id)
                if org_id:
                    uuid.UUID(org_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid UUID format for user_id or org_id")
            
        # Validate fields structure
        if not isinstance(contract.fields, dict) or 'properties' not in contract.fields:
            raise HTTPException(status_code=400, detail="Invalid fields format. Must be a JSON Schema object with 'properties'")
            
        current_time = datetime.utcnow().isoformat()
        
        contract_data = {
            'id': str(uuid.uuid4()),
            'org_id': org_id,
            'user_id': user_id,
            'document_type': contract.document_type.lower(),
            'name': contract.name,
            'fields': contract.fields,
            'version': 1,
            'created_at': current_time,
            'updated_at': current_time,
            'deleted_at': None
        }
        
        result = supabase.table('user_contracts').insert(contract_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create contract from JSON")
            
        return {
            "message": "Contract created successfully from JSON",
            "data": result.data[0]
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions with their original status code
        raise he
    except Exception as e:
        logger.error(f"Error creating contract from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str):
    """
    Delete a user contract.
    
    Args:
        contract_id (str): The ID of the contract to delete.
        
    Returns:
        Dict[str, str]: Success message.
        
    Raises:
        HTTPException: If the contract is not found or there is an error deleting it.
    """
    try:
        existing = supabase.table('user_contracts').select('*').eq('id', contract_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Contract not found")
            
        response = supabase.table('user_contracts').delete().eq('id', contract_id).execute()
        return {"message": "Contract deleted successfully", "data": response.data}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting contract: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))