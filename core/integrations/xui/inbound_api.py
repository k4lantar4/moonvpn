"""
API wrapper for managing XUI inbounds using the internal SDK.
"""

import logging
from typing import List, Optional, Dict, Any
import httpx # Import httpx exceptions

# Import base and custom exceptions
from .base import BaseApi
from .exceptions import XuiOperationError, XuiNotFoundError, XuiValidationError, XuiConnectionError

# Import SDK Pydantic models from their specific modules
from core.integrations.xui_sdk.py3xui.py3xui.inbound.inbound import Inbound as SdkInbound
from core.integrations.xui_sdk.py3xui.py3xui.inbound.settings import Settings as SdkInboundSettings
from core.integrations.xui_sdk.py3xui.py3xui.inbound.stream_settings import StreamSettings as SdkStreamSettings
from core.integrations.xui_sdk.py3xui.py3xui.inbound.sniffing import Sniffing as SdkSniffing

# Import DB model and status enum
from db.models.inbound import Inbound as DbInbound, InboundStatus

logger = logging.getLogger(__name__)

def _map_sdk_inbound_to_db(sdk_inbound: SdkInbound, panel_id: Optional[int] = None) -> DbInbound:
    """Maps an SDK Inbound object to a DB Inbound object."""
    db_inbound_data = {
        "remote_id": sdk_inbound.id,
        "tag": sdk_inbound.tag,
        "protocol": sdk_inbound.protocol,
        "port": sdk_inbound.port,
        "listen": sdk_inbound.listen,
        "remark": sdk_inbound.remark,
        "status": InboundStatus.ACTIVE if sdk_inbound.enable else InboundStatus.DISABLED,
        "settings_json": sdk_inbound.settings.model_dump() if sdk_inbound.settings else {},
        "stream_settings": sdk_inbound.stream_settings.model_dump() if sdk_inbound.stream_settings else {},
        "sniffing": sdk_inbound.sniffing.model_dump() if sdk_inbound.sniffing else {},
        "max_clients": 0, 
    }
    if panel_id:
         db_inbound_data["panel_id"] = panel_id
    return DbInbound(**db_inbound_data)

def _map_db_data_to_sdk_inbound(**kwargs) -> SdkInbound:
    """Maps DB data (or arguments) to an SDK Inbound object for create/update."""
    sdk_data = {}
    if 'enable' in kwargs: sdk_data['enable'] = kwargs['enable']
    if 'port' in kwargs: sdk_data['port'] = kwargs['port']
    if 'protocol' in kwargs: sdk_data['protocol'] = kwargs['protocol']
    if 'remark' in kwargs: sdk_data['remark'] = kwargs['remark']
    if 'tag' in kwargs: sdk_data['tag'] = kwargs['tag']
    if 'listen' in kwargs: sdk_data['listen'] = kwargs['listen']
    
    if 'settings_json' in kwargs and kwargs['settings_json']:
        try:
            sdk_data['settings'] = SdkInboundSettings(**kwargs['settings_json'])
        except Exception as e:
             logger.warning(f"Could not map settings_json to SdkInboundSettings: {e}")
             sdk_data['settings'] = SdkInboundSettings()
    else:
         sdk_data['settings'] = SdkInboundSettings()

    if 'stream_settings' in kwargs and kwargs['stream_settings']:
        try:
            sdk_data['stream_settings'] = SdkStreamSettings(**kwargs['stream_settings'])
        except Exception as e:
             logger.warning(f"Could not map stream_settings to SdkStreamSettings: {e}")
             sdk_data['stream_settings'] = SdkStreamSettings()
    else:
        sdk_data['stream_settings'] = SdkStreamSettings()
        
    if 'sniffing' in kwargs and kwargs['sniffing']:
        try:
            sdk_data['sniffing'] = SdkSniffing(**kwargs['sniffing'])
        except Exception as e:
             logger.warning(f"Could not map sniffing to SdkSniffing: {e}")
             sdk_data['sniffing'] = SdkSniffing()
    else:
        sdk_data['sniffing'] = SdkSniffing()

    # Map total and expiryTime based on XUI names (capitalized)
    if 'total_gb' in kwargs and kwargs['total_gb'] is not None:
        sdk_data['total'] = kwargs['total_gb'] * 1024 * 1024 * 1024
    else:
        sdk_data['total'] = 0 # Default to 0 if not provided
        
    if 'expire_days' in kwargs and kwargs['expire_days'] is not None and kwargs['expire_days'] > 0:
         from datetime import datetime, timedelta
         expiry_datetime = datetime.utcnow() + timedelta(days=kwargs['expire_days'])
         sdk_data['expiryTime'] = int(expiry_datetime.timestamp() * 1000) 
    else:
         sdk_data['expiryTime'] = 0 # Default to 0 (no expiry) if not provided or <= 0
         
    # Ensure required fields for SdkInbound are present
    if 'enable' not in sdk_data: sdk_data['enable'] = True
    if 'port' not in sdk_data: raise ValueError("Port is required for creating/updating inbound")
    if 'protocol' not in sdk_data: raise ValueError("Protocol is required for creating/updating inbound")
    if 'tag' not in sdk_data: sdk_data['tag'] = f"inbound-{sdk_data['port']}" # Generate default tag
    if 'listen' not in sdk_data: sdk_data['listen'] = '' # Default listen IP
    if 'remark' not in sdk_data: sdk_data['remark'] = ''

    return SdkInbound(**sdk_data)

