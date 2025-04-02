from typing import Dict, Any, Optional
import json

from httpx import AsyncClient, Response, HTTPStatusError

class APIError(Exception):
    """Exception raised for API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class BaseAPIClient:
    """Base API client with common functionality."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            base_url: The base URL for the API.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url
        self.timeout = timeout
        
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Response:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: The API endpoint.
            params: Optional query parameters.
            
        Returns:
            The response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with AsyncClient(timeout=self.timeout) as client:
            return await client.get(url, params=params)
            
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Response:
        """
        Make a POST request to the API.
        
        Args:
            endpoint: The API endpoint.
            data: Optional form data.
            json_data: Optional JSON data.
            
        Returns:
            The response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with AsyncClient(timeout=self.timeout) as client:
            return await client.post(url, data=data, json=json_data)
            
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Response:
        """
        Make a PUT request to the API.
        
        Args:
            endpoint: The API endpoint.
            data: Optional form data.
            json_data: Optional JSON data.
            
        Returns:
            The response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with AsyncClient(timeout=self.timeout) as client:
            return await client.put(url, data=data, json=json_data)
            
    async def delete(self, endpoint: str) -> Response:
        """
        Make a DELETE request to the API.
        
        Args:
            endpoint: The API endpoint.
            
        Returns:
            The response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with AsyncClient(timeout=self.timeout) as client:
            return await client.delete(url)
            
    async def head(self, endpoint: str) -> Response:
        """
        Make a HEAD request to the API.
        
        Args:
            endpoint: The API endpoint.
            
        Returns:
            The response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with AsyncClient(timeout=self.timeout) as client:
            return await client.head(url)
    
    def _parse_error_response(self, response: Response) -> str:
        """
        Parse an error response from the API.
        
        Args:
            response: The API response.
            
        Returns:
            A string representation of the error.
        """
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                detail = error_data.get("detail")
                if detail:
                    if isinstance(detail, str):
                        return detail
                    return json.dumps(detail)
                message = error_data.get("message")
                if message:
                    return message
            return json.dumps(error_data)
        except (json.JSONDecodeError, ValueError):
            return response.text or f"HTTP {response.status_code}" 