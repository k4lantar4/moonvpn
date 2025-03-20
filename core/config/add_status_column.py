#!/usr/bin/env python3
"""
Script to add status column to users table

This script adds a status column to the users table and sets default value to 'active'.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path to allow importing modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("add_status_column")

def add_status_column():
    """Add status column to users table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'status'
        """)
        
        if cursor.fetchone() is None:
            # Add status column with default value
            cursor.execute('ALTER TABLE users ADD COLUMN status TEXT DEFAULT %s', ('active',))
            conn.commit()
            logger.info("Status column added to users table")
            
            # Update existing users
            cursor.execute('UPDATE users SET status = %s', ('active',))
            conn.commit()
            
            # Get number of users updated
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            logger.info(f"Updated {count} users with 'active' status")
        else:
            logger.info("Status column already exists")
            
    except Exception as e:
        logger.error(f"Error adding status column: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting add status column script")
    add_status_column()
    logger.info("Add status column completed") 