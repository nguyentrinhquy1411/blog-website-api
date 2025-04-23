from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..schemas.auth import LoginRequest, TokenResponse
from ..database.session import get_db
from ..service import authenticate_user
from ..utils.security.jwt import create_access_token, create_refresh_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.utils.security.jwt import verify_token
from app.schemas.auth import UserMeResponse, RefreshTokenRequest
from app.models.user import User
from typing import Annotated


router = APIRouter(prefix="/auth", tags=["auth"])

security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, data.email, data.password)
    access_token = create_access_token(user_id=str(user.user_id))
    refresh_token=create_refresh_token(user_id=str(user.user_id))
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get new access token using refresh token
    """
    try:
        # Verify the refresh token
        payload = verify_token(data.refresh_token, token_type="refresh")
        
        # Convert sub to UUID for query
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

@router.get("/me", response_model=UserMeResponse)
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    # token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
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
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
    