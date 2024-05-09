from enum import IntEnum
from typing import Literal, Union

from fastapi import Query
from pydantic import BaseModel


class ImageRatingCreateSchema(BaseModel):
    image_id: int
    rating: int = Query(ge=1, le=5, description="Rating from 1 to 5")
