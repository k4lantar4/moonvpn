"""
Custom exceptions for MoonVPN Telegram Bot.

This module defines custom exceptions used throughout the application.
"""

class AdminGroupError(Exception):
    """Base exception for admin group related errors."""
    pass

class AdminGroupNotFoundError(AdminGroupError):
    """Exception raised when an admin group is not found."""
    pass

class AdminGroupAlreadyExistsError(AdminGroupError):
    """Exception raised when trying to create an admin group that already exists."""
    pass

class AdminGroupInvalidTypeError(AdminGroupError):
    """Exception raised when an invalid admin group type is provided."""
    pass

class AdminGroupMemberError(AdminGroupError):
    """Base exception for admin group member related errors."""
    pass

class AdminGroupMemberNotFoundError(AdminGroupMemberError):
    """Exception raised when an admin group member is not found."""
    pass

class AdminGroupMemberAlreadyExistsError(AdminGroupMemberError):
    """Exception raised when trying to add a member that already exists in the group."""
    pass

class AdminGroupMemberInvalidRoleError(AdminGroupMemberError):
    """Exception raised when an invalid member role is provided."""
    pass

class NotificationError(Exception):
    """Base exception for notification related errors."""
    pass

class NotificationSendError(NotificationError):
    """Exception raised when a notification fails to send."""
    pass

class MonitoringError(Exception):
    """Base exception for monitoring related errors."""
    pass

class MonitoringServiceError(MonitoringError):
    """Exception raised when a monitoring service operation fails."""
    pass

class MonitoringDataError(MonitoringError):
    """Exception raised when monitoring data is invalid or missing."""
    pass

"""
Custom exceptions for service integration.
"""
from typing import Any, Dict, Optional

class ServiceError(Exception):
    """Base exception for service errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class InitializationError(ServiceError):
    """Raised when service initialization fails."""
    pass

class ConfigurationError(ServiceError):
    """Raised when service configuration is invalid."""
    pass

class ConnectionError(ServiceError):
    """Raised when service connection fails."""
    pass

class AuthenticationError(ServiceError):
    """Raised when service authentication fails."""
    pass

class ValidationError(ServiceError):
    """Raised when service validation fails."""
    pass

class ResourceError(ServiceError):
    """Raised when resource operation fails."""
    pass

class CacheError(ServiceError):
    """Raised when cache operation fails."""
    pass

class MetricsError(ServiceError):
    """Raised when metrics operation fails."""
    pass

class PanelError(ServiceError):
    """Raised when VPN panel operation fails."""
    pass

class BotError(ServiceError):
    """Raised when Telegram bot operation fails."""
    pass

class PaymentError(ServiceError):
    """Raised when payment operation fails."""
    pass

class NotificationError(ServiceError):
    """Raised when notification operation fails."""
    pass

class DatabaseError(ServiceError):
    """Raised when database operation fails."""
    pass

class SecurityError(ServiceError):
    """Raised when security operation fails."""
    pass

class PerformanceError(ServiceError):
    """Raised when performance operation fails."""
    pass

class MonitoringError(ServiceError):
    """Raised when monitoring operation fails."""
    pass

class BackupError(ServiceError):
    """Raised when backup operation fails."""
    pass

class RecoveryError(ServiceError):
    """Raised when recovery operation fails."""
    pass

class MaintenanceError(ServiceError):
    """Raised when maintenance operation fails."""
    pass

class IntegrationError(ServiceError):
    """Raised when integration operation fails."""
    pass

class OptimizationError(ServiceError):
    """Raised when optimization operation fails."""
    pass

class DocumentationError(ServiceError):
    """Raised when documentation operation fails."""
    pass

class TestingError(ServiceError):
    """Raised when testing operation fails."""
    pass

class DeploymentError(ServiceError):
    """Raised when deployment operation fails."""
    pass

def handle_service_error(error: ServiceError) -> Dict[str, Any]:
    """Convert service error to API response format."""
    return {
        "error": True,
        "message": str(error),
        "type": error.__class__.__name__,
        "details": error.details
    }

"""
Custom exceptions for the application.
"""

from fastapi import HTTPException, status

class PaymentError(HTTPException):
    """Base exception for payment-related errors."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class InsufficientBalanceError(PaymentError):
    """Exception raised when user has insufficient balance."""
    def __init__(self, detail: str):
        super().__init__(detail)

class TransactionNotFoundError(HTTPException):
    """Exception raised when a transaction is not found."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class PaymentVerificationError(PaymentError):
    """Exception raised when payment verification fails."""
    def __init__(self, detail: str):
        super().__init__(detail)

class PaymentGatewayError(PaymentError):
    """Exception raised when payment gateway encounters an error."""
    def __init__(self, detail: str):
        super().__init__(detail)

class InvalidPaymentMethodError(PaymentError):
    """Exception raised when an invalid payment method is selected."""
    def __init__(self, detail: str):
        super().__init__(detail)

class PaymentAmountError(PaymentError):
    """Exception raised when payment amount is invalid."""
    def __init__(self, detail: str):
        super().__init__(detail)

class WalletLimitError(PaymentError):
    """Exception raised when wallet balance limit is exceeded."""
    def __init__(self, detail: str):
        super().__init__(detail) 