
import cloudinary
from cloudinary.utils import cloudinary_url
from src.repository import images as repository_images

from src.conf.config import settings


async def transform_image(image_url, transformation_options=None):
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True)

    # Transform image in cloudinary
    # transformed_url = image_url
    name = await repository_images.get_filename_from_cloudinary_url(image_url)
    if transformation_options:
        transformed_url, options = cloudinary_url(f"PhotoShareApp/{name}", **transformation_options)
        print(transformed_url)
        return transformed_url
