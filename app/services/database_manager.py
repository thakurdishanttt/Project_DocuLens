"""
Database management service.

This module provides a DatabaseManager class for interacting with the Supabase database.
It handles operations related to contracts, documents, and user data, providing a clean
interface for database operations while handling row-level security and admin operations.
"""

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions
from ..core.logging import logger
from ..core.config import get_settings
from typing import Optional, Dict, Any
from datetime import datetime
from typing import Tuple

settings = get_settings()

class DatabaseManager:
    """
    Database manager for Supabase operations.
    
    This class provides methods for interacting with the Supabase database,
    handling both regular client operations and admin operations using service role
    credentials when available.
    
    Attributes:
        supabase (Client): Regular Supabase client instance.
        admin_client (Client): Supabase client with admin privileges when available.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the DatabaseManager with a Supabase client.
        
        Args:
            supabase_client (Client): Supabase client instance.
            
        Raises:
            Exception: If there is an error initializing the DatabaseManager.
        """
        try:
            self.supabase = supabase_client
            
            # Create a service role client for admin operations
            if settings.SUPABASE_SERVICE_ROLE_KEY:
                options = ClientOptions(
                    schema="public",
                    headers={"apiKey": settings.SUPABASE_SERVICE_ROLE_KEY},
                    auto_refresh_token=False,
                    persist_session=False
                )
                
                self.admin_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY,
                    options
                )
            else:
                self.admin_client = self.supabase
                
            self._setup_rls_policies()
            
        except Exception as e:
            logger.error(f"Error initializing DatabaseManager: {str(e)}")
            raise

    def _setup_rls_policies(self):
        """
        Set up row-level security policies for the database.
        
        This method is responsible for configuring row-level security policies,
        but currently skips actual policy setup as it requires database admin privileges.
        Instead, it logs warnings and uses the admin client for operations that would
        otherwise be blocked by RLS.
        
        Raises:
            Exception: If there is an error setting up RLS policies.
        """
        try:
            logger.warning("Skipping RLS policy setup - this requires database admin privileges")
            logger.warning("Please ensure your database has appropriate RLS policies configured")
            
            # Instead of trying to update RLS policies, we'll use the admin client for operations
            # that would otherwise be blocked by RLS
        except Exception as e:
            logger.error(f"Error in setup_rls_policies: {str(e)}")
            # Continue anyway as the application can still function

    async def load_user_contracts(self):
        """
        Load contracts from user_contracts table.
        
        Returns:
            List[Dict]: List of user contracts.
            
        Raises:
            Exception: If there is an error loading user contracts.
        """
        try:
            user_contracts = self.supabase.table('user_contracts').select('*').execute()
            return user_contracts.data if user_contracts.data else []
        except Exception as e:
            logger.error(f"Error loading user contracts: {str(e)}")
            raise

    async def get_document_by_id(self, document_id: str, org_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            document_id (str): ID of the document to retrieve.
            org_id (str, optional): Organization ID to filter by.
        
        Returns:
            Dict[str, Any]: Document data if found, otherwise None.
            
        Raises:
            Exception: If there is an error getting the document by ID.
        """
        try:
            # Try with regular client first
            query = self.supabase.table('documents').select('*').eq('id', document_id)
            response = query.execute()
            
            # If not found with regular client, try admin client
            if not response.data and hasattr(self, 'admin_client'):
                query = self.admin_client.table('documents').select('*').eq('id', document_id)
                response = query.execute()
            
            if not response.data:
                return None
                
            document = response.data[0]
            
            # If org_id is provided, check if document's org_id matches or is null
            if org_id:
                doc_org_id = document.get('org_id')
                if doc_org_id is not None and doc_org_id != org_id:
                    return None
            
            return document
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None

    async def upsert_document(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert or update a document.
        
        Args:
            data (Dict[str, Any]): Document data to insert or update.
        
        Returns:
            Dict[str, Any]: Inserted or updated document data if successful, otherwise None.
            
        Raises:
            Exception: If there is an error upserting the document.
        """
        try:
            response = self.supabase.table('documents').upsert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error upserting document: {str(e)}")
            return None

    def get_user_contracts(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user contracts for a specific organization.
        
        Args:
            org_id (str, optional): Organization ID to filter contracts by. Defaults to None.
        
        Returns:
            Dict[str, Any]: Dictionary containing contract fields.
            
        Raises:
            Exception: If there is an error getting user contracts.
        """
        try:
            query = self.supabase.table('user_contracts')
            if org_id:
                query = query.eq('org_id', org_id)
            
            response = query.select('*').execute()
            
            if not response.data:
                logger.info("No user contracts found")
                return {}
            
            contracts = {}
            for contract in response.data:
                if 'document_type' in contract and 'fields' in contract:
                    contracts[contract['document_type']] = contract['fields']
            
            logger.info(f"Successfully retrieved {len(contracts)} user contracts")
            return contracts
            
        except Exception as e:
            logger.error(f"Error getting user contracts: {str(e)}")
            return {}

    def get_system_contracts(self) -> Dict[str, Any]:
        """
        Get system-defined contracts from the system_contracts table.
        
        Returns:
            Dict[str, Any]: Dictionary containing contract fields.
            
        Raises:
            Exception: If there is an error getting system contracts.
        """
        try:
            response = self.supabase.table('system_contracts').select('*').execute()
            
            if not response.data:
                logger.info("No system contracts found")
                return {}
            
            contracts = {}
            for contract in response.data:
                if 'name' in contract and 'fields' in contract:
                    contracts[contract['name'].lower()] = contract['fields']
            
            logger.info(f"Successfully retrieved {len(contracts)} system contracts")
            return contracts
            
        except Exception as e:
            logger.error(f"Error getting system contracts: {str(e)}")
            return {}

    def insert_user_contract(self, contract_data: Dict[str, Any]) -> bool:
        """
        Insert a new contract into the user_contracts table.
        
        Args:
            contract_data (Dict[str, Any]): Contract data including document_type, schema, name, and description.
        
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            Exception: If there is an error inserting the contract.
        """
        try:
            response = self.supabase.table('user_contracts').insert(contract_data).execute()
            if response.data:
                logger.info(f"Successfully inserted contract: {contract_data['document_type']}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error inserting contract: {str(e)}")
            return False

    async def save_document(self, document) -> bool:
        """
        Save a document to the documents table.
        
        Args:
            document: The document object to save.
            
        Returns:
            bool: True if the save was successful, False otherwise.
        """
        try:
            # Use admin client to bypass RLS
            client = self.admin_client if hasattr(self, 'admin_client') else self.supabase
            
            # Check if document exists
            check_response = client.table('documents').select('*').eq('id', document.document_id).execute()
            
            if not check_response.data:
                # Document doesn't exist, create it
                insert_data = {
                    'id': document.document_id,
                    'file_name': document.filename,
                    'document_type': document.document_type,
                    'confidence': document.confidence,
                    'extracted_data': document.extracted_data,
                    'status': document.status,
                    'error': document.error,
                    'created_at': 'NOW()',
                    'updated_at': 'NOW()'
                }
                
                if hasattr(document, 'user_id') and document.user_id:
                    insert_data['user_id'] = document.user_id
                if hasattr(document, 'org_id') and document.org_id:
                    insert_data['org_id'] = document.org_id
                    
                response = client.table('documents').insert(insert_data).execute()
            else:
                # Document exists, update it
                update_data = {
                    'document_type': document.document_type,
                    'confidence': document.confidence,
                    'extracted_data': document.extracted_data,
                    'status': document.status,
                    'error': document.error,
                    'updated_at': 'NOW()'
                }
                
                if hasattr(document, 'user_id') and document.user_id:
                    update_data['user_id'] = document.user_id
                if hasattr(document, 'org_id') and document.org_id:
                    update_data['org_id'] = document.org_id
                    
                response = client.table('documents').update(update_data).eq('id', document.document_id).execute()
            
            if not response.data:
                logger.error(f"Failed to save document {document.document_id}")
                return False
                
            logger.info(f"Successfully saved document {document.document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            return False
            
    async def save_extracted_data(self, document_id: str, extracted_data: dict, user_id: str = None, org_id: str = None) -> bool:
        """
        Save extracted data to the documents table.
        
        Args:
            document_id (str): ID of the document.
            extracted_data (dict): Extracted data to save.
            user_id (str, optional): User ID to associate with the document.
            org_id (str, optional): Organization ID to associate with the document.
            
        Returns:
            bool: Result of the save operation.
        """
        try:
            # Use admin client to bypass RLS
            client = self.admin_client if hasattr(self, 'admin_client') else self.supabase
            
            # Check if document exists
            check_response = client.table('documents').select('*').eq('id', document_id).execute()
            
            if not check_response.data:
                # Document doesn't exist, create it
                insert_data = {
                    'id': document_id,
                    'extracted_data': extracted_data,
                    'status': 'processed',
                    'file_name': extracted_data.get('filename', 'unknown'),
                    'file_url': extracted_data.get('file_url', ''),
                    'document_type': extracted_data.get('document_type', 'unknown'),
                    'confidence': extracted_data.get('confidence', 0.0),
                    'created_at': 'NOW()',
                    'updated_at': 'NOW()'
                }
                
                if user_id:
                    insert_data['user_id'] = user_id
                if org_id:
                    insert_data['org_id'] = org_id
                    
                response = client.table('documents').insert(insert_data).execute()
            else:
                # Document exists, update it
                update_data = {
                    'extracted_data': extracted_data,
                    'status': 'processed',
                    'updated_at': 'NOW()'
                }
                
                if user_id:
                    update_data['user_id'] = user_id
                if org_id:
                    update_data['org_id'] = org_id
                    
                response = client.table('documents').update(update_data).eq('id', document_id).execute()
            
            if not response.data:
                logger.error(f"Failed to save extracted data for document {document_id}")
                return False
                
            logger.info(f"Successfully saved extracted data for document {document_id}")
            
            # Create audit log entry
            try:
                audit_data = {
                    'org_id': org_id or response.data[0].get('org_id'),
                    'user_id': user_id or response.data[0].get('user_id'),
                    'action': 'EXTRACT_DATA',
                    'entity_id': document_id,
                    'entity_type': 'document',
                    'description': 'Extracted data from document'
                }
                
                client.table('audit_logs').insert(audit_data).execute()
            except Exception as e:
                logger.warning(f"Failed to create audit log for document {document_id}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving extracted data: {str(e)}")
            
            # Update document status to failed
            try:
                client.table('documents').update({
                    'status': 'failed',
                    'updated_at': 'NOW()'
                }).eq('id', document_id).execute()
            except Exception as update_error:
                logger.error(f"Failed to update document status: {str(update_error)}")
            
            return False

    async def handle_user_organization(self, email: str, org_name: str = None) -> Tuple[str, str]:
        """
        Handle user and organization creation/retrieval.
        
        Args:
            email (str): Email of the user.
            org_name (str, optional): Name of the organization.
            
        Returns:
            Tuple[str, str]: A tuple of (user_id, org_id).
        """
        try:
            org_id = None
            # Use admin client
            client = self.admin_client
            
            if org_name:
                org_response = client.table('organizations').select('*').eq('name', org_name).execute()
                org_data = org_response.data

                if not org_data:
                    org_data = client.table('organizations').insert({
                        'name': org_name,
                        'created_at': datetime.now().isoformat()
                    }).execute().data
                
                org_id = org_data[0]['id'] if org_data else None

            user_response = client.table('users').select('*').eq('email', email).execute()
            user_data = user_response.data

            if not user_data:
                user_data = client.table('users').insert({
                    'email': email,
                    'display_name': email.split('@')[0],
                    'org_id': org_id,
                    'role': 'user',
                    'created_at': datetime.now().isoformat()
                }).execute().data
            elif org_id and user_data[0]['org_id'] != org_id:
                # Update org_id without updated_at since it doesn't exist in the table
                user_data = client.table('users').update({
                    'org_id': org_id
                }).eq('id', user_data[0]['id']).execute().data

            user_id = user_data[0]['id'] if user_data else None

            if not user_id:
                raise ValueError("Failed to create/retrieve user")

            return user_id, org_id

        except Exception as e:
            logger.error(f"Error handling user/organization: {str(e)}")
            raise

    def update_user_contract(self, document_type: str, fields: Dict[str, Any], org_id: Optional[str] = None) -> bool:
        """
        Update an existing contract in the user_contracts table.
        
        Args:
            document_type (str): Type of document to update contract for.
            fields (Dict[str, Any]): Updated contract fields.
            org_id (str, optional): Organization ID to filter by. Defaults to None.
        
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            Exception: If there is an error updating the contract.
        """
        try:
            query = self.supabase.table('user_contracts')
            if org_id:
                query = query.eq('org_id', org_id)
            query = query.eq('document_type', document_type)
            
            response = query.update({'fields': fields}).execute()
            if response.data:
                logger.info(f"Successfully updated contract for document type: {document_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating contract: {str(e)}")
            return False
