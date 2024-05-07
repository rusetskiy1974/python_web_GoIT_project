from urllib import request

from fastapi import APIRouter, Depends, status, UploadFile, File, Request, BackgroundTasks, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

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
    """
    The read_users_me function is a GET endpoint that returns the current user's information.
    It uses the auth_service to get the current user, and then returns it.

    :param current_user: User: Get the current user
    :return: The current user
    :doc-author: RSA
    """
    return current_user


@router.patch('/avatar', response_model=UserDbSchema)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: AsyncSession = Depends(get_db)) -> User:
    """
    The update_avatar_user function is used to update the avatar of a user.
    The function takes in an UploadFile object, which contains the file that will be uploaded to Cloudinary.
    It also takes in a User object, which represents the current user who is logged into their account and making this request.
    Finally it takes in an AsyncSession object, which represents our database session for interacting with our PostgreSQL database.

    :param file: UploadFile: Get the file that is being uploaded
    :param current_user: User: Get the current user from the database
    :param db: AsyncSession: Get the database session
    :return: A user object
    :doc-author: RSA
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'PhotoShareApp/{current_user.fullname}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'PhotoSharesApp/{current_user.fullname}') \
        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user


@router.post("/forgot_password")
async def forgot_password(background_tasks: BackgroundTasks,
                          request: Request,
                          body: RequestEmail = Depends(),
                          db: AsyncSession = Depends(get_db)) -> dict:
    """
    The forgot_password function is used to send an email to the user with a link
    to reset their password. The function takes in the request object, which contains
    the base_url of the application, and a body containing an email address. It then
    uses this information to create a task that will be executed by Celery.

    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url of the application
    :param body: RequestEmail: Get the email from the request
    :param db: AsyncSession: Get the database session
    :return: A json response with a message
    :doc-author: RSA
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user:
        background_tasks.add_task(send_email_reset_password, user.email, user.fullname, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.post("/reset_password/{token}")
async def reset_password(token:  str,
                         request_: Request,
                         db: AsyncSession = Depends(get_db)) -> dict:
    """
    The reset_password function is used to reset a user's password.
    It takes in the token that was sent to the user's email address, and then it uses that token
    to get the email of the user who requested a password reset. It then gets that user from
    the database, hashes their new password, and updates their account with this new hashed
    password.

    :param token:  str: Get the token from the url
    :param request_: Request: Get the form data from the request
    :param db: AsyncSession: Pass the database session to the function
    :return: A dict object
    :doc-author: RSA
    """
    form_data = await request_.form()
    new_password = form_data["new_password"]
    email = await auth_service.get_email_from_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_password = await auth_service.get_password_hash(new_password)
    await repository_users.update_password(user, new_password, db)
    return {"message": "Password reset successfully"}


@router.get("/reset_password/{token}", response_class=HTMLResponse)
async def get_reset_password_page(token: str, request_: Request):
    """
    The get_reset_password_page function is a GET request that returns the reset_password.html page,
    which allows users to enter their new password and confirm it.

    :param token: str: Pass the token to the reset_password
    :param request_: Request: Pass the request object to the template
    :return: A templateresponse object
    :doc-author: RSA
    """
    return templates.TemplateResponse("reset_password.html", {"request": request_, "token": token})
