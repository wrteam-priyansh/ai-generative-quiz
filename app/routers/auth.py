from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from typing import Optional
import logging

from app.services.auth_service import GoogleAuthService
from app.models.auth import GoogleAuthURL, TokenResponse
from app.models.response import success_response, error_response
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

auth_service = GoogleAuthService()

@router.get("/google/authorize")
async def get_google_auth_url(state: Optional[str] = Query(None)):
    """Get Google OAuth authorization URL"""
    try:
        auth_url = auth_service.get_authorization_url(state)
        return success_response({
            "auth_url": auth_url
        }, "Authorization URL generated successfully")
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        return error_response("Failed to generate authorization URL")

@router.get("/callback")
async def google_auth_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """Handle Google OAuth callback"""
    if error:
        logger.error(f"OAuth error: {error}")
        return error_response(f"OAuth error: {error}")
    
    try:
        token_data = auth_service.exchange_code_for_tokens(code)
        
        return success_response({
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data["expires_in"],
            "user_info": token_data["user_info"].__dict__,
            "credentials_json": token_data["credentials_json"]
        }, "Authentication completed successfully")
    
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {str(e)}")
        return error_response("Failed to complete authentication")

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        token_data = auth_service.refresh_access_token(refresh_token)
        return success_response({
            "access_token": token_data["access_token"],
            "expires_in": token_data["expires_in"]
        }, "Token refreshed successfully")
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return error_response("Failed to refresh token")

@router.post("/validate")
async def validate_credentials(credentials_json: str):
    """Validate Google credentials"""
    try:
        is_valid = auth_service.validate_credentials(credentials_json)
        return success_response({
            "valid": is_valid,
            "status": "valid" if is_valid else "invalid"
        }, "Credentials validated successfully")
    except Exception as e:
        logger.error(f"Error validating credentials: {str(e)}")
        return error_response("Failed to validate credentials")