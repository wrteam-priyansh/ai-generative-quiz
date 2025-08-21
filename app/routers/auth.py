from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from typing import Optional
import logging
import urllib.parse

from app.services.auth_service import GoogleAuthService
from app.models.auth import GoogleAuthURL, TokenResponse
from app.models.response import success_response, error_response
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

auth_service = GoogleAuthService()

@router.get("/google/authorize", responses={
    200: {
        "description": "Google OAuth authorization URL generated successfully",
        "content": {
            "application/json": {
                "examples": {
                    "auth_url_success": {
                        "summary": "Successful Authorization URL Generation",
                        "description": "Example response when generating Google OAuth URL",
                        "value": {
                            "error": False,
                            "data": {
                                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=your-client-id&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fcallback&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fforms+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&access_type=offline&state=optional-state-parameter"
                            },
                            "message": "Authorization URL generated successfully"
                        }
                    }
                }
            }
        }
    }
})
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

@router.get("/callback", responses={
    302: {
        "description": "Redirect to frontend after successful OAuth",
        "content": {
            "text/html": {
                "examples": {
                    "redirect_success": {
                        "summary": "Successful OAuth Redirect",
                        "description": "Redirects to frontend with authentication success",
                        "value": "Redirecting to frontend..."
                    }
                }
            }
        }
    }
})
async def google_auth_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """Handle Google OAuth callback and redirect to frontend"""
    
    # Handle OAuth errors from Google
    if error:
        logger.error(f"OAuth error from Google: {error}")
        return _redirect_to_frontend(state, "error", f"OAuth error: {error}")
    
    try:
        logger.info("Processing OAuth callback...")
        
        # Exchange code for tokens
        token_data = auth_service.exchange_code_for_tokens(code)
        
        logger.info(f"OAuth successful for user: {token_data['user_info'].email}")
        
        # Instead of returning JSON, redirect to frontend with success
        return _redirect_to_frontend(
            state, 
            "success",
            None,
            {
                "user_email": token_data["user_info"].email,
                "user_name": token_data["user_info"].name,
                "credentials": token_data["credentials_json"]
            }
        )
    
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {str(e)}")
        return _redirect_to_frontend(state, "error", "Failed to complete authentication")


def _redirect_to_frontend(
    state: Optional[str] = None, 
    auth_status: str = "success", 
    error_message: Optional[str] = None,
    auth_data: Optional[dict] = None
) -> RedirectResponse:
    """
    Redirect to frontend with authentication results
    
    Args:
        state: The state parameter from OAuth (contains frontend URL)
        auth_status: 'success' or 'error'
        error_message: Error message if auth_status is 'error'
        auth_data: Authentication data if successful
    """
    try:
        # Default frontend URL
        default_frontend_url = "http://localhost:3000/generate"
        
        # Extract clean base URL from state parameter
        base_url = default_frontend_url
        if state:
            try:
                # URL decode the state parameter
                decoded_state = urllib.parse.unquote(state)
                logger.debug(f"Decoded state parameter: {decoded_state}")
                
                # Validate that it's a safe frontend URL
                allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
                if any(decoded_state.startswith(origin) for origin in allowed_origins):
                    # Extract just the base URL (remove any existing query parameters)
                    if '?' in decoded_state:
                        base_url = decoded_state.split('?')[0]
                    elif '&' in decoded_state:
                        # Handle malformed URLs where & appears without ?
                        base_url = decoded_state.split('&')[0]
                    else:
                        base_url = decoded_state
                else:
                    logger.warning(f"Invalid state URL, using default: {decoded_state}")
                    base_url = default_frontend_url
            except Exception as e:
                logger.error(f"Error parsing state parameter: {str(e)}")
                base_url = default_frontend_url
        
        # Build query parameters
        query_params = [f"auth={auth_status}"]
        
        # Add error message if there's an error
        if error_message and auth_status == "error":
            encoded_error = urllib.parse.quote(error_message)
            query_params.append(f"error={encoded_error}")
        
        # Add user data if successful 
        if auth_data and auth_status == "success":
            if auth_data.get("user_email"):
                query_params.append(f"user_email={urllib.parse.quote(auth_data['user_email'])}")
            if auth_data.get("user_name"):
                query_params.append(f"user_name={urllib.parse.quote(auth_data['user_name'])}")
            
            # Add credentials as base64 encoded JSON for the frontend
            if auth_data.get("credentials"):
                import base64
                import json
                try:
                    # Base64 encode the credentials JSON for URL safety
                    credentials_b64 = base64.b64encode(
                        auth_data["credentials"].encode('utf-8')
                    ).decode('ascii')
                    query_params.append(f"credentials={credentials_b64}")
                    logger.debug("Added encoded credentials to redirect URL")
                except Exception as e:
                    logger.error(f"Error encoding credentials: {str(e)}")
                    # Continue without credentials - frontend can call auth endpoints
        
        # Construct final URL with clean query string
        redirect_url = f"{base_url}?{'&'.join(query_params)}"
        
        logger.info(f"Redirecting to frontend: {redirect_url}")
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Error creating redirect response: {str(e)}")
        # Fallback to simple redirect
        fallback_url = f"{default_frontend_url}?auth=error&error=redirect_failed"
        return RedirectResponse(url=fallback_url, status_code=302)

