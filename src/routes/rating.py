from typing import Optional, List

import cloudinary
import cloudinary.uploader
import requests
from PIL import Image

from fastapi import UploadFile, APIRouter, HTTPException, status, Depends, File, Form, Query, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse, FileResponse

from src.database.db import get_db
from src.models.models import User, Role
from src.conf.config import settings
from src.services.auth import auth_service
from src.schemas.image import ImageCreateSchema, ImageReadSchema, ImageUpdateSchema
from src.repository import images as repository_images
from src.repository import ratings as repository_rating
from src.services.role import RoleAccess
from src.schemas.rating import ImageRatingCreateSchema, ImageRatingReadSchema

router = APIRouter(prefix="/rating", tags=["image_rating"])

role_admin_moderator = RoleAccess([Role.admin, Role.moderator])


@router.get("/all", response_model=List[ImageRatingReadSchema],
            dependencies=[Depends(role_admin_moderator)],
            status_code=status.HTTP_200_OK, )
async def get_all_ratings(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                          db: AsyncSession = Depends(get_db)):
    ratings = await repository_rating.get_all_ratings(limit, offset, db)
    return ratings


@router.delete("/{rating_id}", response_model=ImageReadSchema, dependencies=[Depends(role_admin_moderator)],
               status_code=status.HTTP_200_OK)
async def delete_rating(rating_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    rating = await repository_rating.get_rating(rating_id, db)
    if rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
    return await repository_rating.delete_rating(rating, db)


@router.post("/{image_id}", response_model=ImageReadSchema, status_code=status.HTTP_200_OK)
async def rate_image(body: ImageRatingCreateSchema = Depends(), user: User = Depends(auth_service.get_current_user),
                     db: AsyncSession = Depends(get_db)):
    image = await repository_images.get_image(body.image_id, db)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    image_rating = await repository_rating.rate_image(image, body.rating, user.id, db)
    return image_rating
