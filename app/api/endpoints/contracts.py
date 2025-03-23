"""
API endpoints for contract management.

This module provides endpoints for managing contracts in the Doculens application.
It includes functionality for listing predefined contracts, retrieving the active contract,
and selecting a predefined contract as the active one.

The module interacts with the ContractManager service to perform these operations,
which handles the business logic for contract management, including database operations
and contract validation.
"""

from fastapi import APIRouter, HTTPException, Response, status
from typing import Dict, Any, List
from pydantic import BaseModel
from app.services.contract_manager import ContractManager
from app.core.database import get_supabase_client

router = APIRouter()
contract_service = ContractManager(get_supabase_client())

class ContractResponse(BaseModel):
    """
    Response model for contract data.
    
    Attributes:
        id (str): Unique identifier for the contract.
        contract_data (Dict[str, Any]): Contract data and metadata.
        created_at (str): Timestamp when the contract was created.
    """
    id: str
    contract_data: Dict[str, Any]
    created_at: str

@router.get("/predefined", response_model=List[ContractResponse])
async def list_predefined_contracts(response: Response):
    """
    List all available contracts.
    
    This endpoint retrieves all contracts from the system_contracts table.
    These contracts can be used as a basis for creating custom contracts.
    
    Returns:
        List[ContractResponse]: A list of contracts.
        
    Raises:
        HTTPException: If there is an error retrieving the contracts.
    """
    try:
        contracts = contract_service.list_predefined_contracts()
        return contracts
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}

@router.get("/active")
async def get_active_contract():
    """
    Get the currently active contract.
    
    This endpoint retrieves the currently active contract for the system.
    The active contract is used as the default for document processing.
    
    Returns:
        Dict[str, Any]: The active contract data.
        
    Raises:
        HTTPException: If no active contract is found or there is an error retrieving it.
    """
    try:
        contract = contract_service.get_active_contract()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active contract found"
            )
        return contract
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/select/{contract_id}")
async def select_predefined_contract(contract_id: str):
    """
    Select a contract as the active contract.
    
    This endpoint sets a specified contract from the system_contracts table
    as the active contract for the system. The active contract will be used
    as the default for document processing.
    
    Args:
        contract_id (str): The ID of the contract to set as active.
        
    Returns:
        Dict[str, Any]: The newly activated contract data.
        
    Raises:
        HTTPException: If the contract is not found or there is an error setting it as active.
    """
    try:
        contract = contract_service.select_predefined_contract(contract_id)
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract with ID {contract_id} not found"
            )
        return contract
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
