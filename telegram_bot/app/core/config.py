import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Core API Configuration ---
# Get the base URL for the Core API from environment variables
# Example: CORE_API_URL=http://localhost:8000/api/v1
CORE_API_URL = os.getenv("CORE_API_URL", "http://127.0.0.1:8000/api/v1") # Default to localhost if not set

# --- Telegram Bot Configuration ---
# Get the Telegram Bot Token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# --- Admin Group IDs ---
# Group IDs for admin notifications and management
MANAGE_GROUP_ID = int(os.getenv("MANAGE_GROUP_ID", "-1001000000000")) # Default to placeholder if not set
REPORTS_GROUP_ID = int(os.getenv("REPORTS_GROUP_ID", "-1001000000001")) # Default to placeholder if not set
TRANSACTIONS_GROUP_ID = int(os.getenv("TRANSACTIONS_GROUP_ID", "-1001000000002")) # Default to placeholder if not set
OUTAGES_GROUP_ID = int(os.getenv("OUTAGES_GROUP_ID", "-1001000000003")) # Default to placeholder if not set

# --- Registration Requirements ---
# The numeric ID of the mandatory channel users must join.
# Provided by user: -1002542112596 (@moonvpn1_channel)
REQUIRED_CHANNEL_ID = -1002542112596

# --- Debug Settings ---
# Set DEBUG_MODE to True for additional logging and error reporting
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() in ["true", "1", "yes"]

# --- Other Settings ---
# Add any other bot-wide configurations here

# --- Logging ---
# Basic logging configuration is usually done in main.py or a dedicated logging setup module.

# Ensure essential variables are set (optional but recommended)
if not CORE_API_URL or CORE_API_URL == "http://127.0.0.1:8000/api/v1":
    print("⚠️ WARNING: CORE_API_URL is not set or using default. Ensure the Core API is running at http://127.0.0.1:8000/api/v1 or set the CORE_API_URL environment variable.")

if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("⛔️ ERROR: TELEGRAM_BOT_TOKEN is not set. Please set the TELEGRAM_BOT_TOKEN environment variable.")

# Check admin group settings
if MANAGE_GROUP_ID == -1001000000000:
    print("⚠️ WARNING: MANAGE_GROUP_ID is using default placeholder. Set the MANAGE_GROUP_ID environment variable for proper admin notifications.")
