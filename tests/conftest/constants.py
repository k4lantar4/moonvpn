"""
Test constants for the application.
"""
from datetime import datetime, timedelta

# Test user constants
TEST_USER_PHONE = "+989123456789"
TEST_USER_PASSWORD = "test_password123"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_FULL_NAME = "Test User"

# Test admin constants
TEST_ADMIN_PHONE = "+989123456788"
TEST_ADMIN_PASSWORD = "test_admin_password123"
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_FULL_NAME = "Test Admin"

# Test VPN server constants
TEST_VPN_SERVER_HOST = "test.vpn.example.com"
TEST_VPN_SERVER_PORT = 443
TEST_VPN_SERVER_PROTOCOL = "tls"
TEST_VPN_SERVER_BANDWIDTH_LIMIT = 1000
TEST_VPN_SERVER_LOCATION = "US"

# Test VPN account constants
TEST_VPN_ACCOUNT_USERNAME = "test_vpn_user"
TEST_VPN_ACCOUNT_PASSWORD = "test_password123"

# Test subscription plan constants
TEST_SUBSCRIPTION_PLAN_NAME = "Premium"
TEST_SUBSCRIPTION_PLAN_DESCRIPTION = "Premium VPN plan"
TEST_SUBSCRIPTION_PLAN_PRICE = 9.99
TEST_SUBSCRIPTION_PLAN_DURATION_DAYS = 30
TEST_SUBSCRIPTION_PLAN_FEATURES = [
    "Unlimited bandwidth",
    "All locations",
    "Priority support"
]

# Test subscription constants
TEST_SUBSCRIPTION_START_DATE = datetime.utcnow()
TEST_SUBSCRIPTION_END_DATE = TEST_SUBSCRIPTION_START_DATE + timedelta(days=30)

# Test payment constants
TEST_PAYMENT_AMOUNT = TEST_SUBSCRIPTION_PLAN_PRICE
TEST_PAYMENT_CURRENCY = "USD"
TEST_PAYMENT_METHOD = "credit_card"
TEST_PAYMENT_STATUS = "pending"

# Test payment transaction constants
TEST_PAYMENT_TRANSACTION_ID = "test_transaction_123"
TEST_PAYMENT_TRANSACTION_STATUS = "completed"
TEST_PAYMENT_TRANSACTION_DATE = datetime.utcnow()

# Test Telegram user constants
TEST_TELEGRAM_USER_ID = 123456789
TEST_TELEGRAM_USERNAME = "test_user"
TEST_TELEGRAM_FIRST_NAME = "Test"
TEST_TELEGRAM_LAST_NAME = "User"
TEST_TELEGRAM_LANGUAGE_CODE = "en"

# Test Telegram chat constants
TEST_TELEGRAM_CHAT_ID = 123456789
TEST_TELEGRAM_CHAT_TYPE = "private"
TEST_TELEGRAM_CHAT_TITLE = "Test Chat"

# Test API endpoints
TEST_API_BASE_URL = "http://test"
TEST_API_VERSION = "v1"
TEST_API_PREFIX = f"/api/{TEST_API_VERSION}"

# Test API response codes
TEST_API_SUCCESS_CODE = 200
TEST_API_CREATED_CODE = 201
TEST_API_BAD_REQUEST_CODE = 400
TEST_API_UNAUTHORIZED_CODE = 401
TEST_API_FORBIDDEN_CODE = 403
TEST_API_NOT_FOUND_CODE = 404
TEST_API_CONFLICT_CODE = 409
TEST_API_INTERNAL_ERROR_CODE = 500

# Test API response messages
TEST_API_SUCCESS_MESSAGE = "Success"
TEST_API_CREATED_MESSAGE = "Created"
TEST_API_BAD_REQUEST_MESSAGE = "Bad Request"
TEST_API_UNAUTHORIZED_MESSAGE = "Unauthorized"
TEST_API_FORBIDDEN_MESSAGE = "Forbidden"
TEST_API_NOT_FOUND_MESSAGE = "Not Found"
TEST_API_CONFLICT_MESSAGE = "Conflict"
TEST_API_INTERNAL_ERROR_MESSAGE = "Internal Server Error"

# Test API response fields
TEST_API_RESPONSE_FIELD_STATUS = "status"
TEST_API_RESPONSE_FIELD_MESSAGE = "message"
TEST_API_RESPONSE_FIELD_DATA = "data"
TEST_API_RESPONSE_FIELD_ERROR = "error"

