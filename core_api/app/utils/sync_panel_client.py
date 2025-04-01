#!/usr/bin/env python3
import httpx
import json
import uuid
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the expected cookie name
PANEL_SESSION_COOKIE_NAME = "3x-ui"

class PanelClientError(Exception):
    """Custom exception for panel client errors."""
    pass

class SyncPanelClient:
    """
    Synchronous client for interacting with the 3x-ui panel API.
    This is a more reliable alternative to the async version if you encounter issues with asyncio.
    """
    def __init__(self, base_url: str, username: str, password: str, timeout: float = 10.0):
        """
        Initialize the panel client.
        
        Args:
            base_url: Base URL of the panel (e.g., 'http://example.com/path/')
            username: Admin username for the panel
            password: Admin password for the panel
            timeout: Request timeout in seconds
        """
        # Ensure base_url ends with a slash for proper URL joining
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'
        self.username = username
        self.password = password
        self.timeout = timeout
        self._session_cookie = None
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)
        logger.info(f"SyncPanelClient initialized for base URL: {self.base_url}")
    
    def __enter__(self):
        """Support context manager pattern (with statement)."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources when exiting context."""
        self.close()
        
    def close(self):
        """Close the underlying httpx client."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("SyncPanelClient closed.")
    
    def login(self) -> str:
        """
        Login to the panel and get a session cookie.
        
        Returns:
            Session cookie value
            
        Raises:
            PanelClientError: If login fails
        """
        if self._session_cookie:
            return self._session_cookie
            
        login_url = f"{self.base_url}login"
        login_data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            logger.info(f"Attempting login to {login_url} with username {self.username}")
            response = self._client.post(login_url, data=login_data)
            
            # Check status code
            if response.status_code != 200:
                logger.error(f"Login failed with status code: {response.status_code}")
                raise PanelClientError(f"Login failed: HTTP {response.status_code}")
                
            # Check for success in JSON response (if available)
            try:
                result = response.json()
                if not result.get("success", False):
                    error_msg = result.get("msg", "Unknown error")
                    logger.error(f"Login API reported failure: {error_msg}")
                    raise PanelClientError(f"Login failed: {error_msg}")
            except json.JSONDecodeError:
                # Some panels might not return JSON for login, so we continue
                logger.warning("Could not parse login response as JSON, continuing...")
                
            # Check for session cookie
            if PANEL_SESSION_COOKIE_NAME not in response.cookies:
                logger.error(f"Login response missing expected cookie: {PANEL_SESSION_COOKIE_NAME}")
                raise PanelClientError(f"Login successful but {PANEL_SESSION_COOKIE_NAME} cookie not found")
                
            # Store and return the cookie
            self._session_cookie = response.cookies.get(PANEL_SESSION_COOKIE_NAME)
            logger.info(f"Login successful. Session cookie '{PANEL_SESSION_COOKIE_NAME}' obtained.")
            return self._session_cookie
            
        except httpx.RequestError as e:
            logger.error(f"Network error during login: {e}")
            raise PanelClientError(f"Network error: {str(e)}")
        except Exception as e:
            if not isinstance(e, PanelClientError):
                logger.exception(f"Unexpected error during login: {e}")
                raise PanelClientError(f"Unexpected error: {str(e)}")
            raise
    
    def _ensure_logged_in(self):
        """Make sure we have a session cookie, logging in if necessary."""
        if not self._session_cookie:
            self.login()
        return self._session_cookie
    
    def _make_request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """
        Make an authenticated request to the panel API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path relative to base_url
            **kwargs: Additional arguments to pass to the HTTP client
            
        Returns:
            httpx.Response object
            
        Raises:
            PanelClientError: If the request fails
        """
        # Ensure we have a session cookie
        cookie = self._ensure_logged_in()
        
        # Prepare cookies
        cookies = kwargs.pop('cookies', {})
        cookies[PANEL_SESSION_COOKIE_NAME] = cookie
        
        # Build the full URL
        url = f"{self.base_url}{path}"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            response = self._client.request(method, url, cookies=cookies, **kwargs)
            
            # Check for HTTP errors
            if response.status_code >= 400:
                logger.error(f"Request failed: HTTP {response.status_code}")
                raise PanelClientError(f"Request failed: HTTP {response.status_code}")
                
            return response
            
        except httpx.RequestError as e:
            logger.error(f"Network error during {method} to {url}: {e}")
            raise PanelClientError(f"Network error: {str(e)}")
        except Exception as e:
            if not isinstance(e, PanelClientError):
                logger.exception(f"Unexpected error during {method} to {url}: {e}")
                raise PanelClientError(f"Unexpected error: {str(e)}")
            raise
    
    def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        Get list of all inbounds from the panel.
        
        Returns:
            List of inbound objects
            
        Raises:
            PanelClientError: If the request fails
        """
        try:
            logger.info("Fetching inbounds list")
            response = self._make_request("GET", "panel/api/inbounds/list")
            
            # Parse JSON response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse inbounds response as JSON: {e}")
                raise PanelClientError("Failed to parse response as JSON")
            
            # Check for success
            if not result.get("success", False):
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"API reported failure for get_inbounds: {error_msg}")
                raise PanelClientError(f"Failed to get inbounds: {error_msg}")
            
            # Extract and return the inbounds list
            inbounds = result.get("obj", [])
            logger.info(f"Successfully retrieved {len(inbounds)} inbounds")
            return inbounds
            
        except PanelClientError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in get_inbounds: {e}")
            raise PanelClientError(f"Failed to get inbounds: {str(e)}")
            
    def add_client_to_inbound(self, inbound_id: int, remark: str, total_gb: int = 1, 
                              expire_days: int = 30, limit_ip: int = 0, 
                              flow: str = "xtls-rprx-vision", client_uuid: str = None) -> Dict[str, Any]:
        """
        Add a new client to an existing inbound.
        
        Args:
            inbound_id: ID of the inbound to add the client to
            remark: Name/email for the client
            total_gb: Traffic limit in GB (0 for unlimited)
            expire_days: Days until expiration (0 for unlimited)
            limit_ip: Number of simultaneous connections allowed (0 for unlimited)
            flow: Flow setting for protocols that support it
            client_uuid: Custom UUID (generated if None)
            
        Returns:
            Dictionary with client information
            
        Raises:
            PanelClientError: If the request fails
        """
        try:
            # Generate UUID if not provided
            if not client_uuid:
                client_uuid = str(uuid.uuid4())
            
            # Calculate expiry timestamp (milliseconds since epoch)
            if expire_days > 0:
                expire_time = int((time.time() + (expire_days * 24 * 60 * 60)) * 1000)
            else:
                expire_time = 0
                
            # Convert GB to bytes
            total_bytes = total_gb * 1024 * 1024 * 1024 if total_gb > 0 else 0
            
            # Construct client settings
            client_settings = {
                "clients": [
                    {
                        "id": client_uuid,
                        "email": remark,
                        "totalGB": total_bytes,
                        "expiryTime": expire_time,
                        "limitIp": limit_ip,
                        "flow": flow
                    }
                ]
            }
            
            # Convert to JSON string
            settings_str = json.dumps(client_settings)
            
            # Prepare payload
            payload = {
                "id": inbound_id,
                "settings": settings_str
            }
            
            logger.info(f"Adding client '{remark}' to inbound {inbound_id}")
            response = self._make_request("POST", f"panel/api/inbounds/{inbound_id}/addClient", json=payload)
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse add_client response as JSON: {e}")
                raise PanelClientError("Failed to parse response as JSON")
            
            # Check success
            if not result.get("success", False):
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"API reported failure for add_client: {error_msg}")
                raise PanelClientError(f"Failed to add client: {error_msg}")
            
            # Return client info
            client_info = {
                "inbound_id": inbound_id,
                "uuid": client_uuid,
                "remark": remark,
                "total_gb": total_gb,
                "expire_days": expire_days,
                "expire_time_ms": expire_time,
                "limit_ip": limit_ip,
                "flow": flow,
                "response": result
            }
            
            logger.info(f"Successfully added client '{remark}' to inbound {inbound_id}")
            return client_info
            
        except PanelClientError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in add_client_to_inbound: {e}")
            raise PanelClientError(f"Failed to add client: {str(e)}")
    
    def get_client(self, inbound_id: int, client_email: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific client from an inbound by email/remark.
        
        Args:
            inbound_id: ID of the inbound
            client_email: Email/remark of the client to find
            
        Returns:
            Client information dictionary or None if not found
            
        Raises:
            PanelClientError: If the request fails
        """
        try:
            logger.info(f"Fetching client with email {client_email} from inbound {inbound_id}")
            
            # Get all clients from the inbound
            inbound = self.get_inbound_detail(inbound_id)
            if not inbound:
                logger.error(f"Could not find inbound with ID {inbound_id}")
                return None
                
            # Extract client information from settings
            settings = inbound.get("settings", {})
            clients = settings.get("clients", [])
            
            # Find the client with matching email/remark
            for client in clients:
                if client.get("email") == client_email:
                    logger.info(f"Found client with email {client_email}")
                    return client
                    
            logger.warning(f"Client with email {client_email} not found in inbound {inbound_id}")
            return None
            
        except PanelClientError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in get_client: {e}")
            raise PanelClientError(f"Failed to get client: {str(e)}")
            
    def get_inbound_detail(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific inbound.
        
        Args:
            inbound_id: ID of the inbound
            
        Returns:
            Inbound information dictionary or None if not found
            
        Raises:
            PanelClientError: If the request fails
        """
        try:
            logger.info(f"Fetching details for inbound {inbound_id}")
            response = self._make_request("GET", f"panel/api/inbounds/get/{inbound_id}")
            
            # Parse JSON response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse inbound detail response as JSON: {e}")
                raise PanelClientError("Failed to parse response as JSON")
            
            # Check for success
            if not result.get("success", False):
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"API reported failure for get_inbound_detail: {error_msg}")
                raise PanelClientError(f"Failed to get inbound detail: {error_msg}")
            
            # Extract and return the inbound detail
            inbound = result.get("obj", {})
            logger.info(f"Successfully retrieved inbound {inbound_id} details")
            return inbound
            
        except PanelClientError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in get_inbound_detail: {e}")
            raise PanelClientError(f"Failed to get inbound detail: {str(e)}")
    
    def remove_client(self, inbound_id: int, client_email: str) -> bool:
        """
        Remove a client from an inbound.
        
        Args:
            inbound_id: ID of the inbound
            client_email: Email/remark of the client to remove
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PanelClientError: If the request fails
        """
        try:
            logger.info(f"Removing client with email {client_email} from inbound {inbound_id}")
            
            # Get existing inbound with clients
            inbound = self.get_inbound_detail(inbound_id)
            if not inbound:
                logger.error(f"Could not find inbound with ID {inbound_id}")
                return False
                
            settings = inbound.get("settings", {})
            clients = settings.get("clients", [])
            
            # Find the client to remove
            client_found = False
            new_clients = []
            for client in clients:
                if client.get("email") == client_email:
                    client_found = True
                    logger.info(f"Found client {client_email} to remove")
                else:
                    new_clients.append(client)
                    
            if not client_found:
                logger.warning(f"Client {client_email} not found in inbound {inbound_id}")
                return False
                
            # Update the settings with the new clients list
            settings["clients"] = new_clients
            
            # Update the inbound with the modified settings
            response = self._make_request(
                "POST", 
                f"panel/api/inbounds/update/{inbound_id}",
                json=settings
            )
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                raise PanelClientError("Failed to parse response as JSON")
                
            # Check for success
            if not result.get("success", False):
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"API reported failure: {error_msg}")
                raise PanelClientError(f"Failed to remove client: {error_msg}")
                
            logger.info(f"Successfully removed client {client_email} from inbound {inbound_id}")
            return True
            
        except PanelClientError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in remove_client: {e}")
            raise PanelClientError(f"Failed to remove client: {str(e)}")
            
    def update_client(self, inbound_id: int, client_email: str, 
                     new_total_gb: Optional[int] = None, 
                     new_expire_days: Optional[int] = None,
                     new_limit_ip: Optional[int] = None) -> bool:
        """
        Update an existing client's settings.
        
        Args:
            inbound_id: ID of the inbound
            client_email: Email/remark of the client to update
            new_total_gb: New traffic limit in GB (None to keep current)
            new_expire_days: New expiration in days (None to keep current)
            new_limit_ip: New connection limit (None to keep current)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PanelClientError: If the request fails
        """
        try:
            logger.info(f"Updating client with email {client_email} in inbound {inbound_id}")
            
            # Get existing inbound with clients
            inbound = self.get_inbound_detail(inbound_id)
            if not inbound:
                logger.error(f"Could not find inbound with ID {inbound_id}")
                return False
                
            settings = inbound.get("settings", {})
            clients = settings.get("clients", [])
            
            # Find the client to update
            client_found = False
            
            for i, client in enumerate(clients):
                if client.get("email") == client_email:
                    client_found = True
                    logger.info(f"Found client {client_email} to update")
                    
                    # Update traffic limit if specified
                    if new_total_gb is not None:
                        total_bytes = new_total_gb * 1024 * 1024 * 1024 if new_total_gb > 0 else 0
                        client["totalGB"] = total_bytes
                        logger.info(f"Updated traffic limit to {new_total_gb} GB")
                        
                    # Update expiration if specified
                    if new_expire_days is not None:
                        if new_expire_days > 0:
                            expire_time = int((time.time() + (new_expire_days * 24 * 60 * 60)) * 1000)
                        else:
                            expire_time = 0
                        client["expiryTime"] = expire_time
                        logger.info(f"Updated expiration to {new_expire_days} days")
                        
                    # Update IP limit if specified
                    if new_limit_ip is not None:
                        client["limitIp"] = new_limit_ip
                        logger.info(f"Updated IP limit to {new_limit_ip}")
                        
                    # Update the client in the list
                    clients[i] = client
                    break
                    
            if not client_found:
                logger.warning(f"Client {client_email} not found in inbound {inbound_id}")
                return False
                
            # Update the settings with the modified client
            settings["clients"] = clients
            
            # Update the inbound with the modified settings
            response = self._make_request(
                "POST", 
                f"panel/api/inbounds/update/{inbound_id}",
                json=settings
            )
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                raise PanelClientError("Failed to parse response as JSON")
                
            # Check for success
            if not result.get("success", False):
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"API reported failure: {error_msg}")
                raise PanelClientError(f"Failed to update client: {error_msg}")
                
            logger.info(f"Successfully updated client {client_email} in inbound {inbound_id}")
            return True
            
        except PanelClientError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in update_client: {e}")
            raise PanelClientError(f"Failed to update client: {str(e)}")
    
    def enable_disable_client(self, inbound_id: int, client_email: str, enable: bool = True) -> bool:
        """
        Enable or disable a client.
        
        Args:
            inbound_id: ID of the inbound
            client_email: Email/remark of the client to update
            enable: True to enable, False to disable
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PanelClientError: If the request fails
        """
        try:
            action = "Enabling" if enable else "Disabling"
            logger.info(f"{action} client with email {client_email} in inbound {inbound_id}")
            
            # Get existing inbound with clients
            inbound = self.get_inbound_detail(inbound_id)
            if not inbound:
                logger.error(f"Could not find inbound with ID {inbound_id}")
                return False
                
            settings = inbound.get("settings", {})
            clients = settings.get("clients", [])
            
            # Find the client to update
            client_found = False
            
            for i, client in enumerate(clients):
                if client.get("email") == client_email:
                    client_found = True
                    logger.info(f"Found client {client_email} to {action.lower()}")
                    
                    # Set the enabled flag (if the panel supports it)
                    client["enable"] = enable
                    
                    # Alternative approach: set extremely low quota for disabled clients
                    if not enable:
                        # Set a tiny quota (1MB) to effectively disable
                        client["totalGB"] = 1024 * 1024  # 1MB
                    
                    # Update the client in the list
                    clients[i] = client
                    break
                    
            if not client_found:
                logger.warning(f"Client {client_email} not found in inbound {inbound_id}")
                return False
                
            # Update the settings with the modified client
            settings["clients"] = clients
            
            # Update the inbound with the modified settings
            response = self._make_request(
                "POST", 
                f"panel/api/inbounds/update/{inbound_id}",
                json=settings
            )
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                raise PanelClientError("Failed to parse response as JSON")
                
            # Check for success
            if not result.get("success", False):
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"API reported failure: {error_msg}")
                raise PanelClientError(f"Failed to {action.lower()} client: {error_msg}")
                
            logger.info(f"Successfully {action.lower()}d client {client_email} in inbound {inbound_id}")
            return True
            
        except PanelClientError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in enable_disable_client: {e}")
            raise PanelClientError(f"Failed to enable/disable client: {str(e)}")
            
    def get_client_traffic(self, inbound_id: int, client_email: str) -> Dict[str, Any]:
        """
        Get traffic usage statistics for a specific client.
        
        Args:
            inbound_id: ID of the inbound
            client_email: Email/remark of the client
            
        Returns:
            Dictionary with traffic statistics
            
        Raises:
            PanelClientError: If the request fails
        """
        try:
            logger.info(f"Fetching traffic statistics for client {client_email} in inbound {inbound_id}")
            
            # Note: This endpoint may vary depending on the panel version
            # Adjust the URL and response handling as needed
            response = self._make_request(
                "GET", 
                f"panel/api/inbounds/{inbound_id}/client/{client_email}/traffic"
            )
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                raise PanelClientError("Failed to parse response as JSON")
                
            # Check for success
            if not result.get("success", False):
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"API reported failure: {error_msg}")
                raise PanelClientError(f"Failed to get client traffic: {error_msg}")
                
            # Extract and return the traffic statistics
            traffic_stats = result.get("obj", {})
            logger.info(f"Successfully retrieved traffic statistics for client {client_email}")
            return traffic_stats
            
        except PanelClientError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in get_client_traffic: {e}")
            raise PanelClientError(f"Failed to get client traffic: {str(e)}")


