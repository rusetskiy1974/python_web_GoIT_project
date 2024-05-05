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
from src.models.models import Image, User
from src.conf.config import settings
from src.services.auth import auth_service
from src.schemas.image import ImageCreateSchema, ImageReadSchema
from src.repository import images as repository_images
from src.services.role import RoleAccess

router = APIRouter(prefix='/images', tags=['image'])



cloudinary.config(
    cloud_name=settings.cloudinary_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True
)


@router.get('/tag', response_model=List[ImageReadSchema])
async def get_images_by_tag(tag_name: str = Query(description="Input tag", min_length=3, max_length=50),
                            limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                            db: AsyncSession = Depends(get_db)):
    images = await repository_images.get_images_by_tag(tag_name, limit, offset, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TAG NOT EXISTS")
    return images


@router.post('/add_tag/{image_id}', response_model=ImageReadSchema)
async def add_tag_to_image(image_id: int = Path(ge=1),
                           tag_name: str = Query(description="Input tag", min_length=3, max_length=50),
                           db: AsyncSession = Depends(get_db)):
    result = await repository_images.add_tag_to_image(image_id, tag_name, db)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IMAGE NOT EXISTS")
    return result


@router.get('/all', response_model=List[ImageReadSchema])
async def get_images(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                     db: AsyncSession = Depends(get_db)):
    query = select(Image).offset(offset).limit(limit)
    images = await repository_images.get_images(query, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return images


@router.post("/upload", response_model=ImageReadSchema, status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(..., description="The image file to upload"),
                       title: str = Form(min_length=3, max_length=50),
                       tag: Optional[str] = None,
                       user: User = Depends(auth_service.get_current_user),
                       db: AsyncSession = Depends(get_db)):
    new_name = await repository_images.format_filename()
    size_is_valid = await repository_images.get_file_size(file)
    file_is_valid = await repository_images.file_is_image(file)
    if size_is_valid > settings.max_image_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File too large. Max size is {settings.max_image_size} bytes")
    if not file_is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File is not an image. Only images are allowed")

    r = cloudinary.uploader.upload(file.file, public_id=f'PhotoShareApp/{new_name}', overwrite=True)
    print(r)
    image_path = cloudinary.CloudinaryImage(f'PhotoShareApp/{new_name}')
    image = await repository_images.create_upload_image(size=size_is_valid, image_path=image_path.url, title=title,
                                                        tag=tag, user=user, db=db)

    return image


@router.get('/get_image/{image_id}', response_model=ImageReadSchema, status_code=status.HTTP_200_OK)
async def download_image(image_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            return image
            # return StreamingResponse(response.iter_content(chunk_size=1024),
            #                          media_type=response.headers['content-type'])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.delete('/delete/{image_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: int = Path(ge=1),
                       user: User = Depends(auth_service.get_current_user),
                       db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id).filter_by(user_id=user.id)
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


@router.put('/update/{image_id}', response_model=ImageReadSchema, status_code=status.HTTP_200_OK)
async def update_image(image_id: int = Path(ge=1),
                       title: str = Form(min_length=3, max_length=50),
                       user: User = Depends(auth_service.get_current_user),
                       db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id).filter_by(user_id=user.id)
    image = await repository_images.get_image(query, db)
    if image:
        image = await repository_images.update_image_title(image, title, db)
        return image
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.get('/', response_model=list[ImageReadSchema])
async def get_images_by_user(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                             db: AsyncSession = Depends(get_db),
                             user: User = Depends(auth_service.get_current_user)):
    query = select(Image).filter_by(user_id=user.id).offset(offset).limit(limit)
    images = await repository_images.get_images(query, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return images
