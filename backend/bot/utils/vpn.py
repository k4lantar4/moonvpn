"""
MoonVPN Telegram Bot - VPN Utilities.

This module provides utilities for interacting with VPN servers and managing VPN accounts.
"""

import logging
import aiohttp
import json
import random
import string
import asyncio
from typing import Dict, List, Optional, Tuple, Any

from models import Server, VPNAccount

logger = logging.getLogger(__name__)

async def change_account_server(account: VPNAccount, new_server: Server) -> Tuple[bool, Optional[str]]:
    """
    Change an account from one server to another.
    
    Args:
        account: The VPN account to migrate
        new_server: The target server to migrate to
        
    Returns:
        Tuple of (success, new_config)
    """
    logger.info(f"Changing server for account ID {account.id} to server ID {new_server.id}")
    
    try:
        # Get the account details from the old server
        old_server = Server.get_by_id(account.server_id)
        
        if not old_server:
            logger.error(f"Old server (ID: {account.server_id}) not found")
            return False, None
        
        # For X-UI panel
        if old_server.type.lower() == 'v2ray' or old_server.type.lower() == 'xui':
            # Connect to the server API and get the inbound information
            old_account_details = await get_account_details_from_xui(old_server, account)
            
            if not old_account_details:
                logger.error("Failed to get account details from old server")
                return False, None
            
            # Create the account on the new server
            success, new_account_data = await create_account_on_xui(
                new_server, 
                email=account.email or f"user_{account.user_id}",
                uuid=old_account_details.get('id') or account.uuid,
                traffic_limit=account.traffic_limit,
                expiry_date=account.expiry_date
            )
            
            if not success:
                logger.error("Failed to create account on new server")
                return False, None
            
            # Get the new account configuration
            new_config = await generate_client_config(new_server, new_account_data)
            
            if not new_config:
                logger.error("Failed to generate client configuration")
                return False, None
            
            # Update account details
            account.server_id = new_server.id
            if new_account_data.get('id'):
                account.uuid = new_account_data.get('id')
            
            account.save()
            
            # Remove from old server
            await delete_account_from_xui(old_server, account)
            
            return True, new_config
            
        else:
            # Unsupported server type
            logger.error(f"Unsupported server type: {old_server.type}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error changing server: {e}")
        return False, None

async def get_account_details_from_xui(server: Server, account: VPNAccount) -> Optional[Dict[str, Any]]:
    """
    Get account details from a X-UI panel.
    
    Args:
        server: The server to get the account from
        account: The VPN account
        
    Returns:
        Dictionary with account details if successful, None otherwise
    """
    try:
        # For simplicity, we're mocking this function
        # In a real implementation, this would make API calls to the X-UI panel
        
        # Example implementation:
        # async with aiohttp.ClientSession() as session:
        #     # Login to X-UI panel
        #     auth_data = {
        #         'username': server.username,
        #         'password': server.password
        #     }
        #     login_url = f"https://{server.host}:{server.api_port}/login"
        #     async with session.post(login_url, json=auth_data, ssl=False) as response:
        #         if response.status != 200:
        #             logger.error(f"Login failed: {response.status}")
        #             return None
        #         
        #         cookies = response.cookies
        #         
        #     # Get inbound list
        #     inbounds_url = f"https://{server.host}:{server.api_port}/panel/api/inbounds/list"
        #     async with session.get(inbounds_url, cookies=cookies, ssl=False) as response:
        #         if response.status != 200:
        #             logger.error(f"Failed to get inbounds: {response.status}")
        #             return None
        #             
        #         data = await response.json()
        #         
        #         # Find the client with matching email or UUID
        #         for inbound in data.get('obj', []):
        #             clients = json.loads(inbound.get('settings', '{}')).get('clients', [])
        #             for client in clients:
        #                 if client.get('email') == account.email or client.get('id') == account.uuid:
        #                     return client
        
        # For now, return a mock account
        return {
            'id': account.uuid or '00000000-0000-0000-0000-000000000000',
            'email': account.email or f"user_{account.user_id}",
            'limitIp': 0,
            'totalGB': account.traffic_limit * 1024 * 1024 * 1024,
            'expiryTime': int(account.expiry_date.timestamp() * 1000) if account.expiry_date else 0
        }
    except Exception as e:
        logger.error(f"Error getting account details from XUI panel: {e}")
        return None

