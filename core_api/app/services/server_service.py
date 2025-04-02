import os
import logging
import time
import subprocess
import platform
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import paramiko
from io import StringIO

from sqlalchemy.orm import Session
from app.models.server import Server as ServerModel
from app.db.session import SessionLocal
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServerException(Exception):
    """Base exception for server service errors."""
    pass

class ServerConnectionError(ServerException):
    """Error when connecting to the server."""
    pass

class ServerAuthenticationError(ServerException):
    """Error when authenticating with the server."""
    pass

class ServerCommandError(ServerException):
    """Error when executing a command on the server."""
    pass

class ServerService:
    """
    High-level service for interacting with VPN servers.
    Provides methods for server status checks, SSH connections, and system operations.
    """
    
    def __init__(self, server_id: Optional[int] = None):
        """
        Initialize the server service.
        
        Args:
            server_id: Database ID of the server to use
        """
        self.server_id = server_id
        self._server_info = None
        self._ssh_client = None
        
    def __enter__(self):
        """Support context manager pattern."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        self.close()
        
    def close(self):
        """Close any open connections."""
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
    
    def _get_server_info(self) -> Dict[str, Any]:
        """
        Get server connection information from the database.
        
        Returns:
            Dictionary with server connection details
            
        Raises:
            ServerException: If server info could not be retrieved
        """
        # If we already have server info cached, return it
        if self._server_info:
            return self._server_info
            
        try:
            # Create a new DB session
            db = SessionLocal()
            
            try:
                # Query the server by ID
                if not self.server_id:
                    raise ServerException("No server ID provided")
                    
                server = db.query(ServerModel).filter(ServerModel.id == self.server_id).first()
                    
                if not server:
                    raise ServerException(f"Server with ID {self.server_id} not found")
                    
                # Extract connection details
                server_info = {
                    "id": server.id,
                    "name": server.name,
                    "ip_address": server.ip_address,
                    "hostname": server.hostname,
                    "is_active": server.is_active,
                    "location_id": server.location_id
                }
                
                # Cache the server info
                self._server_info = server_info
                return server_info
                
            finally:
                # Always close the DB session
                db.close()
                
        except Exception as e:
            logger.exception(f"Error retrieving server info: {e}")
            raise ServerException(f"Failed to get server information: {str(e)}")
    
    def check_status(self) -> Dict[str, Any]:
        """
        Check the status of the server by pinging it.
        
        Returns:
            Dictionary with status information
            
        Raises:
            ServerException: If status check fails
        """
        try:
            server_info = self._get_server_info()
            ip_address = server_info["ip_address"]
            
            # Determine ping command based on OS
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            
            # Execute ping command with timeout
            command = ['ping', param, '1', '-w', '1', ip_address]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
            is_up = result.returncode == 0
            
            latency_ms = None
            if is_up:
                # Try to extract latency from ping output
                output = result.stdout.decode('utf-8', errors='ignore')
                if 'time=' in output:
                    try:
                        # Extract time value (works on most systems)
                        time_parts = [part for part in output.split() if 'time=' in part]
                        if time_parts:
                            latency_ms = float(time_parts[0].split('=')[1].replace('ms', ''))
                    except (ValueError, IndexError):
                        # If parsing fails, just leave as None
                        pass
            
            status_info = {
                "server_id": server_info["id"],
                "server_name": server_info["name"],
                "ip_address": ip_address,
                "is_up": is_up,
                "latency_ms": latency_ms,
                "checked_at": datetime.now().isoformat()
            }
            
            return status_info
            
        except Exception as e:
            logger.exception(f"Error checking server status: {e}")
            raise ServerException(f"Failed to check server status: {str(e)}")
    
    def _get_ssh_client(self) -> paramiko.SSHClient:
        """
        Get or create an SSH client connection to the server.
        
        Returns:
            SSHClient instance
            
        Raises:
            ServerConnectionError: If connection fails
            ServerAuthenticationError: If authentication fails
        """
        if self._ssh_client:
            return self._ssh_client
            
        try:
            server_info = self._get_server_info()
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Get credentials
            # In a real implementation, these should be securely stored and retrieved
            username = settings.SSH_USERNAME
            if not username:
                raise ServerAuthenticationError("SSH username not configured")
                
            # Check for different authentication methods
            if settings.SSH_PASSWORD:
                # Password authentication
                try:
                    client.connect(
                        hostname=server_info["ip_address"],
                        username=username,
                        password=settings.SSH_PASSWORD,
                        timeout=10
                    )
                except paramiko.AuthenticationException:
                    raise ServerAuthenticationError("SSH authentication failed with password")
                except paramiko.SSHException as e:
                    raise ServerConnectionError(f"SSH connection error: {str(e)}")
                except Exception as e:
                    raise ServerConnectionError(f"Connection error: {str(e)}")
            
            elif settings.SSH_KEY_PATH:
                # Key-based authentication
                try:
                    key_path = os.path.expanduser(settings.SSH_KEY_PATH)
                    if not os.path.exists(key_path):
                        raise ServerAuthenticationError(f"SSH key file not found at {key_path}")
                        
                    if settings.SSH_KEY_PASSPHRASE:
                        key = paramiko.RSAKey.from_private_key_file(
                            key_path, 
                            password=settings.SSH_KEY_PASSPHRASE
                        )
                    else:
                        key = paramiko.RSAKey.from_private_key_file(key_path)
                        
                    client.connect(
                        hostname=server_info["ip_address"],
                        username=username,
                        pkey=key,
                        timeout=10
                    )
                except paramiko.AuthenticationException:
                    raise ServerAuthenticationError("SSH authentication failed with key")
                except paramiko.SSHException as e:
                    raise ServerConnectionError(f"SSH connection error: {str(e)}")
                except Exception as e:
                    raise ServerConnectionError(f"Connection error: {str(e)}")
            
            else:
                raise ServerAuthenticationError("No SSH authentication method configured")
            
            # Cache the client
            self._ssh_client = client
            return client
            
        except ServerException:
            # Re-raise existing server exceptions
            raise
        except Exception as e:
            logger.exception(f"Error creating SSH client: {e}")
            raise ServerConnectionError(f"Failed to connect to server: {str(e)}")
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a command on the server via SSH.
        
        Args:
            command: The command to execute
            
        Returns:
            Dictionary with command output and status
            
        Raises:
            ServerConnectionError: If connection fails
            ServerAuthenticationError: If authentication fails
            ServerCommandError: If command execution fails
        """
        try:
            client = self._get_ssh_client()
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command, timeout=30)
            
            # Get exit status
            exit_status = stdout.channel.recv_exit_status()
            
            # Read output
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            
            result = {
                "command": command,
                "exit_status": exit_status,
                "success": exit_status == 0,
                "stdout": stdout_data,
                "stderr": stderr_data,
                "executed_at": datetime.now().isoformat()
            }
            
            return result
            
        except ServerException:
            # Re-raise existing server exceptions
            raise
        except Exception as e:
            logger.exception(f"Error executing command: {e}")
            raise ServerCommandError(f"Failed to execute command: {str(e)}")
    
    def restart_xray(self) -> Dict[str, Any]:
        """
        Restart the Xray service on the server.
        
        Returns:
            Dictionary with command output and status
            
        Raises:
            ServerConnectionError: If connection fails
            ServerAuthenticationError: If authentication fails
            ServerCommandError: If command execution fails
        """
        # Command to restart xray service
        return self.execute_command("systemctl restart xray")
    
    def reboot_server(self) -> Dict[str, Any]:
        """
        Reboot the server.
        
        Returns:
            Dictionary with command output and status
            
        Raises:
            ServerConnectionError: If connection fails
            ServerAuthenticationError: If authentication fails
            ServerCommandError: If command execution fails
        """
        # Command to reboot the server
        return self.execute_command("sudo reboot")
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information from the server.
        
        Returns:
            Dictionary with system information
            
        Raises:
            ServerConnectionError: If connection fails
            ServerAuthenticationError: If authentication fails
            ServerCommandError: If command execution fails
        """
        try:
            # Get CPU info
            cpu_info = self.execute_command("cat /proc/cpuinfo | grep 'model name' | head -1")
            cpu_model = cpu_info["stdout"].split(":")[1].strip() if cpu_info["success"] and ":" in cpu_info["stdout"] else "Unknown"
            
            # Get memory info
            mem_info = self.execute_command("free -m")
            
            # Get disk usage
            disk_info = self.execute_command("df -h /")
            
            # Get uptime
            uptime_info = self.execute_command("uptime")
            
            # Get load average
            load_avg = self.execute_command("cat /proc/loadavg")
            
            # Get OS info
            os_info = self.execute_command("cat /etc/os-release | grep PRETTY_NAME")
            os_name = os_info["stdout"].split("=")[1].strip().strip('"') if os_info["success"] and "=" in os_info["stdout"] else "Unknown"
            
            # Check if xray is running
            xray_status = self.execute_command("systemctl is-active xray")
            xray_running = xray_status["stdout"].strip() == "active"
            
            # Compose system info
            system_info = {
                "server_id": self.server_id,
                "cpu_model": cpu_model,
                "memory_info": mem_info["stdout"] if mem_info["success"] else "Failed to retrieve",
                "disk_usage": disk_info["stdout"] if disk_info["success"] else "Failed to retrieve",
                "uptime": uptime_info["stdout"].strip() if uptime_info["success"] else "Failed to retrieve",
                "load_average": load_avg["stdout"].strip() if load_avg["success"] else "Failed to retrieve",
                "os_info": os_name,
                "xray_running": xray_running,
                "collected_at": datetime.now().isoformat()
            }
            
            return system_info
            
        except Exception as e:
            logger.exception(f"Error getting system info: {e}")
            raise ServerException(f"Failed to get system information: {str(e)}")
    
    def get_server_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics from the server.
        
        Returns:
            Dictionary with server metrics
            
        Raises:
            ServerConnectionError: If connection fails
            ServerAuthenticationError: If authentication fails
            ServerCommandError: If command execution fails
        """
        try:
            # Get CPU usage
            cpu_usage = self.execute_command("top -bn1 | grep '%Cpu' | awk '{print $2}'")
            cpu_usage_value = float(cpu_usage["stdout"].strip()) if cpu_usage["success"] and cpu_usage["stdout"].strip() else None
            
            # Get memory usage
            mem_usage = self.execute_command("free | grep Mem | awk '{print $3/$2 * 100.0}'")
            mem_usage_value = float(mem_usage["stdout"].strip()) if mem_usage["success"] and mem_usage["stdout"].strip() else None
            
            # Get network usage
            net_info = self.execute_command("cat /proc/net/dev | grep -v 'lo:' | grep -v 'face' | head -1")
            # This is simplified and may need adjustment based on actual output format
            
            # Get number of active connections
            conn_count = self.execute_command("netstat -an | grep ESTABLISHED | wc -l")
            conn_count_value = int(conn_count["stdout"].strip()) if conn_count["success"] and conn_count["stdout"].strip() else None
            
            # Compose metrics
            metrics = {
                "server_id": self.server_id,
                "cpu_usage_percent": cpu_usage_value,
                "memory_usage_percent": mem_usage_value,
                "active_connections": conn_count_value,
                "collected_at": datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.exception(f"Error getting server metrics: {e}")
            raise ServerException(f"Failed to get server metrics: {str(e)}") 