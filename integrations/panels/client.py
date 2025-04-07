"""
3x-ui Panel API Client

This module provides a client for interacting with 3x-ui panel API.
It handles authentication, connection management, and provides methods
for various panel operations.
"""

import httpx
import logging
import json
import backoff
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List, Union
from urllib.parse import urljoin
import asyncio
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class XuiPanelClient:
    """Client for interacting with 3x-ui panel API.
    
    This client handles authentication and provides methods for various panel operations.
    It includes connection pooling, error handling, and automatic retries.
    """
    
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str, 
        login_path: str = "/login",
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize a new XuiPanelClient.
        
        Args:
            base_url: Base URL of the 3x-ui panel (e.g., "https://example.com:54321")
            username: Admin username for the panel
            password: Admin password for the panel
            login_path: Path for the login endpoint (default: "/login")
            timeout: Request timeout in seconds (default: 10.0)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.login_path = login_path
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Session data
        self.session_cookie = None
        self.last_login = None
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        
        # Base API path for 3x-ui panel
        self.api_base_path = "/panel/api/inbounds"
    
    async def login(self) -> bool:
        """Log in to the 3x-ui panel.
        
        Returns:
            bool: True if login was successful, False otherwise.
        """
        try:
            login_url = urljoin(self.base_url, self.login_path)
            data = {
                "username": self.username,
                "password": self.password
            }
            
            response = await self.client.post(login_url, json=data)
            
            if response.status_code == 200:
                # Check response content - most 3x-ui panels return success status in JSON
                try:
                    result = response.json()
                    if result.get("success", False):
                        # Store session cookie if available
                        if 'Cookie' in response.headers:
                            self.session_cookie = response.headers['Cookie']
                        elif 'Set-Cookie' in response.headers:
                            self.session_cookie = response.headers['Set-Cookie']
                        
                        self.last_login = datetime.now()
                        logger.info(f"Successfully logged in to panel: {self.base_url}")
                        return True
                except json.JSONDecodeError:
                    # Some panels might not return JSON
                    # Check for successful login by checking cookies
                    if response.cookies:
                        self.session_cookie = "; ".join([f"{c.name}={c.value}" for c in response.cookies.jar])
                        self.last_login = datetime.now()
                        logger.info(f"Successfully logged in to panel: {self.base_url}")
                        return True
            
            logger.error(f"Login failed for panel {self.base_url}: Status {response.status_code}")
            return False
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during login to {self.base_url}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during login to {self.base_url}: {str(e)}")
            return False
    
    async def _request(
        self, 
        method: str, 
        path: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_auth: bool = True
    ) -> Tuple[bool, Any]:
        """Make an authenticated request to the panel API.
        
        Args:
            method: HTTP method ("GET", "POST", etc.)
            path: API path (will be joined with base URL)
            data: Request payload (for POST, PUT, etc.)
            params: Query parameters (for GET)
            retry_auth: Whether to retry with fresh auth if session expired
            
        Returns:
            Tuple[bool, Any]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Any: Response data (if successful) or error details
        """
        # Ensure we're logged in
        if not self.session_cookie and not await self.login():
            return False, {"error": "Failed to login to panel"}
        
        url = urljoin(self.base_url, path)
        headers = {}
        if self.session_cookie:
            headers["Cookie"] = self.session_cookie
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = await self.client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await self.client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await self.client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await self.client.delete(url, headers=headers)
                else:
                    return False, {"error": f"Unsupported HTTP method: {method}"}
                
                # Handle response
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if "success" in result and result["success"]:
                            return True, result.get("obj", {})
                        return False, {"error": result.get("msg", "API returned unsuccessful status")}
                    except json.JSONDecodeError:
                        if response.text.strip():
                            return True, response.text
                        return True, {}  # Empty response but successful status code
                
                # Handle authentication errors
                elif response.status_code in (401, 403) and retry_auth:
                    logger.warning(f"Authentication failed for {url}, attempting to re-login")
                    if await self.login():
                        # Update headers with new session cookie
                        headers["Cookie"] = self.session_cookie
                        # Don't increment attempt counter, as this is a special case
                        continue
                    else:
                        return False, {"error": "Re-authentication failed"}
                
                # Server errors might be temporary, so retry
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code} for {url}, attempt {attempt + 1}/{self.max_retries}")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                
                # Other client errors
                else:
                    return False, {
                        "error": f"HTTP error {response.status_code}",
                        "details": response.text
                    }
                
            except httpx.TimeoutException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request timeout for {url}, retrying ({attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                return False, {"error": f"Request timed out after {self.max_retries} attempts: {str(e)}"}
            
            except httpx.HTTPError as e:
                logger.error(f"HTTP error for {url}: {str(e)}")
                return False, {"error": f"HTTP error: {str(e)}"}
            
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {str(e)}")
                return False, {"error": f"Unexpected error: {str(e)}"}
        
        # If we've exhausted all retries
        return False, {"error": f"Request failed after {self.max_retries} attempts"}

    async def get_status(self) -> Tuple[bool, Dict[str, Any]]:
        """Get panel status information.
        
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Panel status information (if successful) or error details
        """
        # Ensure we're logged in
        if not self.session_cookie and not await self.login():
            return False, {"error": "Failed to login to panel"}
        
        try:
            # For 3x-ui, the status endpoint is typically at /server/status
            status_url = urljoin(self.base_url, "/server/status")
            
            headers = {}
            if self.session_cookie:
                headers["Cookie"] = self.session_cookie
            
            response = await self.client.get(status_url, headers=headers)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success", False):
                        return True, result.get("obj", {})
                    return False, {"error": "Panel returned unsuccessful status"}
                except json.JSONDecodeError:
                    return False, {"error": "Failed to parse response from panel"}
            elif response.status_code == 401:
                # Try to login again and retry once
                if await self.login():
                    return await self.get_status()
                return False, {"error": "Authentication failed"}
            else:
                return False, {"error": f"Failed to get status: HTTP {response.status_code}"}
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting status from {self.base_url}: {str(e)}")
            return False, {"error": f"HTTP error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error getting status from {self.base_url}: {str(e)}")
            return False, {"error": f"Unexpected error: {str(e)}"}

    # ----- Inbound Management API Methods -----
    
    async def get_inbounds(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get all inbounds from the panel.
        
        Returns:
            Tuple[bool, List[Dict[str, Any]]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - List: List of inbound configurations or error details
        """
        return await self._request("GET", f"{self.api_base_path}/list")
    
    async def get_inbound(self, inbound_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Get a specific inbound by ID.
        
        Args:
            inbound_id: The ID of the inbound to retrieve
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Inbound configuration or error details
        """
        return await self._request("GET", f"{self.api_base_path}/get/{inbound_id}")
    
    async def add_inbound(self, inbound_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Add a new inbound to the panel.
        
        Args:
            inbound_config: Configuration for the new inbound
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/add", data=inbound_config)
    
    async def update_inbound(self, inbound_id: int, inbound_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Update an existing inbound.
        
        Args:
            inbound_id: The ID of the inbound to update
            inbound_config: New configuration for the inbound
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/update/{inbound_id}", data=inbound_config)
    
    async def delete_inbound(self, inbound_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Delete an inbound.
        
        Args:
            inbound_id: The ID of the inbound to delete
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/del/{inbound_id}")

    # ----- Client Management API Methods -----
    
    async def add_client(self, client_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Add a client to an inbound.
        
        Args:
            client_config: Configuration for the new client including inbound ID
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/addClient", data=client_config)
    
    async def delete_client(self, inbound_id: int, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Delete a client from an inbound.
        
        Args:
            inbound_id: The ID of the inbound containing the client
            client_id: The ID (UUID) of the client to delete
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/{inbound_id}/delClient/{client_id}")
    
    async def update_client(self, client_id: str, client_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Update a client's configuration.
        
        Args:
            client_id: The ID (UUID) of the client to update
            client_config: New configuration for the client
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/updateClient/{client_id}", data=client_config)
    
    async def get_client_traffics(self, email: str) -> Tuple[bool, Dict[str, Any]]:
        """Get traffic statistics for a client by email.
        
        Args:
            email: The email of the client
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Traffic statistics or error details
        """
        return await self._request("GET", f"{self.api_base_path}/getClientTraffics/{email}")
    
    async def get_client_traffics_by_id(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Get traffic statistics for a client by ID.
        
        Args:
            client_id: The ID of the client
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Traffic statistics or error details
        """
        return await self._request("GET", f"{self.api_base_path}/getClientTrafficsById/{client_id}")
    
    async def reset_client_traffic(self, inbound_id: int, email: str) -> Tuple[bool, Dict[str, Any]]:
        """Reset traffic statistics for a client.
        
        Args:
            inbound_id: The ID of the inbound containing the client
            email: The email of the client
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/{inbound_id}/resetClientTraffic/{email}")
    
    async def get_client_ips(self, email: str) -> Tuple[bool, Dict[str, Any]]:
        """Get IP addresses used by a client.
        
        Args:
            email: The email of the client
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: IP address information or error details
        """
        return await self._request("POST", f"{self.api_base_path}/clientIps/{email}")
    
    async def clear_client_ips(self, email: str) -> Tuple[bool, Dict[str, Any]]:
        """Clear recorded IP addresses for a client.
        
        Args:
            email: The email of the client
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/clearClientIps/{email}")

    # ----- Traffic Management API Methods -----
    
    async def reset_all_traffics(self) -> Tuple[bool, Dict[str, Any]]:
        """Reset traffic statistics for all inbounds.
        
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/resetAllTraffics")
    
    async def reset_all_client_traffics(self, inbound_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Reset traffic statistics for all clients in an inbound.
        
        Args:
            inbound_id: The ID of the inbound
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/resetAllClientTraffics/{inbound_id}")

    # ----- System Operations API Methods -----
    
    async def create_backup(self) -> Tuple[bool, Dict[str, Any]]:
        """Create a backup of the panel.
        
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Backup information or error details
        """
        return await self._request("GET", f"{self.api_base_path}/createbackup")
    
    async def delete_depleted_clients(self, inbound_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Delete clients with depleted quotas from an inbound.
        
        Args:
            inbound_id: The ID of the inbound (use -1 for all inbounds)
            
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - Dict: Result data or error details
        """
        return await self._request("POST", f"{self.api_base_path}/delDepletedClients/{inbound_id}")
    
    async def get_online_clients(self) -> Tuple[bool, List[str]]:
        """Get a list of online clients.
        
        Returns:
            Tuple[bool, List[str]]: A tuple containing:
                - bool: True if the request was successful, False otherwise
                - List: List of online client emails or error details
        """
        success, result = await self._request("POST", f"{self.api_base_path}/onlines")
        if success and isinstance(result, list):
            return True, result
        return success, result
    
    async def close(self):
        """Close the client session."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Support for async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the client when exiting context."""
        await self.close()


async def test_panel_connection(
    url: str,
    username: str,
    password: str,
    login_path: str = "/login"
) -> Dict[str, Any]:
    """Test connection to a 3x-ui panel.
    
    This function attempts to connect to a 3x-ui panel and perform basic operations
    to verify that the panel is operational.
    
    Args:
        url: Panel URL (e.g., "https://example.com:54321")
        username: Admin username
        password: Admin password
        login_path: Path for login endpoint (default: "/login")
        
    Returns:
        Dict[str, Any]: Test result dictionary with the following keys:
            - success: True if the test was successful, False otherwise
            - status: Status of the panel ("healthy", "error", etc.)
            - error: Error message if the test failed
            - response_time_ms: Response time in milliseconds
            - inbounds_count: Number of inbounds if available
            - version: Panel version if available
    """
    try:
        logger.info(f"Testing connection to panel at {url}")
        start_time = datetime.now()
        
        # Create client with short timeout and few retries
        client = XuiPanelClient(
            base_url=url,
            username=username,
            password=password,
            login_path=login_path,
            timeout=5.0,
            max_retries=2,
            retry_delay=0.5
        )
        
        # Try to login
        login_result = await client.login()
        if not login_result:
            return {
                "success": False,
                "status": "error",
                "error": "Login failed",
                "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
        
        # Get inbounds to verify API access
        inbounds_success, inbounds = await client.get_inbounds()
        
        # Get panel status if available
        status_success, status = await client.get_status()
        
        # Check online clients
        clients_success, online_clients = await client.get_online_clients()
        
        # Close the client
        await client.close()
        
        # Calculate response time
        response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Build result
        result = {
            "success": True,
            "status": "healthy",
            "response_time_ms": response_time_ms,
            "tested_at": datetime.now().isoformat(),
        }
        
        # Add inbounds info if available
        if inbounds_success:
            result["inbounds_count"] = len(inbounds)
            result["inbounds_available"] = True
        else:
            result["inbounds_available"] = False
        
        # Add status info if available
        if status_success:
            result["system_status"] = status
            if "version" in status:
                result["version"] = status["version"]
        
        # Add online clients info if available
        if clients_success:
            result["online_clients_count"] = len(online_clients)
        
        logger.info(f"Panel connection test successful: {url}")
        return result
        
    except Exception as e:
        logger.error(f"Error testing panel connection: {str(e)}")
        return {
            "success": False,
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000 
                if 'start_time' in locals() else 0
        }


# Simple function to test connection using environment variables
async def test_default_panel_connection() -> Dict[str, Any]:
    """Test connection to the default panel configured in environment variables.
    
    Returns:
        Dict[str, Any]: Connection test results with status and details
    """
    url = settings.PANEL1_URL
    username = settings.PANEL1_USERNAME
    password = settings.PANEL1_PASSWORD
    
    if not all([url, username, password]):
        return {
            "success": False,
            "status": "config_error",
            "error": "Missing panel configuration in environment variables"
        }
    
    return await test_panel_connection(url, username, password)


async def main():
    """Run a test connection to the default panel."""
    result = await test_default_panel_connection()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main()) 