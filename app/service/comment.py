from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Comment, User
from ..schemas.comment import CommentCreate, CommentUpdate

async def create_comment(
    db: AsyncSession,
    comment: CommentCreate,
    user_id: UUID
) -> Comment:
    db_comment = Comment(
        content=comment.content,
        post_id=comment.post_id,
        user_id=user_id,
        parent_id=comment.parent_id
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    
    # Get the comment with related entities to avoid async loading issues
    return await get_comment(db, db_comment.comment_id)

async def get_comments_by_post(
    db: AsyncSession,
    post_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Comment]:
    query = (
        select(Comment)
        .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user)
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().unique())

async def get_comment(
    db: AsyncSession,
    comment_id: UUID
) -> Optional[Comment]:
    query = (
        select(Comment)
        .where(Comment.comment_id == comment_id)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_comment(
    db: AsyncSession,
    db_comment: Comment,
    comment: CommentUpdate
) -> Comment:
    if comment.content is not None:
        db_comment.content = comment.content
    if comment.is_approved is not None:
        db_comment.is_approved = comment.is_approved
    
    await db.commit()
    await db.refresh(db_comment)
    
    # Get the comment with related entities to avoid async loading issues
    return await get_comment(db, db_comment.comment_id)

async def delete_comment(
    db: AsyncSession,
    db_comment: Comment
) -> None:
    await db.delete(db_comment)
    await db.commit()

async def get_comments_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Comment]:
    query = (
        select(Comment)
        .where(Comment.user_id == user_id)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user)
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().unique()) 