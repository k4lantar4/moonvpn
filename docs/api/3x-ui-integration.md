# 3x-UI Panel Integration

## Overview

MoonVPN integrates with external 3x-UI panels to manage VPN accounts across multiple servers. The integration is designed to be robust, secure, and database-driven, allowing for dynamic server management and user migration between servers.

## Session Cookie Authentication

### Background

The 3x-UI panel uses session-based authentication with cookies. Once authenticated, the cookie must be included in subsequent requests. The integration handles this by:

1. Storing session cookies in the database (Server model)
2. Automatically re-authenticating when sessions expire
3. Refreshing cookies periodically to maintain persistent connections

### Implementation

The `PanelClient` class in `bot/api_client.py` manages the authentication and maintains session continuity:

```python
class PanelClient:
    def __init__(self, server_id=None, server_instance=None):
        """Initialize client with either server ID or instance"""
        if server_instance:
            self.server = server_instance
        else:
            self.server = Server.objects.get(id=server_id)
            
        self.host = self.server.host
        self.port = self.server.port
        self.username = self.server.username
        self.password = self.server.password
        self.base_path = self.server.base_path
        self.session = requests.Session()
        
        # Load session cookie if available
        if self.server.session_cookie:
            self.session.cookies.update(json.loads(self.server.session_cookie))
            
    async def ensure_authenticated(self):
        """Ensure the session is authenticated, login if needed"""
        # Try a simple authenticated request
        try:
            test_response = await self.make_request("GET", "/panel/api/stats")
            if test_response.status_code == 200:
                return True
        except Exception:
            pass
            
        # If not authenticated, login
        login_payload = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            login_response = await self.make_request(
                "POST", 
                "/panel/api/login", 
                json=login_payload,
                skip_auth_check=True
            )
            
            if login_response.status_code == 200:
                # Save session cookies to database
                cookie_json = json.dumps(dict(self.session.cookies))
                self.server.session_cookie = cookie_json
                self.server.last_sync = timezone.now()
                self.server.save()
                return True
            else:
                raise Exception(f"Login failed: {login_response.text}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise
            
    async def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request to panel API with authentication handling"""
        skip_auth_check = kwargs.pop('skip_auth_check', False)
        
        if not skip_auth_check:
            await self.ensure_authenticated()
            
        url = f"https://{self.host}:{self.port}{self.base_path}{endpoint}"
        
        try:
            response = await asyncio.to_thread(
                lambda: self.session.request(method, url, **kwargs)
            )
            return response
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise
```

## Database-Driven Server Configuration

All server information is stored in the database, allowing for dynamic management:

1. Server credentials (host, port, username, password)
2. Session cookies for authentication
3. Server capacity and load metrics
4. Location and availability information

This approach enables:
- Adding/removing servers without code changes
- Dynamic load balancing across servers
- Migrating users between servers when needed
- Handling server outages gracefully

## Account Management API

### Creating Accounts

```python
async def create_client(self, email, uuid=None, subscription_days=30, traffic_limit=100):
    """Create a new client on the panel"""
    if not uuid:
        uuid = str(uuid4())
        
    payload = {
        "email": email,
        "uuid": uuid,
        "subscription_days": subscription_days,
        "traffic_limit_gb": traffic_limit
    }
    
    response = await self.make_request(
        "POST", 
        "/panel/api/clients", 
        json=payload
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create client: {response.text}")
```

### Retrieving Accounts

```python
async def get_client(self, email):
    """Get client details by email"""
    response = await self.make_request(
        "GET", 
        f"/panel/api/clients?email={email}"
    )
    
    if response.status_code == 200:
        clients = response.json()
        for client in clients:
            if client.get("email") == email:
                return client
        raise Exception(f"Client not found: {email}")
    else:
        raise Exception(f"Failed to get client: {response.text}")
```

### Updating Traffic Limits

```python
async def update_client_traffic(self, email, new_traffic_limit):
    """Update client traffic limit"""
    client = await self.get_client(email)
    client_id = client.get("id")
    
    payload = {
        "traffic_limit_gb": new_traffic_limit
    }
    
    response = await self.make_request(
        "PATCH", 
        f"/panel/api/clients/{client_id}", 
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to update client traffic: {response.text}")
```

### Migrating Users Between Servers

When migrating a user from one server to another:

1. Retrieve current account details from source server
2. Create identical account on destination server
3. Update database to reflect new server
4. Delete account from source server
5. Send updated configuration to user

