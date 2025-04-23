from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.session import get_db
from ..schemas.user import UserCreate, UserOut, UserUpdate
from ..schemas.post import PostCreate, PostOut
from ..service import user as user_service
from ..service import post as post_service
from app.utils.security.jwt import verify_token
from ..models import User
from ..dependencies import require_superuser, get_current_user
from typing import List, Annotated
import uuid
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/users", tags=["users"])

security = HTTPBearer()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await user_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await user_service.create_user(db=db, user=user)

@router.get("/", response_model=List[UserOut])
@cache(expire=60)
async def read_users(
        # credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
        db: AsyncSession = Depends(get_db),
        skip: int = 0, 
        limit: int = 100, 
        current_user: User = Depends(require_superuser)

    ):
    try:  
        # token_data = credentials.credentials
        # verify_token(token_data)
        # print("Received credentials: ", credentials)
        users = await user_service.get_users(db, skip=skip, limit=limit)
    except HTTPException as http_exc:
        raise http_exc
    return users

@router.get("/me", response_model=UserOut)
async def read_user_me(
    current_user = Depends(get_current_user)
):
    """
    Get current logged in user.
    """
    return current_user

@router.get("/{user_id}", response_model=UserOut)
@cache(expire=60)
async def get_user_by_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db)
):
    try:  
        token_data = credentials.credentials
        verify_token(token_data)
    except HTTPException as http_exc:
        raise http_exc
    return await user_service.get_user(db, user_id=user_id)

@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await user_service.update_user(db=db, user_id=user_id, user=user)

@router.post("/{user_id}/posts/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post_for_user(
    user_id: uuid.UUID, 
    post: PostCreate, 
    db: AsyncSession = Depends(get_db)
):
    return await post_service.create_user_post(db=db, post=post, user_id=user_id)

@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)
):
    """
    Update a user (superuser only).
    """
    return await user_service.update_user(db=db, user_id=user_id, user=user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)
):
    """
    Delete a user (superuser only).
    """
    await user_service.delete_user(db=db, user_id=user_id)
    return None
