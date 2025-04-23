from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache

from ..database.session import get_db
from ..schemas.category import CategoryOut, CategoryCreate, CategoryUpdate
from ..service import category as category_service
from ..dependencies import require_superuser

from typing import List, Optional
import uuid

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/", response_model=List[CategoryOut])
@cache(expire=60)
async def read_categories(
    skip: int = 0, 
    limit: int = 100,
    with_post_count: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all categories.
    
    Optional params:
    - with_post_count: If true, include count of posts in each category
    """
    categories = await category_service.get_categories(
        db, 
        skip=skip, 
        limit=limit,
        with_post_count=with_post_count
    )
    
    return categories

@router.get("/{category_id}", response_model=CategoryOut)
@cache(expire=60)
async def read_category(
    category_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by ID"""
    return await category_service.get_category(db, category_id=category_id)

@router.get("/slug/{slug}", response_model=CategoryOut)
@cache(expire=60)
async def read_category_by_slug(
    slug: str, 
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by slug"""
    category = await category_service.get_category_by_slug(db, slug=slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category

@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)  # Only superusers can create categories
):
    """Create a new category (superuser only)"""
    return await category_service.create_category(db=db, category=category)

@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: uuid.UUID,
    category: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)  # Only superusers can update categories
):
    """Update a category (superuser only)"""
    return await category_service.update_category(
        db=db, 
        category_id=category_id, 
        category=category
    )

@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)  # Only superusers can delete categories
):
    """Delete a category (superuser only)"""
    return await category_service.delete_category(db=db, category_id=category_id)

@router.post("/{category_id}/posts/{post_id}", status_code=status.HTTP_200_OK)
async def add_post_to_category(
    category_id: uuid.UUID,
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)  # Only superusers can manage post categories
):
    """Add a post to a category (superuser only)"""
    return await category_service.add_post_to_category(
        db=db, 
        post_id=post_id, 
        category_id=category_id
    )

@router.delete("/{category_id}/posts/{post_id}", status_code=status.HTTP_200_OK)
async def remove_post_from_category(
    category_id: uuid.UUID,
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_superuser)  # Only superusers can manage post categories
):
    """Remove a post from a category (superuser only)"""
    return await category_service.remove_post_from_category(
        db=db, 
        post_id=post_id, 
        category_id=category_id
    ) 