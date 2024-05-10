import uuid

from fastapi import Query
from pydantic import BaseModel, ConfigDict

from src.schemas.image import ImageReadSchema
from src.schemas.user import UserReadSchema


class ImageRatingReadSchema(BaseModel):
    id: int
    image_id: int
    rating: int
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ImageRatingCreateSchema(BaseModel):
    image_id: int
    rating: int = Query(ge=1, le=5, description="Rating from 1 to 5")
