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
    """Get root comments for a post with their replies loaded recursively"""
    query = (
        select(Comment)
        .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.replies).selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.replies).selectinload(Comment.replies).selectinload(Comment.user)
        )
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().unique())

async def get_comment(
    db: AsyncSession,
    comment_id: UUID
) -> Optional[Comment]:
    """Get a single comment with its replies loaded recursively"""
    query = (
        select(Comment)
        .where(Comment.comment_id == comment_id)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.replies).selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.replies).selectinload(Comment.replies).selectinload(Comment.user)
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
    """Get all comments made by a specific user with nested replies"""
    query = (
        select(Comment)
        .where(Comment.user_id == user_id)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.replies).selectinload(Comment.user),
            selectinload(Comment.post)
        )
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().unique())

async def reply_to_comment(
    db: AsyncSession,
    parent_comment_id: UUID,
    reply_content: str,
    post_id: UUID,
    user_id: UUID
) -> Comment:
    """Create a reply to an existing comment"""
    # Create the reply comment
    db_reply = Comment(
        content=reply_content,
        post_id=post_id,
        user_id=user_id,
        parent_id=parent_comment_id
    )
    
    db.add(db_reply)
    await db.commit()
    await db.refresh(db_reply)
    
    # Get the comment with related entities to avoid async loading issues
    return await get_comment(db, db_reply.comment_id)

async def get_replies_for_comment(
    db: AsyncSession,
    comment_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Comment]:
    """Get all direct replies for a specific comment"""
    query = (
        select(Comment)
        .where(Comment.parent_id == comment_id)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.replies).selectinload(Comment.user)
        )
        .order_by(Comment.created_at.asc())  # Show oldest replies first
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().unique())