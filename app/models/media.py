from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from .base import BaseModel

class Media(BaseModel):
    __tablename__ = "media"

    media_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Foreign keys
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.post_id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    # Relationships
    post = relationship("Post", back_populates="media")
    user = relationship("User", back_populates="media") 