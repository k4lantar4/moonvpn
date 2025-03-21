"""
MoonVPN Telegram Bot - Database Utilities.

This module provides utilities for database operations in the MoonVPN Telegram Bot.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
import json
import psycopg2
from psycopg2.extras import RealDictCursor

from core.config import DATABASE_URL

logger = logging.getLogger(__name__)

def init_database() -> None:
    """Initialize the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create the necessary tables if they don't exist
                cur.execute(open("bot/database/schema.sql", "r").read())
                conn.commit()
                logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_db_connection():
    """Get a connection to the database."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get a user from the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
                return cur.fetchone()
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def get_subscription_plans() -> List[Dict[str, Any]]:
    """Get all subscription plans."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM vpn_packages ORDER BY price")
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Error getting subscription plans: {e}")
        return []

def get_active_servers() -> List[Dict[str, Any]]:
    """Get all active servers."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM servers WHERE is_active = TRUE ORDER BY location")
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Error getting active servers: {e}")
        return []

def get_user_accounts(user_id: int) -> List[Dict[str, Any]]:
    """Get all VPN accounts for a user."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT a.*, s.location, s.host, s.port
                    FROM vpn_accounts a
                    JOIN servers s ON a.server_id = s.id
                    WHERE a.user_id = %s
                    ORDER BY a.created_at DESC
                """, (user_id,))
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Error getting user accounts: {e}")
        return []

def get_user_payments(user_id: int) -> List[Dict[str, Any]]:
    """Get all payments for a user."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM payments
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Error getting user payments: {e}")
        return []

def get_system_stats() -> Dict[str, Any]:
    """Get system statistics."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get user count
                cur.execute("SELECT COUNT(*) FROM users")
                user_count = cur.fetchone()[0]
                
                # Get active account count
                cur.execute("SELECT COUNT(*) FROM vpn_accounts WHERE status = 'active'")
                active_account_count = cur.fetchone()[0]
                
                # Get server count
                cur.execute("SELECT COUNT(*) FROM servers")
                server_count = cur.fetchone()[0]
                
                # Get active server count
                cur.execute("SELECT COUNT(*) FROM servers WHERE is_active = TRUE")
                active_server_count = cur.fetchone()[0]
                
                # Get pending payment count
                cur.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
                pending_payment_count = cur.fetchone()[0]
                
                # Get total payment amount for completed payments
                cur.execute("SELECT SUM(amount) FROM payments WHERE status = 'completed'")
                total_payment_amount = cur.fetchone()[0] or 0
                
                return {
                    "user_count": user_count,
                    "active_account_count": active_account_count,
                    "server_count": server_count,
                    "active_server_count": active_server_count,
                    "pending_payment_count": pending_payment_count,
                    "total_payment_amount": total_payment_amount
                }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            "user_count": 0,
            "active_account_count": 0,
            "server_count": 0,
            "active_server_count": 0,
            "pending_payment_count": 0,
            "total_payment_amount": 0
        }

def create_user(telegram_id: int, username: Optional[str] = None, 
               first_name: Optional[str] = None, last_name: Optional[str] = None,
               language: str = "fa") -> Optional[Dict[str, Any]]:
    """Create a new user."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if user already exists
                cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
                existing_user = cur.fetchone()
                
                if existing_user:
                    return existing_user
                
                # Create new user
                now = time.strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("""
                    INSERT INTO users 
                    (telegram_id, username, first_name, last_name, language, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (telegram_id, username, first_name, last_name, language, now, now))
                conn.commit()
                return cur.fetchone()
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None 