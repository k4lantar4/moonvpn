"""
Base manager classes for service integration.
"""
from typing import Any, Dict, Optional
from datetime import datetime
import asyncio
import logging
from fastapi import HTTPException

from app.core.config import settings
from app.core.cache import Cache
from app.core.metrics import MetricsCollector
from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class BaseManager:
    """Base class for all service managers."""
    
    def __init__(self):
        self.cache = Cache()
        self.metrics = MetricsCollector()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the manager and its dependencies."""
        if self._initialized:
            return
            
        try:
            await self.cache.initialize()
            await self.metrics.initialize()
            await self._initialize_resources()
            self._initialized = True
            logger.info(f"{self.__class__.__name__} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.__class__.__name__}: {str(e)}")
            raise ServiceError(f"Initialization failed: {str(e)}")
            
    async def _initialize_resources(self) -> None:
        """Initialize manager-specific resources. Override in subclasses."""
        pass
        
    async def cleanup(self) -> None:
        """Cleanup manager resources."""
        try:
            await self.cache.cleanup()
            await self.metrics.cleanup()
            await self._cleanup_resources()
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Failed to cleanup {self.__class__.__name__}: {str(e)}")
            raise ServiceError(f"Cleanup failed: {str(e)}")
            
    async def _cleanup_resources(self) -> None:
        """Cleanup manager-specific resources. Override in subclasses."""
        pass
        
    def _check_initialized(self) -> None:
        """Check if manager is initialized."""
        if not self._initialized:
            raise ServiceError(f"{self.__class__.__name__} not initialized")

class ServiceManager(BaseManager):
    """Base class for service-specific managers."""
    
    def __init__(self):
        super().__init__()
        self.retry_count = settings.SERVICE_RETRY_COUNT
        self.retry_delay = settings.SERVICE_RETRY_DELAY
        
    async def execute_with_retry(
        self,
        operation: str,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with retry logic."""
        self._check_initialized()
        
        for attempt in range(self.retry_count):
            try:
                start_time = datetime.utcnow()
                result = await func(*args, **kwargs)
                
                # Record metrics
                duration = (datetime.utcnow() - start_time).total_seconds()
                await self.metrics.record_operation(
                    operation=operation,
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                logger.error(
                    f"Attempt {attempt + 1}/{self.retry_count} failed for {operation}: {str(e)}"
                )
                
                # Record error metrics
                await self.metrics.record_error(
                    operation=operation,
                    error=str(e)
                )
                
                if attempt == self.retry_count - 1:
                    raise ServiceError(f"{operation} failed after {self.retry_count} attempts: {str(e)}")
                    
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                
    async def get_cached_data(
        self,
        key: str,
        fetch_func: callable,
        ttl: int = 300,
        *args,
        **kwargs
    ) -> Any:
        """Get data from cache or fetch and cache it."""
        self._check_initialized()
        
        try:
            # Try to get from cache
            cached_data = await self.cache.get(key)
            if cached_data is not None:
                await self.metrics.record_cache_hit(key)
                return cached_data
                
            # Fetch fresh data
            data = await fetch_func(*args, **kwargs)
            
            # Cache the data
            await self.cache.set(key, data, ttl=ttl)
            await self.metrics.record_cache_miss(key)
            
            return data
            
        except Exception as e:
            logger.error(f"Cache operation failed for key {key}: {str(e)}")
            await self.metrics.record_error(f"cache_{key}", str(e))
            
            # Fallback to direct fetch
            return await fetch_func(*args, **kwargs)
            
    async def invalidate_cache(self, key: str) -> None:
        """Invalidate cached data."""
        self._check_initialized()
        
        try:
            await self.cache.delete(key)
            await self.metrics.record_cache_invalidation(key)
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for key {key}: {str(e)}")
            await self.metrics.record_error(f"cache_invalidate_{key}", str(e))
            raise ServiceError(f"Cache invalidation failed: {str(e)}")
            
class ResourceManager(ServiceManager):
    """Base class for resource-specific managers."""
    
    def __init__(self):
        super().__init__()
        self.resource_type = self.__class__.__name__.lower().replace("manager", "")
        
    async def create_resource(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource."""
        return await self.execute_with_retry(
            operation=f"create_{self.resource_type}",
            func=self._create_resource,
            data=data
        )
        
    async def _create_resource(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create resource implementation. Override in subclasses."""
        raise NotImplementedError
        
    async def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get a resource by ID."""
        return await self.execute_with_retry(
            operation=f"get_{self.resource_type}",
            func=self._get_resource,
            resource_id=resource_id
        )
        
    async def _get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get resource implementation. Override in subclasses."""
        raise NotImplementedError
        
    async def update_resource(
        self,
        resource_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a resource."""
        return await self.execute_with_retry(
            operation=f"update_{self.resource_type}",
            func=self._update_resource,
            resource_id=resource_id,
            data=data
        )
        
    async def _update_resource(
        self,
        resource_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update resource implementation. Override in subclasses."""
        raise NotImplementedError
        
    async def delete_resource(self, resource_id: str) -> None:
        """Delete a resource."""
        await self.execute_with_retry(
            operation=f"delete_{self.resource_type}",
            func=self._delete_resource,
            resource_id=resource_id
        )
        
    async def _delete_resource(self, resource_id: str) -> None:
        """Delete resource implementation. Override in subclasses."""
        raise NotImplementedError 