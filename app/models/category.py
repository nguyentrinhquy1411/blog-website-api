from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from .base import BaseModel

class Category(BaseModel):
    __tablename__ = "categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    slug = Column(String(100), unique=True, nullable=False)

    # Relationships
    posts = relationship("Post", secondary="post_categories", back_populates="categories")