async def create_account_on_xui(server: Server, email: str, uuid: Optional[str] = None,
                               traffic_limit: float = 0.0, expiry_date = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Create a new account on a X-UI panel.
    
    Args:
        server: The server to create the account on
        email: Email identifier for the account
        uuid: Optional UUID (will be generated if not provided)
        traffic_limit: Traffic limit in GB
        expiry_date: Expiry date for the account
        
    Returns:
        Tuple of (success, account_data)
    """
    try:
        # For simplicity, we're mocking this function
        # In a real implementation, this would make API calls to the X-UI panel
        
        if not uuid:
            # Generate a UUID
            uuid = ''.join(random.choices('0123456789abcdef', k=32))
            uuid = f"{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"
        
        # Mock account data
        account_data = {
            'id': uuid,
            'email': email,
            'limitIp': 0,
            'totalGB': traffic_limit * 1024 * 1024 * 1024,
            'expiryTime': int(expiry_date.timestamp() * 1000) if expiry_date else 0
        }
        
        # Example implementation:
        # async with aiohttp.ClientSession() as session:
        #     # Login to X-UI panel
        #     auth_data = {
        #         'username': server.username,
        #         'password': server.password
        #     }
        #     login_url = f"https://{server.host}:{server.api_port}/login"
        #     async with session.post(login_url, json=auth_data, ssl=False) as response:
        #         if response.status != 200:
        #             logger.error(f"Login failed: {response.status}")
        #             return False, {}
        #         
        #         cookies = response.cookies
        #         
        #     # Get the first inbound
        #     inbounds_url = f"https://{server.host}:{server.api_port}/panel/api/inbounds/list"
        #     async with session.get(inbounds_url, cookies=cookies, ssl=False) as response:
        #         if response.status != 200:
        #             logger.error(f"Failed to get inbounds: {response.status}")
        #             return False, {}
        #             
        #         data = await response.json()
        #         if not data.get('obj'):
        #             logger.error("No inbounds found")
        #             return False, {}
        #         
        #         inbound_id = data['obj'][0]['id']
        #         
        #     # Add client to inbound
        #     client_data = {
        #         'id': inbound_id,
        #         'settings': json.dumps({
        #             'clients': [{
        #                 'id': uuid,
        #                 'email': email,
        #                 'limitIp': 0,
        #                 'totalGB': traffic_limit * 1024 * 1024 * 1024,
        #                 'expiryTime': int(expiry_date.timestamp() * 1000) if expiry_date else 0
        #             }]
        #         })
        #     }
        #     
        #     add_client_url = f"https://{server.host}:{server.api_port}/panel/api/inbounds/addClient"
        #     async with session.post(add_client_url, json=client_data, cookies=cookies, ssl=False) as response:
        #         if response.status != 200:
        #             logger.error(f"Failed to add client: {response.status}")
        #             return False, {}
        #         
        #         result = await response.json()
        #         if not result.get('success'):
        #             logger.error(f"Failed to add client: {result.get('msg')}")
        #             return False, {}
        
        # For now, we'll just return the mock account data
        await asyncio.sleep(1)  # Simulate API call delay
        return True, account_data
        
    except Exception as e:
        logger.error(f"Error creating account on XUI panel: {e}")
        return False, {}

async def delete_account_from_xui(server: Server, account: VPNAccount) -> bool:
    """
    Delete an account from a X-UI panel.
    
    Args:
        server: The server to delete the account from
        account: The VPN account to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # For simplicity, we're mocking this function
        # In a real implementation, this would make API calls to the X-UI panel
        
        # Example implementation:
        # async with aiohttp.ClientSession() as session:
        #     # Login to X-UI panel
        #     auth_data = {
        #         'username': server.username,
        #         'password': server.password
        #     }
        #     login_url = f"https://{server.host}:{server.api_port}/login"
        #     async with session.post(login_url, json=auth_data, ssl=False) as response:
        #         if response.status != 200:
        #             logger.error(f"Login failed: {response.status}")
        #             return False
        #         
        #         cookies = response.cookies
        #         
        #     # Get inbound list
        #     inbounds_url = f"https://{server.host}:{server.api_port}/panel/api/inbounds/list"
        #     async with session.get(inbounds_url, cookies=cookies, ssl=False) as response:
        #         if response.status != 200:
        #             logger.error(f"Failed to get inbounds: {response.status}")
        #             return False
        #             
        #         data = await response.json()
        #         
        #         # Find the inbound with the client
        #         for inbound in data.get('obj', []):
        #             inbound_id = inbound.get('id')
        #             clients = json.loads(inbound.get('settings', '{}')).get('clients', [])
        #             for client in clients:
        #                 if client.get('email') == account.email or client.get('id') == account.uuid:
        #                     # Found the client, now delete it
        #                     delete_url = f"https://{server.host}:{server.api_port}/panel/api/inbounds/delClient"
        #                     delete_data = {
        #                         'id': inbound_id,
        #                         'clientId': client.get('id')
        #                     }
        #                     async with session.post(delete_url, json=delete_data, cookies=cookies, ssl=False) as delete_response:
        #                         if delete_response.status != 200:
        #                             logger.error(f"Failed to delete client: {delete_response.status}")
        #                             return False
        #                         
        #                         result = await delete_response.json()
        #                         return result.get('success', False)
        
        # For now, simulate a successful deletion
        await asyncio.sleep(0.5)  # Simulate API call delay
        return True
        
    except Exception as e:
        logger.error(f"Error deleting account from XUI panel: {e}")
        return False

async def generate_client_config(server: Server, account_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate a client configuration string for connecting to the VPN.
    
    Args:
        server: The VPN server
        account_data: Account data including UUID and email
        
    Returns:
        Configuration string if successful, None otherwise
    """
    try:
        # Create a mock configuration
        # In a real implementation, this would generate proper V2Ray/XRay config
        
        uuid = account_data.get('id', '00000000-0000-0000-0000-000000000000')
        email = account_data.get('email', 'user@example.com')
        
        protocol = "vmess"
        if server.config and server.config.get('protocol'):
            protocol = server.config.get('protocol')
        
        # For VMess protocol
        if protocol.lower() == 'vmess':
            config = {
                "v": "2",
                "ps": f"MoonVPN-{server.location}",
                "add": server.host,
                "port": server.port,
                "id": uuid,
                "aid": "0",
                "net": "ws",
                "type": "none",
                "host": "",
                "path": "/",
                "tls": "tls"
            }
            
            import base64
            config_json = json.dumps(config)
            config_str = base64.b64encode(config_json.encode()).decode()
            
            return f"vmess://{config_str}"
        
        # For VLESS protocol
        elif protocol.lower() == 'vless':
            return f"vless://{uuid}@{server.host}:{server.port}?encryption=none&security=tls&type=ws&host={server.host}&path=%2F#{server.location}"
        
        # For Trojan protocol
        elif protocol.lower() == 'trojan':
            return f"trojan://{uuid}@{server.host}:{server.port}?security=tls&type=ws&host={server.host}&path=%2F#{server.location}"
        
        else:
            logger.error(f"Unsupported protocol: {protocol}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating client configuration: {e}")
        return None 