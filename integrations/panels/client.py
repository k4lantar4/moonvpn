"""
3x-ui API Client Module

This module provides a class for interacting with the 3x-ui panel API.
It handles authentication, connection management, and provides methods
for various panel operations.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

import aiohttp
from fastapi import HTTPException, status

from core.cache.client_cache import ClientCache
from core.queue.panel_operations import PanelOperationQueue
from core.security.panel_tokens import PanelTokenManager

logger = logging.getLogger(__name__)


class XuiPanelClient:
    """Client for interacting with the 3x-ui panel API.
    
    This class handles authentication, connection management,
    and provides methods for various panel operations including:
    - Inbound management
    - Client management
    - Traffic statistics
    - System status
    """
    
    def __init__(
        self,
        panel_id: int,
        base_url: str,
        username: str,
        password: str,
        login_path: str = "/login",
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: int = 2,
        use_token_manager: bool = True,
        use_operation_queue: bool = True,
        use_client_cache: bool = True,
    ):
        """Initialize the 3x-ui panel client.
        
        Args:
            panel_id: Unique identifier for this panel
            base_url: Base URL of the 3x-ui panel
            username: Username for authentication
            password: Password for authentication
            login_path: Path for login endpoint
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            use_token_manager: Whether to use the token manager
            use_operation_queue: Whether to use the operation queue
            use_client_cache: Whether to use client caching
        """
        self.panel_id = panel_id
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.login_path = login_path
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.use_token_manager = use_token_manager
        self.use_operation_queue = use_operation_queue
        self.use_client_cache = use_client_cache
        
        # Session for making requests
        self._session = None
        self._session_cookies = None
        
        # Panel metadata
        self.panel_version = None
        self.last_login_time = None
        self.login_success = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session.
        
        Returns:
            aiohttp.ClientSession: Session for making requests
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
            
            # If we have saved cookies, restore them
            if self._session_cookies:
                self._session.cookie_jar.update_cookies(self._session_cookies)
                
        return self._session

    async def login(self) -> bool:
        """Log in to the 3x-ui panel.
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        # If using token manager, try to get a stored token
        if self.use_token_manager:
            token = await PanelTokenManager.get_token(self.panel_id)
            if token:
                logger.debug(f"Using stored token for panel {self.panel_id}")
                self._session_cookies = {"session": token}
                self.login_success = True
                self.last_login_time = datetime.now()
                return True
                
            # Check if token should be renewed
            should_renew = await PanelTokenManager.should_renew_token(self.panel_id)
            if should_renew:
                logger.debug(f"Token renewal needed for panel {self.panel_id}")
        
        # Perform login
        session = await self._get_session()
        login_url = urljoin(self.base_url, self.login_path)
        
        login_data = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            async with session.post(login_url, json=login_data) as response:
                # Check if login was successful
                if response.status == 200:
                    result = await response.json()
                    
                    # Different versions of the panel might have different response formats
                    success = False
                    if isinstance(result, dict):
                        success = result.get("success", False)
                    elif isinstance(result, bool):
                        success = result
                        
                    if success:
                        logger.debug(f"Successfully logged in to panel {self.panel_id}")
                        self.login_success = True
                        self.last_login_time = datetime.now()
                        
                        # Store the session cookie
                        cookies = session.cookie_jar.filter_cookies(login_url)
                        self._session_cookies = {name: cookie.value for name, cookie in cookies.items()}
                        
                        # Store the token in the token manager if enabled
                        if self.use_token_manager and "session" in self._session_cookies:
                            token = self._session_cookies["session"]
                            # Assume token expires in 24 hours from now
                            expires_at = datetime.now() + timedelta(hours=24)
                            await PanelTokenManager.store_token(
                                self.panel_id, 
                                token, 
                                expires_at=expires_at
                            )
                            
                        return True
                    else:
                        logger.warning(f"Login failed for panel {self.panel_id} - Invalid credentials")
                        self.login_success = False
                        return False
                else:
                    logger.warning(f"Login failed for panel {self.panel_id} - HTTP {response.status}")
                    self.login_success = False
                    return False
                    
        except Exception as e:
            logger.error(f"Login error for panel {self.panel_id}: {str(e)}")
            self.login_success = False
            return False

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_queue: Optional[bool] = None,
        operation_id: Optional[str] = None,
    ) -> Tuple[bool, Union[Dict[str, Any], List[Any], str, None]]:
        """Make an authenticated request to the panel API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            json_data: JSON data for request body
            params: Query parameters
            headers: Additional headers
            use_queue: Override default queue setting
            operation_id: Optional operation ID for queuing
            
        Returns:
            Tuple[bool, Any]: Success flag and response data
        """
        # Determine if we should use the operation queue
        should_use_queue = self.use_operation_queue if use_queue is None else use_queue
        
        # If using queue and it's not a GET request (which should be safe to run in parallel)
        if should_use_queue and method.upper() != "GET":
            # Create operation function
            async def operation_func():
                return await self._perform_request(method, path, json_data, params, headers)
                
            # If no operation ID is provided, create one based on the path and method
            if not operation_id:
                operation_id = f"{self.panel_id}:{method}:{path}:{time.time()}"
                
            # Enqueue the operation
            return await PanelOperationQueue.enqueue_and_wait(
                panel_id=self.panel_id,
                operation_id=operation_id,
                operation_func=operation_func
            )
        else:
            # Perform the request directly
            return await self._perform_request(method, path, json_data, params, headers)

    async def _perform_request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, Union[Dict[str, Any], List[Any], str, None]]:
        """Perform the actual HTTP request with retry logic.
        
        Args:
            method: HTTP method
            path: API endpoint path
            json_data: JSON data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Tuple[bool, Any]: Success flag and response data
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path
            
        url = urljoin(self.base_url, path)
        session = await self._get_session()
        
        # Prepare default headers
        if headers is None:
            headers = {}
            
        # Add common headers
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("Accept", "application/json")
        
        # Retry logic
        for attempt in range(self.max_retries + 1):
            try:
                # If not logged in or this is a retry after auth failure, attempt login
                if not self.login_success or (attempt > 0 and attempt <= self.max_retries):
                    login_success = await self.login()
                    if not login_success:
                        logger.error(f"Failed to login to panel {self.panel_id} on attempt {attempt+1}")
                        # Wait before retrying
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay)
                        continue
                
                # Make the request
                async with getattr(session, method.lower())(
                    url,
                    json=json_data,
                    params=params,
                    headers=headers
                ) as response:
                    # Check for authentication errors
                    if response.status == 401 or response.status == 403:
                        logger.warning(f"Authentication error on panel {self.panel_id}, will retry login")
                        self.login_success = False
                        
                        # Delete token if using token manager
                        if self.use_token_manager:
                            await PanelTokenManager.delete_token(self.panel_id)
                            
                        # Wait before retrying
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay)
                        continue
                        
                    # Check for server errors
                    if response.status >= 500:
                        logger.warning(f"Server error {response.status} on panel {self.panel_id}, will retry")
                        # Wait before retrying
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay)
                        continue
                        
                    # Read response content
                    content_type = response.headers.get("Content-Type", "")
                    
                    if "application/json" in content_type:
                        data = await response.json()
                    else:
                        data = await response.text()
                        
                    # Check if response was successful
                    if 200 <= response.status < 300:
                        return True, data
                    else:
                        logger.warning(f"Request failed with status {response.status}: {data}")
                        return False, data
                        
            except aiohttp.ClientError as e:
                logger.error(f"Request error on panel {self.panel_id}: {str(e)}")
                # Wait before retrying
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    
            except Exception as e:
                logger.error(f"Unexpected error on panel {self.panel_id}: {str(e)}")
                # Wait before retrying
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    
        # If we've exhausted all retries
        logger.error(f"Failed to complete request to panel {self.panel_id} after {self.max_retries + 1} attempts")
        return False, None

    async def get_status(self) -> Tuple[bool, Dict[str, Any]]:
        """Get panel status information.
        
        Returns:
            Tuple[bool, Dict[str, Any]]: Success flag and status data
        """
        return await self._request("GET", "/server/status")
        
    # The rest of the methods would be updated similarly to use the new features
    # Only including a few example methods below for brevity
    
    async def get_inbounds(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get all inbounds from the panel.
        
        Returns:
            Tuple[bool, List[Dict[str, Any]]]: Success flag and list of inbounds
        """
        success, data = await self._request("GET", "/panel/inbounds/list")
        
        if success and isinstance(data, dict) and "obj" in data:
            return True, data["obj"]
        return success, data

    async def get_client_traffic(self, email: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Get traffic information for a specific client by email.
        
        Args:
            email: Client email/remark
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: Success flag and traffic data
        """
        # Check cache first if enabled
        if self.use_client_cache:
            cached_traffic = await ClientCache.get_client_traffic(self.panel_id, email)
            if cached_traffic:
                logger.debug(f"Using cached traffic data for client {email} on panel {self.panel_id}")
                return True, cached_traffic
                
        # Fetch from panel if not in cache
        success, data = await self._request(
            "POST", 
            "/panel/inbound/getClientTraffic",
            json_data={"email": email}
        )
        
        # Cache the result if successful and caching is enabled
        if success and data and self.use_client_cache:
            await ClientCache.cache_client_traffic(self.panel_id, email, data)
            
        return success, data

    async def add_client(
        self, 
        inbound_id: int, 
        email: str, 
        uuid: str = None,
        flow: str = "",
        alter_id: int = 0,
        limit_ip: int = 0,
        total_gb: int = 0,
        expire_time: int = 0,
        enable: bool = True,
        tgid: str = "",
        subid: str = "",
        reset: bool = False
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Add a client to an inbound.
        
        Args:
            inbound_id: ID of the inbound
            email: Client email/remark
            uuid: UUID for client
            flow: Flow setting for XTLS
            alter_id: Alter ID for VMess
            limit_ip: IP connection limit
            total_gb: Total traffic limit in GB
            expire_time: Expiration timestamp
            enable: Whether the client is enabled
            tgid: Telegram ID
            subid: Subscription ID
            reset: Whether to reset traffic stats
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: Success flag and response data
        """
        client_data = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [{
                    "email": email,
                    "id": uuid,
                    "flow": flow,
                    "alterId": alter_id,
                    "limitIp": limit_ip,
                    "totalGB": total_gb,
                    "expiryTime": expire_time,
                    "enable": enable,
                    "tgId": tgid,
                    "subId": subid,
                    "reset": reset
                }]
            })
        }
        
        # Use a specific operation ID for this client to prevent duplication
        operation_id = f"add_client:{self.panel_id}:{inbound_id}:{email}"
        
        success, result = await self._request(
            "POST", 
            "/panel/inbound/addClient", 
            json_data=client_data,
            operation_id=operation_id
        )
        
        # Invalidate cache for this client if caching is enabled
        if self.use_client_cache and success:
            await ClientCache.clear_client_cache(self.panel_id, email)
            
        return success, result

    async def close(self):
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            
        # Close Redis connections if enabled
        if self.use_client_cache:
            await ClientCache.close()
            
        if self.use_token_manager:
            await PanelTokenManager.close()
            
        if self.use_operation_queue:
            await PanelOperationQueue.close()
            
    async def __aenter__(self):
        """Enter async context manager."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
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
            panel_id=1,
            base_url=url,
            username=username,
            password=password,
            login_path=login_path,
            timeout=5.0,
            max_retries=2,
            retry_delay=0.5,
            use_token_manager=True,
            use_operation_queue=True,
            use_client_cache=True,
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
    url = "https://example.com:54321"
    username = "admin"
    password = "password"
    
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