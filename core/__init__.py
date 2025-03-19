"""
MoonVPN Core Module

This module contains the core functionality of the MoonVPN application,
including database models, services, and utilities.
"""

__version__ = '0.1.0'

# Import key services for easier access
from core.services import (
    BackupService,
    NotificationService,
    PanelAPI,
    PanelClient,
    SecurityService,
    ServerManager,
    TrafficService,
)

