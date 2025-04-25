from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.session import get_db
from ..schemas.user import UserCreate, UserOut, UserUpdate
from ..schemas.post import PostOut
from ..service import user as user_service
from ..service import post as post_service
from ..models import User
from ..dependencies import require_superuser, get_current_user
from typing import List
import uuid
from fastapi_cache.decorator import cache
from slugify import slugify
from unidecode import unidecode

router = APIRouter(prefix="/users", tags=["users"])

security = HTTPBearer()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    db_user = await user_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await user_service.create_user(db=db, user=user)

@router.get("/", response_model=List[UserOut])
@cache(expire=60)
async def read_users(
        db: AsyncSession = Depends(get_db),
        skip: int = 0, 
        limit: int = 100, 
        current_user: User = Depends(require_superuser)
    ):
    """Get all users (superuser only)"""
    try:
        users = await user_service.get_users(db, skip=skip, limit=limit)
    except HTTPException as http_exc:
        raise http_exc
    return users

@router.get("/me", response_model=UserOut)
async def read_user_me(
    current_user: User = Depends(get_current_user)
):
    """Get current logged in user profile"""
    return current_user

@router.get("/{user_id}", response_model=UserOut)
@cache(expire=60)
async def get_user_by_id(
    user_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID"""
    return await user_service.get_user(db, user_id=user_id)

@router.patch("/me", response_model=UserOut)
async def update_current_user(
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the current user's profile"""
    return await user_service.update_user(db=db, user_id=current_user.user_id, user=user)

@router.patch("/{user_id}", response_model=UserOut)
async def update_user_by_id(
    user_id: uuid.UUID,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a user (can only update your own profile unless superuser)"""
    if user_id != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update other users"
        )
    return await user_service.update_user(db=db, user_id=user_id, user=user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a user (can only delete your own account unless superuser)"""
    if user_id != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete other users"
        )
    await user_service.delete_user(db=db, user_id=user_id)
    return None
