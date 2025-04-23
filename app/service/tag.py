from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import Tag, Post
from ..schemas import TagCreate, TagUpdate, TagOut
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from slugify import slugify


async def get_tag(db: AsyncSession, tag_id: UUID) -> Tag:
    result = await db.execute(
        select(Tag)
        .where(Tag.tag_id == tag_id)
        .options(selectinload(Tag.posts))
    )
    tag = result.scalars().first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

async def get_tag_by_slug(db: AsyncSession, slug: str) -> Tag:
    result = await db.execute(
        select(Tag)
        .where(Tag.slug == slug)
        .options(selectinload(Tag.posts))
    )
    tag = result.scalars().first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

async def get_tags(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
):
    result = await db.execute(
        select(Tag)
        .options(selectinload(Tag.posts))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_tag(db: AsyncSession, tag: TagCreate) -> Tag:
    # Check if tag with same name or slug already exists
    existing_tag = await db.execute(
        select(Tag)
        .where(
            (Tag.name == tag.name) | 
            (Tag.slug == slugify(tag.name))
        )
    )
    existing_tag = existing_tag.scalars().first()
    
    if existing_tag:
        if existing_tag.name == tag.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this slug already exists"
            )
    
    # Create tag
    db_tag = Tag(
        name=tag.name,
        slug=slugify(tag.name)
    )
    
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag

async def update_tag(db: AsyncSession, tag_id: UUID, tag: TagUpdate) -> Tag:
    db_tag = await get_tag(db, tag_id)
    
    update_data = tag.model_dump(exclude_unset=True)
    
    # If name is being updated, update slug as well
    if "name" in update_data:
        update_data["slug"] = slugify(update_data["name"])
    
    for field, value in update_data.items():
        setattr(db_tag, field, value)
    
    db_tag.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_tag)
    return db_tag

async def delete_tag(db: AsyncSession, tag_id: UUID) -> None:
    db_tag = await get_tag(db, tag_id)
    await db.delete(db_tag)
    await db.commit()

async def add_post_to_tag(
    db: AsyncSession,
    tag_id: UUID,
    post_id: UUID
):
    # Check if tag exists and load its posts
    tag = await get_tag(db, tag_id)
    
    # Check if post exists
    from ..service.post import get_post
    post = await get_post(db, post_id)
    
    # Check if relationship already exists
    if post in tag.posts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is already tagged with this tag"
        )
    
    # Add relationship
    tag.posts.append(post)
    await db.commit()
    await db.refresh(tag)
    return {"status": "success", "message": "Post added to tag"}

async def remove_post_from_tag(
    db: AsyncSession,
    tag_id: UUID,
    post_id: UUID
):
    # Check if tag exists and load its posts
    tag = await get_tag(db, tag_id)
    
    # Check if post exists
    from ..service.post import get_post
    post = await get_post(db, post_id)
    
    # Check if relationship exists
    if post not in tag.posts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is not tagged with this tag"
        )
    
    # Remove relationship
    tag.posts.remove(post)
    await db.commit()
    await db.refresh(tag)
    return {"status": "success", "message": "Post removed from tag"}
