import httpx
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import logging # Import logging

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

    async def add_inbound(self, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """ Adds a new inbound/user configuration. """
        path = 'panel/api/inbounds/add' # Correct path based on docs
        try:
            response = await self._make_request("POST", path, json=settings)
            result = response.json()
            if result.get("success"):
                logger.info(f"Successfully added inbound: {result.get('msg')}")
                return result.get("obj")
            else:
                logger.error(f"Panel API reported failure on add_inbound: {result.get('msg')}")
                raise PanelClientError(f"Failed to add inbound: {result.get('msg')}")
        except (PanelClientError, ValueError, KeyError) as e: # Catch JSON errors too
            logger.error(f"Error processing add_inbound: {e}")
            # Return None or re-raise specific error based on desired handling
            return None

    # Example: Get list of inbounds
    async def get_inbounds(self) -> Optional[List[Dict[str, Any]]]:
        path = 'panel/api/inbounds/list'
        try:
            response = await self._make_request("GET", path)
            result = response.json()
            if result.get("success"):
                logger.info(f"Successfully retrieved inbounds.")
                return result.get("obj")
            else:
                logger.error(f"Panel API reported failure on get_inbounds: {result.get('msg')}")
                raise PanelClientError(f"Failed to get inbounds: {result.get('msg')}")
        except (PanelClientError, ValueError, KeyError) as e:
            logger.error(f"Error processing get_inbounds: {e}")
            return None

    # Add other methods: del_inbound, update_inbound, add_client, update_client, etc.
    # Remember to use the correct path from the API docs (e.g., 'panel/api/inbounds/del/:id')
    # and the appropriate HTTP method (POST for most actions, GET for reading).

    # Add methods for get_client_stats, update_client, delete_client etc.
    # Each will need the correct endpoint, method (GET/POST), payload, and cookie handling. 