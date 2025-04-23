from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import Category, Post
from ..schemas import CategoryCreate, CategoryUpdate
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from slugify import slugify
from unidecode import unidecode

async def get_category(db: AsyncSession, category_id: UUID):
    result = await db.execute(
        select(Category)
        .where(Category.category_id == category_id)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category

async def get_category_by_slug(db: AsyncSession, slug: str):
    result = await db.execute(
        select(Category)
        .where(Category.slug == slug)
    )
    return result.scalars().first()

async def get_categories(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    with_post_count: bool = False
):
    if with_post_count:
        # Query with post count
        from sqlalchemy import func, distinct
        result = await db.execute(
            select(
                Category,
                func.count(distinct(Post.post_id)).label("posts_count")
            )
            .outerjoin(Category.posts)
            .group_by(Category.category_id)
            .offset(skip)
            .limit(limit)
        )
        # Process the result to include post count
        categories_with_count = []
        for cat, count in result:
            setattr(cat, "posts_count", count)
            categories_with_count.append(cat)
        return categories_with_count
    else:
        # Simple query without post count
        result = await db.execute(
            select(Category)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

async def create_category(db: AsyncSession, category: CategoryCreate):

    slug = unidecode(slugify(category.name))    
    
    existing_slug = await get_category_by_slug(db, slug=slug)
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this slug already exists"
        )
    
    db_category = Category(
        name=category.name,
        description=category.description,
        slug=slug
    )
    
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

async def update_category(
    db: AsyncSession, 
    category_id: UUID, 
    category: CategoryUpdate
):
    db_category = await get_category(db, category_id)
    
    update_data = category.model_dump(exclude_unset=True)
    
    # If slug is being updated, check if the new slug exists
    if "slug" in update_data and update_data["slug"] != db_category.slug:
        existing_slug = await get_category_by_slug(db, slug=update_data["slug"])
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this slug already exists"
            )
    
    # Update fields
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db_category.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_category)
    return db_category

async def delete_category(db: AsyncSession, category_id: UUID):
    db_category = await get_category(db, category_id)
    
    await db.delete(db_category)
    await db.commit()
    return {"status": "success", "message": "Category deleted"}

async def add_post_to_category(
    db: AsyncSession,
    post_id: UUID,
    category_id: UUID
):
    # Check if post exists
    from ..service.post import get_post
    post = await get_post(db, post_id)
    
    # Check if category exists
    category = await get_category(db, category_id)
    
    # Check if relationship already exists
    if category in post.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is already in this category"
        )
    
    # Add relationship
    post.categories.append(category)
    await db.commit()
    return {"status": "success", "message": "Post added to category"}

async def remove_post_from_category(
    db: AsyncSession,
    post_id: UUID,
    category_id: UUID
):
    # Check if post exists
    from ..service.post import get_post
    post = await get_post(db, post_id)
    
    # Check if category exists
    category = await get_category(db, category_id)
    
    # Check if relationship exists
    if category not in post.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is not in this category"
        )
    
    # Remove relationship
    post.categories.remove(category)
    await db.commit()
    return {"status": "success", "message": "Post removed from category"} 