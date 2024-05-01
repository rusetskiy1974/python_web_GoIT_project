from typing import Optional, List
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from src.models.models import Tag
from src.schemas.user import UserDbSchema, UserReadSchema


class ImageReadSchema(BaseModel):
    id: int
    path: str
    size: int
    title: str
    created_at: datetime
    count_tags: Optional[int] = 0
    owner: UserReadSchema

    model_config = ConfigDict(from_attributes=True)


class ImageCreateSchema(BaseModel):
    path: str
    title: str