# Test API request fields
TEST_API_REQUEST_FIELD_PHONE = "phone"
TEST_API_REQUEST_FIELD_PASSWORD = "password"
TEST_API_REQUEST_FIELD_EMAIL = "email"
TEST_API_REQUEST_FIELD_FULL_NAME = "full_name"
TEST_API_REQUEST_FIELD_USERNAME = "username"
TEST_API_REQUEST_FIELD_AMOUNT = "amount"
TEST_API_REQUEST_FIELD_CURRENCY = "currency"
TEST_API_REQUEST_FIELD_PAYMENT_METHOD = "payment_method"
TEST_API_REQUEST_FIELD_STATUS = "status"

# Test API response data fields
TEST_API_RESPONSE_DATA_FIELD_ID = "id"
TEST_API_RESPONSE_DATA_FIELD_PHONE = "phone"
TEST_API_RESPONSE_DATA_FIELD_EMAIL = "email"
TEST_API_RESPONSE_DATA_FIELD_FULL_NAME = "full_name"
TEST_API_RESPONSE_DATA_FIELD_USERNAME = "username"
TEST_API_RESPONSE_DATA_FIELD_AMOUNT = "amount"
TEST_API_RESPONSE_DATA_FIELD_CURRENCY = "currency"
TEST_API_RESPONSE_DATA_FIELD_PAYMENT_METHOD = "payment_method"
TEST_API_RESPONSE_DATA_FIELD_STATUS = "status"
TEST_API_RESPONSE_DATA_FIELD_CREATED_AT = "created_at"
TEST_API_RESPONSE_DATA_FIELD_UPDATED_AT = "updated_at"

# Test API error fields
TEST_API_ERROR_FIELD_CODE = "code"
TEST_API_ERROR_FIELD_MESSAGE = "message"
TEST_API_ERROR_FIELD_DETAILS = "details"

# Test API validation error fields
TEST_API_VALIDATION_ERROR_FIELD_LOC = "loc"
TEST_API_VALIDATION_ERROR_FIELD_MSG = "msg"
TEST_API_VALIDATION_ERROR_FIELD_TYPE = "type"

# Test API pagination fields
TEST_API_PAGINATION_FIELD_PAGE = "page"
TEST_API_PAGINATION_FIELD_SIZE = "size"
TEST_API_PAGINATION_FIELD_TOTAL = "total"
TEST_API_PAGINATION_FIELD_PAGES = "pages"
TEST_API_PAGINATION_FIELD_ITEMS = "items"

# Test API sorting fields
TEST_API_SORTING_FIELD_SORT = "sort"
TEST_API_SORTING_FIELD_ORDER = "order"

# Test API filtering fields
TEST_API_FILTERING_FIELD_FILTER = "filter"
TEST_API_FILTERING_FIELD_OPERATOR = "operator"
TEST_API_FILTERING_FIELD_VALUE = "value"

# Test API search fields
TEST_API_SEARCH_FIELD_QUERY = "query"
TEST_API_SEARCH_FIELD_FIELDS = "fields"

# Test API response timeouts
TEST_API_RESPONSE_TIMEOUT = 5.0
TEST_API_RESPONSE_INTERVAL = 0.1

# Test API response retries
TEST_API_RESPONSE_RETRIES = 3
TEST_API_RESPONSE_RETRY_DELAY = 1.0

# Test API response cache
TEST_API_RESPONSE_CACHE_TTL = 300
TEST_API_RESPONSE_CACHE_KEY_PREFIX = "test_api_response:"

# Test API response compression
TEST_API_RESPONSE_COMPRESSION_LEVEL = 6
TEST_API_RESPONSE_COMPRESSION_THRESHOLD = 1024

# Test API response encryption
TEST_API_RESPONSE_ENCRYPTION_KEY = "test_encryption_key"
TEST_API_RESPONSE_ENCRYPTION_ALGORITHM = "AES-256-CBC"
TEST_API_RESPONSE_ENCRYPTION_IV_LENGTH = 16

# Test API response signing
TEST_API_RESPONSE_SIGNING_KEY = "test_signing_key"
TEST_API_RESPONSE_SIGNING_ALGORITHM = "HMAC-SHA256"
TEST_API_RESPONSE_SIGNING_HEADER = "X-API-Signature"

# Test API response rate limiting
TEST_API_RESPONSE_RATE_LIMIT = 100
TEST_API_RESPONSE_RATE_LIMIT_WINDOW = 60

# Test API response logging
TEST_API_RESPONSE_LOG_LEVEL = "INFO"
TEST_API_RESPONSE_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
TEST_API_RESPONSE_LOG_FILE = "test_api_response.log"

# Test API response monitoring
TEST_API_RESPONSE_MONITORING_ENABLED = True
TEST_API_RESPONSE_MONITORING_INTERVAL = 60
TEST_API_RESPONSE_MONITORING_METRICS = [
    "response_time",
    "response_size",
    "response_status",
    "response_error"
]

