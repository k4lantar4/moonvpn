import httpx
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import logging # Import logging
import json
import uuid

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the expected cookie name
PANEL_SESSION_COOKIE_NAME = "3x-ui"

class PanelClientError(Exception):
    """Custom exception for panel client errors."""
    pass

class PanelClient:
    """
    Asynchronous client for interacting with the 3x-ui panel API.
    """
    def __init__(self, base_url: str, username: str, password: str):
        # Ensure base_url ends with a slash for urljoin to work correctly
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'
        self.username = username
        self.password = password
        self._session_cookie_value = None
        # Use httpx.AsyncClient for async operations
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0, follow_redirects=True)
        logger.info(f"PanelClient initialized for base URL: {self.base_url}")

    async def _login(self) -> Optional[str]:
        """
        Logs into the panel and retrieves the session cookie.
        Returns the session cookie value if successful, None otherwise.
        Raises PanelClientError on failure.
        """
        login_url = urljoin(self.base_url, 'login') # Adjust path if needed
        login_data = {
            'username': self.username,
            'password': self.password
        }
        try:
            logger.info(f"Attempting login to {login_url} with username {self.username}")
            response = await self.client.post(login_url, data=login_data)

            logger.info(f"Login response status code: {response.status_code}")
            logger.debug(f"Login response cookies: {response.cookies}") # Use debug for potentially large cookies
            # Limit printing response body to avoid excessive logs
            try:
                response_text_preview = await response.aread()
                logger.debug(f"Login response body preview: {response_text_preview[:200]}...")
            except Exception as read_err:
                logger.warning(f"Could not read response body: {read_err}")

            # Check status code first
            response.raise_for_status() # Raise exception for 4xx/5xx errors

            # --- Use the Correct Cookie Name --- >
            if PANEL_SESSION_COOKIE_NAME in response.cookies:
                self._session_cookie_value = response.cookies.get(PANEL_SESSION_COOKIE_NAME)
                # Set the cookie for subsequent requests in this client instance
                self.client.cookies.set(PANEL_SESSION_COOKIE_NAME, self._session_cookie_value)
                logger.info(f"Login successful. Session cookie '{PANEL_SESSION_COOKIE_NAME}' obtained.")
                return self._session_cookie_value
            else:
                logger.error(f"Login seemed successful (status code OK), but the expected cookie '{PANEL_SESSION_COOKIE_NAME}' was not found.")
                raise PanelClientError(f"Login OK by status, but failed: Cookie '{PANEL_SESSION_COOKIE_NAME}' not found.")
            # <--- End Cookie Name Check ---

        except httpx.HTTPStatusError as e:
            logger.error(f"Login HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            raise PanelClientError(f"Login failed: HTTP {e.response.status_code}. Check panel URL and status.") from e
        except httpx.RequestError as e:
            logger.error(f"Login request error: {e}")
            raise PanelClientError(f"Login failed: Could not connect to panel at {login_url}. Check network or panel URL.") from e
        except PanelClientError: # Re-raise specific client errors
            raise
        except Exception as e:
            logger.exception("An unexpected error occurred during login") # Log full traceback
            raise PanelClientError("Login failed due to an unexpected error.") from e

    async def _get_session_cookie(self) -> str:
        """Ensures a valid session cookie exists, logging in if necessary."""
        if not self._session_cookie_value:
            logger.info("Session cookie not found, attempting login.")
            cookie = await self._login()
            if not cookie:
                raise PanelClientError("Unable to obtain session cookie after login attempt.")
            return cookie
        return self._session_cookie_value

    async def close(self):
        """Close the underlying httpx client."""
        await self.client.aclose()
        logger.info("PanelClient closed.")

    # --- API methods using the cookie --- #

    async def _make_request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Helper method to make authenticated requests."""
        cookie_value = await self._get_session_cookie()
        full_url = urljoin(self.base_url, path) # Use urljoin for relative paths
        cookies = {PANEL_SESSION_COOKIE_NAME: cookie_value}
        try:
            logger.debug(f"Making authenticated request: {method} {full_url}")
            response = await self.client.request(method, full_url, cookies=cookies, **kwargs)
            logger.debug(f"Response Status: {response.status_code}, Cookies: {response.cookies}")
            # Check if session seems invalid based on response (e.g., redirect to login, specific error code/message)
            # if response.status_code == 401 or "login required" in response.text.lower():
            #     logger.warning("Session seems invalid, attempting re-login.")
            #     self._session_cookie_value = None # Clear old cookie
            #     cookie_value = await self._get_session_cookie() # Relogin
            #     cookies = {PANEL_SESSION_COOKIE_NAME: cookie_value}
            #     # Retry the request once
            #     response = await self.client.request(method, full_url, cookies=cookies, **kwargs)
            #     logger.debug(f"Retry Response Status: {response.status_code}")

            response.raise_for_status() # Raise error for 4xx/5xx
            return response
        except httpx.HTTPStatusError as e:
            # Log more details on HTTP errors
            error_body = e.response.text[:200]
            logger.error(f"API request to {path} failed: HTTP {e.response.status_code} - {error_body}")
            # Check for specific error messages from the panel API if possible
            # if "authentication failed" in error_body.lower():
            #    raise PanelClientError("Authentication failed for API request.") from e
            raise PanelClientError(f"API request failed: HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"API request error to {path}: {e}")
            raise PanelClientError(f"API request failed: Could not connect to panel.") from e
        except PanelClientError:
             raise
        except Exception as e:
            logger.exception(f"Unexpected error during API request to {path}")
            raise PanelClientError(f"API request failed: Unexpected error - {e}") from e

    async def add_inbound(self,
                          remark: str,
                          protocol: str = "vless",
                          port: int = 0, # 0 means random port
                          total_gb: int = 0, # 0 means unlimited
                          expire_time: int = 0, # 0 means unlimited (timestamp in ms)
                          settings_override: Optional[Dict[str, Any]] = None,
                          stream_settings_override: Optional[Dict[str, Any]] = None,
                          tls_settings_override: Optional[Dict[str, Any]] = None
                         ) -> Optional[Dict[str, Any]]:
        """
        Adds a new inbound/user configuration.

        Args:
            remark: Name or identifier for the user/inbound.
            protocol: Protocol (e.g., "vless", "vmess", "trojan"). Defaults to "vless".
            port: Port for the inbound. 0 for random.
            total_gb: Traffic limit in GB. 0 for unlimited.
            expire_time: Expiration timestamp in milliseconds. 0 for unlimited.
            settings_override: Dictionary to override default protocol settings (e.g., user ID, flow).
            stream_settings_override: Dictionary to override default stream settings (e.g., network, security, wsSettings).
            tls_settings_override: Dictionary to override default TLS settings.

        Returns:
            A dictionary representing the created inbound object from the panel API, or None on failure.
        """
        path = 'panel/api/inbounds/add'

        # --- Constructing the Payload (NEEDS VERIFICATION based on 3x-ui API) ---
        # This is a common structure, but 3x-ui might differ significantly.
        # Especially the format of 'settings', 'streamSettings', 'sniffing'.

        # Convert GB to bytes
        total_bytes = total_gb * 1024 * 1024 * 1024 if total_gb > 0 else 0

        # Default settings (highly likely need adjustment for 3x-ui)
        default_settings = {
            "clients": [
                {
                    # ID (UUID) and other client params (like email for Trojan/SS) are often generated by the panel
                    # or need specific structure based on protocol.
                    # This part *definitely* needs the correct 3x-ui structure.
                    "id": "uuid", # Placeholder - Panel likely generates this
                    "flow": "xtls-rprx-vision" if protocol == "vless" else "", # Example default flow
                    "email": remark # Often uses remark as email/identifier
                }
            ],
            "decryption": "none",
            "fallbacks": []
        }
        if settings_override:
            # Be careful with merging, might need deep merge or specific logic
            logger.warning("Overriding default settings. Ensure structure matches 3x-ui expectations.")
            default_settings.update(settings_override)

        # Default stream settings (common example, needs verification)
        default_stream_settings = {
            "network": "tcp",
            "security": "none",
            "tcpSettings": {
                "header": {"type": "none"}
            }
        }
        if stream_settings_override:
            logger.warning("Overriding default stream settings. Ensure structure matches 3x-ui expectations.")
            default_stream_settings.update(stream_settings_override)
        
        # Default TLS settings (Only relevant if security is 'tls')
        default_tls_settings = {
            "serverName": "", 
            "certificates": []
        }
        if default_stream_settings.get("security") == "tls":
             if tls_settings_override:
                 logger.warning("Overriding default tls settings. Ensure structure matches 3x-ui expectations.")
                 default_tls_settings.update(tls_settings_override)
             default_stream_settings["tlsSettings"] = default_tls_settings # Add TLS settings if applicable
             default_stream_settings["security"] = "tls"
        elif default_stream_settings.get("security") == "reality":
            # Handling Reality needs its specific structure in streamSettings
            logger.warning("Reality stream settings override not fully implemented in placeholder.")
            # default_stream_settings["realitySettings"] = { ... }
            if tls_settings_override: # Reality might still use parts of tlsSettings like sni
                 default_stream_settings["realitySettings"] = default_stream_settings.get("realitySettings", {})
                 default_stream_settings["realitySettings"].update(tls_settings_override) # Example merge
        

        # Payload structure - THIS IS THE MOST UNCERTAIN PART
        payload = {
            "up": 0, # Initial upload (usually 0)
            "down": 0, # Initial download (usually 0)
            "total": total_bytes,
            "remark": remark,
            "enable": True,
            "expiryTime": expire_time,
            "listen": "", # Listen IP, often empty for default
            "port": port,
            "protocol": protocol,
            "settings": json.dumps(default_settings), # Settings often need to be JSON stringified
            "streamSettings": json.dumps(default_stream_settings), # Stream settings too
            "sniffing": json.dumps({"enabled": True, "destOverride": ["http", "tls"]}) # Default sniffing
        }

        logger.info(f"Constructed payload for add_inbound (remark: {remark}): {payload}")
        # --- End Payload Construction ---

        try:
            # Send as JSON, assuming 3x-ui expects JSON payload
            response = await self._make_request("POST", path, json=payload)
            result = response.json()
            if result.get("success"):
                logger.info(f"Successfully added inbound (remark: {remark}): {result.get('msg')}")
                return result.get("obj") # Contains details of the created inbound
            else:
                logger.error(f"Panel API reported failure on add_inbound (remark: {remark}): {result.get('msg')}")
                raise PanelClientError(f"Failed to add inbound: {result.get('msg')}")
        except (PanelClientError, ValueError, KeyError, json.JSONDecodeError) as e: # Catch JSON errors too
            logger.error(f"Error processing add_inbound (remark: {remark}): {e}")
            return None
        except Exception as e:
             logger.exception(f"Unexpected error in add_inbound for remark {remark}")
             raise PanelClientError("Add inbound failed due to an unexpected error.") from e

    # Example: Get list of inbounds
    async def get_inbounds(self) -> Optional[List[Dict[str, Any]]]:
        path = 'panel/api/inbounds/list'
        try:
            # Add explicit DEBUG logging before the request
            logger.debug(f"Attempting to fetch inbounds from {path}")
            
            # Make the request and explicitly catch known errors
            try:
                response = await self._make_request("GET", path)
            except PanelClientError as e:
                logger.error(f"Panel client error when fetching inbounds: {e}")
                raise # Re-raise to be caught by the outer try/except
            except Exception as e:
                logger.exception(f"Unexpected error during inbounds API request: {e}")
                raise PanelClientError(f"Failed to get inbounds: Unexpected error during request: {e}") from e
                
            # Add debug logging for successful response
            logger.debug(f"Received response from {path}, status: {response.status_code}")
            
            # Parse JSON, explicitly catching JSON errors
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from inbounds response: {e}")
                logger.debug(f"Response content: {response.text[:500]}")
                raise PanelClientError(f"Failed to parse inbounds response: Invalid JSON") from e
                
            if result.get("success"):
                logger.info(f"Successfully retrieved inbounds.")
                return result.get("obj")
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Panel API reported failure on get_inbounds: {error_msg}")
                raise PanelClientError(f"Failed to get inbounds: {error_msg}")
        except PanelClientError:
            # Re-raise PanelClientError without wrapping
            raise
        except Exception as e:
            # Catch and wrap any other unexpected errors
            logger.exception(f"Unexpected error in get_inbounds: {e}")
            raise PanelClientError(f"Failed to get inbounds: Unexpected error: {e}") from e

    # Add other methods: del_inbound, update_inbound, add_client, update_client, etc.
    # Remember to use the correct path from the API docs (e.g., 'panel/api/inbounds/del/:id')
    # and the appropriate HTTP method (POST for most actions, GET for reading).

    # Add methods for get_client_stats, update_client, delete_client etc.
    # Each will need the correct endpoint, method (GET/POST), payload, and cookie handling.

    async def add_client_to_inbound(self,
                                    inbound_id: int,
                                    remark: str,
                                    total_gb: int = 0,
                                    expire_time: int = 0, # Timestamp in ms, 0 for unlimited
                                    limit_ip: int = 0,
                                    flow: str = "xtls-rprx-vision", # Example flow, might need adjustment
                                    client_uuid: Optional[str] = None # Optionally provide UUID, otherwise generate
                                   ) -> Optional[Dict[str, Any]]:
        """
        Adds a new client to a specific existing inbound configuration.

        Args:
            inbound_id: The numerical ID of the inbound to add the client to.
            remark: Name or identifier for the client (used as 'email' in settings).
            total_gb: Traffic limit in GB. 0 for unlimited.
            expire_time: Expiration timestamp in milliseconds. 0 for unlimited.
            limit_ip: Limit concurrent IPs for the client (0 = unlimited).
            flow: Flow control setting (e.g., "xtls-rprx-vision"). Depends on inbound protocol/settings.
            client_uuid: Optional UUID string for the client. If None, a new UUID will be generated.

        Returns:
            A dictionary representing the success status or details from the panel API, or None on failure.
            The exact structure of the returned object upon success isn't fully known from docs.
        """
        path = f'panel/api/inbounds/{inbound_id}/addClient'

        # Generate UUID if not provided
        if not client_uuid:
            client_uuid = str(uuid.uuid4())

        # Convert GB to bytes
        total_bytes = total_gb * 1024 * 1024 * 1024 if total_gb > 0 else 0

        # Construct the inner 'settings' JSON object for the client
        client_settings_obj = {
            "clients": [
                {
                    "id": client_uuid,
                    "email": remark, # Using remark as email, common practice
                    "totalGB": total_bytes, # Note: Panel might expect 'totalGB' or just 'total'
                    "expiryTime": expire_time,
                    "limitIp": limit_ip,
                    "flow": flow,
                    # Add other potential fields if needed based on panel specifics
                    # "tgId": "",
                    # "subId": ""
                }
            ]
        }

        # Convert the inner settings object to a JSON string
        try:
            settings_str = json.dumps(client_settings_obj)
        except TypeError as e:
            logger.error(f"Could not serialize client settings to JSON: {e}")
            return None

        # Construct the main payload
        payload = {
            "id": inbound_id,
            "settings": settings_str
        }

        logger.info(f"Adding client to inbound {inbound_id} with payload: {payload}")

        try:
            response = await self._make_request("POST", path, json=payload)
            result = response.json()

            # Check success based on the typical 3x-ui response structure
            if result.get("success"):
                logger.info(f"Successfully added client (remark: {remark}, uuid: {client_uuid}) to inbound {inbound_id}: {result.get('msg')}")
                # Return the 'obj' if it exists and contains useful info, otherwise the whole result
                return result.get("obj") if result.get("obj") is not None else result
            else:
                error_msg = result.get('msg', 'Unknown error from panel')
                logger.error(f"Panel API reported failure on addClient (inbound: {inbound_id}, remark: {remark}): {error_msg}")
                raise PanelClientError(f"Failed to add client: {error_msg}")

        except (PanelClientError, ValueError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error processing addClient (inbound: {inbound_id}, remark: {remark}): {e}")
            return None
        except Exception as e:
             logger.exception(f"Unexpected error in addClient for inbound {inbound_id}, remark {remark}")
             raise PanelClientError("Add client failed due to an unexpected error.") from e

    # --- We might want to modify or remove the old add_inbound method now ---
    # async def add_inbound(...): <--- Review if this is still needed for creating listening ports

    # Add other methods: del_inbound, update_inbound, add_client, update_client, etc.
    # Remember to use the correct path from the API docs (e.g., 'panel/api/inbounds/del/:id')
    # and the appropriate HTTP method (POST for most actions, GET for reading).

    # Add methods for get_client_stats, update_client, delete_client etc.
    # Each will need the correct endpoint, method (GET/POST), payload, and cookie handling. 