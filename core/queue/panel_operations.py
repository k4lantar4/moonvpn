"""
Panel Operations Queue

This module provides a queue system for panel operations to prevent
concurrent operations on the same panel and provide retries for failed operations.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Callable, Awaitable, Tuple
from datetime import datetime, timedelta
import uuid

import redis.asyncio as redis
from fastapi import HTTPException, status

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis connection pool
_redis_pool = None


async def get_redis() -> redis.Redis:
    """Get a Redis connection from the connection pool.
    
    Returns:
        redis.Redis: Redis connection
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True
        )
    
    return redis.Redis(connection_pool=_redis_pool)


class PanelOperationQueue:
    """Queue system for panel operations.
    
    This class provides methods for:
    - Queueing panel operations
    - Executing operations in order
    - Preventing concurrent operations on the same panel
    - Retrying failed operations
    """
    
    # Queue key prefixes
    QUEUE_PREFIX = f"{settings.CACHE_KEY_PREFIX}:panel:queue:"
    LOCK_PREFIX = f"{settings.CACHE_KEY_PREFIX}:panel:lock:"
    RESULT_PREFIX = f"{settings.CACHE_KEY_PREFIX}:panel:result:"
    
    # Default settings
    DEFAULT_TIMEOUT = 60  # seconds
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY = 2  # seconds
    DEFAULT_RESULT_TTL = 3600  # 1 hour
    
    @staticmethod
    async def enqueue_operation(
        panel_id: int,
        operation_type: str,
        operation_data: Dict[str, Any],
        priority: int = 0,
        timeout: int = DEFAULT_TIMEOUT,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_delay: int = DEFAULT_RETRY_DELAY
    ) -> str:
        """Enqueue a panel operation.
        
        Args:
            panel_id: Panel ID
            operation_type: Type of operation (e.g., "add_client", "update_client")
            operation_data: Operation data
            priority: Operation priority (higher number = higher priority)
            timeout: Operation timeout in seconds
            retry_count: Number of retries for failed operations
            retry_delay: Delay between retries in seconds
            
        Returns:
            str: Operation ID for tracking
        """
        redis_client = await get_redis()
        queue_key = f"{PanelOperationQueue.QUEUE_PREFIX}{panel_id}"
        
        # Generate a unique operation ID
        operation_id = str(uuid.uuid4())
        
        # Prepare operation metadata
        operation = {
            "id": operation_id,
            "panel_id": panel_id,
            "type": operation_type,
            "data": operation_data,
            "priority": priority,
            "timeout": timeout,
            "retry_count": retry_count,
            "retry_delay": retry_delay,
            "attempts": 0,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add to sorted set with score = priority
        await redis_client.zadd(
            queue_key,
            {json.dumps(operation): priority}
        )
        
        logger.debug(f"Enqueued {operation_type} operation for panel {panel_id}, ID: {operation_id}")
        return operation_id
    
    @staticmethod
    async def get_operation_status(operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a queued or completed operation.
        
        Args:
            operation_id: Operation ID
            
        Returns:
            Optional[Dict[str, Any]]: Operation status or None if not found
        """
        redis_client = await get_redis()
        
        # Check all panel queues
        all_queues = await redis_client.keys(f"{PanelOperationQueue.QUEUE_PREFIX}*")
        
        # Search in active queues
        for queue_key in all_queues:
            operations = await redis_client.zrange(queue_key, 0, -1)
            
            for op_json in operations:
                try:
                    op = json.loads(op_json)
                    if op.get("id") == operation_id:
                        return op
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Check in results
        result_key = f"{PanelOperationQueue.RESULT_PREFIX}{operation_id}"
        result = await redis_client.get(result_key)
        
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse result for operation {operation_id}")
        
        return None
    
    @staticmethod
    async def wait_for_operation(
        operation_id: str,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Dict[str, Any]:
        """Wait for operation to complete.
        
        Args:
            operation_id: Operation ID
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dict[str, Any]: Operation result
            
        Raises:
            HTTPException: If operation times out or fails
        """
        start_time = time.time()
        check_interval = 0.5  # seconds
        
        while time.time() - start_time < timeout:
            status = await PanelOperationQueue.get_operation_status(operation_id)
            
            if not status:
                await asyncio.sleep(check_interval)
                continue
            
            if status.get("status") == "completed":
                return status.get("result", {})
            
            if status.get("status") == "failed":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Operation failed: {status.get('error', 'Unknown error')}"
                )
            
            await asyncio.sleep(check_interval)
        
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Operation {operation_id} timed out"
        )
    
    @staticmethod
    async def execute_queued_operations(
        panel_id: int,
        executor: Callable[[Dict[str, Any]], Awaitable[Tuple[bool, Any]]],
        max_operations: int = 10
    ) -> int:
        """Execute queued operations for a panel.
        
        Args:
            panel_id: Panel ID
            executor: Function to execute operations
            max_operations: Maximum number of operations to process
            
        Returns:
            int: Number of operations processed
        """
        redis_client = await get_redis()
        queue_key = f"{PanelOperationQueue.QUEUE_PREFIX}{panel_id}"
        lock_key = f"{PanelOperationQueue.LOCK_PREFIX}{panel_id}"
        
        # Try to acquire lock
        locked = await redis_client.set(
            lock_key,
            "1",
            nx=True,
            ex=PanelOperationQueue.DEFAULT_TIMEOUT
        )
        
        if not locked:
            logger.debug(f"Could not acquire lock for panel {panel_id}, another process is executing operations")
            return 0
        
        try:
            # Get operations from queue (sorted by priority, highest first)
            operations = await redis_client.zrevrange(
                queue_key,
                0,
                max_operations - 1,
                withscores=True
            )
            
            if not operations:
                return 0
            
            processed_count = 0
            
            for op_json, _ in operations:
                try:
                    operation = json.loads(op_json)
                    
                    # Update operation status
                    operation["status"] = "processing"
                    operation["attempts"] += 1
                    operation["updated_at"] = datetime.utcnow().isoformat()
                    
                    # Remove from queue
                    await redis_client.zrem(queue_key, op_json)
                    
                    # Execute operation
                    success, result = await executor(operation)
                    
                    if success:
                        # Operation succeeded
                        operation["status"] = "completed"
                        operation["result"] = result
                        operation["completed_at"] = datetime.utcnow().isoformat()
                        
                        # Store result
                        result_key = f"{PanelOperationQueue.RESULT_PREFIX}{operation['id']}"
                        await redis_client.set(
                            result_key,
                            json.dumps(operation),
                            ex=PanelOperationQueue.DEFAULT_RESULT_TTL
                        )
                        
                        processed_count += 1
                        logger.debug(f"Successfully executed {operation['type']} operation for panel {panel_id}")
                    else:
                        # Operation failed
                        if operation["attempts"] < operation["retry_count"]:
                            # Re-queue with delay
                            operation["status"] = "pending"
                            operation["updated_at"] = datetime.utcnow().isoformat()
                            operation["next_attempt"] = (
                                datetime.utcnow() + timedelta(seconds=operation["retry_delay"])
                            ).isoformat()
                            
                            # Add back to queue with same priority
                            await redis_client.zadd(
                                queue_key,
                                {json.dumps(operation): operation.get("priority", 0)}
                            )
                            
                            logger.warning(
                                f"Operation {operation['type']} for panel {panel_id} failed, "
                                f"retrying ({operation['attempts']}/{operation['retry_count']})"
                            )
                        else:
                            # Max retries reached, mark as failed
                            operation["status"] = "failed"
                            operation["error"] = result
                            operation["updated_at"] = datetime.utcnow().isoformat()
                            
                            # Store result
                            result_key = f"{PanelOperationQueue.RESULT_PREFIX}{operation['id']}"
                            await redis_client.set(
                                result_key,
                                json.dumps(operation),
                                ex=PanelOperationQueue.DEFAULT_RESULT_TTL
                            )
                            
                            processed_count += 1
                            logger.error(
                                f"Operation {operation['type']} for panel {panel_id} "
                                f"failed after {operation['attempts']} attempts: {result}"
                            )
                
                except Exception as e:
                    logger.exception(f"Error processing operation from queue: {str(e)}")
            
            return processed_count
            
        finally:
            # Release lock
            await redis_client.delete(lock_key)
    
    @staticmethod
    async def clear_queue(panel_id: int) -> int:
        """Clear all queued operations for a panel.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            int: Number of operations cleared
        """
        redis_client = await get_redis()
        queue_key = f"{PanelOperationQueue.QUEUE_PREFIX}{panel_id}"
        
        # Get count of operations
        count = await redis_client.zcard(queue_key)
        
        # Clear queue
        await redis_client.delete(queue_key)
        
        logger.info(f"Cleared {count} operations from queue for panel {panel_id}")
        return count
    
    @staticmethod
    async def get_queue_length(panel_id: int) -> int:
        """Get number of operations in the queue for a panel.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            int: Number of operations in queue
        """
        redis_client = await get_redis()
        queue_key = f"{PanelOperationQueue.QUEUE_PREFIX}{panel_id}"
        
        return await redis_client.zcard(queue_key)
    
    @staticmethod
    async def is_queue_locked(panel_id: int) -> bool:
        """Check if panel operation queue is locked.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            bool: True if locked, False otherwise
        """
        redis_client = await get_redis()
        lock_key = f"{PanelOperationQueue.LOCK_PREFIX}{panel_id}"
        
        return bool(await redis_client.exists(lock_key))
    
    @staticmethod
    async def close():
        """Close Redis connection pool."""
        global _redis_pool
        if _redis_pool:
            await _redis_pool.disconnect()
            _redis_pool = None 