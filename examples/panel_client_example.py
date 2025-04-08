#!/usr/bin/env python3
"""
Example script demonstrating the use of XuiPanelClient for XUI panel interactions.

This script shows how to use the XuiPanelClient to connect to a panel,
fetch data, and perform various operations on inbounds and clients.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from integrations.panels.client import XuiPanelClient
from integrations.panels.types import InboundInfo, ClientInfo, ClientStats

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def display_inbound_details(client: XuiPanelClient, inbound_id: int):
    """Fetch and display details for a specific inbound."""
    try:
        logger.info(f"Fetching details for inbound ID: {inbound_id}")
        inbound = await client.get_inbound(inbound_id)
        
        if not inbound:
            logger.error(f"❌ Inbound with ID {inbound_id} not found")
            return
        
        logger.info(f"📝 Inbound Details:")
        logger.info(f"  ID: {inbound.id}")
        logger.info(f"  Tag: {inbound.tag}")
        logger.info(f"  Protocol: {inbound.protocol}")
        logger.info(f"  Port: {inbound.port}")
        logger.info(f"  Network: {inbound.network}")
        logger.info(f"  Enable: {inbound.enable}")
        
        # Get clients for this inbound
        clients = await client.list_clients(inbound_id)
        logger.info(f"  Total Clients: {len(clients)}")
        
        # Display first 3 clients (if any)
        if clients:
            logger.info(f"  Sample Clients:")
            for i, client_info in enumerate(clients[:3]):
                logger.info(f"    [{i+1}] Email: {client_info.email}, ID: {client_info.id}")
                
                # Fetch stats for this client
                stats = await client.get_client_stats(inbound_id, client_info.id)
                if stats:
                    logger.info(f"      Down: {stats.down / (1024*1024):.2f} MB, Up: {stats.up / (1024*1024):.2f} MB")
                    logger.info(f"      Total: {stats.total / (1024*1024):.2f} MB, Expiry: {stats.expiry_time}")
    
    except Exception as e:
        logger.error(f"Error displaying inbound details: {str(e)}")


async def add_and_remove_client(client: XuiPanelClient, inbound_id: int):
    """Demonstrate adding and removing a client."""
    try:
        # Create a unique email using current timestamp
        timestamp = int(datetime.now().timestamp())
        email = f"test_client_{timestamp}@example.com"
        
        # Prepare client data
        client_data = {
            "email": email,
            "uuid": f"00000000-0000-0000-0000-{timestamp:012d}",
            "flow": "",
            "limitIp": 0,
            "totalGB": 10, # 10 GB
            "expiryTime": int((datetime.now() + timedelta(days=30)).timestamp()),
            "enable": True,
            "tgId": "",
            "subId": ""
        }
        
        # Add the client
        logger.info(f"Adding new client with email: {email}")
        success = await client.add_client(inbound_id, client_data)
        
        if success:
            logger.info(f"✅ Client added successfully")
            
            # List clients to confirm addition
            clients = await client.list_clients(inbound_id)
            added_client = next((c for c in clients if c.email == email), None)
            
            if added_client:
                logger.info(f"✅ Confirmed client in the list: ID={added_client.id}, Email={added_client.email}")
                
                # Generate subscription link for client
                sub_url = await client.get_client_subscription_url(inbound_id, added_client.id)
                if sub_url:
                    logger.info(f"📱 Subscription URL: {sub_url}")
                
                # Wait a moment
                await asyncio.sleep(2)
                
                # Delete the client
                logger.info(f"Deleting client: {added_client.email}")
                success = await client.delete_client(inbound_id, added_client.id)
                
                if success:
                    logger.info(f"✅ Client deleted successfully")
                    
                    # Verify deletion
                    clients = await client.list_clients(inbound_id)
                    if not any(c.email == email for c in clients):
                        logger.info(f"✅ Confirmed client was removed")
                    else:
                        logger.error(f"❌ Client was not properly removed")
                else:
                    logger.error(f"❌ Failed to delete client")
            else:
                logger.error(f"❌ Could not find added client in the client list")
        else:
            logger.error(f"❌ Failed to add client")
    
    except Exception as e:
        logger.error(f"Error in add_and_remove_client: {str(e)}")


async def manage_traffic_for_client(client: XuiPanelClient, inbound_id: int, client_id: str, traffic_limit_gb: float):
    """Demonstrate traffic management for a client."""
    try:
        # Get current client stats
        stats = await client.get_client_stats(inbound_id, client_id)
        if not stats:
            logger.error(f"❌ Could not retrieve stats for client {client_id}")
            return
        
        # Display current stats
        used_gb = stats.total / (1024 * 1024 * 1024)
        logger.info(f"Current client stats:")
        logger.info(f"  Download: {stats.down / (1024*1024):.2f} MB")
        logger.info(f"  Upload: {stats.up / (1024*1024):.2f} MB")
        logger.info(f"  Total: {used_gb:.4f} GB")
        logger.info(f"  Expiry: {datetime.fromtimestamp(stats.expiry_time).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update traffic limit
        logger.info(f"Updating traffic limit to {traffic_limit_gb} GB")
        
        # First get the client info
        clients = await client.list_clients(inbound_id)
        target_client = next((c for c in clients if c.id == client_id), None)
        
        if not target_client:
            logger.error(f"❌ Client with ID {client_id} not found")
            return
            
        # Create updated client data with new traffic limit
        updated_client = dict(target_client.__dict__)
        updated_client["totalGB"] = traffic_limit_gb
        
        # Update the client
        success = await client.update_client(inbound_id, client_id, updated_client)
        
        if success:
            logger.info(f"✅ Successfully updated traffic limit")
            
            # Verify update
            clients = await client.list_clients(inbound_id)
            updated_client = next((c for c in clients if c.id == client_id), None)
            
            if updated_client and updated_client.total_gb == traffic_limit_gb:
                logger.info(f"✅ Confirmed traffic limit was updated to {updated_client.total_gb} GB")
            else:
                logger.error(f"❌ Traffic limit update could not be verified")
        else:
            logger.error(f"❌ Failed to update traffic limit")
    
    except Exception as e:
        logger.error(f"Error in manage_traffic_for_client: {str(e)}")


async def showcase_panel_features(
    base_url: str, 
    username: str, 
    password: str,
    panel_id: int = 1,
    inbound_id: Optional[int] = None
):
    """Showcase various features of the XuiPanelClient."""
    # Create the client
    client = XuiPanelClient(
        panel_id=panel_id,
        base_url=base_url,
        username=username,
        password=password,
        enable_token_manager=True,  # Use token manager for authentication
        enable_operation_queue=True,  # Use operation queue for operations
        enable_cache=True,           # Enable caching
        cache_ttl=60                  # Cache TTL in seconds
    )
    
    try:
        # Connect to the panel
        logger.info("Connecting to panel...")
        connected = await client.connect()
        
        if not connected:
            logger.error("❌ Failed to connect to panel")
            return
        
        logger.info("✅ Connected to panel successfully")
        
        # Get panel status
        logger.info("Fetching panel status...")
        status = await client.get_status()
        
        logger.info("📊 Panel Status:")
        logger.info(f"  Uptime: {status.uptime if status else 'N/A'}")
        logger.info(f"  Version: {status.v2ray_version if status else 'N/A'}")
        logger.info(f"  CPU: {status.cpu_usage if status else 'N/A'}%")
        logger.info(f"  Memory: {status.mem_usage if status else 'N/A'}%")
        logger.info(f"  OS: {status.os if status else 'N/A'}")
        logger.info(f"  ARCH: {status.arch if status else 'N/A'}")
        
        # Get all inbounds
        logger.info("\nFetching inbounds...")
        inbounds = await client.list_inbounds()
        
        if not inbounds:
            logger.error("❌ No inbounds found or failed to fetch inbounds")
            return
        
        logger.info(f"✅ Found {len(inbounds)} inbounds")
        
        # Select an inbound for testing if not provided
        target_inbound_id = inbound_id
        if target_inbound_id is None and inbounds:
            # Choose the first enabled VLESS or Trojan inbound
            for inbound in inbounds:
                if inbound.enable and inbound.protocol in ["vless", "trojan"]:
                    target_inbound_id = inbound.id
                    break
            
            # If no suitable inbound found, use the first one
            if target_inbound_id is None and inbounds:
                target_inbound_id = inbounds[0].id
        
        if target_inbound_id is None:
            logger.error("❌ No suitable inbound found for testing")
            return
        
        logger.info(f"🎯 Selected inbound ID {target_inbound_id} for testing")
        
        # Display details of the target inbound
        await display_inbound_details(client, target_inbound_id)
        
        # Perform client operations
        logger.info("\n=== Client Management Demo ===")
        await add_and_remove_client(client, target_inbound_id)
        
        # Find an existing client to update
        logger.info("\n=== Traffic Management Demo ===")
        clients = await client.list_clients(target_inbound_id)
        
        if clients:
            # Choose the first client for traffic management
            target_client = clients[0]
            logger.info(f"Selected client: {target_client.email} (ID: {target_client.id})")
            
            # Update traffic for the client
            # Add 5 GB to the current limit
            new_limit = (target_client.total_gb or 0) + 5
            await manage_traffic_for_client(client, target_inbound_id, target_client.id, new_limit)
        else:
            logger.info("No clients found for traffic management demo")
        
        # Cache demonstration
        logger.info("\n=== Cache Performance Demo ===")
        
        # Time uncached operation
        start_time = datetime.now()
        # Clear cache first to ensure we're not using cached data
        client.clear_cache()
        first_inbounds = await client.list_inbounds()
        first_request_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Uncached request time: {first_request_time:.4f} seconds")
        
        # Time cached operation
        start_time = datetime.now()
        second_inbounds = await client.list_inbounds()
        second_request_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Cached request time: {second_request_time:.4f} seconds")
        logger.info(f"Performance improvement: {(1 - second_request_time/first_request_time) * 100:.2f}%")
    
    except Exception as e:
        logger.error(f"Error in showcase_panel_features: {str(e)}")
    finally:
        # Close the client connection
        logger.info("\nClosing connection...")
        await client.close()
        logger.info("Connection closed")


async def main():
    """Run the demo."""
    try:
        logger.info("Starting panel client demo...")
        
        # Panel connection details - replace with actual panel details
        # In a real application, these would come from environment variables or config
        base_url = "http://your-panel-ip:port"
        username = "admin"
        password = "password"
        panel_id = 1
        
        # You can specify a particular inbound ID or let the script choose one
        inbound_id = None  # Set to a specific ID or None to auto-select
        
        await showcase_panel_features(base_url, username, password, panel_id, inbound_id)
        
        logger.info("Demo completed successfully")
    except Exception as e:
        logger.error(f"Demo failed with error: {str(e)}")


if __name__ == "__main__":
    # Run the async demo
    asyncio.run(main()) 