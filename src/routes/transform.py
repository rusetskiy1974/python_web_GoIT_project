from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select

from src.database.db import get_db
from src.models.models import Image
from src.repository import images as repository_images
from src.repository import transform as repository_transform
from sqlalchemy.ext.asyncio import AsyncSession
import requests
from starlette.responses import StreamingResponse

router = APIRouter(prefix='/cloudinary_transform', tags=['cloudinary_transform'])


@router.get('/cloudinary_degrees/{image_id}')
async def get_transform_image_from_cloudinary_degrees(image_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            transformed_image = await repository_transform.transform_image(image.path, transformation_options={
                'format': 'jpg',
                'angle': 45,
                'background': 'blue',
                'crop': 'scale',
                'mode': 'preserve'
            })
            response = requests.get(transformed_image, stream=True)
            return StreamingResponse(response.iter_content(chunk_size=1024),
                                     media_type=response.headers['content-type'])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.get('/cloudinary_ratio/{image_id}')
async def get_transform_image_from_cloudinary_ratio():
    pass


@router.get('/cloudinary_blurred/{image_id}')
async def get_transform_image_from_cloudinary_blured():
    pass


@router.get('/cloudinary_gen_fill/{image_id}')
async def get_transform_image_from_cloudinary_gen_fill():
    pass


@router.get('/cloudinary_black_white/{image_id}')
async def get_transform_image_from_cloudinary_black_white(image_id: int = Path(ge=1),
                                                          db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            transformed_image = await repository_transform.transform_image(image.path, transformation_options={
                'format': 'jpg',
                'effect': 'grayscale',
                'width': 300,
                'height': 200,  # Новая высота изображения
                'crop': 'fill',  # Заполнение области изображения
                'gravity': 'center',  # Выравнивание по центру
                'border': '5px_solid_red'
            })

            response = requests.get(transformed_image, stream=True)
            return StreamingResponse(response.iter_content(chunk_size=1024),
                                     media_type=response.headers['content-type'])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.get('/cloudinary_blur_faces/{image_id}')
async def get_transform_image_from_cloudinary_blur_faces():
    pass
