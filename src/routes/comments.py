from urllib import request

from fastapi import APIRouter, Depends, status, UploadFile, File, Request, BackgroundTasks, HTTPException, Query
from sqlalchemy import Enum
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from src.database.db import get_db
from src.models.models import User, Role
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.conf.config import settings
from src.schemas.user import UserDbSchema, RequestEmail, RequestNewPassword
from src.services.email import send_email_reset_password
from src.schemas.comments import CommentCreateSchema, CommentResponseShema, CommentUpdateSchema, \
    CommentResponseShemaLight
from src.repository import comments as repository_comments

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post('/', response_model=CommentResponseShema, status_code=status.HTTP_201_CREATED)
async def create_comment(image_id: int,
                         text: str,
                         db: AsyncSession = Depends(get_db),
                         user=Depends(auth_service.get_current_user)
                         ):
    comment = await repository_comments.create_comment(image_id, text, db, user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Oooops")
    return comment


@router.get('/all', response_model=list[CommentResponseShemaLight])
async def get_comments(
        image_id: int,
        limit: int = Query(10, ge=10, le=500),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db)
):
    comments = await repository_comments.get_comments(image_id, limit, offset, db)
    return comments


@router.put("/{comment_id}", response_model=CommentResponseShema)
async def update_comment(comment_id: int,
                         text: str,
                         db: AsyncSession = Depends(get_db),
                         user=Depends(auth_service.get_current_user)
                         ):
    comment = await repository_comments.update_contact(comment_id, text, db, user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)
                         ):
    if user.role == Role.user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="U cann't do it")
    comment = await repository_comments.delete_comment(comment_id, db, user)
    return comment
