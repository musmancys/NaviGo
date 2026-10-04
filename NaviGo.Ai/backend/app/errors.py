from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict

class NaviGoException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST", details: Any = None):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(self.message)

class NotFoundException(NaviGoException):
    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(message=message, status_code=404, code="NOT_FOUND", details=details)

class UnauthorizedException(NaviGoException):
    def __init__(self, message: str = "Unauthorized", details: Any = None):
        super().__init__(message=message, status_code=401, code="UNAUTHORIZED", details=details)

class ExternalServiceException(NaviGoException):
    def __init__(self, message: str = "External service unavailable", details: Any = None):
        super().__init__(message=message, status_code=502, code="EXTERNAL_SERVICE_ERROR", details=details)

async def navigo_exception_handler(request: Request, exc: NaviGoException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": exc.errors()
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": str(exc) if request.app.debug else None
            }
        }
    )
