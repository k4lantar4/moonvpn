"""
Migration v20240308_000001: Initial schema setup
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from ..migrations import Migration

class Migration(Migration):
    """Initial database schema migration."""
    
    version = "v20240308_000001"
    description = "Initial schema setup"
    
    async def up(self, db: AsyncIOMotorDatabase):
        """Upgrade database to this version."""
        # Create collections with schemas
        await db.create_collection('users')
        await db.create_collection('sessions')
        await db.create_collection('user_activity')
        await db.create_collection('traffic_history')
        
        # Create indexes
        await db.users.create_index('username', unique=True)
        await db.users.create_index('email', unique=True)
        await db.sessions.create_index('token', unique=True)
        await db.sessions.create_index('expires_at', expireAfterSeconds=0)
        await db.traffic_history.create_index([('user_id', 1), ('timestamp', -1)])
        await db.user_activity.create_index([('user_id', 1), ('timestamp', -1)])
        
    async def down(self, db: AsyncIOMotorDatabase):
        """Downgrade database from this version."""
        # Drop collections
        await db.users.drop()
        await db.sessions.drop()
        await db.user_activity.drop()
        await db.traffic_history.drop() 