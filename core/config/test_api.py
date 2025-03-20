#!/usr/bin/env python3
"""
MoonVPN API Test Script
This script tests the MoonVPN API endpoints and 3x-UI panel integration.
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_test')

# Default API URL
DEFAULT_API_URL = "http://localhost:8000/api"

def get_token(api_url, username, password):
    """Get JWT token from API"""
    url = f"{api_url}/token/"
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["access"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.content}")
        sys.exit(1)

def test_health_endpoint(api_url):
    """Test the health endpoint"""
    url = f"{api_url}/health/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        logger.info(f"✅ Health check successful: {json.dumps(result, indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.content}")
        return False

def test_servers_endpoint(api_url, token):
    """Test the servers endpoint"""
    url = f"{api_url}/servers/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        logger.info(f"✅ Servers check successful. Found {len(result)} servers.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Servers check failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.content}")
        return False

def test_users_endpoint(api_url, token):
    """Test the users endpoint"""
    url = f"{api_url}/users/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        logger.info(f"✅ Users check successful. Found {len(result)} users.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Users check failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.content}")
        return False

def test_change_location(api_url, token, user_id, server_id):
    """Test the change-location endpoint"""
    url = f"{api_url}/change-location/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "user_id": user_id,
        "server_id": server_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        logger.info(f"✅ Change location successful: {json.dumps(result, indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Change location failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.content}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test MoonVPN API endpoints')
    parser.add_argument('--api-url', type=str, default=DEFAULT_API_URL, help='API URL')
    parser.add_argument('--username', type=str, required=True, help='Admin username')
    parser.add_argument('--password', type=str, required=True, help='Admin password')
    parser.add_argument('--user-id', type=int, help='User ID for change-location test')
    parser.add_argument('--server-id', type=int, help='Server ID for change-location test')
    args = parser.parse_args()
    
    # Print test configuration
    logger.info(f"Testing API at: {args.api_url}")
    logger.info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test health endpoint (no auth required)
    health_ok = test_health_endpoint(args.api_url)
    
    if not health_ok:
        logger.error("Health check failed. Stopping tests.")
        sys.exit(1)
    
    # Get token for authenticated endpoints
    token = get_token(args.api_url, args.username, args.password)
    logger.info("✅ Successfully obtained JWT token")
    
    # Test servers endpoint
    servers_ok = test_servers_endpoint(args.api_url, token)
    
    # Test users endpoint
    users_ok = test_users_endpoint(args.api_url, token)
    
    # Test change-location endpoint if user_id and server_id are provided
    if args.user_id and args.server_id:
        change_location_ok = test_change_location(
            args.api_url, token, args.user_id, args.server_id
        )
    else:
        logger.warning("Skipping change-location test (user_id and server_id not provided)")
        change_location_ok = None
    
    # Summary
    logger.info("\n----- TEST SUMMARY -----")
    logger.info(f"Health check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    logger.info(f"Servers endpoint: {'✅ PASS' if servers_ok else '❌ FAIL'}")
    logger.info(f"Users endpoint: {'✅ PASS' if users_ok else '❌ FAIL'}")
    if change_location_ok is not None:
        logger.info(f"Change location: {'✅ PASS' if change_location_ok else '❌ FAIL'}")
    else:
        logger.info("Change location: ⏭️ SKIPPED")
    
    logger.info(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    if health_ok and servers_ok and users_ok and (change_location_ok is None or change_location_ok):
        logger.info("All tests passed successfully! 🎉")
        sys.exit(0)
    else:
        logger.error("Some tests failed! 😢")
        sys.exit(1)

if __name__ == "__main__":
    main() 