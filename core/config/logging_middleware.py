"""Logging middleware for FastAPI."""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.utils.logger import log_access

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging access information."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process the request and log access information."""
        start_time = time.time()
        
        # Get request information
        user_id = getattr(request.state, "user_id", None)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        endpoint = request.url.path
        method = request.method
        
        # Process the request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log access information
        log_access(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            status_code=response.status_code,
            response_time=response_time,
        )
        
        return response 