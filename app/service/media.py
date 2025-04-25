from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ..models import Media, Post, User
from ..schemas.media import MediaCreate
from fastapi import HTTPException, status, UploadFile
import uuid
import os
# import aiofiles # No longer needed for local saving
from datetime import datetime
import cloudinary # Import cloudinary
import cloudinary.uploader # Import uploader
from ..config import settings # Import settings

# Configure Cloudinary using environment variables
print(f"Cloudinary Config - cloud_name: {settings.CLOUD_NAME}, api_key: {settings.API_KEY}")
cloudinary.config(
    cloud_name=settings.CLOUD_NAME,  
    api_key=settings.API_KEY,  
    api_secret=settings.API_SECRET  
)

# async def save_upload_file(file: UploadFile) -> str: # Replaced by upload_to_cloudinary
#     # Create uploads directory if it doesn't exist
#     if not os.path.exists(UPLOAD_DIR):
#         os.makedirs(UPLOAD_DIR)
    
#     # Generate unique filename
#     file_ext = os.path.splitext(file.filename)[1]
#     unique_filename = f"{uuid.uuid4()}{file_ext}"
#     file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
#     # Save file
#     async with aiofiles.open(file_path, 'wb') as out_file:
#         content = await file.read()
#         await out_file.write(content)
    
#     return file_path

async def upload_to_cloudinary(file: UploadFile) -> dict:
    """Upload file to Cloudinary and return resource info"""
    temp_file_path = None # Initialize to None
    try:
        # Create a temporary file path
        temp_file_path = f"temp_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        
        # Write the uploaded file content to the temporary file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Upload the temporary file to Cloudinary with folder parameter set to 'blog_api'
        result = cloudinary.uploader.upload(
            temp_file_path, 
            folder="blog_api",  # Store files in 'blog_api' folder
            resource_type="auto" # Automatically detect resource type (image, video, raw)
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload to Cloudinary: {str(e)}"
        )
    finally:
        # Ensure the temporary file is deleted even if upload fails
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


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

    # Upload file to Cloudinary instead of saving locally
    upload_result = await upload_to_cloudinary(file)
    
    # Create media record using Cloudinary URL
    media = Media(
        file_name=file.filename,
        file_path=upload_result['secure_url'], # Use secure_url from Cloudinary
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
    
    # Delete from Cloudinary if it's a Cloudinary URL
    if "cloudinary.com" in media.file_path:
        try:
            # Extract public_id from URL
            # Example URL: https://res.cloudinary.com/<cloud_name>/<resource_type>/upload/<version>/<folder>/<public_id>.<format>
            parts = media.file_path.split('/')
            public_id_with_ext = parts[-1]
            public_id = os.path.splitext(public_id_with_ext)[0]
            
            # Check if there's a folder structure in the URL
            # Cloudinary public_id includes the folder path if it exists
            folder_parts = parts[parts.index('upload') + 2:-1] # Get parts between 'upload' and the filename
            full_public_id = "/".join(folder_parts + [public_id]) if folder_parts else public_id

            # Determine resource type (needed for deletion of non-image/video types)
            resource_type = parts[parts.index('upload') - 1] if 'upload' in parts else 'image' # Default to image

            # Delete from Cloudinary
            delete_result = cloudinary.uploader.destroy(full_public_id, resource_type=resource_type)
            if delete_result.get("result") != "ok":
                 print(f"Warning: Cloudinary deletion might have failed for public_id {full_public_id}. Result: {delete_result}")

        except Exception as e:
            # Log error but don't prevent DB deletion
            print(f"Error deleting from Cloudinary (public_id likely '{full_public_id}'): {e}")
            
    # Delete file from filesystem (legacy cleanup, might not be needed if only Cloudinary is used)
    # try:
    #     if os.path.exists(media.file_path) and "cloudinary.com" not in media.file_path:
    #         os.remove(media.file_path)
    # except Exception as e:
    #     print(f"Error deleting local file: {e}")
    
    # Delete from database
    await db.delete(media)
    await db.commit()
    return {"status": "success", "message": "Media deleted"}