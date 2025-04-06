"""
3x-ui Panel API Client

This module provides a client for interacting with 3x-ui panel API.
It handles authentication, connection management, and provides methods
for various panel operations.
"""

import httpx
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
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
    
    This is a standalone function to test panel connectivity without
    creating a long-lived client.
    
    Args:
        url: Panel URL
        username: Admin username
        password: Admin password
        login_path: Login path (default: "/login")
    
    Returns:
        Dict[str, Any]: Connection test results with status and details
    """
    start_time = datetime.now()
    result = {
        "success": False,
        "url": url,
        "response_time_ms": None,
        "status": None,
        "error": None,
        "panel_info": None,
        "timestamp": start_time.isoformat()
    }
    
    try:
        async with XuiPanelClient(url, username, password, login_path) as client:
            # Test login
            login_success = await client.login()
            
            if not login_success:
                result["status"] = "auth_failed"
                result["error"] = "Authentication failed"
                return result
            
            # Get panel status
            success, status_data = await client.get_status()
            
            if success:
                result["success"] = True
                result["status"] = "healthy"
                result["panel_info"] = status_data
            else:
                result["status"] = "api_error"
                result["error"] = status_data.get("error", "Unknown API error")
    
    except httpx.ConnectError as e:
        result["status"] = "connect_error"
        result["error"] = f"Connection error: {str(e)}"
    except httpx.TimeoutException as e:
        result["status"] = "timeout"
        result["error"] = f"Connection timeout: {str(e)}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Unexpected error: {str(e)}"
    
    finally:
        # Calculate response time
        end_time = datetime.now()
        result["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
    return result


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
            "error": "Panel configuration is incomplete. Check PANEL1_* environment variables."
        }
    
    return await test_panel_connection(url, username, password)


# CLI test function
async def main():
    """CLI test function for panel connectivity."""
    print("Testing panel connection...")
    result = await test_default_panel_connection()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 