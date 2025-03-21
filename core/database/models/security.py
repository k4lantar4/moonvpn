"""
Security-related database models.
"""

from django.db import models
from django.utils import timezone
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from ..base import Base

# Role-Permission association table
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)

class SecurityEvent(models.Model):
    """Security event log"""
    EVENT_TYPES = [
        ('blocked_ip', 'Blocked IP'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('login_attempt', 'Login Attempt'),
        ('geolocation_anomaly', 'Geolocation Anomaly'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    user_id = models.BigIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    data = models.JSONField()
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['user_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ]

class BlockedIP(models.Model):
    """Blocked IP addresses"""
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=255)
    blocked_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    blocked_by = models.CharField(max_length=50, default='system')

    class Meta:
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['expires_at']),
        ]

class UserLocation(models.Model):
    """User location history"""
    user_id = models.BigIntegerField()
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=2)
    city = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    suspicious = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ]

class RateLimitLog(models.Model):
    """Rate limit tracking"""
    key = models.CharField(max_length=255)  # IP or user_id based key
    action = models.CharField(max_length=50)  # login, payment, api, etc.
    count = models.IntegerField(default=0)
    window_start = models.DateTimeField()
    last_request = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['action']),
            models.Index(fields=['window_start']),
        ]
        unique_together = ['key', 'action', 'window_start']

class LoginAttempt(models.Model):
    """Login attempt tracking"""
    user_id = models.BigIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(default=timezone.now)
    user_agent = models.TextField(null=True, blank=True)
    location_data = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ]

class User(Base):
    """User model for authentication."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32))
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    role_id = Column(Integer, ForeignKey('roles.id'))
    role = relationship('Role', back_populates='users')
    sessions = relationship('UserSession', back_populates='user')

class Role(Base):
    """Role model for role-based access control."""
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship('User', back_populates='role')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')

class Permission(Base):
    """Permission model for fine-grained access control."""
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')

class UserSession(Base):
    """User session model for managing active sessions."""
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(500), unique=True, nullable=False)
    refresh_token = Column(String(500), unique=True, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='sessions')

class SecurityEvent(Base):
    """Security event model for logging security-related events."""
    __tablename__ = 'security_events'

    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(String(500))
    ip_address = Column(String(45))
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(String(1000))  # JSON string for additional event data 