from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

class QuizGenerationException(Exception):
    """Custom exception for quiz generation errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class TextExtractionException(Exception):
    """Custom exception for text extraction errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class GoogleAPIException(Exception):
    """Custom exception for Google API errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationException(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

async def quiz_generation_exception_handler(request: Request, exc: QuizGenerationException):
    """Handle quiz generation exceptions"""
    logger.error(f"Quiz generation error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "data": None,
            "message": exc.message
        }
    )

async def text_extraction_exception_handler(request: Request, exc: TextExtractionException):
    """Handle text extraction exceptions"""
    logger.error(f"Text extraction error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "data": None,
            "message": exc.message
        }
    )

async def google_api_exception_handler(request: Request, exc: GoogleAPIException):
    """Handle Google API exceptions"""
    logger.error(f"Google API error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "data": None,
            "message": exc.message
        }
    )

async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    """Handle authentication exceptions"""
    logger.error(f"Authentication error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "data": None,
            "message": exc.message
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation exceptions"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "data": {
                "validation_errors": exc.errors()
            },
            "message": "Validation error - please check your input data"
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "data": None,
            "message": exc.detail
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "data": None,
            "message": "An unexpected error occurred"
        }
    )