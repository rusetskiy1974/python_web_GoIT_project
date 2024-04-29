from urllib import request

from fastapi import APIRouter, Depends, status, UploadFile, File, Request, BackgroundTasks, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader
from fastapi.templating import Jinja2Templates

from src.database.db import get_db
from src.models.models import User
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.conf.config import settings
from src.schemas.user import UserDbSchema, RequestEmail, RequestNewPassword
from src.services.email import send_email_reset_password

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="src/services/templates")


@router.get("/me/", response_model=UserDbSchema)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    return current_user


@router.patch('/avatar', response_model=UserDbSchema)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: AsyncSession = Depends(get_db)) -> User:
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'NotesApp/{current_user.fullname}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.fullname}') \
        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user


@router.post("/forgot_password")
async def forgot_password(background_tasks: BackgroundTasks,
                          request: Request,
                          body: RequestEmail = Depends(),
                          db: AsyncSession = Depends(get_db)) -> dict:
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user:
        background_tasks.add_task(send_email_reset_password, user.email, user.fullname, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.get("/reset_password/{token}")
async def reset_password(token: str,     # new_password: str = Query(min_length=8, max_length=12),
                         db: AsyncSession = Depends(get_db)) -> dict:
    email = await auth_service.get_email_from_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    def get_reset_password_page():
        return templates.TemplateResponse("reset_password.html", {"request": request})

    new_password = await auth_service.get_password_hash(get_reset_password_page())
    await repository_users.update_password(user, new_password, db)
    return {"message": "Password reset successfully"}
