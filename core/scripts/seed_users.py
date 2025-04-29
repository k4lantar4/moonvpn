#!/usr/bin/env python3
import os
import sys
# Ensure project root is in PYTHONPATH so db package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
from sqlalchemy import text
from db import engine
from db.models.user import User
from db.models.enums import UserRole

async def seed_users():
    # Seed two test users via raw SQL to bypass ORM mapping
    users = [
        (9000000001, 'admin_test', 'ادمین تستی', 'admin'),
        (9000000002, 'user_test', 'کاربر تستی', 'user'),
    ]
    async with engine.begin() as conn:
        for telegram_id, username, full_name, role in users:
            # Insert only if not exists
            await conn.execute(
                text(
                    "INSERT INTO users (telegram_id, username, full_name, role, created_at, status)"
                    " SELECT :telegram_id, :username, :full_name, :role, NOW(), 'active'"
                    " WHERE NOT EXISTS (SELECT 1 FROM users WHERE telegram_id = :telegram_id)"
                ),
                {"telegram_id": telegram_id, "username": username, "full_name": full_name, "role": role}
            )
    print("✅ Users seeded: admin_test, user_test")

if __name__ == '__main__':
    asyncio.run(seed_users()) 