#!/usr/bin/env python3
"""
Test script for 3x-UI panel connection.
This script tests the connection to the 3x-UI panel and retrieves basic information.
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('panel_test')

class PanelConnector:
    """Simple connector for 3x-UI panel API"""
    
    def __init__(self, panel_url=None, username=None, password=None):
        """Initialize with panel credentials"""
        self.panel_url = panel_url or os.environ.get('PANEL_URL', '')
        self.username = username or os.environ.get('PANEL_USERNAME', '')
        self.password = password or os.environ.get('PANEL_PASSWORD', '')
        
        # Remove trailing slash from URL if present
        if self.panel_url and self.panel_url.endswith('/'):
            self.panel_url = self.panel_url[:-1]
            
        # Session management
        self.session = requests.Session()
        self.is_authenticated = False
        
        # Auto login if credentials are provided
        if self.panel_url and self.username and self.password:
            self.login()
    
    def login(self):
        """Authenticate with the panel"""
        try:
            login_url = f"{self.panel_url}/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            logger.info(f"Attempting to login to panel at {self.panel_url}")
            response = self.session.post(login_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.is_authenticated = True
                    logger.info("Authentication successful")
                    return True
                else:
                    logger.error(f"Login failed: {data.get('msg')}")
            else:
                logger.error(f"Login failed with status code: {response.status_code}")
            
            self.is_authenticated = False
            return False
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            self.is_authenticated = False
            return False
    
    def get_server_status(self):
        """Get server status information"""
        if not self.is_authenticated:
            logger.error("Not authenticated")
            return None
        
        try:
            url = f"{self.panel_url}/panel/api/server/status"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('obj')
                else:
                    logger.error(f"Failed to get server status: {data.get('msg')}")
            else:
                logger.error(f"Failed to get server status with status code: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting server status: {str(e)}")
            return None
    
    def get_inbounds(self):
        """Get all inbounds from the panel"""
        if not self.is_authenticated:
            logger.error("Not authenticated")
            return None
        
        try:
            url = f"{self.panel_url}/panel/api/inbounds/list"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('obj')
                else:
                    logger.error(f"Failed to get inbounds: {data.get('msg')}")
            else:
                logger.error(f"Failed to get inbounds with status code: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting inbounds: {str(e)}")
            return None

def main():
    """Main function to test panel connection"""
    # Get panel credentials from environment
    panel_url = os.environ.get('PANEL_URL', '')
    username = os.environ.get('PANEL_USERNAME', '')
    password = os.environ.get('PANEL_PASSWORD', '')
    
    if not all([panel_url, username, password]):
        logger.error("Missing panel credentials in environment variables")
        sys.exit(1)
    
    # Initialize connector
    connector = PanelConnector(panel_url, username, password)
    
    # Check authentication
    if not connector.is_authenticated:
        logger.error("Failed to authenticate with panel")
        sys.exit(1)
    
    # Get server status
    server_status = connector.get_server_status()
    if server_status:
        logger.info("Server status:")
        logger.info(f"  CPU: {server_status.get('cpu', 0)}%")
        logger.info(f"  Memory: {server_status.get('mem', 0)}%")
        logger.info(f"  Disk: {server_status.get('disk', 0)}%")
        logger.info(f"  Xray State: {server_status.get('xray_state', 'unknown')}")
        logger.info(f"  Xray Version: {server_status.get('xray_version', 'unknown')}")
    else:
        logger.error("Failed to get server status")
    
    # Get inbounds
    inbounds = connector.get_inbounds()
    if inbounds:
        logger.info(f"Found {len(inbounds)} inbounds:")
        for inbound in inbounds:
            logger.info(f"  ID: {inbound.get('id')}")
            logger.info(f"  Protocol: {inbound.get('protocol')}")
            logger.info(f"  Port: {inbound.get('port')}")
            logger.info(f"  Remark: {inbound.get('remark')}")
            logger.info(f"  Enable: {inbound.get('enable')}")
            logger.info(f"  Up: {inbound.get('up')} bytes")
            logger.info(f"  Down: {inbound.get('down')} bytes")
            logger.info(f"  Total: {inbound.get('total')} bytes")
            logger.info("  -----")
    else:
        logger.error("Failed to get inbounds")
    
    logger.info("Test completed")

if __name__ == "__main__":
    main() 