# Example usage if this file is run directly
if __name__ == "__main__":
    import os
    import sys
    
    # Get credentials from environment
    base_url = os.getenv("PANEL_BASE_URL")
    username = os.getenv("PANEL_USERNAME")
    password = os.getenv("PANEL_PASSWORD")
    
    if not all([base_url, username, password]):
        print("Error: Missing environment variables.")
        print("Please set PANEL_BASE_URL, PANEL_USERNAME, and PANEL_PASSWORD.")
        sys.exit(1)
    
    # Use context manager for proper cleanup
    with SyncPanelClient(base_url, username, password) as client:
        try:
            # Login
            client.login()
            print("Login successful!")
            
            # Get inbounds
            inbounds = client.get_inbounds()
            print(f"Found {len(inbounds)} inbounds:")
            
            # Display inbounds
            for i, inbound in enumerate(inbounds):
                print(f"  {i+1}. ID: {inbound.get('id')}, "
                      f"Remark: {inbound.get('remark')}, "
                      f"Protocol: {inbound.get('protocol')}, "
                      f"Port: {inbound.get('port')}")
            
            # If there are inbounds, add a client to the first one
            if inbounds:
                first_inbound = inbounds[0]
                inbound_id = first_inbound.get('id')
                
                # Add client
                client_info = client.add_client_to_inbound(
                    inbound_id=inbound_id,
                    remark=f"TestClient_{int(time.time())}",
                    total_gb=1,
                    expire_days=7
                )
                
                print("\nClient added successfully!")
                print("Client information:")
                for key, value in client_info.items():
                    if key != 'response':  # Skip the full response object
                        print(f"  {key}: {value}")
            else:
                print("\nNo inbounds found. Please create an inbound in the panel first.")
                
        except PanelClientError as e:
            print(f"Panel error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc() 