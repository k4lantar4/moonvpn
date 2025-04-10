"""Custom project exceptions."""

class CoreError(Exception):
    """Base exception for core application errors."""
    pass

class ConfigurationError(CoreError):
    """Exception for configuration-related errors."""
    pass

class DatabaseError(CoreError):
    """Exception for database operation errors."""
    pass

class RepositoryError(DatabaseError):
    """Exception specific to repository operations."""
    pass

class NotFoundError(CoreError):
    """Exception raised when a requested resource is not found."""
    pass

class UserNotFoundError(NotFoundError):
    """Specific exception for when a user is not found."""
    pass

class RoleNotFoundException(NotFoundError):
    """Specific exception for when a role is not found."""
    pass

class ServiceError(CoreError):
    """Base exception for service layer errors."""
    pass

class BusinessLogicError(ServiceError):
    """Exception for errors related to business rules."""
    pass

# Define DuplicateUserException after BusinessLogicError
class DuplicateUserException(BusinessLogicError):
    """Specific exception for when trying to create a duplicate user."""
    pass

# Added for wallet/payment operations
class InsufficientBalanceError(BusinessLogicError):
    """Exception raised when a user's wallet balance is insufficient for an operation."""
    pass

# Panel exceptions are moved to integrations/panels/exceptions.py
# class PanelIntegrationError(CoreError):
#     """Base exception for errors during VPN panel interaction."""
#     pass
#
# # Add PanelError as an alias or base for panel integration issues
# class PanelError(PanelIntegrationError):
#     """General error related to panel operations."""
#     pass
#
# class PanelAuthenticationError(PanelIntegrationError):
#     """Exception for authentication failures with the VPN panel."""
#     pass
#
# class PanelAPIError(PanelIntegrationError):
#     """Exception for general API errors from the VPN panel."""
#     pass
#
# class PanelClientError(PanelIntegrationError):
#     """Exception for client-side errors during panel interaction (e.g., network)."""
#     pass

class PaymentGatewayError(CoreError):
    """Base exception for payment gateway interactions."""
    pass

# Add more specific exceptions as needed
