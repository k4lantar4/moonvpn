"""Monitoring middleware for FastAPI."""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.services.monitoring_service import monitoring_service

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring request metrics."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process the request and record metrics."""
        start_time = time.time()
        
        # Get request information
        method = request.method
        endpoint = request.url.path
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            monitoring_service.record_request(
                method=method,
                endpoint=endpoint,
                status=response.status_code,
                duration=duration
            )
            
            # Update system metrics
            monitoring_service.update_system_metrics()
            
            return response
            
        except Exception as e:
            # Record error metrics
            monitoring_service.record_request(
                method=method,
                endpoint=endpoint,
                status=500,
                duration=time.time() - start_time
            )
            raise 