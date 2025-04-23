from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from .user import UserOut
from .category import CategoryOut
from .tag import TagOut
from .media import MediaOut

class CategoryBase(BaseModel):
    name: str
    slug: str

    class Config:
        from_attributes = True

class CategoryForPost(CategoryBase):
    category_id: UUID

class PostBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PostCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    summary: Optional[str] = None
    is_published: bool = False
    category_ids: List[UUID] = []
    tag_ids: List[UUID] = []

    model_config = ConfigDict(from_attributes=True)

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    summary: Optional[str] = None
    is_published: Optional[bool] = None
    category_ids: Optional[List[UUID]] = None
    tag_ids: Optional[List[UUID]] = None

class PostOut(BaseModel):
    post_id: UUID
    title: str
    slug: str
    content: str
    summary: Optional[str] = None
    is_published: bool
    author_id: UUID
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    author: UserOut
    categories: List[CategoryOut] = []
    tags: List[TagOut] = []
    media: List[MediaOut] = []

    model_config = ConfigDict(from_attributes=True)
