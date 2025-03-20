# MoonVPN Database Schema

## Overview

The MoonVPN database schema is designed to support a flexible, database-driven approach to VPN server management. The schema enables dynamic server allocation, user migration between servers, wallet-based payments, and comprehensive reporting.

## Core Models

### User Model

```python
class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    language_code = models.CharField(max_length=10, default='fa')
    referral_code = models.CharField(max_length=20, unique=True)
    referrer = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
```

### Wallet Model

```python
class Wallet(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_transaction = models.DateTimeField(null=True, blank=True)
    
    def deposit(self, amount, description):
        self.balance += amount
        self.total_deposit += amount
        self.last_transaction = timezone.now()
        self.save()
        
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            type='deposit',
            description=description
        )
        return True
        
    def withdraw(self, amount, description):
        if self.balance >= amount:
            self.balance -= amount
            self.total_spent += amount
            self.last_transaction = timezone.now()
            self.save()
            
            Transaction.objects.create(
                wallet=self,
                amount=-amount,
                type='withdraw',
                description=description
            )
            return True
        return False
```

### Transaction Model

```python
class Transaction(models.Model):
    TYPES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus'),
        ('commission', 'Commission'),
    ]
    
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPES)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reference_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, default='completed')
    admin_note = models.TextField(null=True, blank=True)
```

### Server Model

```python
class Server(models.Model):
    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255)  # Server hostname or IP
    port = models.IntegerField(default=2053)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    base_path = models.CharField(max_length=255, default='/')
    location = models.ForeignKey('Location', on_delete=models.CASCADE, related_name='servers')
    is_active = models.BooleanField(default=True)
    max_clients = models.IntegerField(default=500)
    current_clients = models.IntegerField(default=0)
    load_factor = models.FloatField(default=0.0)  # Current server load (0-1)
    last_sync = models.DateTimeField(null=True, blank=True)
    session_cookie = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    def get_available_capacity(self):
        return self.max_clients - self.current_clients
    
    def is_overloaded(self):
        return self.load_factor > 0.8
    
    def update_load_factor(self):
        self.load_factor = self.current_clients / self.max_clients if self.max_clients > 0 else 1.0
        self.save()
```

### Location Model

```python
class Location(models.Model):
    name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=5)
    flag_emoji = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    price_multiplier = models.FloatField(default=1.0)  # For premium locations
    description = models.TextField(null=True, blank=True)
    
    def get_best_server(self):
        """Return the server with the lowest load in this location"""
        return self.servers.filter(is_active=True).order_by('load_factor', 'current_clients').first()
```

### Subscription Plan Model

```python
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=255)
    duration_days = models.IntegerField()
    traffic_limit_gb = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    max_connections = models.IntegerField(default=1)
    description = models.TextField(null=True, blank=True)
    
    def get_monthly_price(self):
        """Calculate the monthly equivalent price for comparison"""
        if self.duration_days >= 28:
            return (self.price / self.duration_days) * 30
        return self.price
```

### VPN Account Model

```python
class VPNAccount(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('traffic_exceeded', 'Traffic Exceeded'),
        ('disabled', 'Disabled'),
        ('pending', 'Pending Creation'),
    ]
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='vpn_accounts')
    server = models.ForeignKey('Server', on_delete=models.CASCADE, related_name='accounts')
    email = models.EmailField(unique=True)  # Used as identifier in 3x-UI panel
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_sync = models.DateTimeField(null=True, blank=True)
    total_traffic_gb = models.IntegerField()
    used_traffic_gb = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remark = models.CharField(max_length=255, null=True, blank=True)  # Custom name in panel
    connection_string = models.TextField(null=True, blank=True)  # Cached connection config
    max_connections = models.IntegerField(default=1)
    
    def get_remaining_traffic(self):
        return max(0, self.total_traffic_gb - self.used_traffic_gb)
    
    def get_remaining_days(self):
        if self.expires_at > timezone.now():
            return (self.expires_at - timezone.now()).days
        return 0
    
    def is_expired(self):
        return self.expires_at < timezone.now()
    
    def has_traffic(self):
        return self.used_traffic_gb < self.total_traffic_gb
    
    def migrate_to_server(self, new_server):
        """Migrate account to a different server"""
        old_server = self.server
        self.server = new_server
        self.status = 'pending'  # Will be recreated on new server
        self.save()
        
        ServerMigration.objects.create(
            vpn_account=self,
            from_server=old_server,
            to_server=new_server,
            initiated_by='system'
        )
        return True
```

