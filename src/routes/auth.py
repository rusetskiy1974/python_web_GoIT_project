import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Security, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repository_users
from src.schemas.users import UserCreateSchema, UserUpdateSchema, TokenSchema, UserResponseSchema
from src.services.auth import auth_service
from src.services.email import send_email
from src.conf import messages

router = APIRouter(prefix="/auth", tags=["auth"])

get_refresh_token = HTTPBearer()


@router.post("/signup/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def signup(background_tasks: BackgroundTasks,request: Request, body: UserCreateSchema = Depends(),
                 db: AsyncSession = Depends(get_db)):
    exist_user = await repository_users.get_user_by_email(email=body.email, db=db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXISTS)
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db=db)
    background_tasks.add_task(send_email, new_user.email, new_user.fullname, str(request.base_url))
    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}



