"""
Feature toggles configuration for MoonVPN.
This module controls which features are enabled/disabled in the system.
"""

# Payment Gateways
ZARINPAL_ENABLED = False  # Default: Disabled
CARD_TO_CARD_ENABLED = True  # Default: Enabled

# Languages
PERSIAN_ENABLED = True  # Default: Enabled (Primary)
ENGLISH_ENABLED = False  # Default: Disabled

# 3x-UI Panel Integration
PANEL_SYNC_ENABLED = True  # Default: Enabled
TRAFFIC_MONITORING_ENABLED = True  # Default: Enabled

# User Features
REFERRAL_SYSTEM_ENABLED = True  # Default: Enabled
NOTIFICATIONS_ENABLED = True  # Default: Enabled
AUTO_RENEWAL_ENABLED = True  # Default: Enabled

# Admin Features
BULK_MESSAGING_ENABLED = True  # Default: Enabled
ANALYTICS_ENABLED = True  # Default: Enabled
BACKUP_SYSTEM_ENABLED = True  # Default: Enabled 