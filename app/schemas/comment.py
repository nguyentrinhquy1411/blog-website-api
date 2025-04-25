from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, ForwardRef
from datetime import datetime
from uuid import UUID
from .user import UserOut

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    post_id: UUID
    parent_id: Optional[UUID] = None

# Specific schema for replying to a comment
class CommentReply(CommentBase):
    post_id: UUID  # Still needed to associate with the post

class CommentUpdate(BaseModel):
    content: Optional[str] = None

# Define a basic comment out without replies first
class CommentOutBase(CommentBase):
    comment_id: UUID
    post_id: UUID
    user_id: UUID
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    user: UserOut

    model_config = ConfigDict(from_attributes=True)

# Then the full CommentOut with replies
class CommentOut(CommentOutBase):
    replies: List['CommentOut'] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# Required for self-referencing model
CommentOut.model_rebuild()