### Server Migration Model

```python
class ServerMigration(models.Model):
    INITIATED_BY_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('system', 'System'),
    ]
    
    vpn_account = models.ForeignKey('VPNAccount', on_delete=models.CASCADE, related_name='migrations')
    from_server = models.ForeignKey('Server', on_delete=models.SET_NULL, null=True, related_name='outgoing_migrations')
    to_server = models.ForeignKey('Server', on_delete=models.CASCADE, related_name='incoming_migrations')
    initiated_by = models.CharField(max_length=10, choices=INITIATED_BY_CHOICES)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(null=True)
    details = models.TextField(null=True, blank=True)
```

### Order Model

```python
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHODS = [
        ('wallet', 'Wallet'),
        ('card', 'Card to Card'),
        ('zarinpal', 'ZarinPal'),
    ]
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='orders')
    subscription_plan = models.ForeignKey('SubscriptionPlan', on_delete=models.CASCADE)
    location = models.ForeignKey('Location', on_delete=models.CASCADE)
    server = models.ForeignKey('Server', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    voucher = models.ForeignKey('Voucher', on_delete=models.SET_NULL, null=True, blank=True)
    transaction = models.ForeignKey('Transaction', on_delete=models.SET_NULL, null=True, blank=True)
    admin_note = models.TextField(null=True, blank=True)
    
    def apply_voucher(self, voucher_code):
        try:
            voucher = Voucher.objects.get(code=voucher_code, is_active=True)
            if voucher.is_valid():
                self.voucher = voucher
                self.discount_amount = (self.total_price * voucher.discount_percent / 100)
                if self.discount_amount > voucher.max_discount:
                    self.discount_amount = voucher.max_discount
                self.final_price = self.total_price - self.discount_amount
                self.save()
                return True
        except Voucher.DoesNotExist:
            pass
        return False
    
    def complete_order(self):
        if self.status != 'processing':
            return False
        
        # Choose best server if not specified
        if not self.server:
            self.server = self.location.get_best_server()
            self.save()
        
        if not self.server:
            self.status = 'failed'
            self.admin_note = "No available server in selected location"
            self.save()
            return False
        
        # Create VPN account
        try:
            email = f"{self.user.telegram_id}_{uuid.uuid4().hex[:8]}@moonvpn.ir"
            account = VPNAccount.objects.create(
                user=self.user,
                server=self.server,
                email=email,
                expires_at=timezone.now() + datetime.timedelta(days=self.subscription_plan.duration_days),
                total_traffic_gb=self.subscription_plan.traffic_limit_gb,
                max_connections=self.subscription_plan.max_connections,
                remark=f"MoonVPN-{self.user.telegram_id}"
            )
            
            self.status = 'completed'
            self.save()
            
            # Update server stats
            self.server.current_clients += 1
            self.server.update_load_factor()
            
            return account
        except Exception as e:
            self.status = 'failed'
            self.admin_note = f"Error creating account: {str(e)}"
            self.save()
            return False
```

### Voucher Model

```python
class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.IntegerField()
    max_discount = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.IntegerField()
    current_uses = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now and
            self.valid_until >= now and
            (self.max_uses == 0 or self.current_uses < self.max_uses)
        )
```

### Admin Group Model

```python
class AdminGroup(models.Model):
    GROUP_TYPES = [
        ('management', 'Management'),
        ('reports', 'Reports'),
        ('logs', 'Logs'),
        ('orders', 'Orders'),
        ('outages', 'Outages'),
        ('sellers', 'Sellers'),
        ('backups', 'Backups'),
    ]
    
    name = models.CharField(max_length=255)
    telegram_chat_id = models.BigIntegerField(unique=True)
    type = models.CharField(max_length=20, choices=GROUP_TYPES)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
```

