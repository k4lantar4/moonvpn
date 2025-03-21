"""
3X-UI API Client for the Telegram bot.

This module provides functions for interacting with 3X-UI panel APIs to create
and manage V2Ray accounts.
"""

import os
import json
import time
import logging
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

from core.config import get_threexui_config
from core.database import get_setting, update_setting

# Configure logging
logger = logging.getLogger("telegram_bot")


class ThreeXUIClient:
    """Client for interacting with 3X-UI panel API."""

    def __init__(self, panel_id: int, base_url: str, username: str, password: str):
        """
        Initialize the 3X-UI API client.
        
        Args:
            panel_id: Panel ID in the database
            base_url: Base URL of the 3X-UI panel (e.g., 'https://example.com:2053')
            username: Username for 3X-UI panel login
            password: Password for 3X-UI panel login
        """
        self.panel_id = panel_id
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=get_threexui_config()["api_timeout"],
            verify=False  # Disable SSL verification (not recommended for production)
        )
        self.cookie = None
        self.cookie_expiry = datetime.now()

    async def login(self) -> bool:
        """
        Login to the 3X-UI panel and get a session cookie.
        
        Returns:
            True if login successful, False otherwise
        """
        # Check if cookie exists and is still valid
        if self.cookie and datetime.now() < self.cookie_expiry:
            self.session.headers.update({'Cookie': self.cookie})
            return True
        
        # Check if cookie exists in the database
        cookie_key = f"threexui_cookie_{self.panel_id}"
        cookie_data = get_setting(cookie_key)
        
        if cookie_data:
            try:
                cookie_info = json.loads(cookie_data)
                expiry = datetime.fromisoformat(cookie_info.get('expiry', '2000-01-01T00:00:00'))
                
                if datetime.now() < expiry:
                    self.cookie = cookie_info.get('cookie')
                    self.cookie_expiry = expiry
                    self.session.headers.update({'Cookie': self.cookie})
                    return True
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing cookie data from database: {e}")
        
        # Cookie doesn't exist or is expired, login to get a new one
        try:
            response = await self.session.post(
                '/login',
                data={
                    'username': self.username,
                    'password': self.password
                }
            )
            
            if response.status_code == 200 and response.json().get('success', False):
                # Extract cookie from response
                cookie = response.headers.get('set-cookie')
                if cookie:
                    self.cookie = cookie
                    # Set expiry time
                    self.cookie_expiry = datetime.now() + timedelta(seconds=get_threexui_config()["session_expiry"])
                    # Save cookie to database
                    cookie_info = {
                        'cookie': cookie,
                        'expiry': self.cookie_expiry.isoformat()
                    }
                    update_setting(cookie_key, json.dumps(cookie_info))
                    
                    self.session.headers.update({'Cookie': self.cookie})
                    return True
            
            logger.error(f"Login failed: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error logging in to 3X-UI panel: {e}")
            return False

    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        Get all inbounds from the 3X-UI panel.
        
        Returns:
            List of inbound configurations
        """
        if not await self.login():
            return []
        
        try:
            response = await self.session.get('/panel/api/inbounds/list')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return data.get('obj', [])
            
            logger.error(f"Failed to get inbounds: {response.text}")
            return []
        except Exception as e:
            logger.error(f"Error getting inbounds: {e}")
            return []

    async def get_inbound(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific inbound from the 3X-UI panel.
        
        Args:
            inbound_id: Inbound ID
            
        Returns:
            Inbound configuration or None if not found
        """
        if not await self.login():
            return None
        
        try:
            response = await self.session.get(f'/panel/api/inbounds/get/{inbound_id}')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return data.get('obj')
            
            logger.error(f"Failed to get inbound {inbound_id}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error getting inbound {inbound_id}: {e}")
            return None

    async def add_client(self, inbound_id: int, email: str, uuid: Optional[str] = None,
                         flow: Optional[str] = "", alter_id: int = 0, subid: str = "") -> Optional[Dict[str, Any]]:
        """
        Add a client to an inbound.
        
        Args:
            inbound_id: Inbound ID
            email: Client email (used as identifier)
            uuid: Optional UUID (will be generated if not provided)
            flow: Flow setting (for XTLS)
            alter_id: Alter ID for VMESS clients
            subid: Sub ID
            
        Returns:
            Client configuration or None if failed
        """
        if not await self.login():
            return None
        
        try:
            # Get inbound to determine protocol
            inbound = await self.get_inbound(inbound_id)
            if not inbound:
                logger.error(f"Inbound {inbound_id} not found")
                return None
            
            protocol = inbound.get('protocol', '').lower()
            
            # Prepare client data based on protocol
            client_data = {
                'email': email,
                'enable': True,
                'expiryTime': 0,  # Will be set later
                'subId': subid
            }
            
            if protocol == 'vmess':
                client_data.update({
                    'id': uuid or '',  # Will be generated by server if empty
                    'alterId': alter_id,
                    'totalGB': 0,  # Will be set later
                    'limitIp': 0
                })
            elif protocol in ['vless', 'trojan']:
                client_data.update({
                    'id': uuid or '',  # Will be generated by server if empty
                    'flow': flow,
                    'totalGB': 0,  # Will be set later
                    'limitIp': 0
                })
            else:
                logger.error(f"Unsupported protocol: {protocol}")
                return None
            
            # Send request to add client
            response = await self.session.post(
                f'/panel/api/inbounds/addClient/{inbound_id}',
                json=client_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    # Get updated inbound to retrieve the added client
                    updated_inbound = await self.get_inbound(inbound_id)
                    if updated_inbound:
                        clients = updated_inbound.get('clientStats', [])
                        for client in clients:
                            if client.get('email') == email:
                                return client
            
            logger.error(f"Failed to add client to inbound {inbound_id}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error adding client to inbound {inbound_id}: {e}")
            return None

    async def update_client(self, inbound_id: int, email: str, expiry_time: int,
                          total_gb: int, enable: bool = True) -> bool:
        """
        Update a client's settings.
        
        Args:
            inbound_id: Inbound ID
            email: Client email
            expiry_time: Expiry time in milliseconds since epoch
            total_gb: Traffic limit in GB
            enable: Whether the client is enabled
            
        Returns:
            True if successful, False otherwise
        """
        if not await self.login():
            return False
        
        try:
            # Get inbound to find client
            inbound = await self.get_inbound(inbound_id)
            if not inbound:
                logger.error(f"Inbound {inbound_id} not found")
                return False
            
            # Find client
            client_found = False
            for client in inbound.get('clientStats', []):
                if client.get('email') == email:
                    client_found = True
                    break
            
            if not client_found:
                logger.error(f"Client {email} not found in inbound {inbound_id}")
                return False
            
            # Prepare client update data
            update_data = {
                'email': email,
                'enable': enable,
                'expiryTime': expiry_time,
                'totalGB': total_gb * 1024 * 1024 * 1024  # Convert GB to bytes
            }
            
            # Send request to update client
            response = await self.session.post(
                f'/panel/api/inbounds/updateClient/{inbound_id}',
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return True
            
            logger.error(f"Failed to update client {email} in inbound {inbound_id}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error updating client {email} in inbound {inbound_id}: {e}")
            return False

    async def remove_client(self, inbound_id: int, email: str) -> bool:
        """
        Remove a client from an inbound.
        
        Args:
            inbound_id: Inbound ID
            email: Client email
            
        Returns:
            True if successful, False otherwise
        """
        if not await self.login():
            return False
        
        try:
            response = await self.session.post(
                f'/panel/api/inbounds/delClient/{inbound_id}/{email}'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return True
            
            logger.error(f"Failed to remove client {email} from inbound {inbound_id}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error removing client {email} from inbound {inbound_id}: {e}")
            return False

    async def get_client_traffic(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get client traffic statistics.
        
        Args:
            email: Client email
            
        Returns:
            Client traffic statistics or None if not found
        """
        if not await self.login():
            return None
        
        try:
            # Get all inbounds
            inbounds = await self.get_inbounds()
            
            # Search for client in all inbounds
            for inbound in inbounds:
                for client in inbound.get('clientStats', []):
                    if client.get('email') == email:
                        return {
                            'up': client.get('up', 0),
                            'down': client.get('down', 0),
                            'total': client.get('total', 0),
                            'expiry_time': client.get('expiryTime', 0),
                            'enable': client.get('enable', False),
                            'inbound_id': inbound.get('id')
                        }
            
            logger.warning(f"Client {email} not found in any inbound")
            return None
        except Exception as e:
            logger.error(f"Error getting client traffic for {email}: {e}")
            return None

    async def reset_client_traffic(self, inbound_id: int, email: str) -> bool:
        """
        Reset client traffic statistics.
        
        Args:
            inbound_id: Inbound ID
            email: Client email
            
        Returns:
            True if successful, False otherwise
        """
        if not await self.login():
            return False
        
        try:
            response = await self.session.post(
                f'/panel/api/inbounds/resetClientTraffic/{inbound_id}/{email}'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return True
            
            logger.error(f"Failed to reset traffic for client {email} in inbound {inbound_id}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error resetting traffic for client {email} in inbound {inbound_id}: {e}")
            return False
    
    async def get_client_subscription_url(self, email: str, subid: str = "") -> Optional[str]:
        """
        Get client subscription URL.
        
        Args:
            email: Client email
            subid: Subscription ID (optional)
            
        Returns:
            Subscription URL or None if not available
        """
        # The subscription URL format is generally:
        # {base_url}/sub/{subid}
        if not subid:
            # If no subid provided, use the email as subid
            subid = email
        
        subscription_url = f"{self.base_url}/sub/{subid}"
        return subscription_url
    
    async def close(self) -> None:
        """Close the HTTP session."""
        await self.session.aclose()

    async def monitor_server_status(self) -> Dict[str, Any]:
        """
        Monitor server status and send notifications if issues are detected.
        
        Returns:
            Dictionary with monitoring results
        """
        try:
            # Ensure we have a valid session
            await self.ensure_login()
            
            # Check inbounds status
            inbounds = await self.list_inbounds()
            
            # Get server stats if available
            server_stats = {}
            try:
                # Some panel versions have server stats API
                stats_url = f"/panel/api/stats"
                response = await self.session.get(stats_url)
                if response.status_code == 200:
                    stats_data = response.json()
                    if stats_data.get("success"):
                        server_stats = stats_data.get("obj", {})
            except Exception as e:
                logger.warning(f"Failed to get server stats: {e}")
                
            # Prepare monitoring results
            results = {
                "timestamp": datetime.now().isoformat(),
                "panel_id": self.panel_id,
                "panel_url": self.base_url,
                "status": "online",
                "inbounds_count": len(inbounds),
                "active_inbounds": sum(1 for i in inbounds if i.get("enable", False)),
                "clients_count": sum(len(i.get("clientStats", [])) for i in inbounds),
                "server_stats": server_stats,
                "issues": []
            }
            
            # Check for inbound issues
            for inbound in inbounds:
                inbound_id = inbound.get("id")
                if not inbound.get("enable", True):
                    results["issues"].append({
                        "type": "inbound_disabled",
                        "inbound_id": inbound_id,
                        "inbound_name": inbound.get("remark", f"Inbound-{inbound_id}"),
                        "severity": "warning"
                    })
                    
                # Check client stats for each inbound
                for client in inbound.get("clientStats", []):
                    client_id = client.get("id")
                    client_email = client.get("email", f"client-{client_id}")
                    
                    # Check for client issues
                    if not client.get("enable", True):
                        results["issues"].append({
                            "type": "client_disabled",
                            "inbound_id": inbound_id,
                            "client_id": client_id,
                            "client_email": client_email,
                            "severity": "info"
                        })
                    
                    # Check for traffic usage
                    if client.get("total", 0) > 0:  # If client has traffic limit
                        used_traffic = client.get("up", 0) + client.get("down", 0)
                        total_traffic = client.get("total", 1)
                        usage_percent = (used_traffic / total_traffic) * 100
                        
                        if usage_percent >= 90:
                            results["issues"].append({
                                "type": "high_traffic_usage",
                                "inbound_id": inbound_id,
                                "client_id": client_id,
                                "client_email": client_email,
                                "usage_percent": round(usage_percent, 2),
                                "severity": "warning" if usage_percent < 95 else "critical"
                            })
                    
                    # Check for expiry
                    if client.get("expiryTime", 0) > 0:  # If client has expiry time
                        expiry_time = datetime.fromtimestamp(client.get("expiryTime", 0) / 1000)
                        now = datetime.now()
                        days_left = (expiry_time - now).days
                        
                        if days_left <= 3:
                            results["issues"].append({
                                "type": "near_expiry",
                                "inbound_id": inbound_id,
                                "client_id": client_id,
                                "client_email": client_email,
                                "expiry_date": expiry_time.isoformat(),
                                "days_left": days_left,
                                "severity": "warning" if days_left > 1 else "critical"
                            })
            
            # Send notifications for critical issues
            if results["issues"]:
                from core.services.notification import notification_service
                
                critical_issues = [i for i in results["issues"] if i.get("severity") == "critical"]
                if critical_issues:
                    server_data = {
                        "name": f"Panel {self.panel_id}",
                        "address": self.base_url
                    }
                    
                    details = "مشکلات حیاتی شناسایی شده:\n"
                    for i, issue in enumerate(critical_issues, 1):
                        if issue["type"] == "high_traffic_usage":
                            details += f"{i}. مصرف بالای ترافیک ({issue['usage_percent']}%) برای کاربر {issue['client_email']}\n"
                        elif issue["type"] == "near_expiry":
                            details += f"{i}. انقضای نزدیک ({issue['days_left']} روز مانده) برای کاربر {issue['client_email']}\n"
                    
                    await notification_service.send_server_monitoring_alert(
                        server_data=server_data,
                        alert_type="مشکلات حیاتی",
                        details=details
                    )
            
            return results
        
        except Exception as e:
            logger.error(f"Error monitoring server status: {e}")
            
            # Send offline notification
            try:
                from core.services.notification import notification_service
                
                server_data = {
                    "name": f"Panel {self.panel_id}",
                    "address": self.base_url
                }
                
                await notification_service.send_server_monitoring_alert(
                    server_data=server_data,
                    alert_type="پنل آفلاین",
                    details=f"پنل در دسترس نیست. خطا: {str(e)}"
                )
            except Exception as notify_error:
                logger.error(f"Failed to send offline notification: {notify_error}")
            
            return {
                "timestamp": datetime.now().isoformat(),
                "panel_id": self.panel_id,
                "panel_url": self.base_url,
                "status": "offline",
                "error": str(e),
                "issues": [{
                    "type": "panel_offline",
                    "severity": "critical",
                    "details": str(e)
                }]
            }


# Panel management functions

async def get_panel(panel_id: int) -> Optional[ThreeXUIClient]:
    """
    Get a 3X-UI panel client by ID.
    
    Args:
        panel_id: Panel ID
        
    Returns:
        ThreeXUIClient instance or None if panel not found
    """
    try:
        # Get panel details from database
        from core.database import get_setting
        
        panel_key = f"threexui_panel_{panel_id}"
        panel_data = get_setting(panel_key)
        
        if not panel_data:
            logger.error(f"Panel {panel_id} not found in database")
            return None
        
        try:
            panel_info = json.loads(panel_data)
        except json.JSONDecodeError:
            logger.error(f"Invalid panel data format for panel {panel_id}")
            return None
        
        base_url = panel_info.get('base_url')
        username = panel_info.get('username')
        password = panel_info.get('password')
        
        if not base_url or not username or not password:
            logger.error(f"Missing required panel information for panel {panel_id}")
            return None
        
        # Create client instance
        client = ThreeXUIClient(panel_id, base_url, username, password)
        
        # Test connection
        if not await client.login():
            logger.error(f"Could not connect to panel {panel_id}")
            return None
        
        return client
    except Exception as e:
        logger.error(f"Error getting panel {panel_id}: {e}")
        return None


async def get_all_panels() -> List[Dict[str, Any]]:
    """
    Get all 3X-UI panels.
    
    Returns:
        List of panel information
    """
    try:
        # Get panel IDs from database
        from core.database import get_setting
        
        panel_ids_data = get_setting("threexui_panel_ids")
        if not panel_ids_data:
            return []
        
        try:
            panel_ids = json.loads(panel_ids_data)
        except json.JSONDecodeError:
            logger.error("Invalid panel IDs format in database")
            return []
        
        panels = []
        for panel_id in panel_ids:
            panel_key = f"threexui_panel_{panel_id}"
            panel_data = get_setting(panel_key)
            
            if panel_data:
                try:
                    panel_info = json.loads(panel_data)
                    panel_info['id'] = panel_id
                    panels.append(panel_info)
                except json.JSONDecodeError:
                    logger.error(f"Invalid panel data format for panel {panel_id}")
        
        return panels
    except Exception as e:
        logger.error(f"Error getting all panels: {e}")
        return []


async def add_panel(base_url: str, username: str, password: str, name: str = "") -> Optional[int]:
    """
    Add a new 3X-UI panel.
    
    Args:
        base_url: Base URL of the panel
        username: Username for panel login
        password: Password for panel login
        name: Panel name (optional)
        
    Returns:
        Panel ID if successful, None otherwise
    """
    try:
        # Get panel IDs from database
        from core.database import get_setting, update_setting
        
        panel_ids_data = get_setting("threexui_panel_ids")
        if panel_ids_data:
            try:
                panel_ids = json.loads(panel_ids_data)
            except json.JSONDecodeError:
                panel_ids = []
        else:
            panel_ids = []
        
        # Generate new panel ID
        new_panel_id = 1
        if panel_ids:
            new_panel_id = max(panel_ids) + 1
        
        # Create panel info
        panel_info = {
            'base_url': base_url,
            'username': username,
            'password': password,
            'name': name or f"Panel {new_panel_id}"
        }
        
        # Test connection
        client = ThreeXUIClient(new_panel_id, base_url, username, password)
        if not await client.login():
            logger.error("Could not connect to new panel")
            await client.close()
            return None
        
        await client.close()
        
        # Save panel info
        panel_key = f"threexui_panel_{new_panel_id}"
        update_setting(panel_key, json.dumps(panel_info))
        
        # Update panel IDs
        panel_ids.append(new_panel_id)
        update_setting("threexui_panel_ids", json.dumps(panel_ids))
        
        return new_panel_id
    except Exception as e:
        logger.error(f"Error adding panel: {e}")
        return None


async def remove_panel(panel_id: int) -> bool:
    """
    Remove a 3X-UI panel.
    
    Args:
        panel_id: Panel ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get panel IDs from database
        from core.database import get_setting, update_setting
        
        panel_ids_data = get_setting("threexui_panel_ids")
        if not panel_ids_data:
            return False
        
        try:
            panel_ids = json.loads(panel_ids_data)
        except json.JSONDecodeError:
            logger.error("Invalid panel IDs format in database")
            return False
        
        # Check if panel exists
        if panel_id not in panel_ids:
            logger.error(f"Panel {panel_id} not found")
            return False
        
        # Remove panel info
        panel_key = f"threexui_panel_{panel_id}"
        update_setting(panel_key, "")
        
        # Remove panel cookie
        cookie_key = f"threexui_cookie_{panel_id}"
        update_setting(cookie_key, "")
        
        # Update panel IDs
        panel_ids.remove(panel_id)
        update_setting("threexui_panel_ids", json.dumps(panel_ids))
        
        return True
    except Exception as e:
        logger.error(f"Error removing panel {panel_id}: {e}")
        return False


# Account management functions

async def create_v2ray_account(panel_id: int, inbound_id: int, email: str, expiry_days: int,
                              traffic_gb: int, uuid: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Create a V2Ray account.
    
    Args:
        panel_id: Panel ID
        inbound_id: Inbound ID
        email: Client email
        expiry_days: Number of days until account expires
        traffic_gb: Traffic limit in GB
        uuid: Optional UUID
        
    Returns:
        Account information or None if failed
    """
    try:
        # Get panel
        panel = await get_panel(panel_id)
        if not panel:
            logger.error(f"Panel {panel_id} not found or not accessible")
            return None
        
        # Calculate expiry time
        expiry_time = int((datetime.now() + timedelta(days=expiry_days)).timestamp() * 1000)
        
        # Add client
        client = await panel.add_client(inbound_id, email, uuid)
        if not client:
            logger.error(f"Failed to add client {email}")
            await panel.close()
            return None
        
        # Update client settings
        if not await panel.update_client(inbound_id, email, expiry_time, traffic_gb):
            logger.error(f"Failed to update client {email} settings")
            # Try to remove the client since update failed
            await panel.remove_client(inbound_id, email)
            await panel.close()
            return None
        
        # Get subscription URL
        subscription_url = await panel.get_client_subscription_url(email)
        
        # Get inbound details for config
        inbound = await panel.get_inbound(inbound_id)
        protocol = inbound.get('protocol', '').lower() if inbound else ''
        
        # Get client details
        client_traffic = await panel.get_client_traffic(email)
        
        # Close panel connection
        await panel.close()
        
        # Return account information
        return {
            'panel_id': panel_id,
            'inbound_id': inbound_id,
            'email': email,
            'uuid': client.get('id', uuid or 'unknown'),  # UUID may have been generated by the server
            'protocol': protocol,
            'subscription_url': subscription_url,
            'expiry_time': expiry_time,
            'traffic_limit': traffic_gb * 1024 * 1024 * 1024,  # Convert GB to bytes
            'traffic_used': client_traffic.get('down', 0) if client_traffic else 0,
            'status': 'active'
        }
    except Exception as e:
        logger.error(f"Error creating V2Ray account: {e}")
        return None


async def update_v2ray_account(panel_id: int, inbound_id: int, email: str, expiry_days: Optional[int] = None,
                             traffic_gb: Optional[int] = None, enable: bool = True) -> bool:
    """
    Update a V2Ray account.
    
    Args:
        panel_id: Panel ID
        inbound_id: Inbound ID
        email: Client email
        expiry_days: Number of days until account expires (from now)
        traffic_gb: Traffic limit in GB
        enable: Whether the account is enabled
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get panel
        panel = await get_panel(panel_id)
        if not panel:
            logger.error(f"Panel {panel_id} not found or not accessible")
            return False
        
        # Get client traffic to get current settings
        client_traffic = await panel.get_client_traffic(email)
        if not client_traffic:
            logger.error(f"Client {email} not found in panel {panel_id}")
            await panel.close()
            return False
        
        # Calculate new expiry time if provided
        expiry_time = client_traffic.get('expiry_time', 0)
        if expiry_days is not None:
            expiry_time = int((datetime.now() + timedelta(days=expiry_days)).timestamp() * 1000)
        
        # Get current traffic limit if not provided
        traffic = traffic_gb
        if traffic is None:
            current_total = client_traffic.get('total', 0)
            traffic = current_total / (1024 * 1024 * 1024)  # Convert bytes to GB
        
        # Update client settings
        result = await panel.update_client(inbound_id, email, expiry_time, traffic, enable)
        
        # Close panel connection
        await panel.close()
        
        return result
    except Exception as e:
        logger.error(f"Error updating V2Ray account: {e}")
        return False


async def delete_v2ray_account(panel_id: int, inbound_id: int, email: str) -> bool:
    """
    Delete a V2Ray account.
    
    Args:
        panel_id: Panel ID
        inbound_id: Inbound ID
        email: Client email
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get panel
        panel = await get_panel(panel_id)
        if not panel:
            logger.error(f"Panel {panel_id} not found or not accessible")
            return False
        
        # Remove client
        result = await panel.remove_client(inbound_id, email)
        
        # Close panel connection
        await panel.close()
        
        return result
    except Exception as e:
        logger.error(f"Error deleting V2Ray account: {e}")
        return False


async def get_v2ray_account_traffic(panel_id: int, email: str) -> Optional[Dict[str, Any]]:
    """
    Get V2Ray account traffic statistics.
    
    Args:
        panel_id: Panel ID
        email: Client email
        
    Returns:
        Traffic statistics or None if failed
    """
    try:
        # Get panel
        panel = await get_panel(panel_id)
        if not panel:
            logger.error(f"Panel {panel_id} not found or not accessible")
            return None
        
        # Get client traffic
        client_traffic = await panel.get_client_traffic(email)
        
        # Close panel connection
        await panel.close()
        
        return client_traffic
    except Exception as e:
        logger.error(f"Error getting V2Ray account traffic: {e}")
        return None


async def reset_v2ray_account_traffic(panel_id: int, inbound_id: int, email: str) -> bool:
    """
    Reset V2Ray account traffic statistics.
    
    Args:
        panel_id: Panel ID
        inbound_id: Inbound ID
        email: Client email
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get panel
        panel = await get_panel(panel_id)
        if not panel:
            logger.error(f"Panel {panel_id} not found or not accessible")
            return False
        
        # Reset client traffic
        result = await panel.reset_client_traffic(inbound_id, email)
        
        # Close panel connection
        await panel.close()
        
        return result
    except Exception as e:
        logger.error(f"Error resetting V2Ray account traffic: {e}")
        return False 