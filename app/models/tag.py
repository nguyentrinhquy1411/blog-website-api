from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from .base import BaseModel

class Tag(BaseModel):
    __tablename__ = "tags"

    tag_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)

    # Relationships
    posts = relationship("Post", secondary="post_tags", back_populates="tags")
