import tempfile

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from sqlalchemy import select
import requests
from PIL import Image
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse, FileResponse

from src.database.db import get_db
from src.models.models import Image, User
from src.repository import images as repository_images
from src.repository import transform as repository_transform
from src.conf.transform import TRANSFORM_METHOD
from src.schemas.transform import TransformedImageResponse, TransformedImageRequest
from src.services.auth import auth_service

router = APIRouter(prefix='/cloudinary_transform', tags=['cloudinary_transform'])

transform_list = list(TRANSFORM_METHOD.keys())


@router.post('/cloudinary_transform/{image_id}')
async def get_transform_image_from_cloudinary(
        method: str = Query(..., description=f"Allowed transform methods: {', '.join(TRANSFORM_METHOD.keys())}"),
        image_id: int = Path(ge=1),
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)):
    query = select(Image).filter_by(id=image_id)
    image = await repository_images.get_image(query, db)
    if image:
        response = requests.get(image.path, stream=True)
        if response.status_code == 200:
            if method not in TRANSFORM_METHOD.keys():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Method not found")

            transformed_image = await repository_transform.transform_image(image.path,
                                                                           transformation_options=TRANSFORM_METHOD[
                                                                               method])
            new_name = await repository_images.format_filename()
            r = cloudinary.uploader.upload(transformed_image, public_id=f'PhotoShareApp/{new_name}')
            image_path = cloudinary.CloudinaryImage(f'PhotoShareApp/{new_name}')
            image = await repository_images.create_upload_image(size=image.size, image_path=image_path.url,
                                                                title=f"{image.title} {method}", user=user, tag=None, db=db)

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
