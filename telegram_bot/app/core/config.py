import os
from dotenv import load_dotenv

# Load .env file from the telegram_bot directory or project root
# Adjust path as necessary
dotenv_path_bot = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env') # Check project root first
dotenv_path_local = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')     # Check bot directory

if os.path.exists(dotenv_path_bot):
    load_dotenv(dotenv_path=dotenv_path_bot)
elif os.path.exists(dotenv_path_local):
    load_dotenv(dotenv_path=dotenv_path_local)
else:
    print("Warning: .env file not found.")

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CORE_API_URL: str = os.getenv("CORE_API_URL", "http://localhost:8000") # Default if Core API runs locally
API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1") # Should match Core API

# --- Optional: Define Admin/Group IDs here or load from DB via API later ---
# SUPERADMIN_TELEGRAM_ID = int(os.getenv("SUPERADMIN_TELEGRAM_ID", "0"))
# MANAGE_GROUP_ID = int(os.getenv("MANAGE_GROUP_ID", "0"))
# ... other group IDs

if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("\n*** WARNING: TELEGRAM_BOT_TOKEN is not set in environment variables or .env file! ***\n")
