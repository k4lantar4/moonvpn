#!/usr/bin/env python3
"""
Example script demonstrating the use of PanelOperationQueue for panel operations.

This script shows how to use the operation queue system for managing panel
operations, handling retries, and implementing graceful error handling.
"""

import asyncio
import logging
import random
from typing import Dict, Any, Tuple, List

from core.system.operation_queue import PanelOperationQueue, Operation
from integrations.panels.client import XuiPanelClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def add_client_operation(queue: PanelOperationQueue, panel_id: int, inbound_id: int, 
                              client_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Create a sample operation to add a client to an inbound."""
    operation = Operation(
        panel_id=panel_id,
        operation_type="add_client",
        payload={
            "inbound_id": inbound_id,
            "client_data": client_data
        },
        priority=1,  # Higher priority (1 is processed before 2)
        retry_count=0,
        max_retries=3
    )
    
    # Add the operation to the queue and wait for it to complete
    success, result = await queue.add_and_wait(operation)
    return success, result


async def delete_client_operation(queue: PanelOperationQueue, panel_id: int, inbound_id: int, 
                                 client_id: str) -> Tuple[bool, Dict[str, Any]]:
    """Create a sample operation to delete a client from an inbound."""
    operation = Operation(
        panel_id=panel_id,
        operation_type="delete_client",
        payload={
            "inbound_id": inbound_id,
            "client_id": client_id
        },
        priority=2,  # Lower priority than add operations
        retry_count=0,
        max_retries=3
    )
    
    # Add the operation to the queue and wait for it to complete
    success, result = await queue.add_and_wait(operation)
    return success, result


async def simulate_operation_processing(queue: PanelOperationQueue):
    """Simulate processing operations from the queue."""
    while True:
        try:
            # Get the next operation from the queue
            operation = await queue.get()
            if not operation:
                # No more operations in the queue for now
                await asyncio.sleep(0.5)
                continue
                
            logger.info(f"Processing operation: {operation.operation_type} (priority: {operation.priority})")
            
            # Simulate processing time
            await asyncio.sleep(1)
            
            # Simulate success or failure (80% success rate)
            if random.random() < 0.8:
                # Operation succeeded
                logger.info(f"✅ Operation {operation.operation_type} completed successfully")
                await queue.mark_completed(operation, {"status": "success", "message": "Operation completed"})
            else:
                # Operation failed
                logger.info(f"❌ Operation {operation.operation_type} failed, attempt {operation.retry_count + 1}")
                if operation.retry_count < operation.max_retries:
                    # Retry the operation
                    logger.info(f"🔄 Retrying operation {operation.operation_type}")
                    await queue.mark_failed(operation, can_retry=True)
                else:
                    # Operation failed permanently
                    logger.error(f"❌ Operation {operation.operation_type} failed permanently after {operation.retry_count + 1} attempts")
                    await queue.mark_failed(operation, can_retry=False, 
                                           result={"status": "error", "message": "Max retries exceeded"})
        
        except Exception as e:
            logger.error(f"Error processing operation: {str(e)}")
            await asyncio.sleep(1)
        

async def demo_with_operation_queue():
    """Demonstrate the operation queue functionality."""
    # Create a new operation queue
    queue = PanelOperationQueue()
    
    # Start the operation processor in the background
    processor_task = asyncio.create_task(simulate_operation_processing(queue))
    
    try:
        # Define some sample data
        panel_id = 1
        inbound_id = 2
        
        # Add multiple client operations to demonstrate priority handling
        logger.info("Adding operations to the queue...")
        
        # Create a list of sample clients
        sample_clients = [
            {
                "email": f"user{i}@example.com",
                "uuid": f"00000000-0000-0000-0000-{i:012d}",
                "limit": i * 10
            } for i in range(1, 6)
        ]
        
        # Add clients with different priorities
        add_tasks = []
        for i, client in enumerate(sample_clients):
            # Alternate between high and normal priority
            priority = 1 if i % 2 == 0 else 2
            
            # Create an operation
            operation = Operation(
                panel_id=panel_id,
                operation_type="add_client",
                payload={
                    "inbound_id": inbound_id,
                    "client_data": client
                },
                priority=priority,
                retry_count=0,
                max_retries=3
            )
            
            # Add to queue (don't wait)
            task = asyncio.create_task(queue.add(operation))
            add_tasks.append(task)
            logger.info(f"Added add_client operation for {client['email']} with priority {priority}")
        
        # Wait for all add operations to be queued
        await asyncio.gather(*add_tasks)
        
        # Show queue statistics
        stats = queue.get_statistics()
        logger.info(f"Queue statistics: {stats}")
        
        # Add a client with wait for completion
        logger.info("\nAdding a client and waiting for completion...")
        success, result = await add_client_operation(
            queue, 
            panel_id, 
            inbound_id, 
            {
                "email": "waituser@example.com",
                "uuid": "00000000-0000-0000-0000-999999999999",
                "limit": 100
            }
        )
        
        if success:
            logger.info(f"✅ Client added successfully with result: {result}")
        else:
            logger.error(f"❌ Failed to add client: {result}")
        
        # Delete the client we just added
        logger.info("\nDeleting the client we just added...")
        success, result = await delete_client_operation(
            queue,
            panel_id,
            inbound_id,
            "00000000-0000-0000-0000-999999999999"
        )
        
        if success:
            logger.info(f"✅ Client deleted successfully with result: {result}")
        else:
            logger.error(f"❌ Failed to delete client: {result}")
        
        # Wait a bit to allow more operations to complete
        logger.info("\nWaiting for remaining operations to complete...")
        await asyncio.sleep(10)
        
        # Show final queue statistics
        stats = queue.get_statistics()
        logger.info(f"Final queue statistics: {stats}")
        
    finally:
        # Cancel the processor task
        processor_task.cancel()
        try:
            await processor_task
        except asyncio.CancelledError:
            logger.info("Operation processor task cancelled")
        
        # Close the queue connection
        await queue.close()


async def main():
    """Run the demo."""
    try:
        logger.info("Starting operation queue demo...")
        await demo_with_operation_queue()
        logger.info("Demo completed successfully")
    except Exception as e:
        logger.error(f"Demo failed with error: {str(e)}")


if __name__ == "__main__":
    # Run the async demo
    asyncio.run(main()) 