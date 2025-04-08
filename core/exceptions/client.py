from core.exceptions import (
    BadRequestException, 
    NotFoundException, 
    ConflictException, 
    ForbiddenException
)

class ClientNotFoundException(NotFoundException):
    def __init__(self, detail: str = "Client not found"):
        super().__init__(detail=detail)

class ClientAlreadyExistsException(ConflictException):
    def __init__(self, detail: str = "Client already exists"):
        super().__init__(detail=detail)

class NoAvailablePanelException(ServiceUnavailableException):
    def __init__(self, detail: str = "No available panel found"):
        super().__init__(detail=detail)

class InvalidTrafficLimitException(BadRequestException):
    def __init__(self, detail: str = "Invalid traffic limit"):
        super().__init__(detail=detail)

class LocationNotFoundException(NotFoundException):
    def __init__(self, detail: str = "Location not found"):
        super().__init__(detail=detail)

class LocationNotActiveException(BadRequestException):
    def __init__(self, detail: str = "Location is not active"):
        super().__init__(detail=detail)

class ExceededMigrationLimitException(ForbiddenException):
    def __init__(self, detail: str = "Exceeded daily migration limit"):
        super().__init__(detail=detail)

class ExceededLocationChangeLimitException(ForbiddenException):
    def __init__(self, detail: str = "Exceeded daily location change limit"):
        super().__init__(detail=detail)

class InvalidConfigException(BadRequestException):
    def __init__(self, detail: str = "Invalid client configuration"):
        super().__init__(detail=detail)

from fastapi import status

class ServiceUnavailableException(Exception):
    def __init__(self, detail: str = "Service unavailable"):
        self.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        self.detail = detail 