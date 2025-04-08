#!/usr/bin/env python3
"""
Example script demonstrating the use of PanelTokenManager with XuiPanelClient.

This script shows how to properly initialize and use the token management system
with the 3x-ui panel client, including proper connection handling, token renewal,
and error handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from core.security.panel_tokens import PanelTokenManager
from integrations.panels.client import XuiPanelClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_with_panel_token_manager():
    """Demonstrate token management with the XuiPanelClient."""
    # Panel connection information
    panel_id = 1
    base_url = "https://your-panel-address:54321"
    username = "admin"
    password = "your-password"

    # Initialize the client with token management enabled
    client = XuiPanelClient(
        panel_id=panel_id,
        base_url=base_url,
        username=username,
        password=password,
        use_token_manager=True,
        use_operation_queue=True,
        use_client_cache=True
    )

    try:
        # Test connection - this will also handle the token management internally
        logger.info("Attempting to log in...")
        login_success = await client.login()
        
        if login_success:
            logger.info("✅ Login successful!")
            
            # Check if we have a stored token
            token = await PanelTokenManager.get_token(panel_id)
            if token:
                logger.info(f"✅ Token is stored in the secure token manager")
                
                # Get token info
                token_info = await PanelTokenManager.get_token_info(panel_id)
                if token_info:
                    expires_at = token_info.get('expires_at')
                    created_at = token_info.get('created_at')
                    
                    logger.info(f"  • Token created at: {created_at}")
                    logger.info(f"  • Token expires at: {expires_at}")
                    
                    if expires_at:
                        # Parse the ISO format datetime string
                        expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        now = datetime.now()
                        time_left = expires_dt - now
                        
                        if time_left.total_seconds() > 0:
                            logger.info(f"  • Token expires in: {time_left}")
                        else:
                            logger.info(f"  • Token has expired")
            
            # Use the client to fetch some data
            logger.info("Fetching panel status...")
            success, status = await client.get_status()
            
            if success:
                logger.info("✅ Status retrieved successfully")
                logger.info(f"  • Panel version: {status.get('version', 'Unknown')}")
                logger.info(f"  • Memory usage: {status.get('mem', 'Unknown')}")
                logger.info(f"  • Uptime: {status.get('uptime', 'Unknown')}")
            else:
                logger.error(f"❌ Failed to get status: {status}")
                
            # Fetch inbounds
            logger.info("Fetching inbounds...")
            success, inbounds = await client.get_inbounds()
            
            if success:
                logger.info(f"✅ Retrieved {len(inbounds)} inbounds")
                # Print first inbound details if available
                if inbounds:
                    inbound = inbounds[0]
                    logger.info(f"  • Inbound #{inbound.get('id')}: {inbound.get('remark')}")
                    logger.info(f"  • Protocol: {inbound.get('protocol')}")
                    logger.info(f"  • Port: {inbound.get('port')}")
            else:
                logger.error(f"❌ Failed to get inbounds: {inbounds}")
                
            # Simulate token expiration and renewal
            logger.info("\nSimulating token expiration and renewal...")
            # Force expiration by setting expiry time to the past
            expired_time = datetime.now() - timedelta(hours=1)
            await PanelTokenManager.store_token(panel_id, "expired-token", expires_at=expired_time)
            
            # Check if token should be renewed
            should_renew = await PanelTokenManager.should_renew_token(panel_id)
            logger.info(f"  • Should token be renewed? {should_renew}")
            
            # Try to get status again - this should trigger a new login and token renewal
            logger.info("Attempting to get status with expired token (should trigger renewal)...")
            success, status = await client.get_status()
            
            if success:
                logger.info("✅ Status retrieved successfully after token renewal")
                # Check if we have a new token
                new_token = await PanelTokenManager.get_token(panel_id)
                logger.info(f"✅ New token stored: {new_token != 'expired-token'}")
            else:
                logger.error(f"❌ Failed to get status after token renewal: {status}")
                
        else:
            logger.error("❌ Login failed. Check your credentials and panel URL.")
    
    finally:
        # Always close the client to clean up resources
        logger.info("Closing client connection...")
        await client.close()
        
        # Also close the token manager explicitly
        logger.info("Closing token manager connection...")
        await PanelTokenManager.close()


async def main():
    """Run the demo."""
    try:
        logger.info("Starting token management demo...")
        await demo_with_panel_token_manager()
        logger.info("Demo completed successfully")
    except Exception as e:
        logger.error(f"Demo failed with error: {str(e)}")


if __name__ == "__main__":
    # Run the async demo
    asyncio.run(main()) 