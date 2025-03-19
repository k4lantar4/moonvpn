"""
MoonVPN Telegram Bot - Server Model

This module provides the Server model for managing VPN server data and operations.
"""

import logging
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

from core.database import get_db_connection, execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete
import api_client

logger = logging.getLogger(__name__)

class Server:
    """Server model for managing VPN server data and operations."""
    
    def __init__(self, id, name, host, port, username, password, api_port, location, 
                 country, country_flag, type, is_active, network_type="tcp", protocol="Vmess",
                 config=None, notes=None, created_at=None, updated_at=None):
        """Initialize a server with given attributes"""
        self.id = id
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.api_port = api_port
        self.location = location
        self.country = country
        self.country_flag = country_flag
        self.type = type
        self.is_active = is_active
        self.network_type = network_type
        self.protocol = protocol
        self.config = config or {}
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def get_by_id(cls, server_id):
        """Get a server by ID"""
        try:
            # Try to get from cache first
            cached_server = cache_get(f"server:id:{server_id}")
            if cached_server:
                return cls(**cached_server)
            
            # Get from database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, host, port, username, password, api_port, location, 
                       country, country_flag, type, is_active, config, notes, created_at, 
                       updated_at, network_type, protocol
                FROM servers WHERE id = %s
                """,
                (server_id,)
            )
            server_data = cursor.fetchone()
            conn.close()
            
            if server_data:
                # Parse config JSON if it exists
                config = json.loads(server_data[12]) if server_data[12] else {}
                
                # Cache server data
                cache_set(f"server:id:{server_id}", dict(server_data), 300)  # Cache for 5 minutes
                
                return cls(
                    id=server_data[0],
                    name=server_data[1],
                    host=server_data[2],
                    port=server_data[3],
                    username=server_data[4],
                    password=server_data[5],
                    api_port=server_data[6],
                    location=server_data[7],
                    country=server_data[8],
                    country_flag=server_data[9],
                    type=server_data[10],
                    is_active=server_data[11],
                    config=config,
                    notes=server_data[13],
                    created_at=server_data[14],
                    updated_at=server_data[15],
                    network_type=server_data[16] or "tcp",
                    protocol=server_data[17] or "Vmess"
                )
            return None
        except Exception as e:
            logger.error(f"Error getting server by ID: {e}")
            return None
    
    @classmethod
    def get_all(cls):
        """Get all servers"""
        try:
            # Get from database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, host, port, username, password, api_port, location, 
                       country, country_flag, type, is_active, config, notes, created_at, 
                       updated_at, network_type, protocol
                FROM servers
                ORDER BY is_active DESC, location ASC
                """
            )
            servers_data = cursor.fetchall()
            conn.close()
            
            servers = []
            for server_data in servers_data:
                # Parse config JSON if it exists
                config = json.loads(server_data[12]) if server_data[12] else {}
                
                servers.append(cls(
                    id=server_data[0],
                    name=server_data[1],
                    host=server_data[2],
                    port=server_data[3],
                    username=server_data[4],
                    password=server_data[5],
                    api_port=server_data[6],
                    location=server_data[7],
                    country=server_data[8],
                    country_flag=server_data[9],
                    type=server_data[10],
                    is_active=server_data[11],
                    config=config,
                    notes=server_data[13],
                    created_at=server_data[14],
                    updated_at=server_data[15],
                    network_type=server_data[16] or "tcp",
                    protocol=server_data[17] or "Vmess"
                ))
            return servers
        except Exception as e:
            logger.error(f"Error getting all servers: {e}")
            return []
    
    @classmethod
    def get_all_active(cls):
        """Get all active servers"""
        try:
            # Get from database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, host, port, username, password, api_port, location, 
                       country, country_flag, type, is_active, config, notes, created_at, 
                       updated_at, network_type, protocol
                FROM servers
                WHERE is_active = TRUE
                ORDER BY location ASC
                """
            )
            servers_data = cursor.fetchall()
            conn.close()
            
            servers = []
            for server_data in servers_data:
                # Parse config JSON if it exists
                config = json.loads(server_data[12]) if server_data[12] else {}
                
                servers.append(cls(
                    id=server_data[0],
                    name=server_data[1],
                    host=server_data[2],
                    port=server_data[3],
                    username=server_data[4],
                    password=server_data[5],
                    api_port=server_data[6],
                    location=server_data[7],
                    country=server_data[8],
                    country_flag=server_data[9],
                    type=server_data[10],
                    is_active=server_data[11],
                    config=config,
                    notes=server_data[13],
                    created_at=server_data[14],
                    updated_at=server_data[15],
                    network_type=server_data[16] or "tcp",
                    protocol=server_data[17] or "Vmess"
                ))
            return servers
        except Exception as e:
            logger.error(f"Error getting active servers: {e}")
            return []
    
    def test_connection(self):
        """Test connection to the server by trying to login to X-UI panel"""
        try:
            # Construct API URL
            api_url = f"http://{self.host}:{self.api_port}/login"
            
            # Prepare login data
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            # Send login request
            response = requests.post(api_url, json=login_data, timeout=10)
            
            # Check if login was successful
            if response.status_code == 200:
                # Parse response to check for success
                data = response.json()
                if data.get("success"):
                    return True, "Connection successful"
                else:
                    return False, f"Authentication failed: {data.get('msg', 'Unknown error')}"
            else:
                return False, f"Connection failed with status code: {response.status_code}"
        except Exception as e:
            logger.error(f"Error testing server connection: {e}")
            return False, f"Connection failed: {str(e)}"
    
    def login(self):
        """Login to X-UI panel and return session token"""
        try:
            # Construct API URL
            api_url = f"http://{self.host}:{self.api_port}/login"
            
            # Prepare login data
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            # Send login request
            response = requests.post(api_url, json=login_data, timeout=10)
            
            # Check if login was successful
            if response.status_code == 200:
                # Parse response to check for success
                data = response.json()
                if data.get("success"):
                    # Get cookies from response
                    cookies = response.cookies
                    return cookies, None
                else:
                    return None, f"Authentication failed: {data.get('msg', 'Unknown error')}"
            else:
                return None, f"Connection failed with status code: {response.status_code}"
        except Exception as e:
            logger.error(f"Error logging into server: {e}")
            return None, f"Login failed: {str(e)}"
    
    def get_inbounds(self):
        """Get list of inbounds from X-UI panel"""
        try:
            # Login to get session
            cookies, error = self.login()
            if not cookies:
                return None, error
            
            # Construct API URL
            api_url = f"http://{self.host}:{self.api_port}/xui/inbound/list"
            
            # Send request with session cookies
            response = requests.post(api_url, cookies=cookies, timeout=10)
            
            # Check if request was successful
            if response.status_code == 200:
                # Parse response
                data = response.json()
                if data.get("success"):
                    return data.get("obj"), None
                else:
                    return None, f"Failed to get inbounds: {data.get('msg', 'Unknown error')}"
            else:
                return None, f"Request failed with status code: {response.status_code}"
        except Exception as e:
            logger.error(f"Error getting inbounds from server: {e}")
            return None, f"Request failed: {str(e)}"
    
    def create_inbound(self, email, uuid_str, traffic_limit, expiry_date):
        """Create a new inbound on X-UI panel"""
        try:
            # For demo purposes, we'll simulate a successful inbound creation
            # In a real implementation, you would make API calls to the X-UI panel
            
            # Simulate success
            logger.info(f"Created inbound for {email} on server {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error creating inbound on server: {e}")
            return False
    
    def delete_inbound(self, email):
        """Delete an inbound from X-UI panel"""
        try:
            # For demo purposes, we'll simulate a successful inbound deletion
            # In a real implementation, you would make API calls to the X-UI panel
            
            # Simulate success
            logger.info(f"Deleted inbound for {email} from server {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting inbound from server: {e}")
            return False
    
    def update_inbound_uuid(self, email, new_uuid):
        """Update UUID for an inbound on X-UI panel"""
        try:
            # For demo purposes, we'll simulate a successful UUID update
            # In a real implementation, you would make API calls to the X-UI panel
            
            # Simulate success
            logger.info(f"Updated UUID for {email} on server {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error updating UUID on server: {e}")
            return False
    
    def update_inbound_expiry(self, email, new_expiry):
        """Update expiry date for an inbound on X-UI panel"""
        try:
            # For demo purposes, we'll simulate a successful expiry update
            # In a real implementation, you would make API calls to the X-UI panel
            
            # Simulate success
            logger.info(f"Updated expiry for {email} on server {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error updating expiry on server: {e}")
            return False
    
    def update_inbound_traffic(self, email, new_limit):
        """Update traffic limit for an inbound on X-UI panel"""
        try:
            # For demo purposes, we'll simulate a successful traffic limit update
            # In a real implementation, you would make API calls to the X-UI panel
            
            # Simulate success
            logger.info(f"Updated traffic limit for {email} on server {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error updating traffic limit on server: {e}")
            return False
    
    def get_inbound_info(self, email):
        """Get information about a specific inbound from X-UI panel"""
        try:
            # For demo purposes, we'll simulate fetching inbound info
            # In a real implementation, you would make API calls to the X-UI panel
            
            # Simulate a response with mock data
            return {
                "traffic_used": 1024 * 1024 * 1024 * 2,  # 2 GB
                "expiry_date": datetime.now(),
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error getting inbound info from server: {e}")
            return None
    
    def update(self, name=None, host=None, port=None, username=None, password=None, 
               api_port=None, location=None, country=None, country_flag=None, 
               type=None, is_active=None, network_type=None, protocol=None, config=None, notes=None):
        """Update server information in database"""
        try:
            # Prepare update data
            update_data = {}
            update_fields = []
            
            if name is not None:
                update_data["name"] = name
                update_fields.append("name = %(name)s")
            
            if host is not None:
                update_data["host"] = host
                update_fields.append("host = %(host)s")
            
            if port is not None:
                update_data["port"] = port
                update_fields.append("port = %(port)s")
            
            if username is not None:
                update_data["username"] = username
                update_fields.append("username = %(username)s")
            
            if password is not None:
                update_data["password"] = password
                update_fields.append("password = %(password)s")
            
            if api_port is not None:
                update_data["api_port"] = api_port
                update_fields.append("api_port = %(api_port)s")
            
            if location is not None:
                update_data["location"] = location
                update_fields.append("location = %(location)s")
            
            if country is not None:
                update_data["country"] = country
                update_fields.append("country = %(country)s")
            
            if country_flag is not None:
                update_data["country_flag"] = country_flag
                update_fields.append("country_flag = %(country_flag)s")
            
            if type is not None:
                update_data["type"] = type
                update_fields.append("type = %(type)s")
            
            if is_active is not None:
                update_data["is_active"] = is_active
                update_fields.append("is_active = %(is_active)s")
            
            if network_type is not None:
                update_data["network_type"] = network_type
                update_fields.append("network_type = %(network_type)s")
            
            if protocol is not None:
                update_data["protocol"] = protocol
                update_fields.append("protocol = %(protocol)s")
            
            if config is not None:
                update_data["config"] = json.dumps(config)
                update_fields.append("config = %(config)s")
            
            if notes is not None:
                update_data["notes"] = notes
                update_fields.append("notes = %(notes)s")
            
            # Add updated_at timestamp
            update_fields.append("updated_at = NOW()")
            
            # If nothing to update, return success
            if not update_fields:
                return True
            
            # Build SQL query
            sql = f"""
                UPDATE servers 
                SET {', '.join(update_fields)}
                WHERE id = %(id)s
            """
            
            # Add ID to update data
            update_data["id"] = self.id
            
            # Execute update
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(sql, update_data)
            conn.commit()
            conn.close()
            
            # Update object attributes
            for key, value in update_data.items():
                if key != "id" and key != "config":
                    setattr(self, key, value)
            
            if config is not None:
                self.config = config
            
            self.updated_at = datetime.now()
            
            return True
        except Exception as e:
            logger.error(f"Error updating server: {e}")
            return False
    
    @classmethod
    def create(cls, name, host, port, username, password, api_port, location, 
               country, country_flag, type="x-ui", is_active=True, network_type="tcp", 
               protocol="Vmess", config=None, notes=None):
        """Create a new server in database"""
        try:
            # Prepare config JSON
            config_json = json.dumps(config or {})
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO servers
                (name, host, port, username, password, api_port, location, country, 
                 country_flag, type, is_active, config, notes, network_type, protocol, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id, created_at, updated_at
                """,
                (name, host, port, username, password, api_port, location, country, 
                 country_flag, type, is_active, config_json, notes, network_type, protocol)
            )
            
            result = cursor.fetchone()
            server_id = result[0]
            created_at = result[1]
            updated_at = result[2]
            
            conn.commit()
            conn.close()
            
            # Return the new server instance
            return cls(
                id=server_id,
                name=name,
                host=host,
                port=port,
                username=username,
                password=password,
                api_port=api_port,
                location=location,
                country=country,
                country_flag=country_flag,
                type=type,
                is_active=is_active,
                network_type=network_type,
                protocol=protocol,
                config=config or {},
                notes=notes,
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            logger.error(f"Error creating server: {e}")
            return None
    
    def delete(self):
        """Delete the server from database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # First check if server has any accounts
            cursor.execute(
                """
                SELECT COUNT(*) FROM vpn_accounts WHERE server_id = %s
                """,
                (self.id,)
            )
            
            count = cursor.fetchone()[0]
            if count > 0:
                # Server has accounts, don't delete
                conn.close()
                return False, f"Cannot delete server with {count} active accounts"
            
            # No accounts, proceed with deletion
            cursor.execute(
                """
                DELETE FROM servers WHERE id = %s
                """,
                (self.id,)
            )
            
            conn.commit()
            conn.close()
            
            return True, "Server deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting server: {e}")
            return False, f"Error deleting server: {str(e)}"

    def save(self) -> bool:
        """
        Save server changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE servers SET
                name = %s,
                host = %s,
                port = %s,
                location = %s,
                protocol = %s,
                username = %s,
                password = %s,
                config = %s,
                notes = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.name,
            self.host,
            self.port,
            self.location,
            self.protocol,
            self.username,
            self.password,
            json.dumps(self.config),
            self.notes,
            self.id
        ))
        
        if success:
            # Clear cache
            cache_delete(f"server:id:{self.id}")
            
        return success

    def update_load(self) -> bool:
        """
        Update server load.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Get account count
        from models.vpn_account import VPNAccount
        count = VPNAccount.count_accounts_by_server(self.id)
        
        # Calculate load percentage
        self.current_load = int((count / self.capacity) * 100) if self.capacity > 0 else 100
        
        # Save changes
        return self.save()

    def ping(self) -> Tuple[bool, float]:
        """
        Ping the server.
        
        Returns:
            Tuple[bool, float]: (success, latency in ms)
        """
        try:
            # Ping the server
            start_time = datetime.now()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex((self.host, self.port))
            s.close()
            
            end_time = datetime.now()
            
            # Calculate latency
            latency = (end_time - start_time).total_seconds() * 1000
            
            return (result == 0, latency)
        except Exception as e:
            logger.error(f"Error pinging server {self.id}: {e}")
            return (False, 0)

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to the server.
        
        Returns:
            Dict[str, Any]: Connection test results
        """
        # Try using API client first
        try:
            result = api_client.test_server_connection(self.id)
            if result and result.get('status') != 'error':
                return result
        except Exception as e:
            logger.error(f"Error testing server connection via API: {e}")
            
        # Fallback to ping
        success, latency = self.ping()
        
        return {
            "status": "success" if success else "error",
            "latency": latency if success else None,
            "message": "Connection successful" if success else "Connection failed"
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get server statistics.
        
        Returns:
            Dict[str, Any]: Server statistics
        """
        # Try using API client first
        try:
            result = api_client.get_server_metrics(self.id)
            if result and result.get('status') != 'error':
                return result
        except Exception as e:
            logger.error(f"Error getting server stats via API: {e}")
            
        # Fallback to basic stats
        success, latency = self.ping()
        
        # Get account count
        from models.vpn_account import VPNAccount
        count = VPNAccount.count_accounts_by_server(self.id)
        
        return {
            "status": "success" if success else "error",
            "online": success,
            "latency": latency if success else None,
            "accounts": count,
            "load_percent": self.current_load
        }

    def sync_with_panel(self) -> bool:
        """
        Sync server with panel.
        
        Returns:
            bool: True if sync was successful, False otherwise
        """
        # Try using API client
        try:
            result = api_client.sync_server(self.id)
            return result
        except Exception as e:
            logger.error(f"Error syncing server with panel: {e}")
            return False

    def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        Get all inbounds for this server.
        
        Returns:
            List[Dict[str, Any]]: Inbounds data
        """
        try:
            # Login to panel if not already
            api_client.x_ui_panel_login()
            
            # Get inbounds
            inbounds = api_client.get_inbounds()
            return inbounds
        except Exception as e:
            logger.error(f"Error getting inbounds: {e}")
            return []

    def create_inbound(self, protocol: str = None, port: int = None, 
                      remark: str = None) -> Optional[int]:
        """
        Create an inbound on the server.
        
        Args:
            protocol (str, optional): Protocol to use (vmess, vless, etc.)
            port (int, optional): Port to use
            remark (str, optional): Remark/name for the inbound
            
        Returns:
            Optional[int]: Inbound ID or None if creation failed
        """
        try:
            # Login to panel if not already
            api_client.x_ui_panel_login()
            
            # Prepare data
            protocol = protocol or self.protocol or "vmess"
            port = port or self.port
            remark = remark or f"MoonVPN-{self.name}"
            
            # Create inbound data
            inbound_data = {
                "protocol": protocol,
                "port": port,
                "remark": remark,
                "enable": True,
                "expiryTime": 0,  # No expiry for the inbound itself
                "listen": "",
                "totalGB": 0,  # No traffic limit for the inbound itself
                "sniffing": True,
                "settings": json.dumps({
                    "clients": [],
                    "disableInsecureEncryption": False
                }),
                "streamSettings": json.dumps({
                    "network": "tcp"
                })
            }
            
            # Create inbound
            inbound = api_client.create_inbound(inbound_data)
            
            if inbound:
                # Get the inbound ID
                inbound_id = inbound.get('id')
                
                if inbound_id:
                    # Update server with inbound ID
                    self.inbound_id = inbound_id
                    self.save()
                    
                    return inbound_id
                    
            return None
        except Exception as e:
            logger.error(f"Error creating inbound: {e}")
            return None

    def update_inbound(self, inbound_id: int = None, protocol: str = None, 
                      port: int = None, remark: str = None) -> bool:
        """
        Update an inbound on the server.
        
        Args:
            inbound_id (int, optional): Inbound ID to update (defaults to server's inbound_id)
            protocol (str, optional): Protocol to use (vmess, vless, etc.)
            port (int, optional): Port to use
            remark (str, optional): Remark/name for the inbound
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Login to panel if not already
            api_client.x_ui_panel_login()
            
            # Get inbound ID
            inbound_id = inbound_id or self.inbound_id
            
            if not inbound_id:
                logger.error(f"No inbound ID specified for server {self.id}")
                return False
                
            # Prepare data
            inbound_data = {}
            
            if protocol:
                inbound_data["protocol"] = protocol
                
            if port:
                inbound_data["port"] = port
                
            if remark:
                inbound_data["remark"] = remark
                
            # Update inbound
            success = api_client.update_inbound(inbound_id, inbound_data)
            
            if success:
                # Update server with new data if needed
                if protocol:
                    self.protocol = protocol
                    
                if port:
                    self.port = port
                    
                self.save()
                
            return success
        except Exception as e:
            logger.error(f"Error updating inbound: {e}")
            return False

    def delete_inbound(self, inbound_id: int = None) -> bool:
        """
        Delete an inbound from the server.
        
        Args:
            inbound_id (int, optional): Inbound ID to delete (defaults to server's inbound_id)
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Login to panel if not already
            api_client.x_ui_panel_login()
            
            # Get inbound ID
            inbound_id = inbound_id or self.inbound_id
            
            if not inbound_id:
                logger.error(f"No inbound ID specified for server {self.id}")
                return False
                
            # Delete inbound
            success = api_client.delete_inbound(inbound_id)
            
            if success:
                # Update server
                self.inbound_id = None
                self.save()
                
            return success
        except Exception as e:
            logger.error(f"Error deleting inbound: {e}")
            return False

    def get_load(self) -> int:
        """
        Get server load percentage.
        
        Returns:
            int: Server load percentage
        """
        # Update load first
        self.update_load()
        return self.current_load

    def is_overloaded(self) -> bool:
        """
        Check if server is overloaded.
        
        Returns:
            bool: True if server is overloaded, False otherwise
        """
        threshold = 90  # 90% capacity is considered overloaded
        return self.get_load() >= threshold

    def is_available(self) -> bool:
        """
        Check if server is available for new accounts.
        
        Returns:
            bool: True if server is available, False otherwise
        """
        return self.is_active and not self.is_overloaded()

    @staticmethod
    def get_best_server() -> Optional['Server']:
        """
        Get the best server for a new account.
        
        Returns:
            Optional[Server]: Best server or None if no servers available
        """
        # Get all active servers
        servers = Server.get_active()
        
        # Filter out overloaded servers
        available_servers = [server for server in servers if not server.is_overloaded()]
        
        if not available_servers:
            return None
            
        # Sort by load (lowest first)
        sorted_servers = sorted(available_servers, key=lambda s: s.get_load())
        
        return sorted_servers[0] if sorted_servers else None

    @staticmethod
    def get_best_server_by_location(location: str) -> Optional['Server']:
        """
        Get the best server for a new account in a specific location.
        
        Args:
            location (str): Server location
            
        Returns:
            Optional[Server]: Best server or None if no servers available
        """
        # Get servers in the specified location
        servers = Server.get_by_location(location)
        
        # Filter active servers
        active_servers = [server for server in servers if server.is_active]
        
        if not active_servers:
            return None
            
        # Filter out overloaded servers
        available_servers = [server for server in active_servers if not server.is_overloaded()]
        
        # If no available servers, return the least loaded one
        if not available_servers:
            return min(active_servers, key=lambda s: s.get_load())
            
        # Sort by load (lowest first)
        sorted_servers = sorted(available_servers, key=lambda s: s.get_load())
        
        return sorted_servers[0] if sorted_servers else None

    @staticmethod
    def count_servers() -> int:
        """
        Count all servers.
        
        Returns:
            int: Number of servers
        """
        query = "SELECT COUNT(*) as count FROM servers"
        result = execute_query(query, fetch="one")
        
        return result.get('count', 0) if result else 0

    @staticmethod
    def count_active_servers() -> int:
        """
        Count active servers.
        
        Returns:
            int: Number of active servers
        """
        query = "SELECT COUNT(*) as count FROM servers WHERE is_active = TRUE"
        result = execute_query(query, fetch="one")
        
        return result.get('count', 0) if result else 0

    @staticmethod
    def get_server_stats() -> Dict[str, Any]:
        """
        Get server statistics.
        
        Returns:
            Dict[str, Any]: Server statistics
        """
        stats = {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "locations": 0,
            "overloaded": 0
        }
        
        # Get counts
        stats["total"] = Server.count_servers()
        stats["active"] = Server.count_active_servers()
        stats["inactive"] = stats["total"] - stats["active"]
        
        # Get locations count
        query = "SELECT COUNT(DISTINCT location) as count FROM servers"
        result = execute_query(query, fetch="one")
        stats["locations"] = result.get('count', 0) if result else 0
        
        # Get overloaded servers
        all_servers = Server.get_all()
        overloaded = [server for server in all_servers if server.is_overloaded()]
        stats["overloaded"] = len(overloaded)
        
        return stats

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert server to dictionary.
        
        Returns:
            Dict[str, Any]: Server data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'location': self.location,
            'protocol': self.protocol,
            'username': self.username,
            'capacity': self.capacity,
            'current_load': self.current_load,
            'is_active': self.is_active,
            'inbound_id': self.inbound_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'load_percent': self.get_load(),
            'is_overloaded': self.is_overloaded(),
            'is_available': self.is_available()
        } 