## Database Relationships

```
User
 ├── Wallet (1:1)
 ├── VPNAccounts (1:N)
 ├── Orders (1:N)
 └── Referrals (1:N)

Server
 ├── Location (N:1)
 ├── VPNAccounts (1:N)
 ├── OutgoingMigrations (1:N)
 └── IncomingMigrations (1:N)

Order
 ├── User (N:1)
 ├── SubscriptionPlan (N:1)
 ├── Location (N:1)
 ├── Server (N:1)
 ├── Voucher (N:1)
 └── Transaction (N:1)

VPNAccount
 ├── User (N:1)
 ├── Server (N:1)
 └── Migrations (1:N)
```

## Database Triggers and Procedures

### Auto Load Balancing

The system includes a procedure to automatically balance the load across servers when capacity exceeds certain thresholds:

```python
def balance_server_load():
    """Check server load and migrate accounts if necessary"""
    overloaded_servers = Server.objects.filter(is_active=True, load_factor__gt=0.9)
    
    for server in overloaded_servers:
        # Find alternative server in same location
        alternative_server = Server.objects.filter(
            location=server.location,
            is_active=True,
            load_factor__lt=0.7
        ).order_by('load_factor').first()
        
        if alternative_server:
            # Find accounts to migrate (oldest accounts first)
            accounts_to_migrate = VPNAccount.objects.filter(
                server=server,
                status='active'
            ).order_by('created_at')[:10]  # Migrate 10 accounts at a time
            
            for account in accounts_to_migrate:
                account.migrate_to_server(alternative_server)
```

### Traffic Monitoring

Regular check of account traffic usage and status updates:

```python
def update_account_traffic():
    """Update traffic usage for all active accounts"""
    active_accounts = VPNAccount.objects.filter(status='active')
    
    for account in active_accounts:
        # Logic to check traffic with 3x-UI panel
        # Update account.used_traffic_gb
        
        if not account.has_traffic():
            account.status = 'traffic_exceeded'
            account.save()
```

### Expiration Checks

Regular check for expired accounts:

```python
def check_expirations():
    """Update status for expired accounts"""
    expired_accounts = VPNAccount.objects.filter(
        status='active',
        expires_at__lt=timezone.now()
    )
    
    for account in expired_accounts:
        account.status = 'expired'
        account.save()
```

## Database Views

### Active Accounts View

```sql
CREATE VIEW active_accounts_view AS
SELECT 
    u.telegram_id,
    u.username,
    u.first_name,
    u.last_name,
    v.email,
    v.uuid,
    v.expires_at,
    v.total_traffic_gb,
    v.used_traffic_gb,
    s.name AS server_name,
    l.name AS location_name,
    l.country_code
FROM 
    vpn_account v
JOIN 
    user u ON v.user_id = u.id
JOIN 
    server s ON v.server_id = s.id
JOIN 
    location l ON s.location_id = l.id
WHERE 
    v.status = 'active';
```

### Revenue Report View

```sql
CREATE VIEW revenue_report_view AS
SELECT 
    DATE(o.created_at) AS date,
    COUNT(o.id) AS total_orders,
    SUM(o.final_price) AS total_revenue,
    l.name AS location_name,
    p.name AS plan_name
FROM 
    order o
JOIN 
    location l ON o.location_id = l.id
JOIN 
    subscription_plan p ON o.subscription_plan_id = p.id
WHERE 
    o.status = 'completed'
GROUP BY 
    DATE(o.created_at), l.name, p.name;
```

### Server Load View

```sql
CREATE VIEW server_load_view AS
SELECT 
    s.name AS server_name,
    l.name AS location_name,
    s.current_clients,
    s.max_clients,
    s.load_factor,
    COUNT(v.id) AS active_accounts,
    AVG(v.used_traffic_gb) AS avg_traffic_usage
FROM 
    server s
JOIN 
    location l ON s.location_id = l.id
LEFT JOIN 
    vpn_account v ON s.id = v.server_id AND v.status = 'active'
GROUP BY 
    s.id, l.id;
``` 