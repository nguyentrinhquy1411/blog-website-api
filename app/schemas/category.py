from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None

class CategoryOut(CategoryBase):
    category_id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime
    posts_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True) 