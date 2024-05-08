import cloudinary
import cloudinary.uploader
import requests

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse

from src.conf.config import settings
from src.database.db import get_db
from src.models.models import User
from src.repository import images as repository_images
from src.repository import transform as repository_transform

from src.conf.transform import TRANSFORM_METHOD
from src.schemas.image import ImageReadSchema
from src.schemas.transform import TransformedImageRequest
from src.services.auth import auth_service

router = APIRouter(prefix='/cloudinary_transform', tags=['cloudinary_transform'])

transform_list = list(TRANSFORM_METHOD.keys())


@router.post('/{image_id}')
async def create_transformed_image(body: TransformedImageRequest = Depends(),
                                   user: User = Depends(auth_service.get_current_user),
                                   db: AsyncSession = Depends(get_db)):
    """
    The create_transformed_image function is used to create a transformed image.
    The function takes in the following parameters:
        body: TransformedImageRequest = Depends(),
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)

    :param body: TransformedImageRequest: Get the image_id and method from the request
    :param user: User: Get the current user from the database
    :param db: AsyncSession: Get the database session
    :return: A streaming response of the qr code, which is then displayed in the browser
    :doc-author: RSA
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )
    image = await repository_images.get_image(body.image_id, db)
    if image:
        try:
            # response = requests.get(image.path, stream=True)
            # if response.status_code == 200:
            if body.method not in TRANSFORM_METHOD.keys():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Method not found")

            transformed_image = await repository_transform.transform_image(image.path,
                                                                           transformation_options=TRANSFORM_METHOD[
                                                                               body.method])
            new_name = await repository_images.format_filename()
            r = cloudinary.uploader.upload(transformed_image, public_id=f'PhotoShareApp/{new_name}')
            image_path = cloudinary.CloudinaryImage(f'PhotoShareApp/{new_name}')
            image = await repository_images.create_image(size=image.size,
                                                         image_path=image_path.url,
                                                         title=f"{image.title} {body.method}",
                                                         user=user,
                                                         tag=None,
                                                         db=db)

            qr_code = await repository_transform.generate_qr_code(transformed_image)
            qr_code.save("qr_code.png")
            return FileResponse("qr_code.png")
            # else:
            #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
