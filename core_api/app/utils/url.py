from fastapi import Request
from app.core.config import settings

def get_base_url(request: Request) -> str:
    """
    Get the base URL of the current request.
    This is useful for generating absolute URLs for affiliate links.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The base URL (e.g., "https://example.com")
    """
    # Try to get from settings first
    if settings.FRONTEND_BASE_URL:
        return settings.FRONTEND_BASE_URL.rstrip('/')
    
    # Otherwise construct from request
    http_protocol = "https" if request.url.scheme == "https" else "http"
    host = request.headers.get("host", "localhost")
    
    return f"{http_protocol}://{host}" 