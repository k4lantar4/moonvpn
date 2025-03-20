from typing import Dict, List
from datetime import datetime

# MongoDB Collection Schemas

USER_SCHEMA = {
    "bsonType": "object",
    "required": [
        "username",
        "email",
        "password",
        "role",
        "subscription",
        "traffic",
        "status",
        "created_at"
    ],
    "properties": {
        "username": {
            "bsonType": "string",
            "description": "Username - must be unique"
        },
        "email": {
            "bsonType": "string",
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            "description": "Email address - must be unique and valid format"
        },
        "password": {
            "bsonType": "string",
            "description": "Hashed password"
        },
        "role": {
            "enum": ["admin", "manager", "user"],
            "description": "User role for permissions"
        },
        "subscription": {
            "bsonType": "object",
            "required": ["plan", "expires_at", "status"],
            "properties": {
                "plan": {
                    "enum": ["basic", "premium", "enterprise"],
                    "description": "Subscription plan type"
                },
                "expires_at": {
                    "bsonType": "date",
                    "description": "Subscription expiry date"
                },
                "status": {
                    "enum": ["active", "expired", "suspended"],
                    "description": "Current subscription status"
                }
            }
        },
        "traffic": {
            "bsonType": "object",
            "required": ["limit", "used"],
            "properties": {
                "limit": {
                    "bsonType": "long",
                    "description": "Traffic limit in bytes"
                },
                "used": {
                    "bsonType": "long",
                    "description": "Traffic used in bytes"
                }
            }
        },
        "status": {
            "enum": ["active", "inactive", "suspended", "deleted"],
            "description": "User account status"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Account creation timestamp"
        },
        "last_active": {
            "bsonType": ["date", "null"],
            "description": "Last activity timestamp"
        }
    }
}

SESSION_SCHEMA = {
    "bsonType": "object",
    "required": ["user_id", "token", "created_at", "expires_at", "active"],
    "properties": {
        "user_id": {
            "bsonType": "objectId",
            "description": "Reference to user"
        },
        "token": {
            "bsonType": "string",
            "description": "Session token"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Session creation timestamp"
        },
        "expires_at": {
            "bsonType": "date",
            "description": "Session expiry timestamp"
        },
        "active": {
            "bsonType": "bool",
            "description": "Whether session is active"
        },
        "ip_address": {
            "bsonType": "string",
            "description": "Client IP address"
        },
        "user_agent": {
            "bsonType": "string",
            "description": "Client user agent"
        }
    }
}

USER_ACTIVITY_SCHEMA = {
    "bsonType": "object",
    "required": ["user_id", "type", "message", "timestamp"],
    "properties": {
        "user_id": {
            "bsonType": "objectId",
            "description": "Reference to user"
        },
        "type": {
            "enum": [
                "login",
                "logout",
                "traffic",
                "subscription",
                "settings",
                "security"
            ],
            "description": "Activity type"
        },
        "message": {
            "bsonType": "string",
            "description": "Activity description"
        },
        "timestamp": {
            "bsonType": "date",
            "description": "Activity timestamp"
        },
        "metadata": {
            "bsonType": "object",
            "description": "Additional activity data"
        }
    }
}

TRAFFIC_HISTORY_SCHEMA = {
    "bsonType": "object",
    "required": ["user_id", "timestamp", "bytes_in", "bytes_out"],
    "properties": {
        "user_id": {
            "bsonType": "objectId",
            "description": "Reference to user"
        },
        "timestamp": {
            "bsonType": "date",
            "description": "Traffic record timestamp"
        },
        "bytes_in": {
            "bsonType": "long",
            "description": "Incoming traffic in bytes"
        },
        "bytes_out": {
            "bsonType": "long",
            "description": "Outgoing traffic in bytes"
        },
        "protocol": {
            "bsonType": "string",
            "description": "Network protocol used"
        },
        "source_ip": {
            "bsonType": "string",
            "description": "Source IP address"
        }
    }
}

# Database initialization function
async def init_db_schemas(db) -> None:
    """Initialize database with collection schemas."""
    try:
        # Create collections with schemas
        await db.command({
            "collMod": "users",
            "validator": {"$jsonSchema": USER_SCHEMA},
            "validationLevel": "strict"
        })
        
        await db.command({
            "collMod": "sessions",
            "validator": {"$jsonSchema": SESSION_SCHEMA},
            "validationLevel": "strict"
        })
        
        await db.command({
            "collMod": "user_activity",
            "validator": {"$jsonSchema": USER_ACTIVITY_SCHEMA},
            "validationLevel": "strict"
        })
        
        await db.command({
            "collMod": "traffic_history",
            "validator": {"$jsonSchema": TRAFFIC_HISTORY_SCHEMA},
            "validationLevel": "strict"
        })
        
        # Create indexes
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        await db.sessions.create_index("token", unique=True)
        await db.sessions.create_index("expires_at", expireAfterSeconds=0)
        await db.traffic_history.create_index([("user_id", 1), ("timestamp", -1)])
        await db.user_activity.create_index([("user_id", 1), ("timestamp", -1)])
        
    except Exception as e:
        raise Exception(f"Failed to initialize database schemas: {str(e)}") 