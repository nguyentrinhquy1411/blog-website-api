from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ..models import Media, Post, User
from ..schemas.media import MediaCreate
from fastapi import HTTPException, status, UploadFile
import uuid
import os
import aiofiles
from datetime import datetime

UPLOAD_DIR = "uploads"

async def save_upload_file(file: UploadFile) -> str:
    # Create uploads directory if it doesn't exist
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    return file_path

async def create_media(
    db: AsyncSession,
    file: UploadFile,
    post_id: uuid.UUID = None,
    user_id: uuid.UUID = None
) -> Media:
    # Validate that either post_id or user_id is provided, but not both
    if post_id and user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot associate media with both post and user"
        )
    
    # Validate post_id if provided
    if post_id:
        result = await db.execute(select(Post).where(Post.post_id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
    
    # Validate user_id if provided
    if user_id:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    
    # Save file
    file_path = await save_upload_file(file)
    
    # Create media record
    media = Media(
        file_name=file.filename,
        file_path=file_path,
        mime_type=file.content_type,
        post_id=post_id,
        user_id=user_id
    )
    
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media

async def get_media(db: AsyncSession, media_id: uuid.UUID) -> Media:
    result = await db.execute(
        select(Media)
        .where(Media.media_id == media_id)
        .options(joinedload(Media.post), joinedload(Media.user))
    )
    media = result.unique().scalar_one_or_none()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    return media

async def get_media_list(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    post_id: uuid.UUID = None,
    user_id: uuid.UUID = None
) -> list[Media]:
    query = select(Media).options(joinedload(Media.post), joinedload(Media.user))
    
    if post_id:
        query = query.where(Media.post_id == post_id)
    if user_id:
        query = query.where(Media.user_id == user_id)
    
    result = await db.execute(query.offset(skip).limit(limit))
    return result.unique().scalars().all()

async def delete_media(db: AsyncSession, media_id: uuid.UUID):
    media = await get_media(db, media_id)
    
    # Delete file from filesystem
    try:
        if os.path.exists(media.file_path):
            os.remove(media.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete from database
    await db.delete(media)
    await db.commit()
    return {"status": "success", "message": "Media deleted"} 