from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache

from app.routes.auth import get_current_user
from ..database.session import get_db
from ..schemas.post import PostOut, PostUpdate, PostCreate
from ..service import post as post_service
from ..dependencies import require_superuser

from typing import List, Optional
from slugify import slugify
import uuid
from unidecode import unidecode

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("/", response_model=List[PostOut])
@cache(expire=60)  # Cache trong 60 giây
async def read_posts(
    skip: int = 0, 
    limit: int = 100,
    published: bool = True,
    category_id: Optional[uuid.UUID] = Query(None, description="Filter posts by category ID"),
    db: AsyncSession = Depends(get_db)
):
    return await post_service.get_posts(
        db, 
        skip=skip, 
        limit=limit, 
        published_only=published,
        category_id=category_id
    )

@router.post("/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Generate slug from title
    slug = slugify(unidecode(post.title))
    return await post_service.create_user_post(
        db=db, 
        post=post, 
        user_id=current_user.user_id,
        slug=slug
    )

@router.get("/{post_id}", response_model=PostOut)
@cache(expire=60)
async def read_post(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await post_service.get_post(db, post_id=post_id)

@router.put("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: uuid.UUID,
    post: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Check if user is author or superuser
    db_post = await post_service.get_post(db, post_id)
    if db_post.author_id != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return await post_service.update_post(db=db, post_id=post_id, post=post)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Check if user is author or superuser
    db_post = await post_service.get_post(db, post_id)
    if db_post.author_id != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    await post_service.delete_post(db=db, post_id=post_id)
    return None

@router.get("/category/{category_id}", response_model=List[PostOut])
@cache(expire=60)
async def get_posts_by_category(
    category_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    published: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get all posts in a specific category"""
    return await post_service.get_posts_by_category(
        db=db, 
        category_id=category_id,
        skip=skip,
        limit=limit,
        published_only=published
    )

