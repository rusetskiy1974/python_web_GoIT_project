from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.schemas.user import UserReadSchema


class TagSchema(BaseModel):
    name: str


class ImageReadSchema(BaseModel):
    id: int
    path: str
    size: int
    title: str
    created_at: datetime
    count_tags: Optional[int] = 0
    tags: list[TagSchema]
    owner: UserReadSchema

    model_config = ConfigDict(from_attributes=True)


class ImageCreateSchema(BaseModel):
    path: str
    title: str
