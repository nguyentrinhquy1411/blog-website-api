from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas.comment import CommentCreate, CommentUpdate, CommentOut, CommentReply
from ..service import comment as comment_service
from ..auth.dependencies import get_current_user

router = APIRouter(
    prefix="/comments",
    tags=["comments"]
)

@router.post("/", response_model=CommentOut)
async def create_comment(
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new comment for a post.
    Can be a reply to another comment by providing parent_id.
    """
    try:
        return await comment_service.create_comment(db, comment, current_user.user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create comment: {str(e)}"
        )

@router.post("/{comment_id}/reply", response_model=CommentOut)
async def reply_to_comment(
    comment_id: UUID,
    reply: CommentReply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a reply to an existing comment.
    """
    try:
        # First verify the parent comment exists
        parent_comment = await comment_service.get_comment(db, comment_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found"
            )
        
        # Create the reply
        return await comment_service.reply_to_comment(
            db, 
            parent_comment_id=comment_id,
            reply_content=reply.content,
            post_id=reply.post_id,
            user_id=current_user.user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create reply: {str(e)}"
        )

@router.get("/post/{post_id}", response_model=List[CommentOut])
async def get_comments_by_post(
    post_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all root comments for a post with their replies.
    """
    try:
        comments = await comment_service.get_comments_by_post(db, post_id, skip, limit)
        return comments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get comments: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=List[CommentOut])
async def get_comments_by_user(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all comments created by a specific user.
    """
    try:
        comments = await comment_service.get_comments_by_user(db, user_id, skip, limit)
        return comments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get comments: {str(e)}"
        )

@router.get("/{comment_id}", response_model=CommentOut)
async def get_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific comment by ID with its replies.
    """
    try:
        comment = await comment_service.get_comment(db, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        return comment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get comment: {str(e)}"
        )

@router.get("/{comment_id}/replies", response_model=List[CommentOut])
async def get_replies_for_comment(
    comment_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all direct replies for a specific comment.
    Useful for paginated loading of comment replies.
    """
    try:
        # First verify the parent comment exists
        parent_comment = await comment_service.get_comment(db, comment_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Get the replies
        replies = await comment_service.get_replies_for_comment(db, comment_id, skip, limit)
        return replies
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get replies: {str(e)}"
        )

@router.patch("/{comment_id}", response_model=CommentOut)
async def update_comment(
    comment_id: UUID,
    comment_update: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a comment's content.
    Only the comment owner or superuser can update a comment.
    """
    try:
        db_comment = await comment_service.get_comment(db, comment_id)
        if not db_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Only allow comment owner or superuser to update
        if db_comment.user_id != current_user.user_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        return await comment_service.update_comment(db, db_comment, comment_update)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update comment: {str(e)}"
        )

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a comment.
    Only the comment owner or superuser can delete a comment.
    Deleting a comment also deletes all its replies.
    """
    try:
        db_comment = await comment_service.get_comment(db, comment_id)
        if not db_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Only allow comment owner or superuser to delete
        if db_comment.user_id != current_user.user_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        await comment_service.delete_comment(db, db_comment)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete comment: {str(e)}"
        )