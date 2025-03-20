from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.core.cache import cache
import gzip
import json
from datetime import datetime

T = TypeVar('T')

class APIOptimizer:
    """API optimizer with response compression, pagination, and request caching."""
    
    def __init__(self):
        """Initialize API optimizer."""
        self._request_stats: Dict[str, int] = {
            "total": 0,
            "cached": 0,
            "compressed": 0,
            "errors": 0
        }
        
    async def get_cached_response(
        self,
        request: Request,
        cache_key: str,
        ttl: int = 300
    ) -> Optional[Response]:
        """Get cached response if available."""
        try:
            cached = await cache.get(cache_key)
            if cached:
                self._request_stats["cached"] += 1
                return JSONResponse(
                    content=cached,
                    headers={"X-Cache": "HIT"}
                )
            self._request_stats["total"] += 1
            return None
        except Exception as e:
            self._request_stats["errors"] += 1
            return None
            
    async def cache_response(
        self,
        response: Response,
        cache_key: str,
        ttl: int = 300
    ) -> None:
        """Cache response for future requests."""
        try:
            if isinstance(response, JSONResponse):
                await cache.set(cache_key, response.body, expire=ttl)
        except Exception as e:
            self._request_stats["errors"] += 1
            
    def compress_response(self, response: Response) -> Response:
        """Compress response if client supports gzip."""
        try:
            if isinstance(response, JSONResponse):
                response.headers["Content-Encoding"] = "gzip"
                response.body = gzip.compress(response.body)
                self._request_stats["compressed"] += 1
            return response
        except Exception as e:
            self._request_stats["errors"] += 1
            return response
            
    def paginate_response(
        self,
        items: List[Any],
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Paginate response data."""
        try:
            total = len(items)
            total_pages = (total + size - 1) // size
            start = (page - 1) * size
            end = start + size
            
            return {
                "data": items[start:end],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        except Exception as e:
            self._request_stats["errors"] += 1
            return {
                "data": [],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                }
            }
            
    def rate_limit_response(
        self,
        request: Request,
        limit: int = 100,
        window: int = 60
    ) -> Optional[Response]:
        """Check rate limit and return error response if exceeded."""
        try:
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}"
            
            # Get current count
            count = cache.get(key) or 0
            
            # Check limit
            if count >= limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too many requests",
                        "retry_after": window
                    },
                    headers={"Retry-After": str(window)}
                )
                
            # Increment count
            cache.set(key, count + 1, expire=window)
            return None
        except Exception as e:
            self._request_stats["errors"] += 1
            return None
            
    def get_request_stats(self) -> Dict[str, int]:
        """Get request statistics."""
        return self._request_stats.copy()
        
    def clear_request_stats(self) -> None:
        """Clear request statistics."""
        self._request_stats = {
            "total": 0,
            "cached": 0,
            "compressed": 0,
            "errors": 0
        }
        
    def get_cache_key(
        self,
        request: Request,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key from request."""
        try:
            key_parts = [
                request.method,
                request.url.path,
                json.dumps(request.query_params, sort_keys=True)
            ]
            
            if params:
                key_parts.append(json.dumps(params, sort_keys=True))
                
            return ":".join(key_parts)
        except Exception as e:
            self._request_stats["errors"] += 1
            return f"error:{datetime.now().timestamp()}"
            
    def should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached."""
        return (
            request.method == "GET"
            and not any(
                header in request.headers
                for header in ["Cache-Control", "Pragma"]
            )
        )
        
    def should_compress_response(
        self,
        request: Request,
        response: Response
    ) -> bool:
        """Determine if response should be compressed."""
        return (
            "gzip" in request.headers.get("Accept-Encoding", "")
            and isinstance(response, JSONResponse)
            and len(response.body) > 1024
        ) 