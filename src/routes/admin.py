import io
import os
from typing import Optional, List

import cloudinary
import cloudinary.uploader
import requests

from fastapi import UploadFile, APIRouter, HTTPException, status, Depends, File, Response, Form, Query, Path, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.database.db import get_db
from src.models.models import Image, User, Role
from src.conf.config import settings
from src.services.auth import auth_service
from src.schemas.image import ImageCreateSchema, ImageReadSchema, ImageUpdateSchema
from src.repository import images as repository_images
from src.services.roles import RolesAccess

router = APIRouter(prefix='/admins', tags=['admin'])

access_delete = RolesAccess([Role.admin])
access_update = RolesAccess([Role.admin, Role.moderator])


@router.delete('/delete/{image_id}', dependencies=[Depends(access_delete)], status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: int = Path(ge=1),
                       db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)

    if image:
        image_name = await repository_images.get_filename_from_cloudinary_url(image.path)
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            cloudinary.uploader.destroy(f'PhotoShareApp/{image_name}')
            await repository_images.delete_image_from_db(image, db)
            return {'ditail': f'Image successfully deleted'}
        else:
            await repository_images.delete_image_from_db(image, db)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.put('/update/{image_id}', dependencies=[Depends(access_update)], response_model=ImageReadSchema, status_code=status.HTTP_200_OK)
async def update_image(body: ImageUpdateSchema = Depends(),
                       db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=body.image_id)
    image = await repository_images.get_image(query, db)
    if image:
        image = await repository_images.update_image_title(image, body.title, db)
        return image
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
