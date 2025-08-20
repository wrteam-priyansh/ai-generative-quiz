from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from typing import Dict, Any, Optional
import json
import logging

from app.core.config import settings
from app.models.auth import UserInfo
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class GoogleAuthService:
    """Service for handling Google OAuth 2.0 authentication"""
    
    # Define scopes in a consistent order that matches Google's expectations
    SCOPES = [
        'openid',  # OpenID Connect - should be first
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile', 
        'https://www.googleapis.com/auth/forms.body',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self):
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured")
        
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        }
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL"""
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                state=state,
                prompt='consent'
            )
            
            return auth_url
        
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate authorization URL")
    
    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        try:
            logger.info(f"Attempting to exchange authorization code (length: {len(code)})")
            logger.debug(f"Using redirect URI: {settings.GOOGLE_REDIRECT_URI}")
            logger.debug(f"Using client ID: {settings.GOOGLE_CLIENT_ID[:10]}...")
            
            # Use the same flow configuration as authorization
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            
            # Log the token exchange attempt
            logger.info("Initiating token exchange with Google OAuth")
            
            # Exchange the code for tokens
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            logger.info("Successfully received credentials from Google")
            
            # Verify we have a valid token
            if not credentials.token:
                logger.error("No access token received from Google")
                raise ValueError("No access token received")
            
            if not credentials.refresh_token:
                logger.warning("No refresh token received - user may need to re-authenticate with prompt=consent")
            
            logger.info("Getting user information from Google API")
            # Get user info
            user_info = self.get_user_info(credentials)
            
            # Calculate actual expiry time if available
            expires_in = 3600  # Default 1 hour
            if hasattr(credentials, 'expiry') and credentials.expiry:
                import datetime
                expires_in = int((credentials.expiry - datetime.datetime.utcnow()).total_seconds())
                expires_in = max(expires_in, 0)  # Ensure not negative
                logger.debug(f"Token expires in {expires_in} seconds")
            
            logger.info(f"OAuth flow completed successfully for user: {user_info.email}")
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_in": expires_in,
                "user_info": user_info,
                "credentials_json": credentials.to_json()
            }
        
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            logger.debug(f"Full error details: {repr(e)}")
            
            # Provide more specific error information
            error_msg = "Failed to exchange authorization code"
            if "Scope has changed" in str(e):
                error_msg = "OAuth scope mismatch - please try authenticating again"
            elif "invalid_grant" in str(e).lower():
                logger.error("Invalid grant error - possible causes: expired code, code reuse, redirect URI mismatch, or clock skew")
                error_msg = "Authorization code expired or invalid. Please start the authentication process again."
            elif "invalid_client" in str(e).lower():
                error_msg = "OAuth client configuration error - check client ID and secret"
            elif "invalid_request" in str(e).lower():
                error_msg = "Invalid OAuth request - check redirect URI configuration"
            
            raise HTTPException(status_code=400, detail=error_msg)
    
    def get_user_info(self, credentials: Credentials) -> UserInfo:
        """Get user information from Google API"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            # Ensure required fields exist
            if not user_info.get('id') or not user_info.get('email'):
                raise ValueError("Incomplete user information received from Google")
            
            return UserInfo(
                id=user_info['id'],
                email=user_info['email'],
                name=user_info.get('name', user_info.get('email', 'Unknown')),
                picture=user_info.get('picture')
            )
        
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get user information")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )
            
            credentials.refresh(Request())
            
            return {
                "access_token": credentials.token,
                "expires_in": 3600,
                "credentials_json": credentials.to_json()
            }
        
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to refresh access token")
    
    def validate_credentials(self, credentials_json: str) -> bool:
        """Validate if credentials are still valid"""
        try:
            credentials = Credentials.from_authorized_user_info(json.loads(credentials_json))
            
            if credentials.expired:
                if credentials.refresh_token:
                    credentials.refresh(Request())
                    return True
                else:
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating credentials: {str(e)}")
            return False
    
    def get_credentials_from_json(self, credentials_json: str) -> Credentials:
        """Create Credentials object from JSON string"""
        try:
            credentials = Credentials.from_authorized_user_info(json.loads(credentials_json))
            
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            
            return credentials
        
        except Exception as e:
            logger.error(f"Error creating credentials from JSON: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid credentials")