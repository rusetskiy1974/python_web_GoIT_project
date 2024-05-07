import cloudinary
import cloudinary.uploader

from fastapi import APIRouter, Depends, HTTPException, status
from io import BytesIO

from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.models.models import Image, User
from src.repository import images as repository_images
from src.repository import transform as repository_transform
from sqlalchemy.ext.asyncio import AsyncSession
import requests
from starlette.responses import StreamingResponse
from src.conf.transform import TRANSFORM_METHOD
from src.schemas.transform import TransformedImageResponse, TransformedImageRequest
from src.services.auth import auth_service

router = APIRouter(prefix='/cloudinary_transform', tags=['cloudinary_transform'])

transform_list = list(TRANSFORM_METHOD.keys())


@router.post('/{image_id}', response_model=TransformedImageResponse, description='No more than 5 requests per minute',
             dependencies=[Depends(RateLimiter(times=5, seconds=60))])
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
    image = await repository_images.get_image(body.image_id, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
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

            response = requests.get(transformed_image, stream=True)

            qr_code = await repository_transform.generate_qr_code(transformed_image)
            qr_image_bytes_io = BytesIO()
            qr_code.save(qr_image_bytes_io, format="PNG")
            qr_image_bytes_io.seek(0)

            return StreamingResponse(qr_image_bytes_io, media_type="image/png")

        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
