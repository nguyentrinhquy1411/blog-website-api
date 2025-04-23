from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID

class MediaBase(BaseModel):
    file_name: str
    file_path: str
    mime_type: str

class MediaCreate(MediaBase):
    post_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

class MediaUpdate(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None

class MediaOut(MediaBase):
    media_id: UUID
    post_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 