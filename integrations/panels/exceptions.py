"""Panel integration specific exceptions."""

# Import the base CoreError if needed, or define a new base here
# For simplicity, let's define a new base specific to panel integrations
class PanelIntegrationError(Exception):
    """Base exception for errors during VPN panel interaction."""
    def __init__(self, message: str = "Panel integration error", status_code: int = 500):
        self.message = message
        self.status_code = status_code # Store status code if available
        super().__init__(self.message)

class PanelError(PanelIntegrationError):
    """General error related to panel operations."""
    pass

class PanelAuthenticationError(PanelIntegrationError):
    """Exception for authentication failures with the VPN panel."""
    pass

class PanelAPIError(PanelIntegrationError):
    """Exception for general API errors from the VPN panel."""
    pass

class PanelClientError(PanelIntegrationError):
    """Exception for client-side errors during panel interaction (e.g., network)."""
    pass

# You can add more specific panel errors here if needed
