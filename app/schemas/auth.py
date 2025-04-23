from pydantic import BaseModel
from uuid import UUID

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserMeResponse(BaseModel):
    user_id: UUID
    email: str
    is_active: bool

    class Config:
        from_attributes = True