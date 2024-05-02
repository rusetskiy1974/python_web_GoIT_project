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
from src.schemas.comments import CommentCreateSchema, CommentResponseShema
from src.repository import comments as repository_comments

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post('/', response_model=CommentResponseShema, status_code=status.HTTP_201_CREATED)
async def create_comment(image_id: int,
                         text: str,
                         db: AsyncSession = Depends(get_db), 
                         user = Depends(auth_service.get_current_user)
                         ):
    comment = await repository_comments.create_comment(image_id, text, db, user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Oooops")
    return comment