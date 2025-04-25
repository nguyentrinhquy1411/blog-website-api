from sqlalchemy import Column, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship, backref
from .base import BaseModel

class Comment(BaseModel):
    __tablename__ = "comments"

    comment_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    content = Column(Text, nullable=False)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.comment_id", ondelete="CASCADE"), nullable=True)

    # Relationships
    replies = relationship(
        "Comment",
        backref=backref("parent", remote_side=[comment_id]),
        cascade="all, delete",
        passive_deletes=True
    )
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
