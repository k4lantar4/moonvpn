#!/usr/bin/env python3
"""
Database Migration Script

This script updates the database schema to the latest version with proper
relations, constraints, indexes, and more sophisticated structure.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path to allow importing modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db_migration")

def run_migration(dry_run=False):
    """
    Run the database migration.
    
    Args:
        dry_run: If True, only show SQL statements without executing them
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        if not dry_run:
            conn.autocommit = False
        
        # List of migration SQL statements
        migrations = [
            # 1. Add missing indexes to existing tables
            """
            -- Add indexes to users table
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
            """,
            
            # 2. Create subscription plans table
            """
            -- Create subscription plans table
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                duration_days INTEGER NOT NULL,
                traffic_limit_gb INTEGER NOT NULL,
                price INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                features JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Add indexes
            CREATE INDEX IF NOT EXISTS idx_subscription_plans_active ON subscription_plans(is_active);
            """,
            
            # 3. Create servers table
            """
            -- Create servers table
            CREATE TABLE IF NOT EXISTS servers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT,
                password TEXT,
                api_port INTEGER,
                location TEXT,
                country TEXT,
                type TEXT DEFAULT 'vmess',
                is_active BOOLEAN DEFAULT TRUE,
                config JSONB DEFAULT '{}',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Add indexes
            CREATE INDEX IF NOT EXISTS idx_servers_active ON servers(is_active);
            CREATE INDEX IF NOT EXISTS idx_servers_location ON servers(location);
            CREATE INDEX IF NOT EXISTS idx_servers_country ON servers(country);
            """,
            
            # 4. Update the accounts table
            """
            -- Make sure accounts table has all needed columns
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS server_id INTEGER;
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS subscription_plan_id INTEGER;
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS uuid TEXT;
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS email TEXT;
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS up_traffic BIGINT DEFAULT 0;
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS down_traffic BIGINT DEFAULT 0;
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS reset_date TIMESTAMP;
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS last_connect TIMESTAMP;
            
            -- Add indexes
            CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
            CREATE INDEX IF NOT EXISTS idx_accounts_server_id ON accounts(server_id);
            CREATE INDEX IF NOT EXISTS idx_accounts_subscription_plan_id ON accounts(subscription_plan_id);
            CREATE INDEX IF NOT EXISTS idx_accounts_expiry_date ON accounts(expiry_date);
            CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
            CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email);
            """,
            
            # 5. Create subscriptions table
            """
            -- Create subscriptions table
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                plan_id INTEGER NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active',
                auto_renew BOOLEAN DEFAULT FALSE,
                payment_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT
            );
            
            -- Add indexes
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id ON subscriptions(plan_id);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_end_date ON subscriptions(end_date);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
            """,
            
            # 6. Create transaction table
            """
            -- Create transactions table
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount INTEGER NOT NULL,
                type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                description TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            
            -- Add indexes
            CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
            CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
            CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
            """,
            
            # 7. Create referrals table
            """
            -- Create referrals table
            CREATE TABLE IF NOT EXISTS referrals (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT NOT NULL,
                referred_id BIGINT NOT NULL,
                status TEXT DEFAULT 'pending',
                bonus_amount INTEGER DEFAULT 0,
                is_paid BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (referred_id) REFERENCES users(id) ON DELETE CASCADE
            );
            
            -- Add unique constraint to prevent duplicate referrals
            ALTER TABLE referrals ADD CONSTRAINT unique_referral UNIQUE (referrer_id, referred_id);
            
            -- Add indexes
            CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
            CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id);
            CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);
            """,
            
            # 8. Update user_preferences table
            """
            -- Make sure user_preferences table has all needed columns
            ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS notification_settings JSONB DEFAULT '{"account_expiry": true, "traffic_threshold": true, "system_notifications": true, "expiry_days": 3, "traffic_threshold_percent": 80}';
            ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS ui_settings JSONB DEFAULT '{"theme": "light", "language": "en"}';
            """,
            
            # 9. Create notifications table
            """
            -- Create notifications table
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                data JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            
            -- Add indexes
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
            CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
            """,
            
            # 10. Add constraints to existing tables
            """
            -- Add foreign key constraints to accounts table
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'fk_accounts_server_id'
                ) THEN
                    ALTER TABLE accounts 
                    ADD CONSTRAINT fk_accounts_server_id 
                    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE SET NULL;
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'fk_accounts_subscription_plan_id'
                ) THEN
                    ALTER TABLE accounts 
                    ADD CONSTRAINT fk_accounts_subscription_plan_id 
                    FOREIGN KEY (subscription_plan_id) REFERENCES subscription_plans(id) ON DELETE SET NULL;
                END IF;
            END;
            $$;
            """,
            
            # 11. Add default subscription plans
            """
            -- Insert default subscription plans if table is empty
            INSERT INTO subscription_plans (name, description, duration_days, traffic_limit_gb, price, features)
            SELECT 'Basic', 'Basic VPN plan', 30, 50, 100000, '{"locations": ["Germany", "Netherlands"], "protocols": ["vmess", "vless"]}'
            WHERE NOT EXISTS (SELECT 1 FROM subscription_plans);
            
            INSERT INTO subscription_plans (name, description, duration_days, traffic_limit_gb, price, features)
            SELECT 'Premium', 'Premium VPN plan with more traffic', 30, 100, 180000, '{"locations": ["Germany", "Netherlands", "France", "USA"], "protocols": ["vmess", "vless", "trojan"]}'
            WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE name = 'Premium');
            
            INSERT INTO subscription_plans (name, description, duration_days, traffic_limit_gb, price, features)
            SELECT 'Ultra', 'Ultimate VPN plan with unlimited traffic', 30, 0, 250000, '{"locations": ["Germany", "Netherlands", "France", "USA", "Singapore", "Japan"], "protocols": ["vmess", "vless", "trojan", "shadowsocks"]}'
            WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE name = 'Ultra');
            """
        ]
        
        # Execute each migration
        for i, migration in enumerate(migrations, 1):
            logger.info(f"Running migration {i}/{len(migrations)}")
            if dry_run:
                logger.info(f"SQL: {migration}")
            else:
                cursor.execute(migration)
                logger.info(f"Migration {i} executed successfully")
        
        # Commit changes
        if not dry_run:
            conn.commit()
            logger.info("All migrations executed and committed successfully")
        else:
            logger.info("Dry run completed - no changes were made to the database")
    
    except Exception as e:
        logger.error(f"Error in migration: {e}")
        if not dry_run:
            conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database migration script")
    parser.add_argument("--dry-run", action="store_true", help="Show SQL statements without executing them")
    args = parser.parse_args()
    
    logger.info(f"Starting database migration {'(dry run)' if args.dry_run else ''}")
    run_migration(dry_run=args.dry_run)
    logger.info("Database migration completed") 