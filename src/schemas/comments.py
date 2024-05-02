from datetime import date, datetime
from pydantic import Field, EmailStr, BaseModel, field_validator, ConfigDict

from src.schemas.user import UserReadSchema
from src.schemas.image import ImageReadSchema

class CommentCreateSchema(BaseModel):
    image_id: int
    text: str= Field(min_length=2, max_length=255)


class CommentResponseShema(BaseModel):
    id: int
    text: str
    created_at: datetime
    updated_at: datetime
    image_id: int
    user: UserReadSchema


class CommentResponseShemaLight(BaseModel):
    id: int
    text: str
    created_at: datetime
    updated_at: datetime
    image_id: int


class CommentUpdateSchema(BaseModel):
    pass
