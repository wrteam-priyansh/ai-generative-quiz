from pydantic import BaseModel
from typing import Optional

class GoogleAuthURL(BaseModel):
    auth_url: str

class GoogleAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None

class UserInfo(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user_info: UserInfo