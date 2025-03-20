#!/usr/bin/env python
"""
Script to fetch and display panel information
"""

import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Panel credentials
panel_domain = os.getenv('V2RAY_PANEL_DOMAIN', '46.105.239.6')
panel_port = os.getenv('V2RAY_PANEL_PORT', '2096')
panel_path = os.getenv('V2RAY_PANEL_PATH', '/jdkfg34lj5468vdfgn943n0235nj7g54')
panel_api_path = os.getenv('V2RAY_PANEL_API_PATH', '/panel/api')
panel_username = os.getenv('V2RAY_PANEL_USERNAME', 'k4lantar4')
panel_password = os.getenv('V2RAY_PANEL_PASSWORD', '}|9QV;y5T5+4')
panel_ssl = os.getenv('V2RAY_PANEL_SSL', 'false').lower() == 'true'

# Construct base URL
protocol = 'https' if panel_ssl else 'http'
base_url = f"{protocol}://{panel_domain}:{panel_port}{panel_path}"
api_base_url = f"{base_url}{panel_api_path}"

print(f"Connecting to panel at: {base_url}")

# Create a session
session = requests.Session()

def login():
    """Login to the panel and return True if successful"""
    login_url = f"{base_url}/login"
    login_data = {
        "username": panel_username,
        "password": panel_password
    }
    
    print(f"Logging in to: {login_url}")
    try:
        login_response = session.post(login_url, json=login_data, timeout=10)
        if login_response.status_code == 200:
            data = login_response.json()
            if data.get('success'):
                print("Login successful!")
                return True
            else:
                print(f"Login failed: {data.get('msg')}")
                return False
        else:
            print(f"Login failed with status code: {login_response.status_code}")
            return False
    except Exception as e:
        print(f"Login error: {str(e)}")
        return False

def get_inbounds():
    """Get all inbounds from the panel"""
    inbounds_url = f"{api_base_url}/inbounds/list"
    try:
        response = session.get(inbounds_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('obj', [])
            else:
                print(f"Failed to get inbounds: {data.get('msg')}")
                return []
        else:
            print(f"Failed to get inbounds with status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting inbounds: {str(e)}")
        return []

def get_clients(inbound_id):
    """Get clients for an inbound"""
    clients_url = f"{api_base_url}/inbounds/getClientTraffics/{inbound_id}"
    try:
        response = session.get(clients_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('obj', [])
            else:
                print(f"Failed to get clients: {data.get('msg')}")
                return []
        else:
            print(f"Failed to get clients with status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting clients: {str(e)}")
        return []

def bytes_to_gb(bytes_value):
    """Convert bytes to GB with 2 decimal places"""
    return round(bytes_value / (1024 * 1024 * 1024), 2)

def timestamp_to_date(timestamp_ms):
    """Convert millisecond timestamp to date string"""
    if timestamp_ms == 0:
        return "Never"
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

def display_inbound_info(inbound):
    """Display information about an inbound"""
    print("\n" + "=" * 50)
    print(f"Inbound ID: {inbound.get('id')}")
    print(f"Remark: {inbound.get('remark')}")
    print(f"Protocol: {inbound.get('protocol')}")
    print(f"Port: {inbound.get('port')}")
    print(f"Enable: {inbound.get('enable')}")
    print(f"Expiry Time: {timestamp_to_date(inbound.get('expiryTime', 0))}")
    print(f"Up: {bytes_to_gb(inbound.get('up', 0))} GB")
    print(f"Down: {bytes_to_gb(inbound.get('down', 0))} GB")
    print(f"Total: {bytes_to_gb(inbound.get('total', 0))} GB")
    
    # Get and display client information
    clients = get_clients(inbound.get('id'))
    if clients:
        print("\nClients:")
        print("-" * 50)
        for client in clients:
            print(f"  Email: {client.get('email')}")
            print(f"  Enable: {client.get('enable')}")
            print(f"  Expiry Time: {timestamp_to_date(client.get('expiryTime', 0))}")
            print(f"  Up: {bytes_to_gb(client.get('up', 0))} GB")
            print(f"  Down: {bytes_to_gb(client.get('down', 0))} GB")
            print(f"  Total: {bytes_to_gb(client.get('total', 0))} GB")
            print("-" * 50)
    else:
        print("\nNo clients found for this inbound.")

# Main execution
if login():
    inbounds = get_inbounds()
    if inbounds:
        print(f"\nFound {len(inbounds)} inbounds:")
        for inbound in inbounds:
            display_inbound_info(inbound)
    else:
        print("\nNo inbounds found.")
else:
    print("Failed to login to the panel. Cannot fetch information.") 