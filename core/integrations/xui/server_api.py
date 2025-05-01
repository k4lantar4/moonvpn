"""
API wrapper for managing XUI server operations using the internal SDK.
"""

import logging
from typing import Optional, Dict, Any
import httpx # Import httpx exceptions

# Import base and custom exceptions
from .base import BaseApi
from .exceptions import XuiOperationError, XuiConnectionError

# Removed import of non-existent SDK exceptions
# from core.integrations.xui_sdk.py3xui.py3xui.server import ServerStatus # If needed, import directly

logger = logging.getLogger(__name__)

class ServerApi(BaseApi):
    """API wrapper for XUI server operations using internal SDK methods but handling httpx errors."""

    async def get_server_status(self) -> Optional[Dict[str, Any]]:
        """Fetches server status using SDK, handles httpx errors."""
        logger.info(f"Attempting to get server status from {self.host}")
        try:
            status_obj = await self.api.server.get_status()
            if not status_obj:
                 logger.warning(f"Received empty status from SDK for {self.host}")
                 return None
                 
            logger.info(f"Successfully retrieved server status from {self.host}")
            if hasattr(status_obj, 'model_dump'):
                return status_obj.model_dump()
            elif isinstance(status_obj, dict):
                 return status_obj
            else:
                 logger.warning(f"Could not map server status type {type(status_obj)} to dict.")
                 return None 
                 
        except AttributeError as e:
             logger.error(f"SDK method get_status not found for server on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for getting server status: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error getting server status for {self.host}: {e.response.status_code}", exc_info=True)
            raise XuiOperationError(f"HTTP error {e.response.status_code} getting server status.") from e
        except httpx.RequestError as e: 
            logger.error(f"Connection/Request Error getting server status for {self.host}: {e}", exc_info=True)
            raise XuiConnectionError(f"Connection failed getting server status: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting server status for {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error getting server status: {e}") from e

    async def get_db_backup(self, save_path: str) -> bool:
        """Downloads DB backup using SDK, handles httpx/IO errors."""
        logger.info(f"Attempting to download DB backup from {self.host} to {save_path}")
        try:
            await self.api.server.get_db(save_path=save_path)
            logger.info(f"Successfully initiated DB backup download to {save_path} via SDK.")
            # We might need to add an os.path.exists check here after the call
            return True
        except AttributeError as e:
             logger.error(f"SDK method get_db not found for server on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for downloading DB backup: {e}") from e
        except httpx.HTTPStatusError as e: # e.g., 403 Forbidden?
            logger.error(f"HTTP Status Error downloading DB backup from {self.host}: {e.response.status_code}", exc_info=True)
            raise XuiOperationError(f"HTTP error {e.response.status_code} downloading DB backup: {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"Connection/Request Error downloading DB backup from {self.host}: {e}", exc_info=True)
            raise XuiConnectionError(f"Connection failed downloading DB backup: {e}") from e
        except IOError as e: # Catch potential file writing errors
            logger.error(f"IO Error saving DB backup to {save_path} from {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Failed to save DB backup file locally: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error downloading DB backup from {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error downloading DB backup: {e}") from e

    async def export_database(self) -> bool:
        """Requests DB export using SDK, handles httpx errors."""
        logger.info(f"Requesting database export on {self.host}")
        try:
            if hasattr(self.api, 'database') and hasattr(self.api.database, 'export'):
                 await self.api.database.export()
            elif hasattr(self.api, 'server') and hasattr(self.api.server, 'export_db'): 
                 await self.api.server.export_db()
            else:
                 raise AttributeError("Could not find export database method in SDK.")
                 
            logger.info(f"Successfully requested database export via SDK on {self.host}.")
            return True
        except AttributeError as e:
             logger.error(f"SDK method export (or similar) not found for database on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for exporting database: {e}") from e
        except httpx.HTTPStatusError as e: 
             logger.error(f"HTTP Status Error requesting DB export on {self.host}: {e.response.status_code}", exc_info=True)
             raise XuiOperationError(f"HTTP error {e.response.status_code} requesting DB export: {e.response.text}") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error requesting DB export on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed requesting DB export: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error requesting DB export on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error requesting DB export: {e}") from e
            
    async def restart_core(self) -> bool:
        """Requests core restart using SDK, handles httpx errors."""
        logger.info(f"Requesting core restart on {self.host}")
        try:
            await self.api.server.restart_core()
            logger.info(f"Successfully requested core restart via SDK on {self.host}.")
            return True 
        except AttributeError as e:
             logger.error(f"SDK method restart_core not found for server on {self.host}: {e}", exc_info=True)
             raise XuiOperationError(f"SDK method missing for restarting core: {e}") from e
        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP Status Error requesting core restart on {self.host}: {e.response.status_code}", exc_info=True)
             raise XuiOperationError(f"HTTP error {e.response.status_code} requesting core restart: {e.response.text}") from e
        except httpx.RequestError as e:
             logger.error(f"Connection/Request Error requesting core restart on {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Connection failed requesting core restart: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error requesting core restart on {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"Unexpected error requesting core restart: {e}") from e

# TODO:
# - Verify the exact method names and signatures in the internal SDK for server operations.
# - Verify return types and Pydantic models used by SDK server methods and adjust mapping if needed. 