class InboundApi(BaseApi):
    """API wrapper for XUI inbounds using internal SDK methods but handling httpx errors."""

    async def get_all_inbounds(self, panel_id: Optional[int] = None) -> List[DbInbound]:
        """Fetches all inbounds using SDK, handles httpx errors."""
        logger.info(f"Fetching all inbounds via internal SDK for host {self.host}")
        try:
            sdk_inbounds: List[SdkInbound] = await self.api.inbound.get_list()
            logger.info(f"Successfully fetched {len(sdk_inbounds)} inbounds from SDK.")
            db_inbounds = [_map_sdk_inbound_to_db(ib, panel_id) for ib in sdk_inbounds]
            logger.debug(f"Mapped {len(db_inbounds)} inbounds to DB models.")
            return db_inbounds
            
        except AttributeError as e:
            logger.error(f"SDK method get_list not found for inbounds on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"SDK method missing for getting inbounds: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error getting inbounds for {self.host}: {e.response.status_code}", exc_info=True)
            raise XuiOperationError(f"HTTP error {e.response.status_code} getting inbounds.") from e
        except httpx.RequestError as e:
            logger.error(f"Connection/Request Error getting inbounds for {self.host}: {e}", exc_info=True)
            raise XuiConnectionError(f"Connection failed getting inbounds: {e}") from e
        except Exception as e: # Catch mapping errors etc.
            logger.error(f"Unexpected error fetching/mapping inbounds for {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error processing inbounds: {e}") from e

    async def get_inbound(self, inbound_id: int, panel_id: Optional[int] = None) -> DbInbound:
        """Fetches a specific inbound by ID using SDK, handles httpx errors."""
        logger.info(f"Fetching inbound with remote_id {inbound_id} via internal SDK for host {self.host}")
        try:
            sdk_inbound: SdkInbound = await self.api.inbound.get_by_id(inbound_id)
            logger.info(f"Successfully fetched inbound {inbound_id} from SDK.")
            return _map_sdk_inbound_to_db(sdk_inbound, panel_id)
            
        except ValueError: # If SDK raises ValueError on not found
             logger.warning(f"Inbound {inbound_id} not found on panel {self.host} (SDK ValueError).")
             raise XuiNotFoundError(f"Inbound with ID {inbound_id} not found.") from None
        except AttributeError as e:
            logger.error(f"SDK method get_by_id not found for inbounds on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"SDK method missing for getting inbound by ID: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error getting inbound {inbound_id} for {self.host}: {e.response.status_code}", exc_info=True)
            if e.response.status_code == 404:
                raise XuiNotFoundError(f"Inbound with ID {inbound_id} not found (404).") from e
            raise XuiOperationError(f"HTTP error {e.response.status_code} getting inbound {inbound_id}.") from e
        except httpx.RequestError as e:
            logger.error(f"Connection/Request Error getting inbound {inbound_id} for {self.host}: {e}", exc_info=True)
            raise XuiConnectionError(f"Connection failed getting inbound {inbound_id}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching/mapping inbound {inbound_id} for {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error processing inbound {inbound_id}: {e}") from e
    
    async def create_inbound(self, **kwargs) -> DbInbound:
        """ Creates an inbound using SDK, handles httpx errors. """
        logger.info(f"Attempting to create inbound on {self.host} with data: {kwargs}")
        try:
            sdk_inbound_to_create = _map_db_data_to_sdk_inbound(**kwargs)
            created_sdk_inbound: SdkInbound = await self.api.inbound.add(sdk_inbound_to_create)
            logger.info(f"Successfully created inbound (ID: {created_sdk_inbound.id}) via SDK on {self.host}.")
            panel_id = kwargs.get('panel_id') 
            return _map_sdk_inbound_to_db(created_sdk_inbound, panel_id)
            
        except ValueError as e: # Catch mapping errors or SDK value errors
             logger.error(f"Value Error creating inbound on {self.host}: {e}", exc_info=True)
             raise XuiValidationError(f"Invalid data for creating inbound: {e}") from e
        except AttributeError as e:
            logger.error(f"SDK method add not found for inbounds on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"SDK method missing for creating inbound: {e}") from e
        except httpx.HTTPStatusError as e: 
             logger.error(f"HTTP Status Error creating inbound on {self.host}: {e.response.status_code}", exc_info=True)
             if e.response.status_code == 422:
                 error_detail = e.response.text
                 raise XuiValidationError(f"Validation failed creating inbound: {error_detail}") from e
             else:
                 raise XuiOperationError(f"HTTP error {e.response.status_code} creating inbound.") from e
        except httpx.RequestError as e:
            logger.error(f"Connection/Request Error creating inbound on {self.host}: {e}", exc_info=True)
            raise XuiConnectionError(f"Connection failed creating inbound: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating inbound on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"An unexpected error occurred while creating inbound: {e}") from e

    async def update_inbound(self, inbound_id: int, **kwargs) -> DbInbound:
        """ Updates an inbound using SDK, handles httpx errors. """
        logger.info(f"Attempting to update inbound {inbound_id} on {self.host} with data: {kwargs}")
        try:
            sdk_inbound_to_update = _map_db_data_to_sdk_inbound(**kwargs)
            updated_sdk_inbound: SdkInbound = await self.api.inbound.update(inbound_id, sdk_inbound_to_update)
            logger.info(f"Successfully updated inbound {inbound_id} via SDK on {self.host}.")
            panel_id = kwargs.get('panel_id')
            return _map_sdk_inbound_to_db(updated_sdk_inbound, panel_id)
            
        except ValueError as e: # Catch mapping errors or SDK value errors
             logger.warning(f"Value Error updating inbound {inbound_id} on panel {self.host}: {e}", exc_info=True)
             # Check if it's a 'not found' error from SDK
             if "not found" in str(e).lower():
                 raise XuiNotFoundError(f"Inbound with ID {inbound_id} not found for update (SDK ValueError).") from e
             else:
                 raise XuiValidationError(f"Invalid data for updating inbound {inbound_id}: {e}") from e
        except AttributeError as e:
            logger.error(f"SDK method update not found for inbounds on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"SDK method missing for updating inbound: {e}") from e
        except httpx.HTTPStatusError as e: 
             logger.error(f"HTTP Status Error updating inbound {inbound_id} on {self.host}: {e.response.status_code}", exc_info=True)
             if e.response.status_code == 404:
                 raise XuiNotFoundError(f"Inbound with ID {inbound_id} not found for update (404).") from e
             elif e.response.status_code == 422:
                 error_detail = e.response.text
                 raise XuiValidationError(f"Validation failed updating inbound {inbound_id}: {error_detail}") from e
             else:
                 raise XuiOperationError(f"HTTP error {e.response.status_code} updating inbound {inbound_id}.") from e
        except httpx.RequestError as e:
            logger.error(f"Connection/Request Error updating inbound {inbound_id} on {self.host}: {e}", exc_info=True)
            raise XuiConnectionError(f"Connection failed updating inbound {inbound_id}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error updating inbound {inbound_id} on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"An unexpected error occurred while updating inbound {inbound_id}: {e}") from e
            
    async def delete_inbound(self, inbound_id: int) -> bool:
        """ Deletes an inbound using SDK, handles httpx errors. """
        logger.info(f"Attempting to delete inbound {inbound_id} on {self.host}")
        try:
            await self.api.inbound.delete(inbound_id)
            logger.info(f"Successfully deleted inbound {inbound_id} via SDK on {self.host}.")
            return True
        except ValueError: # If SDK raises ValueError on not found
             logger.warning(f"Inbound {inbound_id} not found for deletion on panel {self.host} (SDK ValueError).")
             raise XuiNotFoundError(f"Inbound with ID {inbound_id} not found for deletion.") from None
        except AttributeError as e:
            logger.error(f"SDK method delete not found for inbounds on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"SDK method missing for deleting inbound: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error deleting inbound {inbound_id} on {self.host}: {e.response.status_code}", exc_info=True)
            if e.response.status_code == 404:
                 raise XuiNotFoundError(f"Inbound with ID {inbound_id} not found for deletion (404).") from e
            else:
                 error_detail = e.response.text
                 raise XuiOperationError(f"HTTP error {e.response.status_code} deleting inbound {inbound_id}: {error_detail}") from e
        except httpx.RequestError as e:
            logger.error(f"Connection/Request Error deleting inbound {inbound_id} on {self.host}: {e}", exc_info=True)
            raise XuiConnectionError(f"Connection failed deleting inbound {inbound_id}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting inbound {inbound_id} on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"An unexpected error occurred while deleting inbound {inbound_id}: {e}") from e

# TODO: Add methods for other inbound operations if needed (reset traffic, etc.)
# Ensure all necessary SDK exceptions (like SdkValidationError) are imported and handled. 