from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache

from ..database.session import get_db
from ..schemas.post import PostOut, PostUpdate, PostCreate
from ..service import post as post_service
from ..dependencies import get_current_user, require_superuser
from ..models import User

from typing import List, Optional
from slugify import slugify
import uuid
from unidecode import unidecode

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("/", response_model=List[PostOut])
@cache(expire=60)
async def read_posts(
    skip: int = 0, 
    limit: int = 100,
    published: Optional[bool] = Query(True, description="Filter by published status"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter posts by category ID"),
    tag_id: Optional[uuid.UUID] = Query(None, description="Filter posts by tag ID"),
    author_id: Optional[uuid.UUID] = Query(None, description="Filter posts by author ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all posts with various filtering options.
    
    - For public consumption, `published=True` (default)
    - For admin dashboard, use `published=False` to see draft posts too
    - Can filter by category, tag, or author
    """
    # Note: Implement filtering by tag_id in the post_service
    
    return await post_service.get_posts(
        db, 
        skip=skip, 
        limit=limit, 
        published_only=published,
        category_id=category_id,
        author_id=author_id,
        tag_id=tag_id
    )

@router.get("/slug/{slug}", response_model=PostOut)
@cache(expire=60)
async def get_post_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a post by its slug (SEO-friendly URL)"""
    post = await post_service.get_post_by_slug(db, slug=slug)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post

@router.post("/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new post"""
    # Generate slug from title
    slug = slugify(unidecode(post.title))
    
    # Check if slug already exists
    existing_post = await post_service.get_post_by_slug(db, slug)
    if existing_post:
        # Add a unique suffix to make the slug unique
        import random
        import string
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        slug = f"{slug}-{random_suffix}"
        
    return await post_service.create_user_post(
        db=db, 
        post=post, 
        user_id=current_user.user_id,
        slug=slug
    )

@router.get("/{post_id}", response_model=PostOut)
@cache(expire=60)
async def read_post(
    post_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db)
):
    """Get a post by ID"""
    return await post_service.get_post(db, post_id=post_id)

@router.put("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: uuid.UUID,
    post: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a post
    
    Only the post author or superuser can update a post
    """
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
    current_user: User = Depends(get_current_user)
):
    """
    Delete a post
    
    Only the post author or superuser can delete a post
    """
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

@router.get("/user/{user_id}", response_model=List[PostOut])
@cache(expire=60)
async def get_posts_by_user(
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    published: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get posts by a specific user
    
    - If viewing your own posts as the author, you'll see both published and draft posts
    - If viewing as another user, you'll only see published posts
    """
    # If the current user is viewing their own posts or is a superuser,
    # they can see unpublished posts too
    include_unpublished = (current_user.user_id == user_id or current_user.is_superuser)
    
    # If published parameter is explicitly set, use it
    # Otherwise, decide based on the current user
    published_only = published if published is not None else not include_unpublished
    
    return await post_service.get_posts(
        db=db,
        skip=skip,
        limit=limit,
        published_only=published_only,
        author_id=user_id
    )

@router.get("/tag/{tag_id}", response_model=List[PostOut])
@cache(expire=60)
async def get_posts_by_tag(
    tag_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    published: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get all posts with a specific tag"""
    return await post_service.get_posts(
        db=db,
        skip=skip,
        limit=limit,
        published_only=published,
        tag_id=tag_id
    )

