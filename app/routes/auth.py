from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..schemas.auth import LoginRequest, TokenResponse, UserMeResponse, RefreshTokenRequest
from ..schemas.user import UserOut
from ..database.session import get_db
from ..service import authenticate_user
from ..utils.security.jwt import create_access_token, create_refresh_token, verify_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ..models.user import User
from typing import Annotated


router = APIRouter(prefix="/auth", tags=["auth"])

security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Login with email and password"""
    user = await authenticate_user(db, data.email, data.password)
    access_token = create_access_token(user_id=str(user.user_id))
    refresh_token = create_refresh_token(user_id=str(user.user_id))
    
    # Set refresh token as a secure HTTP-only cookie (helpful for automatic refreshes)
    # response.set_cookie(
    #     key="refresh_token",
    #     value=refresh_token,
    #     httponly=True,
    #     secure=True,  # Set to True in production with HTTPS
    #     samesite="lax",
    #     max_age=30 * 24 * 60 * 60  # 30 days in seconds
    # )
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get new access token using refresh token"""
    try:
        # Verify the refresh token
        payload = verify_token(data.refresh_token, token_type="refresh")
        
        # Get user ID from token payload
        user_id = payload.sub
        
        # Get user from database using async query
        query = select(User).where(User.user_id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Create new tokens
        new_access_token = create_access_token(user_id=str(user.user_id))
        new_refresh_token = create_refresh_token(user_id=str(user.user_id))
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/me", response_model=UserOut)
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user information"""
    try:
        payload = verify_token(credentials.credentials)
        
        # Get user ID from token payload
        user_id = payload.sub
        
        # Get user from database using async query
        query = select(User).where(User.user_id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
            
        return user
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
