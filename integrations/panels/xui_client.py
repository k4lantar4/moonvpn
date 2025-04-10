"""3x-ui specific API client using httpx."""

import httpx
import logging
from typing import Any, Dict, Optional, Tuple, List
from urllib.parse import urljoin
import json

from core.config import settings
from integrations.panels.exceptions import PanelAuthenticationError, PanelError, PanelAPIError, PanelClientError

# Get logger instance from core logging setup
logger = logging.getLogger(__name__)

class XuiPanelClient:
    """
    Asynchronous HTTP client for interacting with the 3x-ui panel API.

    Handles authentication, session management, and API requests.
    Credentials and URL are stored in the database (fetched by PanelService).
    """

    def __init__(self, base_url: str, username: str, password: str, panel_id: int):
        """
        Initialize the client.

        Args:
            base_url: The base URL of the 3x-ui panel (e.g., https://panel.example.com:54321).
            username: The admin username for the panel.
            password: The admin password for the panel.
            panel_id: The ID of the panel in our database (for logging purposes).
        """
        self.base_url = base_url.rstrip('/')
        self._username = username
        self._password = password
        self.panel_id = panel_id
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=settings.PANEL_API_TIMEOUT,
            verify=settings.PANEL_VERIFY_SSL, # Allow disabling SSL verification if needed
            follow_redirects=True
        )
        self._login_path = "/login" # Default login path
        self._api_base_path = "/panel/api/inbounds" # Default API base path
        logger.info(f"[Panel-{self.panel_id}] Initialized XuiPanelClient for {self.base_url}")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        attempt_login: bool = True,
        is_login: bool = False
    ) -> Tuple[int, Any]:
        """
        Makes an asynchronous HTTP request to the panel API.

        Handles potential session expiry by attempting login on failure.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API endpoint path (relative to base_url or api_base_path).
            json: Request body JSON data.
            params: URL query parameters.
            attempt_login: Whether to attempt login if the request fails initially.
            is_login: Whether this request itself is the login request.

        Returns:
            A tuple containing the HTTP status code and the parsed JSON response.

        Raises:
            PanelAuthenticationError: If login fails.
            PanelError: For other connection or API errors.
        """
        url = path if is_login else urljoin(self._api_base_path + '/', path.lstrip('/'))
        log_url = urljoin(self.base_url + '/', url.lstrip('/')) # Full URL for logging

        try:
            logger.debug(f"[Panel-{self.panel_id}] Requesting {method} {log_url}...")
            response = await self._client.request(method, url, json=json, params=params)
            logger.debug(f"[Panel-{self.panel_id}] Response Status: {response.status_code}")

            # Check for successful response or authentication errors specifically
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and data.get("success") is False:
                        # Handle cases where API returns 200 OK but success=false
                        error_msg = data.get("msg", "Unknown API error")
                        logger.error(f"[Panel-{self.panel_id}] API Error ({log_url}): {error_msg}")
                        # Decide if this specific error warrants a login attempt
                        if "expire" in error_msg.lower() and attempt_login:
                            logger.warning(f"[Panel-{self.panel_id}] Possible session expiry. Attempting login...")
                            await self.login()
                            return await self._request(method, path, json=json, params=params, attempt_login=False, is_login=is_login)
                        raise PanelError(f"API returned error: {error_msg}", status_code=response.status_code)
                    return response.status_code, data
                except ValueError:
                    logger.error(f"[Panel-{self.panel_id}] Failed to decode JSON response from {log_url}. Content: {response.text[:100]}...")
                    raise PanelError("Invalid JSON response from panel", status_code=response.status_code)

            # Handle common authentication failure status codes (e.g., 401, 403) or redirection to login page
            elif response.status_code in (401, 403) or (response.status_code == 200 and "/login" in str(response.url) and not is_login):
                 if attempt_login:
                    logger.warning(f"[Panel-{self.panel_id}] Authentication required or session expired for {log_url}. Attempting login...")
                    await self.login()
                    # Retry the original request without attempting login again
                    return await self._request(method, path, json=json, params=params, attempt_login=False, is_login=is_login)
                 else:
                    logger.error(f"[Panel-{self.panel_id}] Authentication failed for {log_url} even after login attempt.")
                    raise PanelAuthenticationError("Authentication failed", status_code=response.status_code)
            else:
                logger.error(f"[Panel-{self.panel_id}] HTTP Error {response.status_code} for {log_url}. Response: {response.text[:200]}...")
                response.raise_for_status() # Raise HTTPError for other bad status codes

        except httpx.HTTPStatusError as e:
            logger.error(f"[Panel-{self.panel_id}] HTTP Status Error for {log_url}: {e}")
            raise PanelError(f"HTTP Error: {e.response.status_code}", status_code=e.response.status_code) from e
        except httpx.RequestError as e:
            logger.error(f"[Panel-{self.panel_id}] Connection Error for {log_url}: {e}")
            raise PanelError(f"Connection Error: {e}") from e
        # Keep PanelAuthenticationError specific
        except PanelAuthenticationError:
             raise
        except Exception as e:
            logger.exception(f"[Panel-{self.panel_id}] Unexpected error during request to {log_url}: {e}")
            raise PanelError(f"An unexpected error occurred: {e}") from e

        # This part should ideally not be reached if errors are handled properly
        return response.status_code, {}


    async def login(self) -> bool:
        """
        Authenticates with the 3x-ui panel and stores the session cookie.

        Returns:
            True if login was successful, False otherwise.

        Raises:
            PanelAuthenticationError: If login fails after request.
        """
        logger.info(f"[Panel-{self.panel_id}] Attempting login to {self.base_url}...")
        payload = {"username": self._username, "password": self._password}
        try:
            status_code, response_data = await self._request("POST", self._login_path, json=payload, attempt_login=False, is_login=True)

            # 3x-ui login success is indicated by a 200 OK and success: true in the JSON body
            if status_code == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
                logger.info(f"[Panel-{self.panel_id}] Login successful.")
                # Session cookie is automatically handled by httpx client's cookie jar
                return True
            else:
                error_msg = response_data.get("msg", "Unknown login error") if isinstance(response_data, dict) else "Login failed"
                logger.error(f"[Panel-{self.panel_id}] Login failed: {error_msg} (Status: {status_code})")
                raise PanelAuthenticationError(f"Login failed: {error_msg}", status_code=status_code)
        except (PanelError, PanelAuthenticationError) as e:
            # Rethrow specific auth errors, wrap others
             if isinstance(e, PanelAuthenticationError):
                 raise
             logger.error(f"[Panel-{self.panel_id}] Error during login request: {e}")
             raise PanelAuthenticationError(f"Login request failed: {e}", status_code=getattr(e, 'status_code', 500)) from e
        except Exception as e:
             logger.exception(f"[Panel-{self.panel_id}] Unexpected error during login: {e}")
             raise PanelAuthenticationError(f"Unexpected error during login: {e}") from e


    async def get_inbounds(self) -> list:
        """
        Retrieves the list of all inbounds from the panel.

        Returns:
            A list of inbound objects (dictionaries).

        Raises:
            PanelAuthenticationError: If authentication fails.
            PanelError: For other connection or API errors.
        """
        logger.info(f"[Panel-{self.panel_id}] Fetching inbounds list...")
        status_code, response_data = await self._request("GET", "/list")

        if status_code == 200 and isinstance(response_data, dict) and response_data.get("success") is True and isinstance(response_data.get("obj"), list):
            inbounds = response_data["obj"]
            logger.info(f"[Panel-{self.panel_id}] Successfully fetched {len(inbounds)} inbounds.")
            return inbounds
        else:
            error_msg = response_data.get("msg", "Failed to fetch inbounds") if isinstance(response_data, dict) else "Unknown error"
            logger.error(f"[Panel-{self.panel_id}] Failed to get inbounds: {error_msg}")
            raise PanelError(f"Failed to get inbounds: {error_msg}", status_code=status_code)

    async def add_client(self, inbound_id: int, client_settings: Dict[str, Any], protocol: str) -> Dict[str, Any]:
        """
        Adds a new client to a specific inbound.

        Args:
            inbound_id: The ID of the inbound to add the client to.
            client_settings: A dictionary containing the client details.
                             Expected keys depend on the protocol, commonly includes:
                             'email', 'id' (UUID), 'totalGB' (or 'total'), 'expiryTime', 'flow'.
            protocol: The protocol of the client ('vmess', 'vless', 'trojan', 'shadowsocks').

        Returns:
            The API response dictionary containing 'native_identifier' and 'subscription_url'.

        Raises:
            PanelAuthenticationError: If authentication fails.
            PanelError: For other connection or API errors.
            ValueError: If client_settings format is invalid.
        """
        logger.info(f"[Panel-{self.panel_id}] Attempting to add client to inbound {inbound_id} (protocol: {protocol})...")

        # Validate settings structure (basic check)
        if not isinstance(client_settings, dict) or 'email' not in client_settings:
             logger.error(f"[Panel-{self.panel_id}] Invalid client_settings provided for add_client: {client_settings}")
             raise ValueError("Invalid client_settings format. Must be a dict with at least 'email'.")
        
        if protocol in ['vmess', 'vless', 'trojan'] and 'id' not in client_settings:
             logger.error(f"[Panel-{self.panel_id}] Missing 'id' (UUID) in client_settings for {protocol} protocol")
             raise ValueError(f"Invalid client_settings format for {protocol}. Must include 'id' (UUID).")
        
        if protocol == 'shadowsocks' and 'password' not in client_settings:
             logger.error(f"[Panel-{self.panel_id}] Missing 'password' in client_settings for shadowsocks protocol")
             raise ValueError("Invalid client_settings format for shadowsocks. Must include 'password'.")

        # Construct the payload according to 3x-ui API
        # It expects a JSON body like: {"id": inbound_id, "settings": "{\"clients\": [{\"email\": ..., \"id\": ...}]}"}
        try:
            settings_json_str = json.dumps({"clients": [client_settings]})
        except (TypeError, ValueError) as e:
            logger.error(f"[Panel-{self.panel_id}] Failed to serialize client_settings to JSON: {e}. Settings: {client_settings}")
            raise ValueError(f"Failed to serialize client_settings: {e}") from e

        payload = {
            "id": inbound_id,
            "settings": settings_json_str
        }

        status_code, response_data = await self._request("POST", "/addClient", json=payload)

        if status_code == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
            logger.info(f"[Panel-{self.panel_id}] Successfully added client (Email: {client_settings.get('email')}) to inbound {inbound_id}.")
            
            # Determine the native identifier based on protocol
            native_identifier = None
            if protocol in ['vmess', 'vless']:
                native_identifier = client_settings.get('id')  # UUID
            elif protocol == 'trojan':
                native_identifier = client_settings.get('password')
            elif protocol == 'shadowsocks':
                native_identifier = client_settings.get('email')
            
            # Generate subscription URL
            subscription_url = None
            try:
                # Format varies by panel configuration, but typically includes the client's UUID/password
                if protocol in ['vmess', 'vless']:
                    subscription_url = f"{self.base_url}/{protocol}/{client_settings.get('id')}"
                elif protocol == 'trojan':
                    subscription_url = f"{self.base_url}/trojan/{client_settings.get('password')}"
                elif protocol == 'shadowsocks':
                    # SS might use a different format
                    subscription_url = f"{self.base_url}/shadowsocks/{client_settings.get('password')}"
            except Exception as e:
                logger.warning(f"[Panel-{self.panel_id}] Error generating subscription URL: {e}")

            return {
                "success": True,
                "msg": response_data.get('msg', 'Client added successfully'),
                "native_identifier": native_identifier,
                "subscription_url": subscription_url
            }
        else:
            error_msg = response_data.get("msg", "Failed to add client") if isinstance(response_data, dict) else "Unknown error"
            logger.error(f"[Panel-{self.panel_id}] Failed to add client to inbound {inbound_id}: {error_msg}")
            raise PanelAPIError(f"Failed to add client: {error_msg}", status_code=status_code)

    async def update_client(self, client_identifier: str, protocol: str, updates: Dict[str, Any]) -> bool:
        """
        Updates an existing client in an inbound based on protocol-specific identifier.

        Args:
            client_identifier: The identifier of the client based on protocol (UUID for VLESS/VMess, 
                              password for Trojan, email for Shadowsocks).
            protocol: The protocol of the client ('vmess', 'vless', 'trojan', 'shadowsocks').
            updates: A dictionary containing the fields to update.
                     Expected keys: 'enable', 'email', 'id' (UUID), 'totalGB', 'expiryTime', 'flow', etc.

        Returns:
            True if the API call was successful, False otherwise.

        Raises:
            PanelAuthenticationError: If authentication fails.
            PanelError: For other connection or API errors.
            ValueError: If updates format is invalid.
            NotImplementedError: If the protocol is not supported.
        """
        logger.info(f"[Panel-{self.panel_id}] Attempting to update client {client_identifier} (protocol: {protocol})...")

        if not isinstance(updates, dict):
             logger.error(f"[Panel-{self.panel_id}] Invalid updates format provided for update_client: {updates}")
             raise ValueError("Invalid updates format. Must be a dict.")

        # Determine the correct endpoint and payload based on protocol
        # 3x-ui API paths differ by protocol
        endpoint = None
        payload = {}

        if protocol in ['vmess', 'vless']:
            # For VMess/VLESS, client_identifier should be the UUID
            # The endpoint is /updateClient/:clientId where clientId is internal panel ID
            # We need to find this internal ID by matching the UUID
            logger.info(f"[Panel-{self.panel_id}] For {protocol}, need to find internal panel ID for UUID {client_identifier}")
            
            # This approach requires getting all inbounds, finding client with matching UUID, getting internal ID
            # TEMP: For now, assume client_identifier is already the internal ID (needs to be updated)
            endpoint = f"/updateClient/{client_identifier}"
            try:
                settings_update_json_str = json.dumps({"clients": [updates]})
                payload = {"settings": settings_update_json_str}
            except (TypeError, ValueError) as e:
                logger.error(f"[Panel-{self.panel_id}] Failed to serialize updates to JSON: {e}. Updates: {updates}")
                raise ValueError(f"Failed to serialize updates: {e}") from e
            
        elif protocol == 'trojan':
            # For Trojan, client_identifier should be the password
            # Similar approach needed to find internal ID
            logger.info(f"[Panel-{self.panel_id}] For trojan, need to find internal panel ID for password {client_identifier}")
            endpoint = f"/updateClient/{client_identifier}"  # Assuming same endpoint structure
            try:
                settings_update_json_str = json.dumps({"clients": [updates]})
                payload = {"settings": settings_update_json_str}
            except (TypeError, ValueError) as e:
                logger.error(f"[Panel-{self.panel_id}] Failed to serialize updates to JSON: {e}. Updates: {updates}")
                raise ValueError(f"Failed to serialize updates: {e}") from e
            
        elif protocol == 'shadowsocks':
            # For Shadowsocks, client_identifier should be the email
            # Might have a different endpoint or approach
            logger.info(f"[Panel-{self.panel_id}] For shadowsocks, updating client with email {client_identifier}")
            endpoint = f"/updateClient/{client_identifier}"  # May need adjustment
            try:
                settings_update_json_str = json.dumps({"clients": [updates]})
                payload = {"settings": settings_update_json_str}
            except (TypeError, ValueError) as e:
                logger.error(f"[Panel-{self.panel_id}] Failed to serialize updates to JSON: {e}. Updates: {updates}")
                raise ValueError(f"Failed to serialize updates: {e}") from e
            
        else:
            logger.error(f"[Panel-{self.panel_id}] Unsupported protocol: {protocol}")
            raise NotImplementedError(f"update_client not implemented for protocol: {protocol}")

        # Make the request
        status_code, response_data = await self._request("POST", endpoint, json=payload)

        if status_code == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
            logger.info(f"[Panel-{self.panel_id}] Successfully updated client {client_identifier} (protocol: {protocol}).")
            return True
        else:
            error_msg = response_data.get("msg", "Failed to update client") if isinstance(response_data, dict) else "Unknown error"
            logger.error(f"[Panel-{self.panel_id}] Failed to update client {client_identifier} (protocol: {protocol}): {error_msg}")
            raise PanelAPIError(f"Failed to update client: {error_msg}", status_code=status_code)

    async def delete_client(self, inbound_id: int, client_identifier: str, protocol: str) -> bool:
        """
        Deletes a client from a specific inbound using the client identifier.

        Args:
            inbound_id: The ID of the inbound.
            client_identifier: The client's identifier based on protocol (UUID for VLESS/VMess, 
                              password for Trojan, email for Shadowsocks).
            protocol: The protocol of the client ('vmess', 'vless', 'trojan', 'shadowsocks').

        Returns:
            True if deletion was successful, False otherwise.

        Raises:
            PanelAuthenticationError: If authentication fails.
            PanelError: For other connection or API errors.
            NotImplementedError: If the protocol is not supported.
        """
        logger.info(f"[Panel-{self.panel_id}] Attempting to delete client {client_identifier} (protocol: {protocol}) from inbound {inbound_id}...")

        # Determine endpoint based on protocol
        endpoint = None

        if protocol in ['vmess', 'vless']:
            # For VMess/VLESS, client_identifier should be the UUID
            endpoint = f"/{inbound_id}/delClient/{client_identifier}"
        elif protocol == 'trojan':
            # For Trojan, client_identifier should be the password
            endpoint = f"/{inbound_id}/delClient/{client_identifier}"
        elif protocol == 'shadowsocks':
            # For Shadowsocks, client_identifier should be the email
            # May have a different endpoint
            endpoint = f"/{inbound_id}/delClientByEmail/{client_identifier}"
        else:
            logger.error(f"[Panel-{self.panel_id}] Unsupported protocol: {protocol}")
            raise NotImplementedError(f"delete_client not implemented for protocol: {protocol}")

        status_code, response_data = await self._request("POST", endpoint)

        if status_code == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
            logger.info(f"[Panel-{self.panel_id}] Successfully deleted client {client_identifier} (protocol: {protocol}) from inbound {inbound_id}.")
            return True
        else:
            error_msg = response_data.get("msg", "Failed to delete client") if isinstance(response_data, dict) else "Unknown error"
            logger.error(f"[Panel-{self.panel_id}] Failed to delete client {client_identifier} (protocol: {protocol}) from inbound {inbound_id}: {error_msg}")
            raise PanelAPIError(f"Failed to delete client: {error_msg}", status_code=status_code)

    async def get_client_traffics(self, client_identifier: str, protocol: str) -> Optional[Dict[str, Any]]:
        """
        Gets traffic statistics for a client based on protocol-specific identifier.

        Args:
            client_identifier: The identifier of the client based on protocol (UUID for VLESS/VMess, 
                              password for Trojan, email for Shadowsocks).
            protocol: The protocol of the client ('vmess', 'vless', 'trojan', 'shadowsocks').

        Returns:
            A dictionary containing traffic stats (e.g., {'up': ..., 'down': ..., 'total': ..., 'expiryTime': ...})
            or None if the client is not found or an error occurs.

        Raises:
            PanelAuthenticationError: If authentication fails.
            PanelError: For other connection or API errors.
            NotImplementedError: If the protocol is not supported.
        """
        logger.debug(f"[Panel-{self.panel_id}] Fetching traffic stats for client {client_identifier} (protocol: {protocol})...")

        # Determine endpoint based on protocol
        endpoint = None
        
        # For 3x-ui, getClientTraffics only works with email for all protocols
        # We might need to find the email from the identifier for non-Shadowsocks protocols
        # For now, we'll use the assumption that client_identifier is directly usable
        
        if protocol == 'shadowsocks':
            # For Shadowsocks, client_identifier should be the email already
            endpoint = f"/getClientTraffics/{client_identifier}"
        elif protocol in ['vmess', 'vless', 'trojan']:
            # For other protocols, we need to find the client's email using identifier
            # This is a temporary approach - in production, we should have the email stored or use a lookup
            endpoint = f"/getClientTraffics/{client_identifier}"
            logger.warning(f"[Panel-{self.panel_id}] Using {protocol} identifier directly as email for traffic stats - may not work!")
        else:
            logger.error(f"[Panel-{self.panel_id}] Unsupported protocol: {protocol}")
            raise NotImplementedError(f"get_client_traffics not implemented for protocol: {protocol}")
        
        try:
            status_code, response_data = await self._request("GET", endpoint)

            if status_code == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
                client_data = response_data.get("obj")
                if client_data:
                    logger.debug(f"[Panel-{self.panel_id}] Successfully fetched traffic stats for {client_identifier} (protocol: {protocol}).")
                    # Ensure keys are what we expect
                    return {
                        "up": client_data.get("up", 0),
                        "down": client_data.get("down", 0),
                        "total": client_data.get("total", 0),
                        "expiryTime": client_data.get("expiryTime", 0)
                    }
                else:
                    logger.warning(f"[Panel-{self.panel_id}] Traffic stats data ('obj') missing for {client_identifier} (protocol: {protocol}), though API reported success.")
                    return None
            elif status_code == 404: # Explicitly handle Not Found
                 logger.warning(f"[Panel-{self.panel_id}] Client {client_identifier} (protocol: {protocol}) not found for traffic stats.")
                 return None
            else:
                error_msg = response_data.get("msg", "Failed to get traffic stats") if isinstance(response_data, dict) else "Unknown error"
                logger.error(f"[Panel-{self.panel_id}] Failed to get traffic stats for {client_identifier} (protocol: {protocol}): {error_msg} (Status: {status_code})")
                raise PanelAPIError(f"Failed to get client traffic: {error_msg}", status_code=status_code)

        except PanelAPIError as e:
            # If the API error specifically indicates not found, treat as None
            if e.status_code == 404 or "not found" in str(e).lower():
                 logger.warning(f"[Panel-{self.panel_id}] Client {client_identifier} (protocol: {protocol}) not found for traffic stats (handled from exception).")
                 return None
            raise # Re-raise other API errors
        except Exception as e:
            # Includes PanelAuthenticationError, PanelError
            logger.error(f"[Panel-{self.panel_id}] Error fetching traffic stats for {client_identifier} (protocol: {protocol}): {e}")
            raise # Re-raise other exceptions

    async def reset_client_traffic(self, client_identifier: str, protocol: str, inbound_id: int) -> bool:
        """Resets traffic for a given client based on protocol and identifier.
        
        Args:
            client_identifier: The identifier of the client based on protocol (UUID for VLESS/VMess, 
                              password for Trojan, email for Shadowsocks).
            protocol: The protocol of the client ('vmess', 'vless', 'trojan', 'shadowsocks').
            inbound_id: The ID of the inbound the client belongs to.
            
        Returns:
            True if successful, False otherwise.
            
        Raises:
            PanelAuthenticationError: If authentication fails.
            PanelError: For other connection or API errors.
            NotImplementedError: If the protocol is not supported.
        """
        logger.info(f"[Panel-{self.panel_id}] Attempting to reset traffic for client {client_identifier} (protocol: {protocol}, inbound: {inbound_id})...")

        # Determine endpoint based on protocol
        endpoint = None
        
        if protocol == 'shadowsocks':
            # For Shadowsocks, client_identifier should be the email
            endpoint = f"/{inbound_id}/resetClientTraffic/{client_identifier}"
        elif protocol in ['vmess', 'vless']:
            # For VMess/VLESS, client_identifier should be the UUID
            endpoint = f"/{inbound_id}/resetClientTraffic/{client_identifier}"
        elif protocol == 'trojan':
            # For Trojan, client_identifier should be the password
            endpoint = f"/{inbound_id}/resetClientTraffic/{client_identifier}"
        else:
            logger.error(f"[Panel-{self.panel_id}] Unsupported protocol: {protocol}")
            raise NotImplementedError(f"reset_client_traffic not implemented for protocol: {protocol}")

        try:
            status_code, response_data = await self._request("POST", endpoint)
            
            if status_code == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
                logger.info(f"[Panel-{self.panel_id}] Successfully reset traffic for client {client_identifier} (protocol: {protocol}, inbound: {inbound_id}).")
                return True
            else:
                error_msg = response_data.get("msg", "Failed to reset traffic") if isinstance(response_data, dict) else "Unknown error"
                logger.error(f"[Panel-{self.panel_id}] Failed to reset traffic for {client_identifier} (protocol: {protocol}): {error_msg}")
                raise PanelAPIError(f"Failed to reset client traffic: {error_msg}", status_code=status_code)
        
        except PanelAPIError as e:
            # If error indicates client not found, return False instead of raising
            if e.status_code == 404 or "not found" in str(e).lower():
                logger.warning(f"[Panel-{self.panel_id}] Client {client_identifier} not found for traffic reset.")
                return False
            raise # Re-raise other API errors
        except Exception as e:
            logger.error(f"[Panel-{self.panel_id}] Error resetting traffic for {client_identifier}: {e}")
            raise

    async def get_client_details(self, client_identifier: str, protocol: str, inbound_id: int) -> Optional[Dict[str, Any]]:
        """Fetches detailed configuration for a client.
        
        Args:
            client_identifier: The identifier of the client based on protocol (UUID for VLESS/VMess, 
                              password for Trojan, email for Shadowsocks).
            protocol: The protocol of the client ('vmess', 'vless', 'trojan', 'shadowsocks').
            inbound_id: The ID of the inbound the client belongs to.
            
        Returns:
            Dictionary containing client configuration details or None if not found.
            
        Raises:
            PanelAuthenticationError: If authentication fails.
            PanelError: For other connection or API errors.
            NotImplementedError: If the protocol is not supported.
        """
        logger.info(f"[Panel-{self.panel_id}] Fetching details for client {client_identifier} (protocol: {protocol}, inbound: {inbound_id})...")

        # 3x-ui doesn't have a direct API to get client details by ID
        # We need to fetch the inbound details and find the client in the settings
        
        try:
            # Get the entire inbound
            inbound_data = await self.get_inbound(inbound_id)
            if not inbound_data:
                logger.warning(f"[Panel-{self.panel_id}] Inbound {inbound_id} not found, cannot get client details.")
                return None
                
            # Extract clients from settings based on protocol
            clients = []
            inbound_settings = inbound_data.get("settings", {})
            
            if isinstance(inbound_settings, str):
                try:
                    inbound_settings = json.loads(inbound_settings)
                except json.JSONDecodeError:
                    logger.error(f"[Panel-{self.panel_id}] Failed to parse inbound settings JSON.")
                    return None
                    
            clients = inbound_settings.get("clients", [])
            
            # Find the specific client using the identifier
            target_client = None
            for client in clients:
                if protocol in ['vmess', 'vless'] and client.get('id') == client_identifier:
                    target_client = client
                    break
                elif protocol == 'trojan' and client.get('password') == client_identifier:
                    target_client = client
                    break
                elif protocol == 'shadowsocks' and client.get('email') == client_identifier:
                    target_client = client
                    break
            
            if target_client:
                logger.info(f"[Panel-{self.panel_id}] Found client {client_identifier} in inbound {inbound_id}.")
                
                # Add additional useful information that might not be in the client object
                result = dict(target_client)
                result["inbound_id"] = inbound_id
                result["protocol"] = protocol
                
                # Generate subscription URL
                try:
                    base_url = self.base_url.rstrip('/')
                    if protocol in ['vmess', 'vless']:
                        result["subscription_url"] = f"{base_url}/{protocol}/{client_identifier}"
                    elif protocol == 'trojan':
                        result["subscription_url"] = f"{base_url}/trojan/{client_identifier}"
                    elif protocol == 'shadowsocks':
                        result["subscription_url"] = f"{base_url}/shadowsocks/{client_identifier}"
                except Exception as e:
                    logger.warning(f"[Panel-{self.panel_id}] Error generating subscription URL: {e}")
                
                return result
            else:
                logger.warning(f"[Panel-{self.panel_id}] Client {client_identifier} not found in inbound {inbound_id}.")
                return None
                
        except (PanelAuthenticationError, PanelAPIError) as e:
            logger.error(f"[Panel-{self.panel_id}] API error getting client details: {e}")
            raise
        except Exception as e:
            logger.exception(f"[Panel-{self.panel_id}] Unexpected error getting client details: {e}")
            raise ServiceError(f"Unexpected error getting client details: {e}")

    # --- Original Methods (Potentially Redundant/Needing Update) --- #

    async def get_inbound(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves details for a specific inbound.

        Args:
            inbound_id: The ID of the inbound.

        Returns:
            A dictionary containing the inbound details or None if not found.

        Raises:
            PanelAuthenticationError: If authentication fails.
            PanelError: For other connection or API errors.
        """
        logger.info(f"[Panel-{self.panel_id}] Fetching details for inbound {inbound_id}...")
        endpoint = f"/get/{inbound_id}"
        try:
            status_code, response_data = await self._request("GET", endpoint)

            if status_code == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
                inbound_data = response_data.get("obj")
                if inbound_data:
                    logger.info(f"[Panel-{self.panel_id}] Successfully fetched details for inbound {inbound_id}.")
                    return inbound_data
                else:
                    logger.warning(f"[Panel-{self.panel_id}] Inbound data ('obj') missing for ID {inbound_id}, though API reported success.")
                    return None
            elif status_code == 404:
                 logger.warning(f"[Panel-{self.panel_id}] Inbound with ID {inbound_id} not found.")
                 return None
            else:
                error_msg = response_data.get("msg", "Failed to get inbound") if isinstance(response_data, dict) else "Unknown error"
                logger.error(f"[Panel-{self.panel_id}] Failed to get inbound {inbound_id}: {error_msg} (Status: {status_code})")
                raise PanelAPIError(f"Failed to get inbound: {error_msg}", status_code=status_code)

        except PanelAPIError as e:
             if e.status_code == 404 or "not found" in str(e).lower():
                 logger.warning(f"[Panel-{self.panel_id}] Inbound with ID {inbound_id} not found (handled from exception).")
                 return None
             raise
        except Exception as e:
             logger.error(f"[Panel-{self.panel_id}] Error fetching inbound {inbound_id}: {e}")
             raise

    # --- Context Manager --- #

    async def close(self):
        """Closes the underlying httpx client."""
        await self._client.aclose()
        logger.info(f"[Panel-{self.panel_id}] Closed XuiPanelClient for {self.base_url}")

    async def __aenter__(self):
        # Optional: Add logic here if needed when entering context, e.g., ensure login
        # await self.login() # Could ensure login on entry, but might be inefficient
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

"""
Example Usage (within an async function):

async def main():
    # Assuming panel details are fetched from DB by a service
    panel_url = "YOUR_PANEL_URL"
    panel_user = "YOUR_PANEL_USERNAME"
    panel_pass = "YOUR_PANEL_PASSWORD"
    panel_db_id = 1 # Example panel ID from DB

    client = XuiPanelClient(panel_url, panel_user, panel_pass, panel_db_id)
    try:
        async with client: # Use context manager for automatic closing
            # Login is usually handled automatically by _request on first API call failure
            # await client.login() # Explicit login is possible but often not needed first

            inbounds = await client.get_inbounds()
            print(f"Fetched {len(inbounds)} inbounds.")
            if inbounds:
                print("First inbound details:", inbounds[0])

            # Add more API calls here...

    except PanelAuthenticationError as e:
        print(f"Authentication Error: {e} (Status: {e.status_code})")
    except PanelError as e:
        print(f"Panel Error: {e} (Status: {e.status_code})")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    import asyncio
    # Replace with actual panel details for testing
    # asyncio.run(main())
    print("XuiPanelClient defined. Run example usage within an async context.")
"""
