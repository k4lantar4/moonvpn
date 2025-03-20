#!/usr/bin/env python3
"""
Script to update existing users' status to 'active'

This script updates all users in the database who don't have a status
and sets their status to 'active'.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path to allow importing modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database import get_db_connection, setup_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("update_users")

def update_users_status():
    """Update all users without a status to 'active'."""
    # First set up the database to ensure the status column exists
    setup_database()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check for users with NULL status
        cursor.execute('SELECT COUNT(*) FROM users WHERE status IS NULL')
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Update users without status
            cursor.execute('UPDATE users SET status = %s WHERE status IS NULL', ('active',))
            conn.commit()
            logger.info(f"Updated {count} users to 'active' status")
        else:
            logger.info("No users need status update")
            
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting user status update script")
    update_users_status()
    logger.info("User status update completed") 