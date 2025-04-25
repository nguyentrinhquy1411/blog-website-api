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

# Helper function to convert empty strings to None for Optional UUIDs from Forms
async def empty_str_to_none(value: Optional[str] = Form(None)) -> Optional[uuid.UUID]:
    if value == "":
        return None
    elif value is not None:
        return uuid.UUID(value)
    # Pydantic will handle the UUID conversion if it's not None or ""
    return None

router = APIRouter(prefix="/media", tags=["media"])

@router.post("/upload", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    # Use the helper dependency for optional UUIDs from form data
    post_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file and associate it with a post or user.
    Only superusers can upload for any user, regular users can only upload for themselves.
    """
    post_uuid = await empty_str_to_none(post_id)
    user_uuid = await empty_str_to_none(user_id)
    
    # Check permissions
    if user_uuid and user_uuid != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only upload media for yourself"
        )
    
    # If post_id is provided, check if the user has permission to add media to this post
    if post_uuid:
        from ..service import post as post_service
        post = await post_service.get_post(db, post_uuid)
        if post.author_id != current_user.user_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only upload media for your own posts"
            )
    
    return await media_service.create_media(
        db=db,
        file=file,
        post_id=post_uuid,
        user_id=user_uuid
    )

@router.post("/profile-image", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a profile image for the current logged-in user.
    This will replace any existing profile image and update the user's profile_picture field.
    """
    # Check if user already has a profile image, if so, delete it
    existing_media = await media_service.get_media_list(
        db=db,
        user_id=current_user.user_id
    )
    
    for media in existing_media:
        # Optionally, you could check if the media is actually used as a profile picture
        # For now, we'll just delete all user media to simplify
        await media_service.delete_media(db, media.media_id)
    
    # Upload new profile image
    media = await media_service.create_media(
        db=db,
        file=file,
        user_id=current_user.user_id
    )
    
    # Update user's profile_picture field
    from ..service import user as user_service
    from ..schemas.user import UserUpdate
    
    user_update = UserUpdate(profile_picture=media.file_path)
    await user_service.update_user(db, current_user.user_id, user_update)
    
    return media

@router.post("/post-image/{post_id}", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def upload_post_image(
    post_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image for a specific post.
    Only the post author or superusers can upload images for a post.
    """
    # Check if the post exists and belongs to the current user
    from ..service import post as post_service
    post = await post_service.get_post(db, post_id)
    
    # Check permissions
    if post.author_id != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only upload images for your own posts"
        )
    
    # Upload new post image
    return await media_service.create_media(
        db=db,
        file=file,
        post_id=post_id
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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