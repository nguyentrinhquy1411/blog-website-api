from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class TagBase(BaseModel):
    name: str = Field(..., max_length=50)

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)

class TagOut(TagBase):
    tag_id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

