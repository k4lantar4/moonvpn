"""Test database connection."""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import async_engine
from core.config import settings

async def test_connection():
    """Test database connection."""
    print(f"Testing connection to database: {settings.SQLALCHEMY_DATABASE_URI}")
    try:
        async with async_engine.connect() as conn:
            print("Successfully connected to database!")
            result = await conn.execute("SELECT 1")
            print("Successfully executed test query!")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 