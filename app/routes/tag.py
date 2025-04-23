from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache

from ..database.session import get_db
from ..schemas.tag import TagOut, TagCreate, TagUpdate
from ..service import tag as tag_service
from ..dependencies import require_superuser

from typing import List
import uuid

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/", response_model=List[TagOut])
@cache(expire=60)
async def read_tags(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tags with pagination.
    """
    return await tag_service.get_tags(db, skip=skip, limit=limit)

@router.get("/{tag_id}", response_model=TagOut)
@cache(expire=60)
async def read_tag(
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific tag by ID.
    """
    return await tag_service.get_tag(db, tag_id)

@router.get("/slug/{slug}", response_model=TagOut)
@cache(expire=60)
async def read_tag_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific tag by slug.
    """
    return await tag_service.get_tag_by_slug(db, slug)

@router.post("/", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tag.
    """
    return await tag_service.create_tag(db, tag)

@router.put("/{tag_id}", response_model=TagOut)
async def update_tag(
    tag_id: uuid.UUID,
    tag: TagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a tag.
    """
    return await tag_service.update_tag(db, tag_id, tag)

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a tag.
    """
    await tag_service.delete_tag(db, tag_id)
    return None

@router.post("/{tag_id}/posts/{post_id}", status_code=status.HTTP_200_OK)
async def add_post_to_tag(
    tag_id: uuid.UUID,
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)  # Only superusers can manage post tags
):
    """
    Add a post to a tag (superuser only).
    """
    return await tag_service.add_post_to_tag(
        db=db,
        tag_id=tag_id,
        post_id=post_id
    )

@router.delete("/{tag_id}/posts/{post_id}", status_code=status.HTTP_200_OK)
async def remove_post_from_tag(
    tag_id: uuid.UUID,
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)  # Only superusers can manage post tags
):
    """
    Remove a post from a tag (superuser only).
    """
    return await tag_service.remove_post_from_tag(
        db=db,
        tag_id=tag_id,
        post_id=post_id
    ) 