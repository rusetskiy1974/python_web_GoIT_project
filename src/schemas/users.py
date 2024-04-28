import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


class UserDbSchema(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: str
    avatar: Optional[str] = None
    refresh_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    confirmed: bool
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(BaseModel):
    user: UserDbSchema
    detail: str = "User successfully created."


class UserCreateSchema(BaseModel):
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Пароль користувача")
    confirm_password: str = Field(..., description="Підтвердження пароля")

    @field_validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("Паролі не співпадають")
        return v


class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = Field(min_length=2, max_length=50)
    last_name: Optional[str] = Field(min_length=2, max_length=50)
    email: Optional[EmailStr]


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
