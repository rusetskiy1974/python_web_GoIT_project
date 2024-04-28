import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator, model_validator
from pydantic.v1 import validator


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
    password: str = Field(..., min_length=8, max_length=12, description="Пароль користувача")
    confirm_password: str = Field(..., min_length=8, max_length=12, description="Підтвердіть пароль")
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    def passwords_match(cls, values):
        print(values)

        if values['password'] != values['confirm_password']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Паролі не співпадають')
        values.pop('confirm_password', None)
        print(values)
        return values

    # @classmethod
    # def parse_obj(cls, obj):
    #     obj = obj.copy()
    #     obj.pop("confirm_password", None)  # Видаляємо confirm_password з словника
    #     return super().parse_obj(obj)

    # @field_validator("password")
    # def check_password(cls, value):
    #     # Convert the password to a string if it is not already
    #     value = str(value)
    #
    #     # Check that the password meets the criteria
    #     if len(value) < 8:
    #         raise ValueError("Password must have at least 8 characters")
    #
    #     if not any(c.isupper() and c.islower() and c.isdigit() and c in string.punctuation for c in value):
    #         raise ValueError("Password must have at least one uppercase letter, one lowercase letter, and one digit")
    #
    #     return value

    # @validator('password')
    # def passwords_match(self, v, values, **kwargs):
    #     confirm_password = values.get('confirm_password')
    #     if confirm_password and v != confirm_password:
    #         raise ValueError('Паролі не співпадають')
    #     return v


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
