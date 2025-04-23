import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from pydantic import BaseModel
from ...config import settings as config

class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int  # timestamp
    type: str

def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Tạo JWT token từ user ID"""
    expire_minutes = int(config.ACCESS_TOKEN_EXPIRE_MINUTES)  # Convert sang int
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=expire_minutes))
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access" 
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

def create_refresh_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    expire_days = int(config.REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.utcnow() + (expires_delta or timedelta(days=expire_days))
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"  # Important to distinguish from access token
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> TokenPayload:
    """Xác thực JWT token"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        token_data = TokenPayload(**payload)
        
        if token_data.type != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type: expected {token_type}",
            )
            
        return token_data
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )