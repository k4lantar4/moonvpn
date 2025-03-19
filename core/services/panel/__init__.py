"""
Panel Services Module

This module provides interfaces for interacting with VPN panels.
"""

from core.services.panel.api import PanelAPI
from core.services.panel.client import PanelClient

__all__ = ['PanelAPI', 'PanelClient']