# Test API response alerting
TEST_API_RESPONSE_ALERTING_ENABLED = True
TEST_API_RESPONSE_ALERTING_THRESHOLD = 1000
TEST_API_RESPONSE_ALERTING_CHANNEL = "slack"

# Test API response analytics
TEST_API_RESPONSE_ANALYTICS_ENABLED = True
TEST_API_RESPONSE_ANALYTICS_INTERVAL = 300
TEST_API_RESPONSE_ANALYTICS_METRICS = [
    "requests",
    "responses",
    "errors",
    "latency"
]

# Test API response reporting
TEST_API_RESPONSE_REPORTING_ENABLED = True
TEST_API_RESPONSE_REPORTING_INTERVAL = 3600
TEST_API_RESPONSE_REPORTING_FORMAT = "json"

# Test API response backup
TEST_API_RESPONSE_BACKUP_ENABLED = True
TEST_API_RESPONSE_BACKUP_INTERVAL = 86400
TEST_API_RESPONSE_BACKUP_RETENTION = 7

# Test API response cleanup
TEST_API_RESPONSE_CLEANUP_ENABLED = True
TEST_API_RESPONSE_CLEANUP_INTERVAL = 3600
TEST_API_RESPONSE_CLEANUP_THRESHOLD = 1000

# Test API response validation
TEST_API_RESPONSE_VALIDATION_ENABLED = True
TEST_API_RESPONSE_VALIDATION_SCHEMA = "test_api_response_schema.json"
TEST_API_RESPONSE_VALIDATION_STRICT = True

# Test API response transformation
TEST_API_RESPONSE_TRANSFORMATION_ENABLED = True
TEST_API_RESPONSE_TRANSFORMATION_RULES = "test_api_response_rules.json"
TEST_API_RESPONSE_TRANSFORMATION_CACHE = True

# Test API response security
TEST_API_RESPONSE_SECURITY_ENABLED = True
TEST_API_RESPONSE_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}
TEST_API_RESPONSE_SECURITY_CORS = {
    "allow_origins": ["*"],
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "allow_credentials": True
}

# Test API response performance
TEST_API_RESPONSE_PERFORMANCE_ENABLED = True
TEST_API_RESPONSE_PERFORMANCE_THRESHOLD = 1000
TEST_API_RESPONSE_PERFORMANCE_METRICS = [
    "response_time",
    "response_size",
    "response_status",
    "response_error"
]

# Test API response reliability
TEST_API_RESPONSE_RELIABILITY_ENABLED = True
TEST_API_RESPONSE_RELIABILITY_THRESHOLD = 0.99
TEST_API_RESPONSE_RELIABILITY_METRICS = [
    "success_rate",
    "error_rate",
    "timeout_rate",
    "retry_rate"
]

# Test API response scalability
TEST_API_RESPONSE_SCALABILITY_ENABLED = True
TEST_API_RESPONSE_SCALABILITY_THRESHOLD = 1000
TEST_API_RESPONSE_SCALABILITY_METRICS = [
    "requests_per_second",
    "responses_per_second",
    "errors_per_second",
    "latency_per_second"
]

# Test API response maintainability
TEST_API_RESPONSE_MAINTAINABILITY_ENABLED = True
TEST_API_RESPONSE_MAINTAINABILITY_THRESHOLD = 0.8
TEST_API_RESPONSE_MAINTAINABILITY_METRICS = [
    "code_complexity",
    "code_coverage",
    "code_duplication",
    "code_smells"
]

# Test API response documentation
TEST_API_RESPONSE_DOCUMENTATION_ENABLED = True
TEST_API_RESPONSE_DOCUMENTATION_FORMAT = "openapi"
TEST_API_RESPONSE_DOCUMENTATION_VERSION = "3.0.0"
TEST_API_RESPONSE_DOCUMENTATION_TITLE = "Test API"
TEST_API_RESPONSE_DOCUMENTATION_DESCRIPTION = "Test API documentation"
TEST_API_RESPONSE_DOCUMENTATION_CONTACT = {
    "name": "Test Team",
    "email": "test@example.com",
    "url": "http://test.example.com"
}
TEST_API_RESPONSE_DOCUMENTATION_LICENSE = {
    "name": "MIT",
    "url": "http://test.example.com/license"
}
TEST_API_RESPONSE_DOCUMENTATION_SERVERS = [
    {
        "url": "http://test.example.com",
        "description": "Test server"
    }
]
TEST_API_RESPONSE_DOCUMENTATION_TAGS = [
    {
        "name": "users",
        "description": "User operations"
    },
    {
        "name": "vpn",
        "description": "VPN operations"
    },
    {
        "name": "subscriptions",
        "description": "Subscription operations"
    },
    {
        "name": "payments",
        "description": "Payment operations"
    },
    {
        "name": "telegram",
        "description": "Telegram operations"
    }
] 