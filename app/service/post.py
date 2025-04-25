from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from ..models import Post, Category, Tag
from ..schemas import PostCreate, PostUpdate
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime

async def get_post(db: AsyncSession, post_id: UUID):
    result = await db.execute(
        select(Post)
        .where(Post.post_id == post_id)
        .options(
            selectinload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.tags),
            selectinload(Post.comments),
            selectinload(Post.media)
        )
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post

async def get_posts(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    published_only: bool = True,
    category_id: UUID = None,
    author_id: UUID = None,
    tag_id: UUID = None
):
    query = select(Post).options(
        selectinload(Post.author),
        selectinload(Post.categories),
        selectinload(Post.tags),
        selectinload(Post.media)
    )
    
    if published_only:
        query = query.where(Post.is_published == True)
    
    # Filter by category if provided
    if category_id:
        query = query.join(Post.categories).where(Category.category_id == category_id)
    
    # Filter by author if provided
    if author_id:
        query = query.where(Post.author_id == author_id)
    
    # Filter by tag if provided
    if tag_id:
        query = query.join(Post.tags).where(Tag.tag_id == tag_id)
    
    # Order by created date, newest first
    query = query.order_by(Post.created_at.desc())
    
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def get_post_by_slug(db: AsyncSession, slug: str):
    result = await db.execute(
        select(Post)
        .where(Post.slug == slug)
        .options(
            selectinload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.tags),
            selectinload(Post.comments),
            selectinload(Post.media)
        )
    )
    return result.scalars().first()


async def create_user_post(
    db: AsyncSession, 
    post: PostCreate, 
    user_id: UUID,
    slug: str
):
    db_post = Post(
        **post.model_dump(exclude={"category_ids", "tag_ids"}),
        author_id=user_id,
        slug=slug
    )
    
    # Add categories if provided
    if post.category_ids:
        for category_id in post.category_ids:
            result = await db.execute(
                select(Category).where(Category.category_id == category_id)
            )
            category = result.scalars().first()
            if category:
                db_post.categories.append(category)
    
    # Add tags if provided
    if post.tag_ids:
        for tag_id in post.tag_ids:
            result = await db.execute(
                select(Tag).where(Tag.tag_id == tag_id)
            )
            tag = result.scalars().first()
            if tag:
                db_post.tags.append(tag)
    
    db.add(db_post)
    await db.commit()
    
    # Reload the post with all relationships
    result = await db.execute(
        select(Post)
        .where(Post.post_id == db_post.post_id)
        .options(
            joinedload(Post.author),
            joinedload(Post.categories),
            joinedload(Post.tags),
            joinedload(Post.media)
        )
    )
    return result.unique().scalar_one()

async def update_post(
    db: AsyncSession, 
    post_id: UUID, 
    post: PostUpdate
):
    db_post = await get_post(db, post_id)
    
    update_data = post.model_dump(exclude_unset=True, exclude={"category_ids", "tag_ids"})
    
    # Auto-set published_at if publishing
    if update_data.get('is_published') and not db_post.published_at:
        update_data['published_at'] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_post, field, value)
    
    # Update categories if provided
    if hasattr(post, "category_ids") and post.category_ids is not None:
        # Clear existing categories
        db_post.categories = []
        
        # Add new categories
        for category_id in post.category_ids:
            result = await db.execute(
                select(Category).where(Category.category_id == category_id)
            )
            category = result.scalars().first()
            if category:
                db_post.categories.append(category)

    # Update tags if provided
    if hasattr(post, "tag_ids") and post.tag_ids is not None:
        # Clear existing tags
        db_post.tags = []
        
        # Add new tags
        for tag_id in post.tag_ids:
            result = await db.execute(
                select(Tag).where(Tag.tag_id == tag_id)
            )
            tag = result.scalars().first()
            if tag:
                db_post.tags.append(tag)
    
    await db.commit()
    
    # Reload the post with all relationships
    result = await db.execute(
        select(Post)
        .where(Post.post_id == post_id)
        .options(
            joinedload(Post.author),
            joinedload(Post.categories),
            joinedload(Post.tags),
            joinedload(Post.media)
        )
    )
    return result.unique().scalar_one()

async def delete_post(db: AsyncSession, post_id: UUID):
    db_post = await get_post(db, post_id)
    await db.delete(db_post)
    await db.commit()
    return {"status": "success", "message": "Post deleted"}

async def get_posts_by_category(
    db: AsyncSession,
    category_id: UUID,
    skip: int = 0,
    limit: int = 100,
    published_only: bool = True
):
    """Get all posts in a specific category"""
    return await get_posts(
        db=db,
        skip=skip,
        limit=limit,
        published_only=published_only,
        category_id=category_id
    )
