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
    
    SCOPES = [
        'https://www.googleapis.com/auth/forms.body',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
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
                include_granted_scopes='true',
                state=state
            )
            
            return auth_url
        
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate authorization URL")
    
    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Get user info
            user_info = self.get_user_info(credentials)
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_in": 3600,  # Default 1 hour
                "user_info": user_info,
                "credentials_json": credentials.to_json()
            }
        
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
    
    def get_user_info(self, credentials: Credentials) -> UserInfo:
        """Get user information from Google API"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            return UserInfo(
                id=user_info['id'],
                email=user_info['email'],
                name=user_info['name'],
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