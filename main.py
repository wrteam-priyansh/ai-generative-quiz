from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import auth, quiz, forms
from app.core.config import settings
from app.utils.logging_config import setup_logging
from app.utils.exceptions import (
    QuizGenerationException,
    TextExtractionException,
    GoogleAPIException,
    AuthenticationException,
    quiz_generation_exception_handler,
    text_extraction_exception_handler,
    google_api_exception_handler,
    authentication_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Setup logging
setup_logging()

app = FastAPI(
    title="AI Quiz Generator API",
    description="Backend for AI-powered quiz generation with Google Forms integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(QuizGenerationException, quiz_generation_exception_handler)
app.add_exception_handler(TextExtractionException, text_extraction_exception_handler)
app.add_exception_handler(GoogleAPIException, google_api_exception_handler)
app.add_exception_handler(AuthenticationException, authentication_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
app.include_router(forms.router, prefix="/forms", tags=["google-forms"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "error": False,
        "data": {
            "message": "AI Quiz Generator API is running",
            "version": "1.0.0",
            "endpoints": {
                "authentication": "/auth",
                "quiz_generation": "/quiz",
                "google_forms": "/forms",
                "documentation": "/docs",
                "openapi_schema": "/openapi.json"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "error": False,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "ai_service": "Google Gemini",
                "google_oauth": "Google OAuth 2.0",
                "google_forms": "Google Forms API",
                "text_extraction": "PyPDF2, python-docx"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)