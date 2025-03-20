"""Test constants used across test files."""

# User test data
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "test_password123"
TEST_USER_USERNAME = "test_user"
TEST_USER_FULL_NAME = "Test User"

# VPN test data
TEST_VPN_NAME = "test_vpn_config"
TEST_VPN_SERVER = "test.vpn.server"
TEST_VPN_PORT = 1194
TEST_VPN_PROTOCOL = "udp"
TEST_VPN_CIPHER = "AES-256-CBC"
TEST_VPN_AUTH = "SHA256"
TEST_VPN_CA_CERT = "test_ca_cert"
TEST_VPN_CLIENT_CERT = "test_client_cert"
TEST_VPN_CLIENT_KEY = "test_client_key"
TEST_VPN_TLS_AUTH = "test_tls_auth"

# Payment test data
TEST_PAYMENT_AMOUNT = 10.0
TEST_PAYMENT_CURRENCY = "USD"
TEST_PAYMENT_METHOD = "credit_card"
TEST_PAYMENT_STATUS = "completed"
TEST_PAYMENT_TRANSACTION_ID = "test_transaction_id"

# Telegram test data
TEST_TELEGRAM_ID = 123456789
TEST_TELEGRAM_USERNAME = "test_telegram_user"
TEST_TELEGRAM_FIRST_NAME = "Test"
TEST_TELEGRAM_LAST_NAME = "User"

# API endpoints
API_V1_PREFIX = "/api/v1"
AUTH_PREFIX = f"{API_V1_PREFIX}/auth"
USERS_PREFIX = f"{API_V1_PREFIX}/users"
VPN_PREFIX = f"{API_V1_PREFIX}/vpn"
PAYMENTS_PREFIX = f"{API_V1_PREFIX}/payments"
TELEGRAM_PREFIX = f"{API_V1_PREFIX}/telegram"

# Response schemas
USER_RESPONSE_SCHEMA = {
    "id": int,
    "email": str,
    "username": str,
    "is_active": bool,
    "is_superuser": bool,
    "created_at": str,
    "updated_at": str
}

VPN_CONFIG_RESPONSE_SCHEMA = {
    "id": int,
    "name": str,
    "server": str,
    "port": int,
    "protocol": str,
    "cipher": str,
    "auth": str,
    "ca_cert": str,
    "client_cert": str,
    "client_key": str,
    "tls_auth": str,
    "is_active": bool,
    "user_id": int,
    "created_at": str,
    "updated_at": str
}

PAYMENT_RESPONSE_SCHEMA = {
    "id": int,
    "amount": float,
    "currency": str,
    "payment_method": str,
    "status": str,
    "transaction_id": str,
    "user_id": int,
    "created_at": str,
    "updated_at": str
}

TELEGRAM_USER_RESPONSE_SCHEMA = {
    "id": int,
    "telegram_id": int,
    "username": str,
    "first_name": str,
    "last_name": str,
    "is_active": bool,
    "user_id": int,
    "created_at": str,
    "updated_at": str
}

# Error messages
ERROR_MESSAGES = {
    "not_found": "Item not found",
    "unauthorized": "Not authenticated",
    "forbidden": "Not enough permissions",
    "validation_error": "Validation error",
    "server_error": "Internal server error"
}

# Test timeouts
DEFAULT_TIMEOUT = 5.0
DEFAULT_INTERVAL = 0.1
PERFORMANCE_TEST_TIMEOUT = 30 