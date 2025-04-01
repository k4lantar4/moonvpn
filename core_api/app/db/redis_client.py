# core_api/app/db/redis_client.py
import redis.asyncio as redis # Use asyncio version of redis-py
from typing import Optional

from app.core.config import settings

# Connection pool (recommended for managing connections)
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True # Decode responses from bytes to strings
)

# Key prefix for OTPs to avoid collisions
OTP_KEY_PREFIX = "otp:"

async def get_redis_connection() -> redis.Redis:
    """Gets a Redis connection from the pool."""
    # In a more complex app, you might manage the pool lifecycle (startup/shutdown)
    return redis.Redis(connection_pool=redis_pool)

async def set_otp(telegram_id: int, otp: str):
    """
    Stores the OTP for a given Telegram ID in Redis with an expiry time.

    Args:
        telegram_id: The user's Telegram ID.
        otp: The OTP code to store.
    """
    r = await get_redis_connection()
    key = f"{OTP_KEY_PREFIX}{telegram_id}"
    try:
        # Set the OTP with the configured expiry time
        await r.set(key, otp, ex=settings.OTP_EXPIRE_SECONDS)
    finally:
        # Ensure the connection is closed/released (important with pools)
        await r.aclose()

async def get_otp(telegram_id: int) -> Optional[str]:
    """
    Retrieves the OTP for a given Telegram ID from Redis and deletes it immediately.
    This ensures an OTP can only be used once.

    Args:
        telegram_id: The user's Telegram ID.

    Returns:
        The OTP string if found and valid, otherwise None.
    """
    r = await get_redis_connection()
    key = f"{OTP_KEY_PREFIX}{telegram_id}"
    try:
        # Use GETDEL (atomic get and delete) if available and suitable,
        # otherwise, use a transaction or simple get then delete.
        # Simple get then delete:
        otp = await r.get(key)
        if otp:
            await r.delete(key)
        return otp # Returns the value if found, None otherwise
    finally:
        await r.aclose()

# Optional: Function to delete OTP if needed without retrieving
async def delete_otp(telegram_id: int):
    """
    Explicitly deletes the OTP for a given Telegram ID.
    """
    r = await get_redis_connection()
    key = f"{OTP_KEY_PREFIX}{telegram_id}"
    try:
        await r.delete(key)
    finally:
        await r.aclose() 