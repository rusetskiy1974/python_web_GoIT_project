import string
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator, model_validator, root_validator
from pydantic.v1 import validator


class UserReadSchema(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserDbSchema(UserReadSchema):
    role: str
    avatar: Optional[str] = None
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
    password: str = Field(..., min_length=8, max_length=12)


class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = Field(min_length=2, max_length=50)
    last_name: Optional[str] = Field(min_length=2, max_length=50)
    email: Optional[EmailStr]


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class ConfirmationResponse(BaseModel):
    message: str


class LogoutResponseSchema(BaseModel):
    message: str


class RequestNewPassword(BaseModel):
    new_password: str = Field(min_length=8, max_length=12)
