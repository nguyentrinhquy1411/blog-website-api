from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from .base import BaseModel

# Define the association table
post_tags = Table(
    "post_tags",
    BaseModel.metadata,
    Column("post_id", UUID(as_uuid=True), ForeignKey("posts.post_id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.tag_id"), primary_key=True),
    Column("created_at", BaseModel.created_at.type, server_default=text("CURRENT_TIMESTAMP"))
)
