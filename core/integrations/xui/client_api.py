"""
API wrapper for managing XUI clients using the internal SDK.
"""

import logging
from typing import List, Optional, Dict, Any
import uuid # For generating client UUID if needed
import httpx # Import httpx exceptions

# Import base and custom exceptions
from .base import BaseApi
from .exceptions import XuiOperationError, XuiNotFoundError, XuiValidationError, XuiConnectionError

# Using the vendored SDK with full path for Pydantic models etc.
from core.integrations.xui_sdk.py3xui.py3xui.client import (
    Client as SdkClient
)
# Removed import of non-existent SDK exceptions

# We might need DB models later if mapping happens here, but ideally in Service layer
# from db.models.client_account import ClientAccount

logger = logging.getLogger(__name__)

# --- Helper functions for mapping (Similar to InboundApi) --- 

def _map_sdk_client_to_dict(sdk_client: SdkClient) -> Dict[str, Any]:
    """Maps an SDK Client object to a dictionary (simple mapping)."""
    if not sdk_client:
        return {}
    if hasattr(sdk_client, 'model_dump'):
        return sdk_client.model_dump(exclude_unset=True) # Exclude unset to avoid sending nulls
    elif isinstance(sdk_client, dict):
        return sdk_client # Already a dict
    else:
        logger.warning(f"Cannot map SDK client of type {type(sdk_client)} to dict.")
        return {}

def _map_kwargs_to_sdk_client(**kwargs) -> SdkClient:
    """Maps keyword arguments to an SDK Client object for add/update operations."""
    sdk_data = {}
    if 'email' in kwargs: sdk_data['email'] = kwargs['email']
    if 'uuid' in kwargs: sdk_data['id'] = kwargs['uuid']
    if 'enable' in kwargs: sdk_data['enable'] = kwargs['enable']
    if 'total_gb' in kwargs and kwargs['total_gb'] is not None:
         # py3xui expects bytes
         sdk_data['totalGB'] = kwargs['total_gb'] * 1024 * 1024 * 1024
    if 'expire_time' in kwargs and kwargs['expire_time'] is not None:
         # py3xui expects timestamp in milliseconds
         sdk_data['expiryTime'] = int(kwargs['expire_time'] * 1000) if kwargs['expire_time'] > 0 else 0
    if 'limit_ip' in kwargs: sdk_data['limitIp'] = kwargs['limit_ip']
    if 'flow' in kwargs: sdk_data['flow'] = kwargs['flow']
    if 'sub_id' in kwargs: sdk_data['subId'] = kwargs['sub_id']
    if 'telegram_id' in kwargs: sdk_data['tgId'] = kwargs['telegram_id']

    if 'id' not in sdk_data: 
        sdk_data['id'] = str(uuid.uuid4())
        logger.warning(f"Generated new UUID {sdk_data['id']} for client creation.")
        
    # Need to know all required fields for SdkClient to avoid validation issues
    # For example, py3xui might always require 'email' even if empty
    if 'email' not in sdk_data: sdk_data['email'] = f"{sdk_data['id']}@placeholder.email" # Use UUID if missing? Or require from service layer?
    if 'enable' not in sdk_data: sdk_data['enable'] = True
    if 'totalGB' not in sdk_data: sdk_data['totalGB'] = 0
    if 'expiryTime' not in sdk_data: sdk_data['expiryTime'] = 0
    if 'limitIp' not in sdk_data: sdk_data['limitIp'] = 0
    # Flow might not be required by default in XUI panel itself? Defaulting to empty string if not provided
    if 'flow' not in sdk_data: sdk_data['flow'] = "" 
    if 'subId' not in sdk_data: sdk_data['subId'] = ""
    if 'tgId' not in sdk_data: sdk_data['tgId'] = ""

    return SdkClient(**sdk_data)

