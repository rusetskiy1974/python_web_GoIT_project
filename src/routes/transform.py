from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select

from src.database.db import get_db
from src.models.models import Image, Role
from src.repository import images as repository_images
from src.repository import transform as repository_transform
from sqlalchemy.ext.asyncio import AsyncSession
import requests
from starlette.responses import StreamingResponse
from src.services.role import RoleAccess

router = APIRouter(prefix='/cloudinary_transform', tags=['cloudinary_transform'])
role_user = RoleAccess([Role.user])


@router.get('/cloudinary_angle/{image_id}', dependencies=[Depends(role_user)])
async def get_transform_image_from_cloudinary_angle(image_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            transformed_image = await repository_transform.transform_image(image.path, transformation_options={
                'format': 'jpg',
                'angle': 45,
                'background': 'blue',
                'width': 300,
                'height': 300,
                'crop': 'scale'
            })
            response = requests.get(transformed_image, stream=True)
            return StreamingResponse(response.iter_content(chunk_size=1024),
                                     media_type=response.headers['content-type'])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.get('/cloudinary_sepia/{image_id}', dependencies=[Depends(role_user)])
async def get_transform_image_from_cloudinary_sepia(image_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            transformed_image = await repository_transform.transform_image(image.path, transformation_options={
                'format': 'jpg',
                'group': 'fill',
                'width': 300,
                'height': 300,
                'radius': 20,
                'effect': 'sepia'
            })
            response = requests.get(transformed_image, stream=True)
            return StreamingResponse(response.iter_content(chunk_size=1024),
                                     media_type=response.headers['content-type'])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.get('/cloudinary_radius/{image_id}', dependencies=[Depends(role_user)])
async def get_transform_image_from_cloudinary_radius(image_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            transformed_image = await repository_transform.transform_image(image.path, transformation_options={
                'format': 'jpg',
                'width': 300,  # Нова ширина зображення
                'height': 300,  # Нова висота зображення
                'crop': 'fill',  # Обрізка до заданих розмірів зі збереженням пропорцій
                'gravity': 'face',  # Вирівнювання по обличчю
                'radius': 'max',  # Максимальний радіус для круглого вирізу
                'fetch_format': 'auto'  # Автоматичне визначення формату зображення
            })
            response = requests.get(transformed_image, stream=True)
            return StreamingResponse(response.iter_content(chunk_size=1024),
                                     media_type=response.headers['content-type'])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.get('/cloudinary_black_white/{image_id}', dependencies=[Depends(role_user)])
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
                'height': 300,  # Новая высота изображения
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


@router.get('/cloudinary_pixelate/{image_id}', dependencies=[Depends(role_user)])
async def get_transform_image_from_cloudinary_pixelate(image_id: int = Path(ge=1),
                                                         db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            transformed_image = await repository_transform.transform_image(image.path, transformation_options={
                'format': 'jpg',
                'width': 300,  # Нова ширина зображення
                'height': 200,  # Нова висота зображення
                'crop': 'fill',  # Обрізка до заданих розмірів зі збереженням пропорцій
                'gravity': 'face',  # Вирівнювання по обличчю
                'effect': 'pixelate:5',  # Ефект мозаїки з коефіцієнтом 5
                'fetch_format': 'auto'
            })

            response = requests.get(transformed_image, stream=True)
            return StreamingResponse(response.iter_content(chunk_size=1024),
                                     media_type=response.headers['content-type'])
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
