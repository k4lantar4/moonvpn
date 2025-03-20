from typing import Any, Dict, List, Optional, Set
from app.core.cache import cache
import gc
import psutil
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ResourceOptimizer:
    """Resource optimizer for memory, connection pooling, and cleanup routines."""
    
    def __init__(self):
        """Initialize resource optimizer."""
        self.memory_threshold = 0.85  # 85% memory usage
        self.cleanup_interval = 300  # 5 minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        self._active_connections: Dict[str, Set[Any]] = {}
        self._connection_pools: Dict[str, Any] = {}
        
    async def start_cleanup(self) -> None:
        """Start cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
    async def stop_cleanup(self) -> None:
        """Stop cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
    async def _cleanup_loop(self) -> None:
        """Cleanup loop."""
        while True:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                continue
                
    async def _perform_cleanup(self) -> None:
        """Perform cleanup operations."""
        try:
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.memory_threshold:
                await self._cleanup_memory()
                
            # Cleanup expired connections
            await self._cleanup_connections()
            
            # Cleanup expired cache entries
            await self._cleanup_cache()
            
            # Run garbage collection
            gc.collect()
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            
    async def _cleanup_memory(self) -> None:
        """Cleanup memory usage."""
        try:
            # Clear unused cache entries
            await cache.clear()
            
            # Clear unused connection pools
            for pool in self._connection_pools.values():
                await pool.close()
            self._connection_pools.clear()
            
            # Clear unused active connections
            for connections in self._active_connections.values():
                connections.clear()
                
            # Run garbage collection
            gc.collect()
            
            logger.info("Memory cleanup completed")
        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")
            
    async def _cleanup_connections(self) -> None:
        """Cleanup expired connections."""
        try:
            for pool_id, connections in self._active_connections.items():
                # Remove closed connections
                connections = {conn for conn in connections if not conn.closed}
                self._active_connections[pool_id] = connections
                
            logger.info("Connection cleanup completed")
        except Exception as e:
            logger.error(f"Connection cleanup error: {e}")
            
    async def _cleanup_cache(self) -> None:
        """Cleanup expired cache entries."""
        try:
            # Get all cache keys
            keys = await cache.keys("*")
            
            # Check each key
            for key in keys:
                try:
                    # Try to get value to check if expired
                    value = await cache.get(key)
                    if value is None:
                        await cache.delete(key)
                except Exception:
                    # If error, try to delete key
                    await cache.delete(key)
                    
            logger.info("Cache cleanup completed")
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            
    async def register_connection(self, pool_id: str, connection: Any) -> None:
        """Register active connection."""
        if pool_id not in self._active_connections:
            self._active_connections[pool_id] = set()
        self._active_connections[pool_id].add(connection)
        
    async def unregister_connection(self, pool_id: str, connection: Any) -> None:
        """Unregister active connection."""
        if pool_id in self._active_connections:
            self._active_connections[pool_id].discard(connection)
            
    async def get_connection_pool(self, pool_id: str, create_func: callable) -> Any:
        """Get or create connection pool."""
        if pool_id not in self._connection_pools:
            self._connection_pools[pool_id] = await create_func()
        return self._connection_pools[pool_id]
        
    async def close_connection_pool(self, pool_id: str) -> None:
        """Close connection pool."""
        if pool_id in self._connection_pools:
            await self._connection_pools[pool_id].close()
            del self._connection_pools[pool_id]
            
    async def get_resource_stats(self) -> Dict[str, Any]:
        """Get resource usage statistics."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            return {
                "memory": {
                    "total": memory.total,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "percent": disk.percent
                },
                "connections": {
                    pool_id: len(connections)
                    for pool_id, connections in self._active_connections.items()
                },
                "pools": len(self._connection_pools)
            }
        except Exception as e:
            logger.error(f"Resource stats error: {e}")
            return {}
            
    async def optimize_resources(self) -> None:
        """Optimize resource usage."""
        try:
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.memory_threshold:
                await self._cleanup_memory()
                
            # Optimize connection pools
            for pool_id, pool in self._connection_pools.items():
                if hasattr(pool, "optimize"):
                    await pool.optimize()
                    
            # Run garbage collection
            gc.collect()
            
            logger.info("Resource optimization completed")
        except Exception as e:
            logger.error(f"Resource optimization error: {e}")
            
    async def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics."""
        try:
            return {
                "last_cleanup": datetime.now().isoformat(),
                "active_connections": sum(
                    len(connections)
                    for connections in self._active_connections.values()
                ),
                "connection_pools": len(self._connection_pools),
                "memory_usage": psutil.virtual_memory().percent
            }
        except Exception as e:
            logger.error(f"Cleanup stats error: {e}")
            return {} 