class ClientApi(BaseApi):
    """API wrapper for XUI clients using the internal SDK's methods but handling httpx errors."""

    async def get_clients_by_inbound(self, inbound_id: int) -> List[Dict[str, Any]]:
        """Fetches clients for an inbound using SDK, handles httpx errors."""
        logger.info(f"Attempting to get clients for inbound {inbound_id} on {self.host}")
        try:
            # Assuming SDK has get_list() and we filter manually
            all_clients_sdk: List[SdkClient] = await self.api.client.get_list() 
            # Careful with attribute names, check SdkClient model definition if possible
            clients_sdk = [c for c in all_clients_sdk if getattr(c, 'inboundId', None) == inbound_id] # Use inboundId ?
            
            logger.info(f"Successfully fetched {len(clients_sdk)} clients for inbound {inbound_id} via SDK.")
            return [_map_sdk_client_to_dict(c) for c in clients_sdk]
            
        except AttributeError as e:
             logger.error(f"SDK method get_list or attribute error accessing client data on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method/attribute missing for getting client list: {e}") from e
        except httpx.HTTPStatusError as e:
             # 404 for inbound not found? Or just empty list? Assume empty list is success.
             logger.error(f"HTTP Status Error getting clients for inbound {inbound_id} on {self.host}: {e.response.status_code}", exc_info=True)
             raise XuiOperationError(f"HTTP error {e.response.status_code} getting clients for inbound {inbound_id}.") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error getting clients for inbound {inbound_id} on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed getting clients for inbound {inbound_id}: {e}") from e
        except Exception as e: # Catch potential mapping errors or other unexpected issues
            logger.error(f"Unexpected error fetching/mapping clients for inbound {inbound_id} on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error processing clients for inbound {inbound_id}: {e}") from e

    async def get_client_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetches a client by email using SDK, handles httpx errors."""
        logger.info(f"Fetching client by email '{email}' on {self.host}")
        try:
             # Assuming get_by_email exists and raises ValueError or returns None if not found (based on py3xui code)
            sdk_client: Optional[SdkClient] = await self.api.client.get_by_email(email)
            if sdk_client:
                 logger.info(f"Successfully fetched client by email '{email}'.")
                 return _map_sdk_client_to_dict(sdk_client)
            else:
                 logger.warning(f"Client with email '{email}' not found on {self.host} (SDK returned None).")
                 return None
        except ValueError: # py3xui uses ValueError if email not found
             logger.warning(f"Client with email '{email}' not found on {self.host} (SDK ValueError).")
             return None
        except AttributeError as e:
             logger.error(f"SDK method get_by_email not found for clients on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for get_by_email: {e}") from e
        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP Status Error getting client by email '{email}' on {self.host}: {e.response.status_code}", exc_info=True)
             raise XuiOperationError(f"HTTP error {e.response.status_code} getting client by email '{email}'.") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error getting client by email '{email}' on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed getting client by email '{email}': {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching/mapping client by email '{email}' on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error processing client by email '{email}': {e}") from e

    async def get_client_by_uuid(self, client_uuid: str) -> Optional[Dict[str, Any]]:
        """Fetches a client by UUID using SDK, handles httpx errors."""
        logger.info(f"Fetching client by UUID '{client_uuid}' on {self.host}")
        try:
            # Assuming SDK client.get(uuid) exists
            sdk_client: Optional[SdkClient] = await self.api.client.get(client_uuid)
            if sdk_client:
                logger.info(f"Successfully fetched client by UUID '{client_uuid}'.")
                return _map_sdk_client_to_dict(sdk_client)
            else:
                # Should SDK raise error or return None? Assuming None based on get_by_email
                logger.warning(f"Client with UUID '{client_uuid}' not found (SDK returned None).")
                raise XuiNotFoundError(f"Client with UUID '{client_uuid}' not found.")
        except ValueError: # If SDK raises ValueError on not found
             logger.warning(f"Client with UUID '{client_uuid}' not found (SDK ValueError).")
             raise XuiNotFoundError(f"Client with UUID '{client_uuid}' not found.") from None
        except AttributeError as e:
             logger.error(f"SDK method get not found for clients on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for get client by UUID: {e}") from e
        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP Status Error getting client UUID '{client_uuid}' on {self.host}: {e.response.status_code}", exc_info=True)
             if e.response.status_code == 404:
                 raise XuiNotFoundError(f"Client with UUID '{client_uuid}' not found (404).") from e
             raise XuiOperationError(f"HTTP error {e.response.status_code} getting client UUID '{client_uuid}'.") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error getting client UUID '{client_uuid}' on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed getting client UUID '{client_uuid}': {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching/mapping client UUID '{client_uuid}' on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error processing client UUID '{client_uuid}': {e}") from e
            
    async def add_client(self, inbound_id: int, **kwargs) -> Dict[str, Any]:
        """Adds a new client using SDK, handles httpx errors."""
        logger.info(f"Attempting to add client to inbound {inbound_id} on {self.host} with data: {kwargs}")
        try:
            sdk_client_to_add = _map_kwargs_to_sdk_client(**kwargs)
            # Assuming SDK add returns the created client
            created_sdk_client: SdkClient = await self.api.client.add(inbound_id=inbound_id, client=sdk_client_to_add)
            logger.info(f"Successfully added client (UUID: {created_sdk_client.id}) to inbound {inbound_id} via SDK.")
            return _map_sdk_client_to_dict(created_sdk_client)
            
        except AttributeError as e:
             logger.error(f"SDK method add not found for clients on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for adding client: {e}") from e
        except httpx.HTTPStatusError as e: # Check for 422 Unprocessable Entity or others
             logger.error(f"HTTP Status Error adding client to inbound {inbound_id} on {self.host}: {e.response.status_code}", exc_info=True)
             if e.response.status_code == 422:
                 # Try to parse error message from response if possible
                 error_detail = e.response.text
                 raise XuiValidationError(f"Validation failed adding client: {error_detail}") from e
             else:
                 raise XuiOperationError(f"HTTP error {e.response.status_code} adding client.") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error adding client to inbound {inbound_id} on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed adding client to inbound {inbound_id}: {e}") from e
        except Exception as e: # Catch potential mapping errors or other SDK issues
            logger.error(f"Unexpected error adding client to inbound {inbound_id} on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error adding client: {e}") from e

    async def update_client(self, client_uuid: str, **kwargs) -> Dict[str, Any]:
        """Updates a client using SDK, handles httpx errors."""
        logger.info(f"Attempting to update client {client_uuid} on {self.host} with data: {kwargs}")
        try:
            # Important: Ensure kwargs includes the UUID for mapping
            if 'uuid' not in kwargs: kwargs['uuid'] = client_uuid 
            sdk_client_to_update = _map_kwargs_to_sdk_client(**kwargs)
            
            # Assuming SDK update returns the updated client
            updated_sdk_client: SdkClient = await self.api.client.update(client_uuid, sdk_client_to_update)
            logger.info(f"Successfully updated client {client_uuid} via SDK.")
            return _map_sdk_client_to_dict(updated_sdk_client)

        except AttributeError as e:
             logger.error(f"SDK method update not found for clients on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for updating client: {e}") from e
        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP Status Error updating client {client_uuid} on {self.host}: {e.response.status_code}", exc_info=True)
             if e.response.status_code == 404:
                 raise XuiNotFoundError(f"Client {client_uuid} not found for update (404).") from e
             elif e.response.status_code == 422:
                 error_detail = e.response.text
                 raise XuiValidationError(f"Validation failed updating client {client_uuid}: {error_detail}") from e
             else:
                 raise XuiOperationError(f"HTTP error {e.response.status_code} updating client {client_uuid}.") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error updating client {client_uuid} on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed updating client {client_uuid}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error updating client {client_uuid} on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error updating client {client_uuid}: {e}") from e
            
    async def delete_client(self, client_uuid: str) -> bool:
        """Deletes a client using SDK, handles httpx errors."""
        logger.info(f"Attempting to delete client {client_uuid} on {self.host}")
        try:
            await self.api.client.delete(client_uuid)
            logger.info(f"Successfully deleted client {client_uuid} via SDK.")
            return True
        except AttributeError as e:
             logger.error(f"SDK method delete not found for clients on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for deleting client: {e}") from e
        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP Status Error deleting client {client_uuid} on {self.host}: {e.response.status_code}", exc_info=True)
             if e.response.status_code == 404:
                  # Treat 404 on delete as success (idempotent) or raise? Let's raise for now.
                 raise XuiNotFoundError(f"Client {client_uuid} not found for deletion (404).") from e
             else: # Maybe 422 if it cannot be deleted?
                  error_detail = e.response.text
                  raise XuiOperationError(f"HTTP error {e.response.status_code} deleting client {client_uuid}: {error_detail}") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error deleting client {client_uuid} on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed deleting client {client_uuid}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting client {client_uuid} on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error deleting client {client_uuid}: {e}") from e

    async def reset_client_traffic(self, client_uuid: str) -> bool:
        """Resets traffic using SDK, handles httpx errors."""
        logger.info(f"Attempting to reset traffic for client {client_uuid} on {self.host}")
        try:
            await self.api.client.reset_traffic(client_uuid)
            logger.info(f"Successfully reset traffic for client {client_uuid} via SDK.")
            return True 
        except AttributeError as e:
             logger.error(f"SDK method reset_traffic not found for clients on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for resetting client traffic: {e}") from e
        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP Status Error resetting traffic for client {client_uuid} on {self.host}: {e.response.status_code}", exc_info=True)
             if e.response.status_code == 404:
                 raise XuiNotFoundError(f"Client {client_uuid} not found for traffic reset (404).") from e
             else:
                 error_detail = e.response.text
                 raise XuiOperationError(f"HTTP error {e.response.status_code} resetting traffic for client {client_uuid}: {error_detail}") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error resetting traffic for client {client_uuid} on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed resetting traffic for client {client_uuid}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error resetting traffic for client {client_uuid} on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error resetting traffic for client {client_uuid}: {e}") from e

# TODO:
# - Verify the exact method names and signatures in the internal SDK for client operations (get, add, update, delete, reset_traffic, get_by_email, get_list).
# - Verify the structure of the SdkClient Pydantic model and adjust mapping functions accordingly.
# - Add methods for other client operations if needed (e.g., getting traffic stats). 