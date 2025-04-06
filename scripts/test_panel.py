#!/usr/bin/env python3
"""
Panel Connection Test Script

A simple command-line tool to test connectivity to a 3x-ui panel.
This script can be run directly to verify panel configuration and connectivity.
"""

import asyncio
import argparse
import json
import sys
import os
import logging
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrations.panels.client import test_panel_connection, test_default_panel_connection
from core.logging import setup_logging
from core.config import get_settings

# Setup logging
setup_logging()
logger = logging.getLogger("test_panel")
settings = get_settings()


async def run_panel_test(
    url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    use_default: bool = False
) -> Dict[str, Any]:
    """Run panel connection test using the provided credentials or defaults.
    
    Args:
        url: Panel URL (optional if use_default is True)
        username: Admin username (optional if use_default is True)
        password: Admin password (optional if use_default is True)
        use_default: Use default panel configuration from environment
    
    Returns:
        Dict[str, Any]: Test results
    """
    if use_default:
        return await test_default_panel_connection()
    else:
        if not all([url, username, password]):
            return {
                "success": False,
                "status": "missing_parameters",
                "error": "Panel URL, username, and password are required"
            }
        
        return await test_panel_connection(url, username, password)


def print_result(result: Dict[str, Any], json_output: bool = False) -> None:
    """Pretty-print the test results.
    
    Args:
        result: Test results dictionary
        json_output: If True, output raw JSON instead of formatted text
    """
    if json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    # Format the output as text
    success = result.get("success", False)
    status = result.get("status", "unknown")
    url = result.get("url", "N/A")
    response_time = result.get("response_time_ms")
    error = result.get("error")
    panel_info = result.get("panel_info", {})
    
    # Print header
    print("\n" + "="*50)
    print(f"📡 PANEL CONNECTION TEST: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("="*50)
    
    # Print basic information
    print(f"🔗 URL: {url}")
    print(f"🏷️ Status: {status}")
    if response_time:
        print(f"⏱️ Response Time: {response_time} ms")
    
    # Print error if any
    if error:
        print(f"❌ Error: {error}")
    
    # Print panel info if available
    if panel_info and isinstance(panel_info, dict):
        print("\n📊 PANEL INFORMATION:")
        print("-"*50)
        
        # CPU
        if "cpu" in panel_info:
            print(f"🔄 CPU Usage: {panel_info['cpu']}%")
        
        # Memory
        if "mem" in panel_info and isinstance(panel_info["mem"], dict):
            mem = panel_info["mem"]
            total_mem = mem.get("total", 0)
            used_mem = mem.get("used", 0)
            
            if total_mem > 0:
                percent = (used_mem / total_mem) * 100
                print(f"💾 Memory: {used_mem} MB / {total_mem} MB ({percent:.1f}%)")
        
        # Disk
        if "disk" in panel_info and isinstance(panel_info["disk"], dict):
            disk = panel_info["disk"]
            total_disk = disk.get("total", 0)
            used_disk = disk.get("used", 0)
            
            if total_disk > 0:
                percent = (used_disk / total_disk) * 100
                print(f"💿 Disk: {used_disk} GB / {total_disk} GB ({percent:.1f}%)")
        
        # Xray status
        if "xray" in panel_info:
            xray_status = panel_info["xray"]
            print(f"🚀 Xray Status: {'✅ Running' if xray_status == 'running' else '❌ Not Running'}")
        
        # Uptime
        if "uptime" in panel_info:
            print(f"⏰ Uptime: {panel_info['uptime']}")
        
        # Other info
        for key, value in panel_info.items():
            if key not in ["cpu", "mem", "disk", "xray", "uptime"]:
                print(f"ℹ️ {key}: {value}")
    
    print("="*50 + "\n")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test connectivity to a 3x-ui panel",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Define arguments
    parser.add_argument("-u", "--url", help="Panel URL (e.g., https://example.com:54321)")
    parser.add_argument("-n", "--username", help="Admin username")
    parser.add_argument("-p", "--password", help="Admin password")
    parser.add_argument("-d", "--default", action="store_true", help="Use default panel from environment variables")
    parser.add_argument("-j", "--json", action="store_true", help="Output raw JSON instead of formatted text")
    
    args = parser.parse_args()
    
    # Run the test
    result = asyncio.run(run_panel_test(args.url, args.username, args.password, args.default))
    
    # Print the result
    print_result(result, args.json)
    
    # Exit with appropriate status code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main() 