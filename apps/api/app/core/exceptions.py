from typing import Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import uuid


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class FileParseError(AppError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__("FILE_PARSE_ERROR", message, status_code=422, details=details)


class ClarificationGateError(AppError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__("CLARIFICATION_REQUIRED", message, status_code=409, details=details)


class ExternalProviderError(AppError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__("EXTERNAL_PROVIDER_ERROR", message, status_code=502, details=details)


class CompilationError(AppError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__("COMPILATION_ERROR", message, status_code=500, details=details)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "meta": {
                "request_id": req_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )
