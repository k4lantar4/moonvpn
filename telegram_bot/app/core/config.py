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

# --- Registration Requirements ---
# The numeric ID of the mandatory channel users must join.
# Provided by user: -1002542112596 (@moonvpn1_channel)
REQUIRED_CHANNEL_ID = -1002542112596

# --- Other Settings ---
# Add any other bot-wide configurations here

# --- Logging ---
# Basic logging configuration is usually done in main.py or a dedicated logging setup module.

# Ensure essential variables are set (optional but recommended)
if not CORE_API_URL or CORE_API_URL == "http://127.0.0.1:8000/api/v1":
    print("⚠️ WARNING: CORE_API_URL is not set or using default. Ensure the Core API is running at http://127.0.0.1:8000/api/v1 or set the CORE_API_URL environment variable.")

if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("⛔️ ERROR: TELEGRAM_BOT_TOKEN is not set. Please set the TELEGRAM_BOT_TOKEN environment variable.")
