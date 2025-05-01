"""
Base API class for interacting with the internally cloned XUI SDK.
"""

import logging
from typing import Optional
import httpx # Import httpx exceptions

# Using the vendored SDK with full path for the core API class
from core.integrations.xui_sdk.py3xui.py3xui import AsyncApi
# Removed import of non-existent SDK exceptions

# Import custom exceptions (These we define and raise ourselves)
from .exceptions import (
    XuiAuthenticationError,
    XuiConnectionError,
    XuiOperationError,
    XuiNotFoundError, # Add other custom exceptions if needed later
    XuiValidationError
)

logger = logging.getLogger(__name__)

class BaseApi:
    """Base class for XUI API wrappers using the internal SDK."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
    ) -> None:
        """
        Initializes the BaseApi.

        Args:
            host: The panel URL (e.g., 'http://127.0.0.1:2053').
            username: The panel username.
            password: The panel password.
        """
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        
        self.api = AsyncApi(
            host=self.host,
            username=self.username,
            password=self.password
        )
        logger.debug(f"Internal AsyncApi initialized for {self.host}")

    async def login(self) -> None:
        """
        Performs login using the internal SDK's login method.
        Handles potential httpx exceptions and raises custom exceptions.
        """
        logger.info(f"Attempting login via internal SDK for {self.host}")
        try:
            # The SDK's login method itself might raise ValueError on non-cookie response
            await self.api.login() 
            logger.info(f"Internal SDK login successful for {self.host}. Session assumed active.")
        except ValueError as e: # Catch SDK's specific error for bad login
            logger.error(f"SDK ValueError during login (likely bad credentials) for {self.host}: {e}", exc_info=True)
            raise XuiAuthenticationError(f"Login failed: Invalid credentials or panel issue for {self.host}.") from e
        except httpx.ConnectError as e:
            logger.error(f"Connection failed for {self.host}: {e}", exc_info=True)
            raise XuiConnectionError(f"Could not connect to panel at {self.host}. {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error during login for {self.host}: {e.response.status_code}", exc_info=True)
            if e.response.status_code == 401: # Unauthorized
                 raise XuiAuthenticationError(f"Login failed (401 Unauthorized) for {self.host}.") from e
            else:
                 raise XuiOperationError(f"HTTP error {e.response.status_code} during login for {self.host}.") from e
        except httpx.RequestError as e: # Catch other httpx request errors
             logger.error(f"httpx Request Error during login for {self.host}: {e}", exc_info=True)
             raise XuiConnectionError(f"Request failed during login for {self.host}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during internal SDK login for {self.host}: {e}", exc_info=True)
            raise XuiOperationError(f"An unexpected error occurred during login: {e}") from e
            
    async def is_logged_in(self) -> bool:
        """
        Checks if the session is likely active by checking internal state.
        """
        is_active = hasattr(self.api, '_session') and self.api._session is not None
        logger.debug(f"is_logged_in check: session attribute exists and is not None: {is_active}")
        return is_active 