"""
Database configuration settings.
"""

import os
from typing import Dict, Any

# Database connection settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "moonvpn")
DB_USER = os.getenv("DB_USER", "moonvpn")
DB_PASSWORD = os.getenv("DB_PASSWORD", "moonvpn")

# Connection pool settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

# Database configuration dictionary
DATABASE_CONFIG: Dict[str, Any] = {
    "host": DB_HOST,
    "port": DB_PORT,
    "database": DB_NAME,
    "username": DB_USER,
    "password": DB_PASSWORD,
    "pool_size": DB_POOL_SIZE,
    "max_overflow": DB_MAX_OVERFLOW,
    "pool_timeout": DB_POOL_TIMEOUT,
    "pool_recycle": DB_POOL_RECYCLE
}

# Database URL for direct connection
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}" 