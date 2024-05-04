import uuid
from pydantic import BaseModel
from src.models.models import Role


class UserStatusUpdate(BaseModel):
    email: str
    is_active: bool

class ImageRequest(BaseModel):
    image_id: int

class UserRoleUpdate(BaseModel):
    user_id: uuid.UUID
    role: Role