from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func, expression
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
from sqlalchemy import text
from .post_category import post_categories  # Import the table
from .post_tag import post_tags  # Import the table


class Post(BaseModel):
    __tablename__ = "posts"

    post_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    is_published = Column(Boolean, server_default=text("false"))
    published_at = Column(DateTime(timezone=True))
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    categories = relationship("Category", secondary="post_categories", back_populates="posts")
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")
    media = relationship("Media", back_populates="post")