from core.exceptions import InternalServerErrorException, ServiceUnavailableException

class PanelConnectionError(ServiceUnavailableException):
    def __init__(self, detail: str = "Failed to connect to panel"):
        super().__init__(detail=detail)

class PanelAuthenticationError(InternalServerErrorException):
    def __init__(self, detail: str = "Failed to authenticate with panel"):
        super().__init__(detail=detail)

class PanelApiError(InternalServerErrorException):
    def __init__(self, detail: str = "Panel API error"):
        super().__init__(detail=detail)

class ClientCreationError(InternalServerErrorException):
    def __init__(self, detail: str = "Failed to create client on panel"):
        super().__init__(detail=detail)

class ClientDeletionError(InternalServerErrorException):
    def __init__(self, detail: str = "Failed to delete client from panel"):
        super().__init__(detail=detail)

class ClientUpdateError(InternalServerErrorException):
    def __init__(self, detail: str = "Failed to update client on panel"):
        super().__init__(detail=detail)

class DuplicateClientRemarkError(InternalServerErrorException):
    def __init__(self, detail: str = "Client with this remark already exists on panel"):
        super().__init__(detail=detail)

class PanelHealthCheckError(ServiceUnavailableException):
    def __init__(self, detail: str = "Panel health check failed"):
        super().__init__(detail=detail) 