```python
async def migrate_user(user_id, from_server_id, to_server_id):
    """Migrate user from one server to another"""
    # Get VPN account
    account = VPNAccount.objects.get(
        user_id=user_id,
        server_id=from_server_id
    )
    
    # Source panel client
    source_client = PanelClient(server_id=from_server_id)
    
    # Get client details from source server
    source_account = await source_client.get_client(account.email)
    
    # Create identical account on destination server
    dest_client = PanelClient(server_id=to_server_id)
    new_account = await dest_client.create_client(
        email=account.email,
        uuid=str(account.uuid),
        subscription_days=(account.expires_at - timezone.now()).days,
        traffic_limit=account.total_traffic_gb
    )
    
    # Update database
    old_server = account.server
    new_server = Server.objects.get(id=to_server_id)
    
    # Create migration record
    migration = ServerMigration.objects.create(
        vpn_account=account,
        from_server=old_server,
        to_server=new_server,
        initiated_by='admin'
    )
    
    # Update account
    account.server = new_server
    account.save()
    
    # Update server statistics
    old_server.current_clients -= 1
    old_server.update_load_factor()
    
    new_server.current_clients += 1
    new_server.update_load_factor()
    
    # Delete from source server
    await source_client.delete_client(account.email)
    
    # Mark migration as complete
    migration.completed_at = timezone.now()
    migration.success = True
    migration.save()
    
    return account
```

## Traffic Monitoring

The integration includes regular traffic monitoring:

```python
async def get_client_traffic(self, email):
    """Get client traffic usage"""
    client = await self.get_client(email)
    client_id = client.get("id")
    
    response = await self.make_request(
        "GET", 
        f"/panel/api/clients/{client_id}/stats"
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get client traffic: {response.text}")
```

This data is then synchronized with the database for reporting and management:

```python
async def sync_account_traffic():
    """Sync traffic data for all accounts"""
    active_accounts = VPNAccount.objects.filter(status='active')
    
    for account in active_accounts:
        client = PanelClient(server_id=account.server.id)
        
        try:
            traffic_data = await client.get_client_traffic(account.email)
            
            # Update account traffic
            account.used_traffic_gb = traffic_data.get("used_traffic_gb", 0)
            account.last_sync = timezone.now()
            
            # Check if traffic exceeded
            if account.used_traffic_gb >= account.total_traffic_gb:
                account.status = 'traffic_exceeded'
                
            account.save()
            
        except Exception as e:
            logger.error(f"Error syncing traffic for {account.email}: {str(e)}")
```

## Error Handling

The integration implements robust error handling:

1. Automatic retries for transient errors
2. Authentication failure recovery
3. Connection timeout handling
4. Rate limiting detection and backoff

```python
async def make_request_with_retry(self, method, endpoint, max_retries=3, **kwargs):
    """Make request with automatic retry for certain errors"""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = await self.make_request(method, endpoint, **kwargs)
            
            # Check if rate limited
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                await asyncio.sleep(retry_after)
                retry_count += 1
                continue
                
            return response
            
        except requests.exceptions.ConnectionError:
            # Connection errors may be transient
            retry_count += 1
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            
        except Exception as e:
            # Don't retry for other errors
            logger.error(f"Request failed: {str(e)}")
            raise
            
    raise Exception(f"Max retries exceeded for {endpoint}")
```

## Security Considerations

1. Server credentials are stored encrypted in the database
2. HTTPS is used for all API communications
3. Session cookies are stored securely
4. Authentication is refreshed periodically
5. Failed login attempts are logged and monitored

## Handling Server Outages

When a server becomes unavailable:

1. The system detects failed API calls
2. The server is marked as inactive
3. Users are notified about the outage
4. Critical accounts are migrated to healthy servers
5. The server is periodically checked for recovery

```python
async def check_server_health():
    """Check health for all servers"""
    servers = Server.objects.filter(is_active=True)
    
    for server in servers:
        client = PanelClient(server_instance=server)
        
        try:
            await client.ensure_authenticated()
            response = await client.make_request("GET", "/panel/api/stats")
            
            if response.status_code == 200:
                # Server is healthy
                if not server.is_active:
                    server.is_active = True
                    server.save()
                    notify_admins(f"Server {server.name} is back online")
            else:
                # Server is having issues
                server.is_active = False
                server.save()
                notify_admins(f"Server {server.name} is experiencing issues: {response.status_code}")
                
        except Exception as e:
            # Server is down
            server.is_active = False
            server.save()
            notify_admins(f"Server {server.name} is down: {str(e)}")
``` 