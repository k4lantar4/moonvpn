#!/usr/bin/env python
"""
3x-ui Panel Test Script

This script tests connection and operations with a 3x-ui panel.
It can be used to verify that the panel client works correctly.

Usage:
    python test_panel.py [--panel URL] [--username USERNAME] [--password PASSWORD]
"""

import asyncio
import argparse
import sys
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path so we can import from modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.panels.client import XuiPanelClient, test_panel_connection
from core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("panel_test")
settings = get_settings()


async def test_basic_connection(url: str, username: str, password: str) -> Dict[str, Any]:
    """Test basic connection to a 3x-ui panel.
    
    Args:
        url: Panel URL
        username: Admin username
        password: Admin password
        
    Returns:
        Dict[str, Any]: Connection test result
    """
    logger.info(f"Testing connection to panel: {url}")
    start_time = time.time()
    
    result = await test_panel_connection(url, username, password)
    
    end_time = time.time()
    logger.info(f"Connection test completed in {end_time - start_time:.2f} seconds")
    logger.info(f"Status: {result['status']}")
    
    if result["success"]:
        logger.info("✅ Connection test successful!")
        if result.get("panel_info"):
            logger.info(f"Panel info: {json.dumps(result['panel_info'], indent=2)}")
    else:
        logger.error(f"❌ Connection test failed: {result.get('error')}")
    
    return result


async def test_inbound_operations(client: XuiPanelClient) -> bool:
    """Test inbound operations.
    
    Args:
        client: XuiPanelClient instance
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    logger.info("\n=== Testing Inbound Operations ===")
    
    # Get all inbounds
    success, inbounds = await client.get_inbounds()
    if not success:
        logger.error(f"❌ Failed to get inbounds: {inbounds.get('error')}")
        return False
    
    logger.info(f"✅ Retrieved {len(inbounds)} inbounds")
    
    if not inbounds:
        logger.warning("⚠️ No inbounds found, skipping inbound tests")
        return True
    
    # Get first inbound details
    inbound_id = inbounds[0]["id"]
    logger.info(f"Testing with inbound ID: {inbound_id}")
    
    success, inbound = await client.get_inbound(inbound_id)
    if not success:
        logger.error(f"❌ Failed to get inbound details: {inbound.get('error')}")
        return False
    
    logger.info(f"✅ Retrieved inbound details: {inbound.get('remark', 'Unnamed')}")
    
    return True


async def test_client_operations(client: XuiPanelClient) -> bool:
    """Test client operations.
    
    Args:
        client: XuiPanelClient instance
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    logger.info("\n=== Testing Client Operations ===")
    
    # Get all inbounds first
    success, inbounds = await client.get_inbounds()
    if not success or not inbounds:
        logger.error("❌ Cannot test client operations: No inbounds available")
        return False
    
    # Find an inbound with clients
    inbound_with_clients = None
    for inbound in inbounds:
        if inbound.get("clientStats") and len(inbound.get("clientStats", [])) > 0:
            inbound_with_clients = inbound
            break
    
    if not inbound_with_clients:
        logger.warning("⚠️ No inbounds with clients found, skipping client tests")
        return True
    
    inbound_id = inbound_with_clients["id"]
    client_email = inbound_with_clients["clientStats"][0]["email"]
    
    logger.info(f"Testing with inbound ID: {inbound_id}, client: {client_email}")
    
    # Get client traffic
    success, traffic = await client.get_client_traffics(client_email)
    if not success:
        logger.error(f"❌ Failed to get client traffic: {traffic.get('error')}")
        return False
    
    logger.info(f"✅ Retrieved traffic for client {client_email}")
    
    # Get client IPs
    success, ips = await client.get_client_ips(client_email)
    if not success:
        logger.error(f"❌ Failed to get client IPs: {ips.get('error')}")
        return False
    
    logger.info(f"✅ Retrieved IPs for client {client_email}")
    
    return True


async def test_online_clients(client: XuiPanelClient) -> bool:
    """Test getting online clients.
    
    Args:
        client: XuiPanelClient instance
        
    Returns:
        bool: True if test passed, False otherwise
    """
    logger.info("\n=== Testing Online Clients ===")
    
    success, onlines = await client.get_online_clients()
    if not success:
        logger.error(f"❌ Failed to get online clients: {onlines.get('error')}")
        return False
    
    logger.info(f"✅ Retrieved {len(onlines)} online clients")
    return True


async def test_system_operations(client: XuiPanelClient) -> bool:
    """Test system operations.
    
    Args:
        client: XuiPanelClient instance
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    logger.info("\n=== Testing System Operations ===")
    
    # Get panel status
    success, status = await client.get_status()
    if not success:
        logger.error(f"❌ Failed to get panel status: {status.get('error')}")
        return False
    
    logger.info(f"✅ Panel status: {json.dumps(status, indent=2)}")
    
    return True


async def run_all_tests(url: str, username: str, password: str):
    """Run all panel tests.
    
    Args:
        url: Panel URL
        username: Admin username
        password: Admin password
    """
    logger.info("Starting 3x-ui Panel Test Suite")
    logger.info("=" * 50)
    
    # Test basic connection
    connection_result = await test_basic_connection(url, username, password)
    if not connection_result["success"]:
        logger.error("Basic connection test failed, aborting further tests.")
        return
    
    # Run detailed tests with client
    logger.info("\nRunning detailed operation tests...")
    async with XuiPanelClient(url, username, password) as client:
        # Test login
        login_success = await client.login()
        if not login_success:
            logger.error("❌ Login failed, aborting further tests.")
            return
        
        logger.info("✅ Login successful")
        
        # Run all test suites
        test_results = {
            "inbound_operations": await test_inbound_operations(client),
            "client_operations": await test_client_operations(client),
            "online_clients": await test_online_clients(client),
            "system_operations": await test_system_operations(client)
        }
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("Test Summary:")
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            if not result:
                all_passed = False
            logger.info(f"{test_name}: {status}")
        
        if all_passed:
            logger.info("\n🎉 All tests passed successfully!")
        else:
            logger.error("\n⚠️ Some tests failed. See logs above for details.")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test connection to a 3x-ui panel")
    parser.add_argument("--panel", help="Panel URL (e.g., http://example.com:54321)")
    parser.add_argument("--username", help="Admin username")
    parser.add_argument("--password", help="Admin password")
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    # Use command line args if provided, otherwise use env vars
    panel_url = args.panel or os.getenv("PANEL_URL") or settings.PANEL1_URL
    username = args.username or os.getenv("PANEL_USERNAME") or settings.PANEL1_USERNAME
    password = args.password or os.getenv("PANEL_PASSWORD") or settings.PANEL1_PASSWORD
    
    if not all([panel_url, username, password]):
        logger.error(
            "Missing panel credentials. Provide them via command line arguments "
            "or environment variables (PANEL_URL, PANEL_USERNAME, PANEL_PASSWORD)"
        )
        sys.exit(1)
    
    try:
        await run_all_tests(panel_url, username, password)
    except Exception as e:
        logger.exception(f"Error during tests: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 