@router.post("/refresh", responses={
    200: {
        "description": "Access token refreshed successfully",
        "content": {
            "application/json": {
                "examples": {
                    "refresh_success": {
                        "summary": "Successful Token Refresh",
                        "description": "Example response when access token is refreshed",
                        "value": {
                            "error": False,
                            "data": {
                                "access_token": "ya29.a0AfH6SMC_new_token...",
                                "expires_in": 3599
                            },
                            "message": "Token refreshed successfully"
                        }
                    }
                }
            }
        }
    }
})
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

@router.post("/validate", responses={
    200: {
        "description": "Credentials validation completed",
        "content": {
            "application/json": {
                "examples": {
                    "validation_success": {
                        "summary": "Valid Credentials",
                        "description": "Example response when credentials are valid",
                        "value": {
                            "error": False,
                            "data": {
                                "valid": True,
                                "status": "valid"
                            },
                            "message": "Credentials validated successfully"
                        }
                    },
                    "validation_failure": {
                        "summary": "Invalid Credentials",
                        "description": "Example response when credentials are invalid",
                        "value": {
                            "error": False,
                            "data": {
                                "valid": False,
                                "status": "invalid"
                            },
                            "message": "Credentials validated successfully"
                        }
                    }
                }
            }
        }
    }
})
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

@router.get("/debug", responses={
    200: {
        "description": "OAuth configuration debug information",
        "content": {
            "application/json": {
                "examples": {
                    "debug_info": {
                        "summary": "OAuth Debug Information",
                        "description": "Configuration details for debugging OAuth issues",
                        "value": {
                            "error": False,
                            "data": {
                                "redirect_uri": "http://localhost:8000/auth/callback",
                                "client_id_configured": True,
                                "client_secret_configured": True,
                                "scopes": ["openid", "https://www.googleapis.com/auth/userinfo.email", "..."],
                                "oauth_urls": {
                                    "authorization": "/auth/google/authorize",
                                    "callback": "/auth/callback"
                                }
                            },
                            "message": "OAuth debug information retrieved"
                        }
                    }
                }
            }
        }
    }
})
async def debug_oauth_config():
    """Get OAuth configuration for debugging (development only)"""
    try:
        return success_response({
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "client_id_configured": bool(settings.GOOGLE_CLIENT_ID),
            "client_secret_configured": bool(settings.GOOGLE_CLIENT_SECRET),
            "client_id_preview": settings.GOOGLE_CLIENT_ID[:20] + "..." if settings.GOOGLE_CLIENT_ID else None,
            "scopes": auth_service.SCOPES,
            "oauth_urls": {
                "authorization": "/auth/google/authorize",
                "callback": "/auth/callback"
            },
            "common_issues": [
                "Ensure redirect URI matches exactly in Google Console",
                "Check that client ID and secret are correct",
                "Verify OAuth consent screen is configured",
                "Authorization codes expire in ~10 minutes",
                "Codes can only be used once"
            ]
        }, "OAuth debug information retrieved")
    except Exception as e:
        logger.error(f"Error getting debug info: {str(e)}")
        return error_response("Failed to get debug information")

@router.post("/exchange-session", responses={
    200: {
        "description": "Get full authentication data for authenticated user",
        "content": {
            "application/json": {
                "examples": {
                    "session_data": {
                        "summary": "Full Authentication Data",
                        "description": "Complete authentication data including credentials",
                        "value": {
                            "error": False,
                            "data": {
                                "access_token": "ya29.a0AfH6SMC...",
                                "refresh_token": "1//04vOK...",
                                "expires_in": 3599,
                                "user_info": {
                                    "id": "123456789",
                                    "email": "user@example.com",
                                    "name": "John Doe",
                                    "picture": "https://lh3.googleusercontent.com/a/..."
                                },
                                "credentials_json": "{\"token\": \"ya29.a0AfH6SMC...\"}"
                            },
                            "message": "Authentication data retrieved successfully"
                        }
                    }
                }
            }
        }
    }
})
async def exchange_session_for_tokens(user_email: str):
    """
    Exchange user email (from redirect) for full authentication data
    This is called by frontend after OAuth redirect to get credentials
    """
    try:
        # This is a simplified approach - in production, you'd want to store 
        # the auth data temporarily and use a session token instead of email
        logger.info(f"Frontend requesting auth data for: {user_email}")
        
        # For now, return a message indicating the frontend should handle auth differently
        # In a production app, you would store the auth data in a temporary cache/session
        return success_response({
            "message": "Use the credentials from the redirect URL or implement session storage",
            "user_email": user_email,
            "note": "This endpoint would typically retrieve stored auth data from a session cache"
        }, "Session exchange information")
        
    except Exception as e:
        logger.error(f"Error exchanging session: {str(e)}")
        return error_response("Failed to exchange session data")