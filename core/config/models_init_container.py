"""
Models package initialization for MoonVPN Telegram Bot.

This module imports all models to make them available through
the models package.
"""

# Import models so they're available from models package
from models.users import User, Profile, UserNote, UserLoginHistory, UserActivity
from models.system import (
    SystemConfig, FeatureFlag, SystemBackup, SystemLog,
    Notification, SystemStats
)
from models.groups import (
    AllowedGroup, BotManagementGroup, GroupMessage, GroupEvent
)

# Add more model imports as needed 