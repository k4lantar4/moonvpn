"""
Configuration module (legacy wrapper)

This module imports and re-exports settings functionality from core.config package.
It is maintained for backwards compatibility.
"""

from core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
