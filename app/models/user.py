from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    bio = Column(Text)
    profile_picture = Column(String(255))
    is_active = Column(Boolean, server_default=text("true"))
    is_superuser = Column(Boolean, server_default=text("false"))

    # Relationships
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="user")
    media = relationship("Media", back_populates="user")