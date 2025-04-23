from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache
from typing import List, Optional
import uuid

from ..database.session import get_db
from ..schemas.media import MediaOut
from ..service import media as media_service
from ..auth.dependencies import get_current_user
from ..dependencies import require_superuser
from ..models import User

router = APIRouter(prefix="/media", tags=["media"])

@router.post("/upload", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    post_id: Optional[uuid.UUID] = Form(None),
    user_id: Optional[uuid.UUID] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file and associate it with a post or user.
    Only superusers can upload for any user, regular users can only upload for themselves.
    """
    # Check permissions
    if user_id and user_id != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only upload media for yourself"
        )
    
    return await media_service.create_media(
        db=db,
        file=file,
        post_id=post_id,
        user_id=user_id
    )

@router.get("/{media_id}", response_model=MediaOut)
@cache(expire=60)
async def get_media_by_id(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get media by ID.
    """
    return await media_service.get_media(db, media_id=media_id)

@router.get("/", response_model=List[MediaOut])
@cache(expire=60)
async def list_media(
    skip: int = 0,
    limit: int = 100,
    post_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List media with optional filtering by post or user.
    """
    return await media_service.get_media_list(
        db,
        skip=skip,
        limit=limit,
        post_id=post_id,
        user_id=user_id
    )

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media_by_id(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete media by ID.
    Only superusers or the owner can delete media.
    """
    # Get media first to check ownership
    media = await media_service.get_media(db, media_id)
    
    # Check permissions
    if media.user_id != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await media_service.delete_media(db, media_id)
    return None 