"""Integration tests for VPN API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.vpn import ServerCreate, VPNAccountCreate
from app.core.security import create_access_token

client = TestClient(app)

class TestVPNServerEndpoints:
    """Test VPN server API endpoints."""
    
    def test_create_server(self, db, authorized_client):
        """Test creating a new VPN server via API."""
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == server_data["name"]
        assert data["host"] == server_data["host"]
        assert data["port"] == server_data["port"]
        assert data["protocol"] == server_data["protocol"]
        assert data["country"] == server_data["country"]
        assert data["city"] == server_data["city"]
        assert data["is_active"] == server_data["is_active"]
        assert data["max_connections"] == server_data["max_connections"]
        assert data["current_connections"] == server_data["current_connections"]
        assert data["bandwidth_limit"] == server_data["bandwidth_limit"]
        assert data["description"] == server_data["description"]
        assert "id" in data
    
    def test_get_servers(self, db, authorized_client):
        """Test getting list of VPN servers via API."""
        # Create multiple servers first
        server_data1 = {
            "name": "Server 1",
            "host": "server1.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "First test server"
        }
        
        server_data2 = {
            "name": "Server 2",
            "host": "server2.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "UK",
            "city": "London",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Second test server"
        }
        
        authorized_client.post("/api/v1/vpn/servers/", json=server_data1)
        authorized_client.post("/api/v1/vpn/servers/", json=server_data2)
        
        response = authorized_client.get("/api/v1/vpn/servers/")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        assert any(s["name"] == "Server 1" for s in data)
        assert any(s["name"] == "Server 2" for s in data)
    
    def test_get_server(self, db, authorized_client):
        """Test getting a specific VPN server via API."""
        # Create a server first
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        server_id = response.json()["id"]
        
        response = authorized_client.get(f"/api/v1/vpn/servers/{server_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == server_data["name"]
        assert data["host"] == server_data["host"]
        assert data["port"] == server_data["port"]
        assert data["protocol"] == server_data["protocol"]
        assert data["country"] == server_data["country"]
        assert data["city"] == server_data["city"]
        assert data["is_active"] == server_data["is_active"]
        assert data["max_connections"] == server_data["max_connections"]
        assert data["current_connections"] == server_data["current_connections"]
        assert data["bandwidth_limit"] == server_data["bandwidth_limit"]
        assert data["description"] == server_data["description"]
        assert data["id"] == server_id
    
    def test_update_server(self, db, authorized_client):
        """Test updating a VPN server via API."""
        # Create a server first
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        server_id = response.json()["id"]
        
        # Update the server
        update_data = {
            "name": "Updated Server",
            "description": "Updated description"
        }
        
        response = authorized_client.put(f"/api/v1/vpn/servers/{server_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["host"] == server_data["host"]  # Unchanged
        assert data["port"] == server_data["port"]  # Unchanged
    
    def test_delete_server(self, db, authorized_client):
        """Test deleting a VPN server via API."""
        # Create a server first
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        server_id = response.json()["id"]
        
        # Delete the server
        response = authorized_client.delete(f"/api/v1/vpn/servers/{server_id}")
        assert response.status_code == 204
        
        # Verify server is deleted
        response = authorized_client.get(f"/api/v1/vpn/servers/{server_id}")
        assert response.status_code == 404

class TestVPNAccountEndpoints:
    """Test VPN account API endpoints."""
    
    def test_create_account(self, db, authorized_client):
        """Test creating a new VPN account via API."""
        # Create a server first
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        server_id = response.json()["id"]
        
        # Create account
        account_data = {
            "username": "testuser",
            "password": "testpass123",
            "server_id": server_id,
            "is_active": True,
            "bandwidth_limit": 1000,
            "expiry_date": None
        }
        
        response = authorized_client.post("/api/v1/vpn/accounts/", json=account_data)
        assert response.status_code == 201
        data = response.json()
        
        assert data["username"] == account_data["username"]
        assert data["server_id"] == account_data["server_id"]
        assert data["is_active"] == account_data["is_active"]
        assert data["bandwidth_limit"] == account_data["bandwidth_limit"]
        assert data["expiry_date"] == account_data["expiry_date"]
        assert "id" in data
    
    def test_get_accounts(self, db, authorized_client):
        """Test getting list of VPN accounts via API."""
        # Create a server first
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        server_id = response.json()["id"]
        
        # Create multiple accounts
        account_data1 = {
            "username": "user1",
            "password": "pass123",
            "server_id": server_id,
            "is_active": True,
            "bandwidth_limit": 1000,
            "expiry_date": None
        }
        
        account_data2 = {
            "username": "user2",
            "password": "pass456",
            "server_id": server_id,
            "is_active": True,
            "bandwidth_limit": 1000,
            "expiry_date": None
        }
        
        authorized_client.post("/api/v1/vpn/accounts/", json=account_data1)
        authorized_client.post("/api/v1/vpn/accounts/", json=account_data2)
        
        response = authorized_client.get("/api/v1/vpn/accounts/")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        assert any(a["username"] == "user1" for a in data)
        assert any(a["username"] == "user2" for a in data)
    
    def test_get_account(self, db, authorized_client):
        """Test getting a specific VPN account via API."""
        # Create a server first
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        server_id = response.json()["id"]
        
        # Create account
        account_data = {
            "username": "testuser",
            "password": "testpass123",
            "server_id": server_id,
            "is_active": True,
            "bandwidth_limit": 1000,
            "expiry_date": None
        }
        
        response = authorized_client.post("/api/v1/vpn/accounts/", json=account_data)
        account_id = response.json()["id"]
        
        response = authorized_client.get(f"/api/v1/vpn/accounts/{account_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == account_data["username"]
        assert data["server_id"] == account_data["server_id"]
        assert data["is_active"] == account_data["is_active"]
        assert data["bandwidth_limit"] == account_data["bandwidth_limit"]
        assert data["expiry_date"] == account_data["expiry_date"]
        assert data["id"] == account_id
    
    def test_update_account(self, db, authorized_client):
        """Test updating a VPN account via API."""
        # Create a server first
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        server_id = response.json()["id"]
        
        # Create account
        account_data = {
            "username": "testuser",
            "password": "testpass123",
            "server_id": server_id,
            "is_active": True,
            "bandwidth_limit": 1000,
            "expiry_date": None
        }
        
        response = authorized_client.post("/api/v1/vpn/accounts/", json=account_data)
        account_id = response.json()["id"]
        
        # Update the account
        update_data = {
            "is_active": False,
            "bandwidth_limit": 2000
        }
        
        response = authorized_client.put(f"/api/v1/vpn/accounts/{account_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_active"] == update_data["is_active"]
        assert data["bandwidth_limit"] == update_data["bandwidth_limit"]
        assert data["username"] == account_data["username"]  # Unchanged
        assert data["server_id"] == account_data["server_id"]  # Unchanged
    
    def test_delete_account(self, db, authorized_client):
        """Test deleting a VPN account via API."""
        # Create a server first
        server_data = {
            "name": "Test Server",
            "host": "test.example.com",
            "port": 1194,
            "protocol": "udp",
            "country": "US",
            "city": "New York",
            "is_active": True,
            "max_connections": 100,
            "current_connections": 0,
            "bandwidth_limit": 1000,
            "description": "Test server description"
        }
        
        response = authorized_client.post("/api/v1/vpn/servers/", json=server_data)
        server_id = response.json()["id"]
        
        # Create account
        account_data = {
            "username": "testuser",
            "password": "testpass123",
            "server_id": server_id,
            "is_active": True,
            "bandwidth_limit": 1000,
            "expiry_date": None
        }
        
        response = authorized_client.post("/api/v1/vpn/accounts/", json=account_data)
        account_id = response.json()["id"]
        
        # Delete the account
        response = authorized_client.delete(f"/api/v1/vpn/accounts/{account_id}")
        assert response.status_code == 204
        
        # Verify account is deleted
        response = authorized_client.get(f"/api/v1/vpn/accounts/{account_id}")
        assert response.status_code == 404 