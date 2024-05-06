import uuid
from pydantic import BaseModel, EmailStr

from src.models.models import Role


class UserStatusUpdate(BaseModel):
    email: EmailStr
    is_active: bool


class ImageRequest(BaseModel):
    image_id: int


class UserRoleUpdate(BaseModel):
    user_id: uuid.UUID
    role: Role
