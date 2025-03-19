"""
MoonVPN Bot - Django Integration.

This module provides functions to set up Django for the bot.
"""

import os
import sys
import django
from pathlib import Path

def setup_django():
    """
    Set up Django environment for the bot.
    
    This function configures Django settings for the bot to access the database
    and other Django features.
    """
    # Add the parent directory to sys.path
    parent_dir = str(Path(__file__).resolve().parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.moonvpn.settings')
    
    # Set up Django
    django.setup()
    
    # Import models after setup
    from backend.models import (
        User, AdminGroup, Wallet, Transaction, Order, Voucher,
        Server, Location, VPNAccount, SubscriptionPlan
    )
    
    # Log success
    print("Django setup complete. Models imported successfully.")
    
if __name__ == "__main__":
    setup_django()
    
    # Test imports
    from backend.models import User
    print(f"Test import successful. User model: {User}")
    
    # Test database connection
    try:
        user_count = User.objects.count()
        print(f"Database connection successful. User count: {user_count}")
    except Exception as e:
        print(f"Database connection failed: {e}") 