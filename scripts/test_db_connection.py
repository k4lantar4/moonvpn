import asyncio
import os
import asyncmy
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    load_dotenv() # Load .env variables
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("❌ DATABASE_URL not found in environment variables.")
        return

    logger.info(f"Attempting to connect using DATABASE_URL: {db_url}")

    # Basic parsing assumes mysql+asyncmy://user:pass@host:port/db
    try:
        if not db_url.startswith("mysql+asyncmy://"):
            raise ValueError("DATABASE_URL does not start with mysql+asyncmy://")

        parts = db_url.split("://")[1]
        user_pass, host_db = parts.split("@")
        user, password = user_pass.split(":")
        host_port, db_name_query = host_db.split("/")
        db_name = db_name_query.split("?")[0] # Remove query params if any
        
        if ":" in host_port:
            host, port_str = host_port.split(":")
            port = int(port_str)
        else:
            host = host_port
            port = 3306 # Default MySQL port

        logger.info(f"Parsed connection details:")
        logger.info(f"  Host: {host}")
        logger.info(f"  Port: {port}")
        logger.info(f"  User: {user}")
        # Avoid logging password directly
        logger.info(f"  Password: ***") 
        logger.info(f"  Database: {db_name}")

        conn = None
        try:
            logger.info("Connecting...")
            conn = await asyncmy.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                db=db_name,
                # connect_timeout=10 # Add a timeout
            )
            logger.info("✅ Successfully connected to the database!")
            cursor = await conn.cursor()
            await cursor.execute("SELECT VERSION();")
            result = await cursor.fetchone()
            logger.info(f"MySQL Version: {result[0]}")
            await cursor.close()
            logger.info("Cursor closed.")
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()
                logger.info("Connection closed.")
            else:
                logger.warning("Connection object was None, nothing to close.")
                
    except Exception as parse_error:
        logger.error(f"❌ Error parsing DATABASE_URL '{db_url}': {parse_error}", exc_info=True)


if __name__ == "__main__":
    logger.info("Starting database connection test script...")
    asyncio.run(test_connection())
    logger.info("Script finished.") 